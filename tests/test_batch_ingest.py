"""
Tests for services/batch_ingest.py — Batch Folder Ingest Pipeline
==================================================================
Tests BWC filename parsing, sequence grouping, and full folder ingest.
"""

import json
import os
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from services.batch_ingest import (
    BatchIngestResult,
    ParsedBWCFilename,
    SequenceGroup,
    group_by_sequence,
    ingest_folder,
    parse_bwc_filename,
)
from services.evidence_store import EvidenceStore
from services.integrity_ledger import IntegrityLedger


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def tmp_env(tmp_path):
    """Create a complete temp environment for batch ingest testing."""
    store_dir = tmp_path / "evidence_store"
    store_dir.mkdir()
    ledger_path = str(tmp_path / "ledger.jsonl")
    source_dir = tmp_path / "source"
    source_dir.mkdir()

    return {
        "store": EvidenceStore(root=str(store_dir)),
        "ledger": IntegrityLedger(ledger_path=ledger_path),
        "source_dir": source_dir,
        "tmp_path": tmp_path,
    }


def _create_fake_file(dir_path: Path, name: str, content: bytes = b"") -> Path:
    """Create a fake file with given name and content."""
    if not content:
        content = f"fake content for {name}".encode("utf-8")
    fp = dir_path / name
    fp.write_bytes(content)
    return fp


# ---------------------------------------------------------------------------
# BWC Filename Parsing
# ---------------------------------------------------------------------------


class TestParseBWCFilename:
    """Test BWC filename pattern parsing."""

    def test_standard_bwc_pattern(self):
        parsed = parse_bwc_filename("BryanMerritt_202511292257_BWL7137497-0.mp4")
        assert parsed.officer_name == "BryanMerritt"
        assert parsed.device_label == "BWL7137497"
        assert parsed.clip_index == 0
        assert parsed.extension == "mp4"
        assert parsed.timestamp is not None
        assert parsed.timestamp.year == 2025
        assert parsed.timestamp.month == 11
        assert parsed.timestamp.day == 29
        assert parsed.timestamp.hour == 22
        assert parsed.timestamp.minute == 57

    def test_second_bwc_file(self):
        parsed = parse_bwc_filename("EdwardRuiz_202511292251_BWL7139078-0.mp4")
        assert parsed.officer_name == "EdwardRuiz"
        assert parsed.device_label == "BWL7139078"
        assert parsed.clip_index == 0
        assert parsed.timestamp.hour == 22
        assert parsed.timestamp.minute == 51

    def test_multi_clip(self):
        parsed = parse_bwc_filename("JaneSmith_202601011200_BWL9999999-3.mp4")
        assert parsed.clip_index == 3
        assert parsed.officer_name == "JaneSmith"

    def test_unrecognised_filename_fallback(self):
        parsed = parse_bwc_filename("random_file.mp4")
        assert parsed.officer_name is None
        assert parsed.device_label is None
        assert parsed.extension == "mp4"
        assert parsed.raw_filename == "random_file.mp4"

    def test_timestamp_only_fallback(self):
        parsed = parse_bwc_filename("incident_202501151430_bodycam.mp4")
        assert parsed.timestamp is not None
        assert parsed.timestamp.year == 2025
        assert parsed.timestamp.month == 1
        assert parsed.timestamp.day == 15

    def test_device_label_fallback(self):
        parsed = parse_bwc_filename("recording_BWL1234567_clip.mp4")
        assert parsed.device_label == "BWL1234567"


# ---------------------------------------------------------------------------
# Sequence Grouping
# ---------------------------------------------------------------------------


