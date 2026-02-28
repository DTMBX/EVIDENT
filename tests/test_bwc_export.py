"""
Tests for B30 Phase 7 — BWC Case Export & Compression
=====================================================
Validates:
  - Deterministic ZIP naming
  - Size tier classification
  - Original and derivative packing
  - Ledger extract inclusion
  - Search index snapshot filtering
  - Manifest integrity (SHA-256 for every file)
  - Integrity report generation
  - Empty / missing evidence handling
  - Ledger recording of export events
"""

import hashlib
import json
import os
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from services.bwc_export import (
    BWCCaseExporter,
    BWCExportResult,
    TIER_SMALL_MAX,
    TIER_MEDIUM_MAX,
    _compute_sha256,
    _size_tier,
)
from services.integrity_ledger import IntegrityLedger


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def evidence_store(tmp_path):
    """Create a minimal evidence_store layout with two evidence items."""
    store = tmp_path / "evidence_store"
    (store / "originals").mkdir(parents=True)
    (store / "manifests").mkdir(parents=True)
    (store / "derivatives").mkdir(parents=True)

    items = {}
    for idx, (eid, filename, content) in enumerate([
        ("ev-001", "officer_20240101_cam1-001.mp4", b"FAKE_VIDEO_CONTENT_001"),
        ("ev-002", "officer_20240101_cam1-002.mp4", b"FAKE_VIDEO_CONTENT_002"),
    ]):
        sha = hashlib.sha256(content).hexdigest()

        # Original file (stored by sha256 name)
        orig_path = store / "originals" / sha
        orig_path.write_bytes(content)

        # Manifest
        manifest = {
            "evidence_id": eid,
            "sha256": sha,
            "original_filename": filename,
        }
        (store / "manifests" / f"{eid}.json").write_text(
            json.dumps(manifest), encoding="utf-8"
        )

        # Derivatives (thumbnail)
        deriv_dir = store / "derivatives" / sha / "thumbnail"
        deriv_dir.mkdir(parents=True)
        thumb_content = b"FAKE_THUMB_" + str(idx).encode()
        (deriv_dir / "thumb.jpg").write_bytes(thumb_content)

        items[eid] = {"sha256": sha, "filename": filename}

    return store, items


@pytest.fixture
def ledger(tmp_path):
    """Create an integrity ledger with some pre-existing entries."""
    ledger_path = str(tmp_path / "test_ledger.jsonl")
    lg = IntegrityLedger(ledger_path=ledger_path)
    # Simulate prior ingest entries
    lg.append(action="INGEST", evidence_id="ev-001", sha256="aaa", actor="system")
    lg.append(action="INGEST", evidence_id="ev-002", sha256="bbb", actor="system")
    lg.append(action="NORMALIZE", evidence_id="ev-001", sha256="ccc", actor="system")
    return lg


@pytest.fixture
def export_dir(tmp_path):
    d = tmp_path / "exports"
    d.mkdir()
    return d


@pytest.fixture
def exporter(evidence_store, export_dir, ledger):
    store_path, _ = evidence_store
    return BWCCaseExporter(
        evidence_base=str(store_path),
        export_dir=str(export_dir),
        ledger=ledger,
    )


@pytest.fixture
def fixed_time():
    return datetime(2025, 1, 15, 10, 30, 0, tzinfo=timezone.utc)


# ---------------------------------------------------------------------------
# Size tier tests
# ---------------------------------------------------------------------------

class TestSizeTier:
    def test_small(self):
        assert _size_tier(0) == "small"
        assert _size_tier(50 * 1024 * 1024) == "small"
        assert _size_tier(TIER_SMALL_MAX) == "small"

    def test_medium(self):
        assert _size_tier(TIER_SMALL_MAX + 1) == "medium"
        assert _size_tier(500 * 1024 * 1024) == "medium"
        assert _size_tier(TIER_MEDIUM_MAX) == "medium"

    def test_large(self):
        assert _size_tier(TIER_MEDIUM_MAX + 1) == "large"
        assert _size_tier(10 * 1024 * 1024 * 1024) == "large"


# ---------------------------------------------------------------------------
# Export result tests
# ---------------------------------------------------------------------------

class TestBWCExportResult:
    def test_to_dict(self):
        r = BWCExportResult(
            success=True,
            export_path="/tmp/test.zip",
            package_sha256="abc123",
            evidence_count=2,
            file_count=5,
            total_bytes=1024,
            size_tier="small",
        )
        d = r.to_dict()
        assert d["success"] is True
        assert d["evidence_count"] == 2
        assert d["size_tier"] == "small"
        assert d["error"] is None

    def test_failure_result(self):
        r = BWCExportResult(success=False, error="Something broke")
        assert r.success is False
        assert r.error == "Something broke"


# ---------------------------------------------------------------------------
# Core export tests
# ---------------------------------------------------------------------------

