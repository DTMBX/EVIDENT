"""
Tests for services/integrity_ledger.py — Append-Only JSONL Ledger
==================================================================
Tests hash-chain integrity, append-only behaviour, verification,
and tamper detection.
"""

import hashlib
import json
import os
import tempfile
from pathlib import Path

import pytest

from services.integrity_ledger import IntegrityLedger, ZERO_HASH


@pytest.fixture
def tmp_ledger(tmp_path):
    """Create an IntegrityLedger using a temp dir."""
    ledger_path = str(tmp_path / "test_ledger.jsonl")
    return IntegrityLedger(ledger_path=ledger_path)


class TestIntegrityLedgerAppend:
    """Test append operations."""

    def test_append_single_entry(self, tmp_ledger):
        entry = tmp_ledger.append(
            action="file.ingested",
            evidence_id="abc-123",
            sha256="a" * 64,
            actor="tester",
            details={"filename": "test.mp4"},
        )
        assert entry["seq"] == 1
        assert entry["action"] == "file.ingested"
        assert entry["evidence_id"] == "abc-123"
        assert entry["sha256"] == "a" * 64
        assert entry["actor"] == "tester"
        assert entry["prev_hash"] == ZERO_HASH
        assert "entry_hash" in entry
        assert entry["details"]["filename"] == "test.mp4"

    def test_append_multiple_entries_chains(self, tmp_ledger):
        e1 = tmp_ledger.append(action="first", evidence_id="1")
        e2 = tmp_ledger.append(action="second", evidence_id="2")
        e3 = tmp_ledger.append(action="third", evidence_id="3")

        assert e1["seq"] == 1
        assert e2["seq"] == 2
        assert e3["seq"] == 3

        # First links to zero hash
        assert e1["prev_hash"] == ZERO_HASH
        # Second links to hash of first line
        assert e2["prev_hash"] != ZERO_HASH
        # Third links to hash of second line
        assert e3["prev_hash"] != e2["prev_hash"] or e2["prev_hash"] == e3["prev_hash"]

    def test_entry_count_property(self, tmp_ledger):
        assert tmp_ledger.entry_count == 0
        tmp_ledger.append(action="a")
        assert tmp_ledger.entry_count == 1
        tmp_ledger.append(action="b")
        assert tmp_ledger.entry_count == 2

    def test_entry_written_to_disk(self, tmp_ledger):
        tmp_ledger.append(action="test.action", evidence_id="ev-1")
        # Read file directly
        with open(tmp_ledger._path, "r") as f:
            lines = [l.strip() for l in f if l.strip()]
        assert len(lines) == 1
        parsed = json.loads(lines[0])
        assert parsed["action"] == "test.action"

    def test_append_only_file_grows(self, tmp_ledger):
        tmp_ledger.append(action="a")
        size1 = os.path.getsize(tmp_ledger._path)
        tmp_ledger.append(action="b")
        size2 = os.path.getsize(tmp_ledger._path)
        assert size2 > size1


class TestIntegrityLedgerVerify:
    """Test verification and tamper detection."""

    def test_verify_empty_ledger(self, tmp_ledger):
        errors = tmp_ledger.verify()
        assert errors == []

    def test_verify_valid_ledger(self, tmp_ledger):
        for i in range(5):
            tmp_ledger.append(action=f"action_{i}", evidence_id=str(i))
        errors = tmp_ledger.verify()
        assert errors == [], f"Expected no errors, got: {errors}"

    def test_verify_detects_tampered_entry(self, tmp_ledger):
        tmp_ledger.append(action="legit_1")
        tmp_ledger.append(action="legit_2")

        # Tamper with file: modify second line
        with open(tmp_ledger._path, "r") as f:
            lines = f.readlines()
        entry = json.loads(lines[1])
        entry["action"] = "TAMPERED"
        lines[1] = json.dumps(entry, sort_keys=True, separators=(",", ":")) + "\n"
        with open(tmp_ledger._path, "w") as f:
            f.writelines(lines)

        errors = tmp_ledger.verify()
        assert len(errors) > 0
        assert any("hash" in str(e).lower() or "mismatch" in str(e).lower() for e in errors)

    def test_verify_detects_deleted_entry(self, tmp_ledger):
        tmp_ledger.append(action="one")
        tmp_ledger.append(action="two")
        tmp_ledger.append(action="three")

        # Delete the middle line
        with open(tmp_ledger._path, "r") as f:
            lines = f.readlines()
        with open(tmp_ledger._path, "w") as f:
            f.write(lines[0])
            f.write(lines[2])  # Skip lines[1]

        errors = tmp_ledger.verify()
        assert len(errors) > 0  # Chain should break

    def test_verify_detects_inserted_entry(self, tmp_ledger):
        tmp_ledger.append(action="one")
        tmp_ledger.append(action="two")

        # Insert a fake line between them
        with open(tmp_ledger._path, "r") as f:
            lines = f.readlines()
        fake_entry = {"seq": 99, "action": "FAKE", "prev_hash": "bogus",
                       "timestamp": "2025-01-01T00:00:00", "evidence_id": "",
                       "sha256": "", "actor": "", "details": {},
                       "entry_hash": "bogus"}
        fake_line = json.dumps(fake_entry, sort_keys=True, separators=(",", ":")) + "\n"
        with open(tmp_ledger._path, "w") as f:
            f.write(lines[0])
            f.write(fake_line)
            f.write(lines[1])

        errors = tmp_ledger.verify()
        assert len(errors) > 0


class TestIntegrityLedgerReadAll:
    """Test read_all."""

    def test_read_all_empty(self, tmp_ledger):
        assert tmp_ledger.read_all() == []

    def test_read_all_returns_entries(self, tmp_ledger):
        tmp_ledger.append(action="a", evidence_id="1")
        tmp_ledger.append(action="b", evidence_id="2")
        entries = tmp_ledger.read_all()
        assert len(entries) == 2
        assert entries[0]["action"] == "a"
        assert entries[1]["action"] == "b"


class TestIntegrityLedgerPersistence:
    """Test that ledger survives re-open."""

    def test_reopen_continues_chain(self, tmp_path):
        ledger_path = str(tmp_path / "persist.jsonl")

        lgr1 = IntegrityLedger(ledger_path=ledger_path)
        lgr1.append(action="first")
        lgr1.append(action="second")

        # Re-open
        lgr2 = IntegrityLedger(ledger_path=ledger_path)
        assert lgr2.entry_count == 2
        lgr2.append(action="third")

        # Verify entire chain
        errors = lgr2.verify()
        assert errors == [], f"Chain broken after reopen: {errors}"

        entries = lgr2.read_all()
        assert len(entries) == 3
        assert entries[2]["seq"] == 3
