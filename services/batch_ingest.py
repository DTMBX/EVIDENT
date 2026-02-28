"""
B30 Phase 2 — Batch Folder Ingest Pipeline
============================================
Ingests a folder of BWC files (messy dump) into the evidence store.

Pipeline steps per file:
  1. Walk the folder and discover media/document files.
  2. SHA-256 hash every file.
  3. Check for duplicates (idempotent — re-run safe).
  4. Ingest each file into EvidenceStore (immutable originals).
  5. Capture device label + timestamp from filename heuristics.
  6. Record every action in the IntegrityLedger (JSONL, append-only).
  7. Emit a batch manifest JSON summarizing the ingest.
  8. Attempt sequence grouping (time adjacency + device label).

Design principles:
  - Fail closed: if a file can't be hashed or ingested, record the error
    and continue with remaining files — never silently skip.
  - Idempotent: re-running on the same folder does not duplicate originals.
  - Deterministic: same folder → same manifest (modulo timestamps).
  - No originals overwritten. Ever.
"""

import json
import logging
import os
import re
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from services.evidence_store import EvidenceStore, compute_file_hash
from services.integrity_ledger import IntegrityLedger

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# BWC filename parsing heuristics
# ---------------------------------------------------------------------------

# Pattern: OfficerName_YYYYMMDDHHMI_DeviceSerial-ClipIndex.ext
BWC_FILENAME_RE = re.compile(
    r"^(?P<officer>[A-Za-z]+)_"
    r"(?P<ts>\d{12})_"
    r"(?P<device>[A-Z0-9]+)-"
    r"(?P<clip>\d+)"
    r"\.(?P<ext>\w+)$"
)

# Broader pattern for files with timestamps
TIMESTAMP_RE = re.compile(r"(\d{12,14})")


@dataclass
class ParsedBWCFilename:
    """Result of parsing a BWC filename."""
    officer_name: Optional[str] = None
    timestamp: Optional[datetime] = None
    device_label: Optional[str] = None
    clip_index: Optional[int] = None
    extension: Optional[str] = None
    raw_filename: str = ""


def parse_bwc_filename(filename: str) -> ParsedBWCFilename:
    """
    Parse a BWC-style filename into structured metadata.

    Supports patterns like:
      BryanMerritt_202511292257_BWL7137497-0.mp4
      EdwardRuiz_202511292251_BWL7139078-0.mp4

    Returns ParsedBWCFilename with whatever fields can be extracted.
    """
    result = ParsedBWCFilename(raw_filename=filename)
    name = Path(filename).stem
    result.extension = Path(filename).suffix.lstrip(".")

    m = BWC_FILENAME_RE.match(filename)
    if m:
        result.officer_name = m.group("officer")
        result.device_label = m.group("device")
        result.clip_index = int(m.group("clip"))
        result.extension = m.group("ext")
        try:
            result.timestamp = datetime.strptime(m.group("ts"), "%Y%m%d%H%M")
        except ValueError:
            pass
        return result

    # Fallback: try to extract timestamp from anywhere in filename
    ts_match = TIMESTAMP_RE.search(name)
    if ts_match:
        ts_str = ts_match.group(1)
        try:
            if len(ts_str) == 12:
                result.timestamp = datetime.strptime(ts_str, "%Y%m%d%H%M")
            elif len(ts_str) == 14:
                result.timestamp = datetime.strptime(ts_str, "%Y%m%d%H%M%S")
        except ValueError:
            pass

    # Try to extract device label (BWL + digits pattern)
    device_match = re.search(r"(BWL\d+)", name)
    if device_match:
        result.device_label = device_match.group(1)

    return result


# ---------------------------------------------------------------------------
# Sequence grouping
# ---------------------------------------------------------------------------

@dataclass
class SequenceGroup:
    """A group of related evidence files."""
    group_id: str
    group_name: str
    device_labels: List[str] = field(default_factory=list)
    start_time: Optional[str] = None  # ISO format
    end_time: Optional[str] = None
    members: List[Dict] = field(default_factory=list)


