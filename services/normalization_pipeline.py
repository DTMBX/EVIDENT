"""
B30 Phase 3 — Normalize / Proxy / Thumbnail / Waveform Pipeline
=================================================================
Orchestrates deterministic derivative generation for ingested evidence.

For each original evidence file, generates:
  - Video: metadata extract, thumbnail (JPEG), proxy (720p MP4), audio waveform (PNG)
  - Audio: waveform (PNG), metadata extract
  - Image: OCR text extract
  - PDF:   text extract (native + OCR fallback)
  - DOCX:  text extract

Every derivative is:
  1. Generated with deterministic parameters (no randomness).
  2. SHA-256 hashed.
  3. Stored in EvidenceStore under derivatives/<sha256_prefix>/<sha256>/<type>/.
  4. Recorded in DerivedArtifact (DB model) for querying.
  5. Logged in the IntegrityLedger (append-only JSONL).

Design principles:
  - Originals are never modified.
  - Every derivative references its original's SHA-256.
  - All parameters are recorded for reproducibility.
  - Waveform generation uses deterministic ffmpeg settings.
  - Errors are caught and logged — never swallowed.
"""

import json
import logging
import os
import subprocess
import tempfile
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from services.evidence_processor import (
    extract_image_text,
    extract_pdf_text,
    extract_video_metadata,
    generate_proxy_video,
    generate_thumbnail,
)
from services.evidence_store import EvidenceStore, compute_file_hash
from services.integrity_ledger import IntegrityLedger

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------


@dataclass
class DerivativeResult:
    """Result of generating a single derivative."""
    artifact_type: str
    success: bool
    sha256: str = ""
    stored_path: str = ""
    size_bytes: int = 0
    parameters: Dict = field(default_factory=dict)
    error: Optional[str] = None
    processing_seconds: float = 0.0


@dataclass
class NormalizationResult:
    """Result of normalizing a single evidence item."""
    evidence_id: str
    original_sha256: str
    original_filename: str
    mime_type: str
    derivatives: List[DerivativeResult] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)
    total_seconds: float = 0.0
    success: bool = True
    errors: List[str] = field(default_factory=list)


@dataclass
class BatchNormalizationResult:
    """Result of normalizing a batch of evidence items."""
    batch_id: str
    total_items: int = 0
    total_derivatives: int = 0
    total_errors: int = 0
    items: List[NormalizationResult] = field(default_factory=list)
    started_at: str = ""
    completed_at: str = ""


# ---------------------------------------------------------------------------
# Waveform generation (NEW — not in existing processor)
# ---------------------------------------------------------------------------

# Deterministic waveform settings
WAVEFORM_WIDTH = 1800
WAVEFORM_HEIGHT = 140
WAVEFORM_COLOR = "0x3b82f6"  # Blue-500
WAVEFORM_BG_COLOR = "0x1e293b"  # Slate-800


def generate_waveform(
    audio_or_video_path: str,
    output_path: str,
    width: int = WAVEFORM_WIDTH,
    height: int = WAVEFORM_HEIGHT,
    color: str = WAVEFORM_COLOR,
    bg_color: str = WAVEFORM_BG_COLOR,
) -> bool:
    """
    Generate an audio waveform PNG from a video or audio file using ffmpeg.

    Uses the showwavespic filter with deterministic settings.

    Args:
        audio_or_video_path: Path to source media file.
        output_path: Path to write the PNG waveform.
        width: Waveform image width in pixels.
        height: Waveform image height in pixels.
        color: Waveform foreground colour (hex without #).
        bg_color: Background colour (hex without #).

    Returns True on success.
    """
    try:
        cmd = [
            "ffmpeg",
            "-y",
            "-i", str(audio_or_video_path),
            "-filter_complex",
            f"showwavespic=s={width}x{height}:colors={color}",
            "-frames:v", "1",
            str(output_path),
        ]
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=120,
        )
        if result.returncode != 0:
            logger.error("Waveform generation failed: %s", result.stderr[:500])
            return False

        return Path(output_path).exists() and Path(output_path).stat().st_size > 0

    except subprocess.TimeoutExpired:
        logger.error("Waveform generation timed out for %s", audio_or_video_path)
        return False
    except Exception as exc:
        logger.error("Waveform generation error: %s", exc)
        return False