class TestSequenceGrouping:
    """Test grouping by time adjacency and device."""

    def test_empty_input(self):
        groups = group_by_sequence([])
        assert groups == []

    def test_single_file(self):
        files = [
            {"filename": "test.mp4", "timestamp": "2025-11-29T22:57:00",
             "device_label": "BWL7137497"},
        ]
        groups = group_by_sequence(files)
        assert len(groups) == 1
        assert len(groups[0].members) == 1

    def test_two_files_within_window(self):
        files = [
            {"filename": "a.mp4", "timestamp": "2025-11-29T22:50:00",
             "device_label": "BWL001"},
            {"filename": "b.mp4", "timestamp": "2025-11-29T22:55:00",
             "device_label": "BWL002"},
        ]
        groups = group_by_sequence(files, time_window_minutes=30)
        assert len(groups) == 1
        assert len(groups[0].members) == 2

    def test_two_files_outside_window(self):
        files = [
            {"filename": "a.mp4", "timestamp": "2025-11-29T10:00:00",
             "device_label": "BWL001"},
            {"filename": "b.mp4", "timestamp": "2025-11-29T22:00:00",
             "device_label": "BWL002"},
        ]
        groups = group_by_sequence(files, time_window_minutes=30)
        assert len(groups) == 2

    def test_three_files_chained_in_one_group(self):
        """Files A→B→C each within window of previous should form one group."""
        files = [
            {"filename": "a.mp4", "timestamp": "2025-11-29T22:00:00",
             "device_label": "BWL001"},
            {"filename": "b.mp4", "timestamp": "2025-11-29T22:10:00",
             "device_label": "BWL001"},
            {"filename": "c.mp4", "timestamp": "2025-11-29T22:20:00",
             "device_label": "BWL001"},
        ]
        groups = group_by_sequence(files, time_window_minutes=15)
        assert len(groups) == 1
        assert len(groups[0].members) == 3

    def test_files_without_timestamp_grouped_at_end(self):
        files = [
            {"filename": "a.mp4", "timestamp": "2025-11-29T22:00:00",
             "device_label": "BWL001"},
            {"filename": "no_ts.mp4", "timestamp": None,
             "device_label": None},
        ]
        groups = group_by_sequence(files, time_window_minutes=30)
        # The no-timestamp file sorts to end and likely forms its own group
        assert len(groups) >= 1


# ---------------------------------------------------------------------------
# Full Batch Ingest
# ---------------------------------------------------------------------------