def group_by_sequence(
    ingested_files: List[Dict],
    time_window_minutes: int = 30,
) -> List[SequenceGroup]:
    """
    Group ingested files by time adjacency and device label.

    Files within `time_window_minutes` of each other that share
    a device label (or are from the same naming batch) are grouped together.

    Returns a list of SequenceGroup.
    """
    if not ingested_files:
        return []

    # Sort by timestamp (files without timestamp go to end)
    def sort_key(f):
        ts = f.get("timestamp")
        if ts:
            return ts
        return "9999-99-99"

    sorted_files = sorted(ingested_files, key=sort_key)

    groups: List[SequenceGroup] = []
    current_group: Optional[SequenceGroup] = None

    for f in sorted_files:
        ts_str = f.get("timestamp")
        device = f.get("device_label") or "unknown"

        if current_group is None:
            # Start new group
            current_group = SequenceGroup(
                group_id=str(uuid.uuid4()),
                group_name=f"Sequence_{len(groups) + 1}",
                device_labels=[device] if device != "unknown" else [],
                start_time=ts_str,
                end_time=ts_str,
                members=[f],
            )
            continue

        # Check if this file belongs to current group
        belongs = False
        if ts_str and current_group.end_time:
            try:
                current_end = datetime.fromisoformat(current_group.end_time)
                file_time = datetime.fromisoformat(ts_str)
                delta = abs((file_time - current_end).total_seconds())
                if delta <= time_window_minutes * 60:
                    belongs = True
            except (ValueError, TypeError):
                pass

        if belongs:
            current_group.members.append(f)
            if device != "unknown" and device not in current_group.device_labels:
                current_group.device_labels.append(device)
            if ts_str:
                # Extend end_time
                if not current_group.end_time or ts_str > current_group.end_time:
                    current_group.end_time = ts_str
                if not current_group.start_time or ts_str < current_group.start_time:
                    current_group.start_time = ts_str
        else:
            # Close current group, start new one
            groups.append(current_group)
            current_group = SequenceGroup(
                group_id=str(uuid.uuid4()),
                group_name=f"Sequence_{len(groups) + 1}",
                device_labels=[device] if device != "unknown" else [],
                start_time=ts_str,
                end_time=ts_str,
                members=[f],
            )

    if current_group and current_group.members:
        groups.append(current_group)

    # Update group names with device info
    for g in groups:
        labels = [lbl for lbl in g.device_labels if lbl]
        if labels:
            g.group_name = f"BWC_{'+'.join(labels[:3])}_{g.start_time or 'unknown'}"

    return groups


# ---------------------------------------------------------------------------
# Batch ingest result
# ---------------------------------------------------------------------------

@dataclass
class BatchIngestResult:
    """Result of a folder batch ingest operation."""
    batch_id: str
    source_folder: str
    total_files_found: int = 0
    total_files_ingested: int = 0
    total_duplicates: int = 0
    total_errors: int = 0
    total_bytes: int = 0
    files: List[Dict] = field(default_factory=list)
    errors: List[Dict] = field(default_factory=list)
    sequence_groups: List[Dict] = field(default_factory=list)
    manifest_path: str = ""
    ledger_entries: int = 0
    started_at: str = ""
    completed_at: str = ""


# ---------------------------------------------------------------------------
# Supported file extensions for ingest
# ---------------------------------------------------------------------------

INGEST_EXTENSIONS = {
    # Video
    ".mp4", ".avi", ".mov", ".mkv", ".webm", ".flv",
    # Audio
    ".mp3", ".wav", ".flac", ".aac", ".m4a",
    # Images
    ".jpg", ".jpeg", ".png", ".tiff", ".bmp", ".webp", ".gif",
    # Documents
    ".pdf", ".docx", ".doc", ".txt",
}


# ---------------------------------------------------------------------------
# Core batch ingest
# ---------------------------------------------------------------------------