# ---------------------------------------------------------------------------
# MIME type → processing strategy
# ---------------------------------------------------------------------------

VIDEO_MIMES = {"video/mp4", "video/avi", "video/quicktime", "video/x-matroska",
               "video/webm", "video/x-flv", "video/x-msvideo"}
AUDIO_MIMES = {"audio/mpeg", "audio/wav", "audio/flac", "audio/aac",
               "audio/mp4", "audio/x-wav", "audio/x-m4a"}
IMAGE_MIMES = {"image/jpeg", "image/png", "image/tiff", "image/bmp",
               "image/webp", "image/gif"}
PDF_MIMES = {"application/pdf"}
DOCX_MIMES = {"application/vnd.openxmlformats-officedocument.wordprocessingml.document"}


def _classify_mime(mime_type: str) -> str:
    """Classify a MIME type into a processing category."""
    if not mime_type:
        return "unknown"
    mime_lower = mime_type.lower()
    if mime_lower in VIDEO_MIMES or mime_lower.startswith("video/"):
        return "video"
    if mime_lower in AUDIO_MIMES or mime_lower.startswith("audio/"):
        return "audio"
    if mime_lower in IMAGE_MIMES or mime_lower.startswith("image/"):
        return "image"
    if mime_lower in PDF_MIMES:
        return "pdf"
    if mime_lower in DOCX_MIMES:
        return "docx"
    if mime_lower.startswith("text/"):
        return "text"
    return "unknown"


# ---------------------------------------------------------------------------
# Per-type normalization
# ---------------------------------------------------------------------------