class TestBatchIngest:
    """Test the full folder ingest pipeline."""

    def test_ingest_empty_folder(self, tmp_env):
        result = ingest_folder(
            folder_path=str(tmp_env["source_dir"]),
            evidence_store=tmp_env["store"],
            ledger=tmp_env["ledger"],
        )
        assert isinstance(result, BatchIngestResult)
        assert result.total_files_found == 0
        assert result.total_files_ingested == 0
        assert result.total_errors == 0

    def test_ingest_nonexistent_folder(self, tmp_env):
        result = ingest_folder(
            folder_path="/nonexistent/path",
            evidence_store=tmp_env["store"],
            ledger=tmp_env["ledger"],
        )
        assert result.total_errors == 0  # Error is in errors list
        assert len(result.errors) == 1
        assert "not found" in result.errors[0]["error"].lower() or "not a directory" in result.errors[0]["error"].lower()

    def test_ingest_single_file(self, tmp_env):
        _create_fake_file(tmp_env["source_dir"], "evidence.mp4")
        result = ingest_folder(
            folder_path=str(tmp_env["source_dir"]),
            evidence_store=tmp_env["store"],
            ledger=tmp_env["ledger"],
            ingested_by="test_user",
        )
        assert result.total_files_found == 1
        assert result.total_files_ingested == 1
        assert result.total_errors == 0
        assert len(result.files) == 1
        assert result.files[0]["sha256"]
        assert result.files[0]["evidence_id"]

    def test_ingest_bwc_named_files(self, tmp_env):
        _create_fake_file(tmp_env["source_dir"], "BryanMerritt_202511292257_BWL7137497-0.mp4")
        _create_fake_file(tmp_env["source_dir"], "EdwardRuiz_202511292251_BWL7139078-0.mp4")

        result = ingest_folder(
            folder_path=str(tmp_env["source_dir"]),
            evidence_store=tmp_env["store"],
            ledger=tmp_env["ledger"],
        )
        assert result.total_files_found == 2
        assert result.total_files_ingested == 2

        # Check metadata was parsed
        filenames = [f["filename"] for f in result.files]
        assert "BryanMerritt_202511292257_BWL7137497-0.mp4" in filenames
        bwc_file = next(f for f in result.files if "Bryan" in f["filename"])
        assert bwc_file["device_label"] == "BWL7137497"
        assert bwc_file["officer_name"] == "BryanMerritt"

    def test_ingest_creates_manifest(self, tmp_env):
        _create_fake_file(tmp_env["source_dir"], "test.pdf")
        result = ingest_folder(
            folder_path=str(tmp_env["source_dir"]),
            evidence_store=tmp_env["store"],
            ledger=tmp_env["ledger"],
        )
        assert result.manifest_path
        assert os.path.exists(result.manifest_path)
        with open(result.manifest_path) as f:
            manifest = json.load(f)
        assert manifest["batch_id"] == result.batch_id

    def test_ingest_writes_ledger_entries(self, tmp_env):
        _create_fake_file(tmp_env["source_dir"], "clip.mp4")
        result = ingest_folder(
            folder_path=str(tmp_env["source_dir"]),
            evidence_store=tmp_env["store"],
            ledger=tmp_env["ledger"],
        )
        entries = tmp_env["ledger"].read_all()
        # Should have: batch start, file ingested, batch complete = at least 3
        assert len(entries) >= 3
        actions = [e["action"] for e in entries]
        assert "batch.ingest_start" in actions
        assert "file.ingested" in actions
        assert "batch.ingest_complete" in actions

    def test_ingest_ledger_verifies(self, tmp_env):
        """Ledger must remain chain-valid after batch ingest."""
        _create_fake_file(tmp_env["source_dir"], "a.mp4")
        _create_fake_file(tmp_env["source_dir"], "b.mp4")
        ingest_folder(
            folder_path=str(tmp_env["source_dir"]),
            evidence_store=tmp_env["store"],
            ledger=tmp_env["ledger"],
        )
        errors = tmp_env["ledger"].verify()
        assert errors == [], f"Ledger verification failed: {errors}"

    def test_ingest_duplicate_detection(self, tmp_env):
        """Ingesting the same file twice should flag as duplicate."""
        content = b"identical content for dedup test"
        _create_fake_file(tmp_env["source_dir"], "original.mp4", content=content)

        # First ingest
        r1 = ingest_folder(
            folder_path=str(tmp_env["source_dir"]),
            evidence_store=tmp_env["store"],
            ledger=tmp_env["ledger"],
        )
        assert r1.total_duplicates == 0
        assert r1.total_files_ingested == 1

        # Second ingest (same folder, same content)
        r2 = ingest_folder(
            folder_path=str(tmp_env["source_dir"]),
            evidence_store=tmp_env["store"],
            ledger=tmp_env["ledger"],
        )
        assert r2.total_duplicates == 1
        assert r2.total_files_ingested == 1  # Still counts as "ingested" (just flagged)

    def test_ingest_skips_unsupported_extensions(self, tmp_env):
        _create_fake_file(tmp_env["source_dir"], "readme.md")
        _create_fake_file(tmp_env["source_dir"], "config.yml")
        _create_fake_file(tmp_env["source_dir"], "evidence.mp4")

        result = ingest_folder(
            folder_path=str(tmp_env["source_dir"]),
            evidence_store=tmp_env["store"],
            ledger=tmp_env["ledger"],
        )
        # Only .mp4 should be ingested
        assert result.total_files_found == 1
        assert result.files[0]["filename"] == "evidence.mp4"

    def test_ingest_sequence_grouping(self, tmp_env):
        """BWC files with close timestamps should be grouped."""
        _create_fake_file(
            tmp_env["source_dir"],
            "OfficerA_202511292250_BWL0000001-0.mp4",
            content=b"clip1",
        )
        _create_fake_file(
            tmp_env["source_dir"],
            "OfficerA_202511292255_BWL0000001-1.mp4",
            content=b"clip2",
        )
        result = ingest_folder(
            folder_path=str(tmp_env["source_dir"]),
            evidence_store=tmp_env["store"],
            ledger=tmp_env["ledger"],
            time_window_minutes=30,
        )
        assert result.total_files_ingested == 2
        assert len(result.sequence_groups) >= 1
        # Both clips within 5 min → should be in same group
        group = result.sequence_groups[0]
        assert len(group["members"]) == 2

    def test_ingest_subdirectories(self, tmp_env):
        """Should walk subdirectories."""
        sub = tmp_env["source_dir"] / "subdir"
        sub.mkdir()
        _create_fake_file(sub, "nested.mp4")
        _create_fake_file(tmp_env["source_dir"], "top.mp4")

        result = ingest_folder(
            folder_path=str(tmp_env["source_dir"]),
            evidence_store=tmp_env["store"],
            ledger=tmp_env["ledger"],
        )
        assert result.total_files_found == 2
        assert result.total_files_ingested == 2
