"""
Tests for services/normalization_pipeline.py — Phase 3
=======================================================
Tests MIME classification, waveform generation, and normalization orchestration.
Uses mocking for ffmpeg/ffprobe since they may not be available in CI.
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from services.evidence_store import EvidenceStore, DerivativeRecord
from services.integrity_ledger import IntegrityLedger
from services.normalization_pipeline import (
    DerivativeResult,
    NormalizationResult,
    _classify_mime,
    generate_waveform,
    normalize_evidence,
    WAVEFORM_WIDTH,
    WAVEFORM_HEIGHT,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def tmp_env(tmp_path):
    """Create a complete temp environment."""
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


def _create_file(dir_path: Path, name: str, content: bytes = b"fake") -> Path:
    fp = dir_path / name
    fp.write_bytes(content)
    return fp


# ---------------------------------------------------------------------------
# MIME Classification
# ---------------------------------------------------------------------------


class TestMimeClassification:
    """Test MIME type → category mapping."""

    def test_video_types(self):
        assert _classify_mime("video/mp4") == "video"
        assert _classify_mime("video/quicktime") == "video"
        assert _classify_mime("video/x-matroska") == "video"

    def test_audio_types(self):
        assert _classify_mime("audio/mpeg") == "audio"
        assert _classify_mime("audio/wav") == "audio"
        assert _classify_mime("audio/flac") == "audio"

    def test_image_types(self):
        assert _classify_mime("image/jpeg") == "image"
        assert _classify_mime("image/png") == "image"

    def test_document_types(self):
        assert _classify_mime("application/pdf") == "pdf"
        assert _classify_mime("application/vnd.openxmlformats-officedocument.wordprocessingml.document") == "docx"

    def test_text_types(self):
        assert _classify_mime("text/plain") == "text"
        assert _classify_mime("text/csv") == "text"

    def test_unknown(self):
        assert _classify_mime("application/octet-stream") == "unknown"
        assert _classify_mime("") == "unknown"
        assert _classify_mime("application/zip") == "unknown"


# ---------------------------------------------------------------------------
# Waveform generation (mocked)
# ---------------------------------------------------------------------------


class TestGenerateWaveform:
    """Test waveform generation with mocked ffmpeg."""

    @patch("services.normalization_pipeline.subprocess.run")
    def test_waveform_success(self, mock_run, tmp_path):
        output = tmp_path / "waveform.png"
        # Create fake output file to simulate ffmpeg success
        output.write_bytes(b"\x89PNG fake waveform data")

        mock_run.return_value = MagicMock(returncode=0, stderr="", stdout="")

        result = generate_waveform(
            str(tmp_path / "input.mp4"),
            str(output),
        )
        assert result is True
        mock_run.assert_called_once()
        cmd = mock_run.call_args[0][0]
        assert "ffmpeg" in cmd[0]
        assert "showwavespic" in str(cmd)

    @patch("services.normalization_pipeline.subprocess.run")
    def test_waveform_failure(self, mock_run, tmp_path):
        output = tmp_path / "waveform.png"
        mock_run.return_value = MagicMock(returncode=1, stderr="error")

        result = generate_waveform(
            str(tmp_path / "input.mp4"),
            str(output),
        )
        assert result is False

    @patch("services.normalization_pipeline.subprocess.run")
    def test_waveform_deterministic_params(self, mock_run, tmp_path):
        output = tmp_path / "waveform.png"
        output.write_bytes(b"\x89PNG")
        mock_run.return_value = MagicMock(returncode=0)

        generate_waveform(str(tmp_path / "input.mp4"), str(output))
        cmd = mock_run.call_args[0][0]
        filter_str = cmd[cmd.index("-filter_complex") + 1]
        assert f"s={WAVEFORM_WIDTH}x{WAVEFORM_HEIGHT}" in filter_str


# ---------------------------------------------------------------------------
# Normalization pipeline (integration-style with mocking)
# ---------------------------------------------------------------------------


class TestNormalizeEvidence:
    """Test the normalize_evidence orchestration."""

    def test_normalize_unknown_mime(self, tmp_env):
        """Unknown MIME types should pass through without error."""
        f = _create_file(tmp_env["source_dir"], "data.bin")
        result = normalize_evidence(
            file_path=str(f),
            original_sha256="a" * 64,
            evidence_id="test-ev-1",
            mime_type="application/octet-stream",
            original_filename="data.bin",
            store=tmp_env["store"],
            ledger=tmp_env["ledger"],
        )
        assert isinstance(result, NormalizationResult)
        assert result.evidence_id == "test-ev-1"
        # No derivatives for unknown type
        assert len(result.derivatives) == 0

    def test_normalize_logs_to_ledger(self, tmp_env):
        """Normalization should log start and complete to ledger."""
        f = _create_file(tmp_env["source_dir"], "unknown.bin")
        normalize_evidence(
            file_path=str(f),
            original_sha256="b" * 64,
            evidence_id="test-ev-2",
            mime_type="application/octet-stream",
            original_filename="unknown.bin",
            store=tmp_env["store"],
            ledger=tmp_env["ledger"],
        )
        entries = tmp_env["ledger"].read_all()
        actions = [e["action"] for e in entries]
        assert "normalize.start" in actions
        assert "normalize.complete" in actions

    def test_normalize_text_file(self, tmp_env):
        """Plain text files should produce a text_extract derivative."""
        f = _create_file(
            tmp_env["source_dir"], "notes.txt",
            content=b"This is a plain text evidence note with important details.",
        )

        # First ingest the file so the store has the original
        from services.evidence_store import compute_file_hash
        digest = compute_file_hash(str(f))

        result = normalize_evidence(
            file_path=str(f),
            original_sha256=digest.sha256,
            evidence_id="test-ev-txt",
            mime_type="text/plain",
            original_filename="notes.txt",
            store=tmp_env["store"],
            ledger=tmp_env["ledger"],
        )
        assert result.evidence_id == "test-ev-txt"
        # Should have text_extract derivative
        text_derivs = [d for d in result.derivatives if d.artifact_type == "text_extract"]
        assert len(text_derivs) == 1
        assert text_derivs[0].success is True
        assert text_derivs[0].sha256 != ""

    @patch("services.normalization_pipeline.generate_waveform", return_value=False)
    @patch("services.normalization_pipeline.generate_thumbnail", return_value=False)
    @patch("services.normalization_pipeline.extract_video_metadata")
    def test_normalize_video_no_ffmpeg(self, mock_meta, mock_thumb, mock_wave, tmp_env):
        """Video normalization should handle missing ffmpeg gracefully."""
        mock_meta.return_value = {"error": "ffmpeg not found"}

        f = _create_file(tmp_env["source_dir"], "body_cam.mp4")
        result = normalize_evidence(
            file_path=str(f),
            original_sha256="c" * 64,
            evidence_id="test-ev-vid",
            mime_type="video/mp4",
            original_filename="body_cam.mp4",
            store=tmp_env["store"],
            ledger=tmp_env["ledger"],
        )
        assert isinstance(result, NormalizationResult)
        # Failed derivatives should be recorded
        failed = [d for d in result.derivatives if not d.success]
        assert len(failed) >= 1  # Thumbnail and waveform should fail

    @patch("services.normalization_pipeline.generate_waveform")
    @patch("services.normalization_pipeline.generate_thumbnail")
    @patch("services.normalization_pipeline.extract_video_metadata")
    def test_normalize_video_with_mocked_ffmpeg(
        self, mock_meta, mock_thumb, mock_wave, tmp_env
    ):
        """Video normalization with simulated ffmpeg success."""
        mock_meta.return_value = {
            "duration_seconds": 120.0,
            "video": {"codec": "h264", "width": 1920, "height": 1080},
        }

        # Simulate thumbnail success
        def fake_thumbnail(video_path, output_path, timestamp=10.0):
            Path(output_path).write_bytes(b"\xff\xd8\xff fake jpeg")
            return True
        mock_thumb.side_effect = fake_thumbnail

        # Simulate waveform success
        def fake_waveform(media_path, output_path, **kwargs):
            Path(output_path).write_bytes(b"\x89PNG fake waveform")
            return True
        mock_wave.side_effect = fake_waveform

        f = _create_file(tmp_env["source_dir"], "cam.mp4", content=b"MP4 fake video data")
        from services.evidence_store import compute_file_hash
        digest = compute_file_hash(str(f))

        result = normalize_evidence(
            file_path=str(f),
            original_sha256=digest.sha256,
            evidence_id="test-ev-vid-ok",
            mime_type="video/mp4",
            original_filename="cam.mp4",
            store=tmp_env["store"],
            ledger=tmp_env["ledger"],
        )

        # Should have: metadata_extract, thumbnail, waveform (no proxy by default)
        types = [d.artifact_type for d in result.derivatives if d.success]
        assert "metadata_extract" in types
        assert "thumbnail" in types
        assert "waveform" in types
        assert "proxy" not in types  # Not requested

        # All successful derivatives must have SHA-256
        for d in result.derivatives:
            if d.success:
                assert d.sha256 != ""
                assert d.stored_path != ""

    def test_normalize_ledger_chain_valid(self, tmp_env):
        """Ledger must remain chain-valid after normalization."""
        f = _create_file(
            tmp_env["source_dir"], "doc.txt",
            content=b"Test document content for chain validation.",
        )
        from services.evidence_store import compute_file_hash
        digest = compute_file_hash(str(f))

        normalize_evidence(
            file_path=str(f),
            original_sha256=digest.sha256,
            evidence_id="chain-test",
            mime_type="text/plain",
            original_filename="doc.txt",
            store=tmp_env["store"],
            ledger=tmp_env["ledger"],
        )
        errors = tmp_env["ledger"].verify()
        assert errors == [], f"Ledger chain broken: {errors}"