class TestBWCExport:
    def test_export_basic(self, exporter, export_dir, fixed_time):
        result = exporter.export(
            evidence_ids=["ev-001", "ev-002"],
            case_ref="CASE2025",
            exported_by="test_user",
            export_time=fixed_time,
        )
        assert result.success is True
        assert result.evidence_count == 2
        assert result.file_count > 0
        assert result.total_bytes > 0
        assert result.size_tier == "small"
        assert result.package_sha256 != ""
        assert Path(result.export_path).exists()

    def test_deterministic_naming(self, exporter, export_dir, fixed_time):
        result = exporter.export(
            evidence_ids=["ev-001"],
            case_ref="XYZ123",
            export_time=fixed_time,
        )
        assert "BWC_EXPORT_XYZ123_20250115_103000" in result.export_path
        assert result.export_path.endswith(".zip")

    def test_zip_contents(self, exporter, export_dir, fixed_time):
        result = exporter.export(
            evidence_ids=["ev-001"],
            case_ref="TEST",
            export_time=fixed_time,
        )
        with zipfile.ZipFile(result.export_path, "r") as zf:
            names = zf.namelist()
            # Must have manifest and integrity report
            assert any("manifest.json" in n for n in names)
            assert any("integrity_report.md" in n for n in names)
            # Must have at least one original
            assert any("/originals/" in n for n in names)

    def test_originals_packed(self, exporter, export_dir, fixed_time, evidence_store):
        _, items = evidence_store
        result = exporter.export(
            evidence_ids=["ev-001"],
            case_ref="TEST",
            export_time=fixed_time,
        )
        with zipfile.ZipFile(result.export_path, "r") as zf:
            orig_files = [n for n in zf.namelist() if "/originals/" in n]
            assert len(orig_files) == 1
            assert items["ev-001"]["filename"] in orig_files[0]

    def test_derivatives_packed(self, exporter, export_dir, fixed_time):
        result = exporter.export(
            evidence_ids=["ev-001"],
            case_ref="TEST",
            export_time=fixed_time,
            include_derivatives=True,
        )
        with zipfile.ZipFile(result.export_path, "r") as zf:
            deriv_files = [n for n in zf.namelist() if "/derivatives/" in n]
            assert len(deriv_files) >= 1
            assert any("thumb.jpg" in n for n in deriv_files)

    def test_no_derivatives_when_excluded(self, exporter, export_dir, fixed_time):
        result = exporter.export(
            evidence_ids=["ev-001"],
            case_ref="TEST",
            export_time=fixed_time,
            include_derivatives=False,
        )
        with zipfile.ZipFile(result.export_path, "r") as zf:
            deriv_files = [n for n in zf.namelist() if "/derivatives/" in n]
            assert len(deriv_files) == 0

    def test_manifest_contains_all_files(self, exporter, export_dir, fixed_time):
        result = exporter.export(
            evidence_ids=["ev-001", "ev-002"],
            case_ref="TEST",
            export_time=fixed_time,
        )
        manifest = result.manifest
        assert manifest is not None
        assert manifest["evidence_found"] == 2
        assert manifest["file_count"] > 0
        # Every file entry must have sha256
        for fentry in manifest["files"]:
            assert "sha256" in fentry
            assert len(fentry["sha256"]) == 64

    def test_manifest_sha256_present(self, exporter, export_dir, fixed_time):
        result = exporter.export(
            evidence_ids=["ev-001"],
            case_ref="TEST",
            export_time=fixed_time,
        )
        assert "manifest_sha256" in result.manifest
        assert len(result.manifest["manifest_sha256"]) == 64

    def test_package_sha256_verifiable(self, exporter, export_dir, fixed_time):
        result = exporter.export(
            evidence_ids=["ev-001"],
            case_ref="TEST",
            export_time=fixed_time,
        )
        recomputed = _compute_sha256(result.export_path)
        assert recomputed == result.package_sha256


# ---------------------------------------------------------------------------
# Ledger integration tests
# ---------------------------------------------------------------------------

class TestLedgerIntegration:
    def test_ledger_extract_included(self, exporter, export_dir, fixed_time):
        result = exporter.export(
            evidence_ids=["ev-001"],
            case_ref="TEST",
            export_time=fixed_time,
        )
        with zipfile.ZipFile(result.export_path, "r") as zf:
            ledger_files = [n for n in zf.namelist() if "ledger_extract" in n]
            assert len(ledger_files) == 1
            content = zf.read(ledger_files[0]).decode("utf-8")
            # Should contain ev-001 entries only (INGEST + NORMALIZE)
            lines = [l for l in content.strip().split("\n") if l]
            assert len(lines) >= 2  # INGEST + NORMALIZE
            for line in lines:
                entry = json.loads(line)
                assert "ev-001" in entry.get("evidence_id", "")

    def test_export_recorded_in_ledger(self, exporter, export_dir, fixed_time, ledger):
        initial_count = ledger.entry_count
        exporter.export(
            evidence_ids=["ev-001"],
            case_ref="TEST",
            export_time=fixed_time,
        )
        assert ledger.entry_count == initial_count + 1
        entries = ledger.read_all()
        last = entries[-1]
        assert last["action"] == "EXPORT_PACKAGE"
        assert "TEST" in last["details"]["case_ref"]

    def test_ledger_still_verifies_after_export(
        self, exporter, export_dir, fixed_time, ledger
    ):
        exporter.export(
            evidence_ids=["ev-001", "ev-002"],
            case_ref="TEST",
            export_time=fixed_time,
        )
        errors = ledger.verify()
        assert errors == []