def ingest_folder(
    folder_path: str,
    evidence_store: Optional[EvidenceStore] = None,
    ledger: Optional[IntegrityLedger] = None,
    ingested_by: str = "system",
    case_id: Optional[str] = None,
    time_window_minutes: int = 30,
) -> BatchIngestResult:
    """
    Ingest all supported files from a folder into the evidence store.

    Steps:
      1. Walk folder and discover files.
      2. Hash each file (SHA-256).
      3. Ingest into evidence store (duplicate-safe).
      4. Parse BWC filename metadata.
      5. Record in integrity ledger (append-only JSONL).
      6. Group by sequence (time + device).
      7. Write batch manifest.

    Args:
        folder_path: Path to the folder to ingest.
        evidence_store: EvidenceStore instance (default: creates one).
        ledger: IntegrityLedger instance (default: creates one).
        ingested_by: Actor identifier for audit.
        case_id: Optional case ID to associate files with.
        time_window_minutes: Window for sequence grouping.

    Returns:
        BatchIngestResult with full details.
    """
    store = evidence_store or EvidenceStore()
    lgr = ledger or IntegrityLedger()

    batch_id = str(uuid.uuid4())
    started_at = datetime.now(timezone.utc).isoformat()

    result = BatchIngestResult(
        batch_id=batch_id,
        source_folder=folder_path,
        started_at=started_at,
    )

    # Record batch start in ledger
    lgr.append(
        action="batch.ingest_start",
        evidence_id=batch_id,
        actor=ingested_by,
        details={"folder": folder_path, "case_id": case_id},
    )

    # 1. Discover files
    folder = Path(folder_path)
    if not folder.exists() or not folder.is_dir():
        error = {"error": f"Folder not found or not a directory: {folder_path}"}
        result.errors.append(error)
        lgr.append(
            action="batch.ingest_error",
            evidence_id=batch_id,
            actor=ingested_by,
            details=error,
        )
        result.completed_at = datetime.now(timezone.utc).isoformat()
        return result

    files_to_ingest = []
    for root, _dirs, files in os.walk(str(folder)):
        for fname in sorted(files):
            ext = Path(fname).suffix.lower()
            if ext in INGEST_EXTENSIONS:
                files_to_ingest.append(Path(root) / fname)

    result.total_files_found = len(files_to_ingest)

    # 2-5. Process each file
    ingested_metadata: List[Dict] = []

    for file_path in files_to_ingest:
        file_result = _ingest_single_file(
            file_path=file_path,
            store=store,
            ledger=lgr,
            batch_id=batch_id,
            ingested_by=ingested_by,
        )

        result.files.append(file_result)

        if file_result.get("error"):
            result.total_errors += 1
            result.errors.append(file_result)
        elif file_result.get("duplicate"):
            result.total_duplicates += 1
            result.total_files_ingested += 1
            ingested_metadata.append(file_result)
        else:
            result.total_files_ingested += 1
            result.total_bytes += file_result.get("size_bytes", 0)
            ingested_metadata.append(file_result)

    # 6. Sequence grouping
    groups = group_by_sequence(ingested_metadata, time_window_minutes)
    result.sequence_groups = [asdict(g) for g in groups]

    for g in groups:
        lgr.append(
            action="batch.sequence_group_created",
            evidence_id=batch_id,
            actor=ingested_by,
            details={
                "group_id": g.group_id,
                "group_name": g.group_name,
                "member_count": len(g.members),
                "device_labels": g.device_labels,
            },
        )

    # 7. Write batch manifest
    result.completed_at = datetime.now(timezone.utc).isoformat()
    result.ledger_entries = lgr.entry_count

    manifest_dir = store.root / "manifests"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = manifest_dir / f"batch_{batch_id}.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(asdict(result), f, indent=2, default=str)
    result.manifest_path = str(manifest_path)

    # Record batch completion
    lgr.append(
        action="batch.ingest_complete",
        evidence_id=batch_id,
        actor=ingested_by,
        details={
            "total_files": result.total_files_found,
            "ingested": result.total_files_ingested,
            "duplicates": result.total_duplicates,
            "errors": result.total_errors,
            "groups": len(groups),
        },
    )

    logger.info(
        "Batch ingest %s complete: %d found, %d ingested, %d dups, %d errors, %d groups",
        batch_id[:8], result.total_files_found, result.total_files_ingested,
        result.total_duplicates, result.total_errors, len(groups),
    )
    return result


def _ingest_single_file(
    file_path: Path,
    store: EvidenceStore,
    ledger: IntegrityLedger,
    batch_id: str,
    ingested_by: str,
) -> Dict:
    """Ingest a single file, recording in ledger. Returns metadata dict."""
    fname = file_path.name

    try:
        # Parse BWC filename metadata
        parsed = parse_bwc_filename(fname)

        # Ingest into evidence store (handles hashing + duplicate check)
        ingest_result = store.ingest(
            source_path=str(file_path),
            original_filename=fname,
            ingested_by=ingested_by,
            device_label=parsed.device_label,
        )

        metadata = {
            "filename": fname,
            "evidence_id": ingest_result.evidence_id,
            "sha256": ingest_result.sha256,
            "size_bytes": ingest_result.metadata.size_bytes,
            "mime_type": ingest_result.metadata.mime_type,
            "stored_path": ingest_result.stored_path,
            "duplicate": ingest_result.duplicate,
            "device_label": parsed.device_label,
            "officer_name": parsed.officer_name,
            "clip_index": parsed.clip_index,
            "timestamp": parsed.timestamp.isoformat() if parsed.timestamp else None,
        }

        if not ingest_result.success:
            metadata["error"] = ingest_result.error
            ledger.append(
                action="file.ingest_error",
                evidence_id=ingest_result.evidence_id,
                sha256=ingest_result.sha256,
                actor=ingested_by,
                details={"filename": fname, "error": ingest_result.error, "batch_id": batch_id},
            )
        elif ingest_result.duplicate:
            ledger.append(
                action="file.ingest_duplicate",
                evidence_id=ingest_result.evidence_id,
                sha256=ingest_result.sha256,
                actor=ingested_by,
                details={"filename": fname, "batch_id": batch_id},
            )
        else:
            ledger.append(
                action="file.ingested",
                evidence_id=ingest_result.evidence_id,
                sha256=ingest_result.sha256,
                actor=ingested_by,
                details={
                    "filename": fname,
                    "size_bytes": ingest_result.metadata.size_bytes,
                    "device_label": parsed.device_label,
                    "batch_id": batch_id,
                },
            )

        return metadata

    except Exception as exc:
        error_id = str(uuid.uuid4())
        error_detail = {
            "filename": fname,
            "error": str(exc),
            "error_id": error_id,
            "batch_id": batch_id,
        }
        ledger.append(
            action="file.ingest_exception",
            evidence_id=error_id,
            actor=ingested_by,
            details=error_detail,
        )
        logger.error("Ingest error for %s: %s", fname, exc, exc_info=True)
        return {"filename": fname, "error": str(exc), "error_id": error_id}