def _normalize_video(
    file_path: str,
    original_sha256: str,
    store: EvidenceStore,
    ledger: IntegrityLedger,
    evidence_id: str,
    actor: str,
    generate_proxy: bool = False,
) -> List[DerivativeResult]:
    """Generate derivatives for a video file."""
    derivatives = []

    # 1. Metadata extraction
    start = time.time()
    metadata = extract_video_metadata(file_path)
    elapsed = time.time() - start

    if "error" not in metadata or metadata.get("duration_seconds"):
        # Store metadata as JSON derivative
        with tempfile.NamedTemporaryFile(
            suffix=".json", mode="w", delete=False, encoding="utf-8"
        ) as f:
            json.dump(metadata, f, indent=2)
            meta_tmp = f.name

        try:
            record = store.store_derivative(
                original_sha256=original_sha256,
                derivative_type="metadata_extract",
                source_path=meta_tmp,
                filename="video_metadata.json",
            )
            derivatives.append(DerivativeResult(
                artifact_type="metadata_extract",
                success=True,
                sha256=record.sha256,
                stored_path=store.get_derivative_path(
                    original_sha256, "metadata_extract", "video_metadata.json"
                ) or "",
                size_bytes=record.size_bytes,
                parameters={"source": "ffprobe"},
                processing_seconds=elapsed,
            ))
            ledger.append(
                action="derivative.created",
                evidence_id=evidence_id,
                sha256=record.sha256,
                actor=actor,
                details={"type": "metadata_extract", "original_sha256": original_sha256},
            )
        finally:
            if os.path.exists(meta_tmp):
                os.unlink(meta_tmp)

    # 2. Thumbnail
    start = time.time()
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
        thumb_tmp = f.name

    try:
        duration = metadata.get("duration_seconds", 0)
        ts = min(10.0, duration / 2) if duration > 0 else 0.0
        thumb_params = {"timestamp_sec": ts, "format": "jpeg", "quality": 2}

        if generate_thumbnail(file_path, thumb_tmp, timestamp=ts):
            record = store.store_derivative(
                original_sha256=original_sha256,
                derivative_type="thumbnail",
                source_path=thumb_tmp,
                filename="thumbnail.jpg",
            )
            derivatives.append(DerivativeResult(
                artifact_type="thumbnail",
                success=True,
                sha256=record.sha256,
                stored_path=store.get_derivative_path(
                    original_sha256, "thumbnail", "thumbnail.jpg"
                ) or "",
                size_bytes=record.size_bytes,
                parameters=thumb_params,
                processing_seconds=time.time() - start,
            ))
            ledger.append(
                action="derivative.created",
                evidence_id=evidence_id,
                sha256=record.sha256,
                actor=actor,
                details={"type": "thumbnail", "original_sha256": original_sha256},
            )
        else:
            derivatives.append(DerivativeResult(
                artifact_type="thumbnail",
                success=False,
                error="Thumbnail generation failed",
                parameters=thumb_params,
                processing_seconds=time.time() - start,
            ))
    finally:
        if os.path.exists(thumb_tmp):
            os.unlink(thumb_tmp)

    # 3. Proxy video (optional)
    if generate_proxy:
        start = time.time()
        proxy_params = {"codec": "libx264", "crf": 23, "height": 720, "audio_codec": "aac",
                        "audio_bitrate": "128k"}
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
            proxy_tmp = f.name

        try:
            if generate_proxy_video(file_path, proxy_tmp, target_height=720):
                record = store.store_derivative(
                    original_sha256=original_sha256,
                    derivative_type="proxy",
                    source_path=proxy_tmp,
                    filename="proxy_720p.mp4",
                )
                derivatives.append(DerivativeResult(
                    artifact_type="proxy",
                    success=True,
                    sha256=record.sha256,
                    stored_path=store.get_derivative_path(
                        original_sha256, "proxy", "proxy_720p.mp4"
                    ) or "",
                    size_bytes=record.size_bytes,
                    parameters=proxy_params,
                    processing_seconds=time.time() - start,
                ))
                ledger.append(
                    action="derivative.created",
                    evidence_id=evidence_id,
                    sha256=record.sha256,
                    actor=actor,
                    details={"type": "proxy", "original_sha256": original_sha256},
                )
            else:
                derivatives.append(DerivativeResult(
                    artifact_type="proxy",
                    success=False,
                    error="Proxy generation failed",
                    parameters=proxy_params,
                    processing_seconds=time.time() - start,
                ))
        finally:
            if os.path.exists(proxy_tmp):
                os.unlink(proxy_tmp)

    # 4. Waveform
    start = time.time()
    waveform_params = {
        "width": WAVEFORM_WIDTH,
        "height": WAVEFORM_HEIGHT,
        "color": WAVEFORM_COLOR,
        "bg_color": WAVEFORM_BG_COLOR,
    }
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        wave_tmp = f.name

    try:
        if generate_waveform(file_path, wave_tmp):
            record = store.store_derivative(
                original_sha256=original_sha256,
                derivative_type="waveform",
                source_path=wave_tmp,
                filename="audio_waveform.png",
            )
            derivatives.append(DerivativeResult(
                artifact_type="waveform",
                success=True,
                sha256=record.sha256,
                stored_path=store.get_derivative_path(
                    original_sha256, "waveform", "audio_waveform.png"
                ) or "",
                size_bytes=record.size_bytes,
                parameters=waveform_params,
                processing_seconds=time.time() - start,
            ))
            ledger.append(
                action="derivative.created",
                evidence_id=evidence_id,
                sha256=record.sha256,
                actor=actor,
                details={"type": "waveform", "original_sha256": original_sha256},
            )
        else:
            derivatives.append(DerivativeResult(
                artifact_type="waveform",
                success=False,
                error="Waveform generation failed (ffmpeg may not be available)",
                parameters=waveform_params,
                processing_seconds=time.time() - start,
            ))
    finally:
        if os.path.exists(wave_tmp):
            os.unlink(wave_tmp)

    return derivatives