# ---------------------------------------------------------------------------
# Edge case tests
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_empty_evidence_ids(self, exporter):
        result = exporter.export(evidence_ids=[], case_ref="TEST")
        assert result.success is False
        assert "No evidence" in result.error

    def test_missing_evidence_generates_warning(
        self, exporter, export_dir, fixed_time
    ):
        result = exporter.export(
            evidence_ids=["ev-001", "ev-nonexistent"],
            case_ref="TEST",
            export_time=fixed_time,
        )
        assert result.success is True
        assert result.evidence_count == 1
        assert any("ev-nonexistent" in w for w in result.warnings)

    def test_all_missing_evidence(self, exporter, export_dir, fixed_time):
        result = exporter.export(
            evidence_ids=["ev-missing1", "ev-missing2"],
            case_ref="TEST",
            export_time=fixed_time,
        )
        # Should succeed (ZIP created) but with warnings and 0 evidence
        assert result.success is True
        assert result.evidence_count == 0
        assert len(result.warnings) == 2

    def test_no_ledger(self, evidence_store, export_dir, fixed_time):
        store_path, _ = evidence_store
        exporter = BWCCaseExporter(
            evidence_base=str(store_path),
            export_dir=str(export_dir),
            ledger=None,
        )
        result = exporter.export(
            evidence_ids=["ev-001"],
            case_ref="TEST",
            export_time=fixed_time,
        )
        assert result.success is True
        # No ledger extract in ZIP
        with zipfile.ZipFile(result.export_path, "r") as zf:
            assert not any("ledger_extract" in n for n in zf.namelist())


# ---------------------------------------------------------------------------
# Search index snapshot tests
# ---------------------------------------------------------------------------

class TestSearchIndexSnapshot:
    def test_search_index_included(self, evidence_store, export_dir, fixed_time, ledger):
        store_path, _ = evidence_store
        # Create a mock search index
        index_data = {
            "documents": {
                "ev-001": {"text": "officer body camera footage"},
                "ev-002": {"text": "second clip of footage"},
                "ev-999": {"text": "unrelated evidence"},
            }
        }
        (store_path / "search_index.json").write_text(
            json.dumps(index_data), encoding="utf-8"
        )
        exporter = BWCCaseExporter(
            evidence_base=str(store_path),
            export_dir=str(export_dir),
            ledger=ledger,
        )
        result = exporter.export(
            evidence_ids=["ev-001"],
            case_ref="TEST",
            export_time=fixed_time,
        )
        with zipfile.ZipFile(result.export_path, "r") as zf:
            idx_files = [n for n in zf.namelist() if "search_index.json" in n]
            assert len(idx_files) == 1
            idx = json.loads(zf.read(idx_files[0]))
            # Only ev-001 should be included
            assert "ev-001" in idx["documents"]
            assert "ev-999" not in idx["documents"]

    def test_no_search_index_when_excluded(
        self, exporter, export_dir, fixed_time
    ):
        result = exporter.export(
            evidence_ids=["ev-001"],
            case_ref="TEST",
            export_time=fixed_time,
            include_search_index=False,
        )
        with zipfile.ZipFile(result.export_path, "r") as zf:
            assert not any("search_index" in n for n in zf.namelist())


# ---------------------------------------------------------------------------
# Integrity report tests
# ---------------------------------------------------------------------------

class TestIntegrityReport:
    def test_report_is_markdown(self, exporter, export_dir, fixed_time):
        result = exporter.export(
            evidence_ids=["ev-001"],
            case_ref="CASE42",
            export_time=fixed_time,
        )
        with zipfile.ZipFile(result.export_path, "r") as zf:
            report_files = [n for n in zf.namelist() if "integrity_report.md" in n]
            assert len(report_files) == 1
            content = zf.read(report_files[0]).decode("utf-8")
            assert "# Evidence Export Integrity Report" in content
            assert "CASE42" in content
            assert "Composite file hash" in content
            assert "Evident Technologies" in content

    def test_report_lists_all_files(self, exporter, export_dir, fixed_time):
        result = exporter.export(
            evidence_ids=["ev-001", "ev-002"],
            case_ref="MULTI",
            export_time=fixed_time,
        )
        with zipfile.ZipFile(result.export_path, "r") as zf:
            report_files = [n for n in zf.namelist() if "integrity_report.md" in n]
            content = zf.read(report_files[0]).decode("utf-8")
            # Should list all packed files in the table
            assert "| 1 |" in content
            # At least 2 originals + 2 thumbnails = 4 rows
            assert "| 4 |" in content