def _normalize_audio(
    file_path: str,
    original_sha256: str,
    store: EvidenceStore,
    ledger: IntegrityLedger,
    evidence_id: str,
    actor: str,
) -> List[DerivativeResult]:
    """Generate derivatives for an audio file (waveform + metadata)."""
    derivatives = []

    # Metadata via ffprobe
    start = time.time()
    metadata = extract_video_metadata(file_path)  # ffprobe works for audio too
    if "error" not in metadata:
        with tempfile.NamedTemporaryFile(
            suffix=".json", mode="w", delete=False, encoding="utf-8"
        ) as f:
            json.dump(metadata, f, indent=2)
            meta_tmp = f.name
        try:
            record = store.store_derivative(
                original_sha256=original_sha256,
                derivative_type="metadata_extract",
                source_path=meta_tmp,
                filename="audio_metadata.json",
            )
            derivatives.append(DerivativeResult(
                artifact_type="metadata_extract",
                success=True,
                sha256=record.sha256,
                stored_path=store.get_derivative_path(
                    original_sha256, "metadata_extract", "audio_metadata.json"
                ) or "",
                size_bytes=record.size_bytes,
                parameters={"source": "ffprobe"},
                processing_seconds=time.time() - start,
            ))
            ledger.append(
                action="derivative.created",
                evidence_id=evidence_id,
                sha256=record.sha256,
                actor=actor,
                details={"type": "metadata_extract", "original_sha256": original_sha256},
            )
        finally:
            if os.path.exists(meta_tmp):
                os.unlink(meta_tmp)

    # Waveform
    start = time.time()
    waveform_params = {
        "width": WAVEFORM_WIDTH, "height": WAVEFORM_HEIGHT,
        "color": WAVEFORM_COLOR, "bg_color": WAVEFORM_BG_COLOR,
    }
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        wave_tmp = f.name
    try:
        if generate_waveform(file_path, wave_tmp):
            record = store.store_derivative(
                original_sha256=original_sha256,
                derivative_type="waveform",
                source_path=wave_tmp,
                filename="audio_waveform.png",
            )
            derivatives.append(DerivativeResult(
                artifact_type="waveform",
                success=True,
                sha256=record.sha256,
                stored_path=store.get_derivative_path(
                    original_sha256, "waveform", "audio_waveform.png"
                ) or "",
                size_bytes=record.size_bytes,
                parameters=waveform_params,
                processing_seconds=time.time() - start,
            ))
            ledger.append(
                action="derivative.created",
                evidence_id=evidence_id,
                sha256=record.sha256,
                actor=actor,
                details={"type": "waveform", "original_sha256": original_sha256},
            )
        else:
            derivatives.append(DerivativeResult(
                artifact_type="waveform",
                success=False,
                error="Waveform generation failed",
                parameters=waveform_params,
                processing_seconds=time.time() - start,
            ))
    finally:
        if os.path.exists(wave_tmp):
            os.unlink(wave_tmp)

    return derivatives


def _normalize_document(
    file_path: str,
    original_sha256: str,
    store: EvidenceStore,
    ledger: IntegrityLedger,
    evidence_id: str,
    actor: str,
    mime_type: str,
) -> List[DerivativeResult]:
    """Generate text extract derivative for PDF/DOCX/image/text files."""
    derivatives = []
    start = time.time()

    category = _classify_mime(mime_type)
    extract_result = None
    task_type = "unknown"

    try:
        if category == "pdf":
            extract_result = extract_pdf_text(file_path)
            task_type = "pdf_text"
        elif category == "image":
            extract_result = extract_image_text(file_path)
            task_type = "image_ocr"
        elif category == "docx":
            from services.evidence_processor import extract_docx_text
            extract_result = extract_docx_text(file_path)
            task_type = "docx_text"
        elif category == "text":
            # Plain text passthrough
            text = Path(file_path).read_text(encoding="utf-8", errors="replace")
            from services.evidence_processor import ExtractionResult
            extract_result = ExtractionResult(
                success=True, evidence_id=0, task_type="plaintext",
                full_text=text, word_count=len(text.split()),
                character_count=len(text),
            )
            task_type = "plaintext"
    except Exception as exc:
        derivatives.append(DerivativeResult(
            artifact_type="text_extract",
            success=False,
            error=str(exc),
            processing_seconds=time.time() - start,
        ))
        return derivatives

    if extract_result and extract_result.success and extract_result.full_text:
        # Store extracted text as derivative
        with tempfile.NamedTemporaryFile(
            suffix=".txt", mode="w", delete=False, encoding="utf-8"
        ) as f:
            f.write(extract_result.full_text)
            text_tmp = f.name
        try:
            record = store.store_derivative(
                original_sha256=original_sha256,
                derivative_type="text_extract",
                source_path=text_tmp,
                filename=f"{task_type}_extract.txt",
            )
            derivatives.append(DerivativeResult(
                artifact_type="text_extract",
                success=True,
                sha256=record.sha256,
                stored_path=store.get_derivative_path(
                    original_sha256, "text_extract", f"{task_type}_extract.txt"
                ) or "",
                size_bytes=record.size_bytes,
                parameters={
                    "task_type": task_type,
                    "word_count": extract_result.word_count,
                    "character_count": extract_result.character_count,
                    "page_count": extract_result.page_count,
                },
                processing_seconds=time.time() - start,
            ))
            ledger.append(
                action="derivative.created",
                evidence_id=evidence_id,
                sha256=record.sha256,
                actor=actor,
                details={
                    "type": "text_extract",
                    "task_type": task_type,
                    "original_sha256": original_sha256,
                    "word_count": extract_result.word_count,
                },
            )
        finally:
            if os.path.exists(text_tmp):
                os.unlink(text_tmp)
    elif extract_result:
        derivatives.append(DerivativeResult(
            artifact_type="text_extract",
            success=False,
            error=extract_result.error_message or "No text extracted",
            parameters={"task_type": task_type},
            processing_seconds=time.time() - start,
        ))

    return derivatives


# ---------------------------------------------------------------------------
# Main normalization entry point
# ---------------------------------------------------------------------------


def normalize_evidence(
    file_path: str,
    original_sha256: str,
    evidence_id: str,
    mime_type: str,
    original_filename: str,
    store: Optional[EvidenceStore] = None,
    ledger: Optional[IntegrityLedger] = None,
    actor: str = "system",
    generate_proxy: bool = False,
) -> NormalizationResult:
    """
    Normalize a single evidence file — generate all applicable derivatives.

    Dispatches to the appropriate handler based on MIME type.

    Args:
        file_path: Path to the original file in the evidence store.
        original_sha256: SHA-256 of the original file.
        evidence_id: UUID or DB ID of the evidence item.
        mime_type: MIME type of the original file.
        original_filename: Original filename for logging.
        store: EvidenceStore instance (default: creates one).
        ledger: IntegrityLedger instance (default: creates one).
        actor: Actor identifier for audit.
        generate_proxy: Whether to generate proxy video for video files.

    Returns:
        NormalizationResult with all derivative results.
    """
    store = store or EvidenceStore()
    ledger = ledger or IntegrityLedger()

    start = time.time()
    result = NormalizationResult(
        evidence_id=evidence_id,
        original_sha256=original_sha256,
        original_filename=original_filename,
        mime_type=mime_type,
    )

    category = _classify_mime(mime_type)

    ledger.append(
        action="normalize.start",
        evidence_id=evidence_id,
        sha256=original_sha256,
        actor=actor,
        details={"category": category, "filename": original_filename},
    )

    try:
        if category == "video":
            result.derivatives = _normalize_video(
                file_path, original_sha256, store, ledger, evidence_id, actor,
                generate_proxy=generate_proxy,
            )
            # Include video metadata in result
            metadata = extract_video_metadata(file_path)
            if "error" not in metadata:
                result.metadata = metadata

        elif category == "audio":
            result.derivatives = _normalize_audio(
                file_path, original_sha256, store, ledger, evidence_id, actor,
            )

        elif category in ("pdf", "image", "docx", "text"):
            result.derivatives = _normalize_document(
                file_path, original_sha256, store, ledger, evidence_id, actor,
                mime_type=mime_type,
            )

        else:
            logger.info(
                "Skipping normalization for unsupported type: %s (%s)",
                original_filename, mime_type,
            )

    except Exception as exc:
        result.success = False
        result.errors.append(str(exc))
        logger.error(
            "Normalization failed for %s: %s", original_filename, exc, exc_info=True,
        )

    # Summarize
    result.total_seconds = time.time() - start
    failed = [d for d in result.derivatives if not d.success]
    if failed:
        result.errors.extend([d.error or "Unknown error" for d in failed])
    result.success = len(failed) == 0 or any(d.success for d in result.derivatives)

    ledger.append(
        action="normalize.complete",
        evidence_id=evidence_id,
        sha256=original_sha256,
        actor=actor,
        details={
            "derivatives_created": sum(1 for d in result.derivatives if d.success),
            "derivatives_failed": len(failed),
            "total_seconds": round(result.total_seconds, 2),
        },
    )

    return result
