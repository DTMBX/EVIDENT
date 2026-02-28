"""
B30 Phase 7 — BWC Case Export & Compression
=============================================
Produces court-ready ZIP packages from the B30 evidence pipeline.

Features:
  - Batch composition: export any selection of evidence IDs
  - Size tiers: small (<100 MB), medium (<1 GB), large (1 GB+)
  - Deterministic naming: ``BWC_EXPORT_{case_ref}_{YYYYMMDD_HHMMSS}.zip``
  - Integrity ledger extract included as verification proof
  - SHA-256 of the final package recorded in the ledger
  - Reproducible from originals + ledger

Package layout::

    BWC_EXPORT_{case_ref}_{timestamp}/
      originals/          — immutable original evidence files
      derivatives/        — thumbnails, proxies, waveforms
      ledger_extract.jsonl — relevant ledger entries (hash-chained)
      search_index.json   — search index snapshot for included evidence
      manifest.json       — full package manifest with SHA-256 for every file
      integrity_report.md — human-readable verification summary

Design constraints:
  - Never modifies originals
  - Deterministic: same inputs → same logical output (modulo timestamp)
  - Self-verifying: manifest SHA-256 covers every file in package
  - Append-only: every export action recorded in the integrity ledger
"""

import hashlib
import json
import logging
import os
import zipfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Size tiers (bytes)
# ---------------------------------------------------------------------------
TIER_SMALL_MAX = 100 * 1024 * 1024       # 100 MB
TIER_MEDIUM_MAX = 1024 * 1024 * 1024     # 1 GB

# Supported derivative subdirectories
DERIVATIVE_TYPES = ("thumbnail", "proxy", "waveform", "transcript", "metadata")


def _compute_sha256(filepath: str, block_size: int = 65536) -> str:
    """Stream SHA-256 of a file (64 KiB blocks)."""
    sha = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(block_size), b""):
            sha.update(chunk)
    return sha.hexdigest()


def _size_tier(total_bytes: int) -> str:
    """Classify total package size into a tier label."""
    if total_bytes <= TIER_SMALL_MAX:
        return "small"
    if total_bytes <= TIER_MEDIUM_MAX:
        return "medium"
    return "large"


# ---------------------------------------------------------------------------
# Result data structure
# ---------------------------------------------------------------------------

@dataclass
class BWCExportResult:
    """Outcome of a BWC export operation."""
    success: bool
    export_path: str = ""
    package_sha256: str = ""
    evidence_count: int = 0
    file_count: int = 0
    total_bytes: int = 0
    size_tier: str = ""
    manifest: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "export_path": self.export_path,
            "package_sha256": self.package_sha256,
            "evidence_count": self.evidence_count,
            "file_count": self.file_count,
            "total_bytes": self.total_bytes,
            "size_tier": self.size_tier,
            "error": self.error,
            "warnings": self.warnings,
        }


# ---------------------------------------------------------------------------
# BWC Case Exporter
# ---------------------------------------------------------------------------

class BWCCaseExporter:
    """
    Builds court-ready ZIP packages from the B30 evidence pipeline.

    Consumes:
      - evidence_store/ originals and derivatives (filesystem)
      - integrity_ledger.jsonl (hash-chained audit trail)
      - search_index.json (optional, for included evidence)

    Produces:
      - Deterministic ZIP with manifest, ledger extract, and integrity report
    """

    def __init__(
        self,
        evidence_base: str = "evidence_store",
        export_dir: str = "exports/bwc",
        ledger=None,
    ):
        self._evidence_base = Path(evidence_base)
        self._export_dir = Path(export_dir)
        self._export_dir.mkdir(parents=True, exist_ok=True)
        self._ledger = ledger

    def export(
        self,
        evidence_ids: List[str],
        case_ref: str = "NOCASE",
        exported_by: str = "system",
        export_time: Optional[datetime] = None,
        include_derivatives: bool = True,
        include_search_index: bool = True,
        compression: int = zipfile.ZIP_DEFLATED,
    ) -> BWCExportResult:
        """
        Build a court-ready ZIP for the given evidence IDs.

        Args:
            evidence_ids: List of evidence UUIDs to include.
            case_ref: Case reference string for deterministic naming.
            exported_by: Identity of the actor performing the export.
            export_time: Override timestamp (for determinism in tests).
            include_derivatives: Include derivative files (thumbnails, etc.).
            include_search_index: Include search index snapshot.
            compression: ZIP compression method.

        Returns:
            BWCExportResult with package details.
        """
        if not evidence_ids:
            return BWCExportResult(success=False, error="No evidence IDs provided")

        if export_time is None:
            export_time = datetime.now(timezone.utc)

        timestamp = export_time.strftime("%Y%m%d_%H%M%S")
        package_name = f"BWC_EXPORT_{case_ref}_{timestamp}"
        zip_name = f"{package_name}.zip"
        zip_path = self._export_dir / zip_name

        warnings: List[str] = []
        file_manifest: List[Dict[str, Any]] = []
        total_bytes = 0
        evidence_found = 0

        try:
            with zipfile.ZipFile(str(zip_path), "w", compression) as zf:
                prefix = package_name

                # --- 1. Pack originals ---
                for eid in evidence_ids:
                    packed = self._pack_original(zf, prefix, eid, file_manifest)
                    if packed > 0:
                        evidence_found += 1
                        total_bytes += packed
                    else:
                        warnings.append(f"Original not found for evidence_id={eid}")

                # --- 2. Pack derivatives ---
                if include_derivatives:
                    for eid in evidence_ids:
                        total_bytes += self._pack_derivatives(
                            zf, prefix, eid, file_manifest
                        )

                # --- 3. Ledger extract ---
                ledger_bytes = self._pack_ledger_extract(
                    zf, prefix, evidence_ids
                )
                if ledger_bytes > 0:
                    total_bytes += ledger_bytes

                # --- 4. Search index snapshot ---
                if include_search_index:
                    idx_bytes = self._pack_search_index(
                        zf, prefix, evidence_ids
                    )
                    total_bytes += idx_bytes

                # --- 5. Manifest ---
                tier = _size_tier(total_bytes)
                manifest_dict = {
                    "package_name": package_name,
                    "case_ref": case_ref,
                    "exported_at": export_time.isoformat(),
                    "exported_by": exported_by,
                    "evidence_ids": evidence_ids,
                    "evidence_found": evidence_found,
                    "file_count": len(file_manifest),
                    "total_bytes": total_bytes,
                    "size_tier": tier,
                    "files": file_manifest,
                }
                manifest_json = json.dumps(manifest_dict, indent=2, sort_keys=True)
                manifest_sha = hashlib.sha256(manifest_json.encode("utf-8")).hexdigest()
                manifest_dict["manifest_sha256"] = manifest_sha
                # Rewrite with the hash included
                manifest_json = json.dumps(manifest_dict, indent=2, sort_keys=True)
                zf.writestr(f"{prefix}/manifest.json", manifest_json)

                # --- 6. Integrity report ---
                report_md = self._generate_integrity_report(
                    manifest_dict, file_manifest, export_time
                )
                zf.writestr(f"{prefix}/integrity_report.md", report_md)

            # --- 7. Package hash ---
            pkg_sha256 = _compute_sha256(str(zip_path))

            # --- 8. Record in ledger ---
            if self._ledger is not None:
                self._ledger.append(
                    action="EXPORT_PACKAGE",
                    evidence_id=",".join(evidence_ids[:10]),
                    sha256=pkg_sha256,
                    actor=exported_by,
                    details={
                        "case_ref": case_ref,
                        "package_name": zip_name,
                        "evidence_count": evidence_found,
                        "file_count": len(file_manifest),
                        "total_bytes": total_bytes,
                        "size_tier": tier,
                    },
                )

            return BWCExportResult(
                success=True,
                export_path=str(zip_path),
                package_sha256=pkg_sha256,
                evidence_count=evidence_found,
                file_count=len(file_manifest),
                total_bytes=total_bytes,
                size_tier=tier,
                manifest=manifest_dict,
                warnings=warnings,
            )

        except Exception as exc:
            logger.exception("Export failed: %s", exc)
            # Clean up partial ZIP
            if zip_path.exists():
                zip_path.unlink()
            return BWCExportResult(
                success=False,
                error=str(exc),
                warnings=warnings,
            )

    # ------------------------------------------------------------------
    # Pack originals
    # ------------------------------------------------------------------

    def _pack_original(
        self,
        zf: zipfile.ZipFile,
        prefix: str,
        evidence_id: str,
        file_manifest: List[Dict],
    ) -> int:
        """Pack the original file for an evidence ID. Returns bytes packed."""
        manifest_path = self._evidence_base / "manifests" / f"{evidence_id}.json"
        if not manifest_path.exists():
            return 0

        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest = json.load(f)
        except (json.JSONDecodeError, OSError):
            return 0

        sha256 = manifest.get("sha256", "")
        original_filename = manifest.get("original_filename", "")
        if not sha256:
            return 0

        original_path = self._evidence_base / "originals" / sha256
        if not original_path.exists():
            return 0

        arc_name = f"{prefix}/originals/{original_filename or sha256}"
        zf.write(str(original_path), arc_name)
        size = original_path.stat().st_size
        file_manifest.append({
            "path": arc_name,
            "sha256": sha256,
            "size_bytes": size,
            "type": "original",
            "evidence_id": evidence_id,
        })
        return size

    # ------------------------------------------------------------------
    # Pack derivatives
    # ------------------------------------------------------------------

    def _pack_derivatives(
        self,
        zf: zipfile.ZipFile,
        prefix: str,
        evidence_id: str,
        file_manifest: List[Dict],
    ) -> int:
        """Pack all derivative files for an evidence ID. Returns bytes packed."""
        manifest_path = self._evidence_base / "manifests" / f"{evidence_id}.json"
        if not manifest_path.exists():
            return 0

        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest = json.load(f)
        except (json.JSONDecodeError, OSError):
            return 0

        sha256 = manifest.get("sha256", "")
        if not sha256:
            return 0

        deriv_base = self._evidence_base / "derivatives" / sha256
        if not deriv_base.exists():
            return 0

        total = 0
        for dtype in DERIVATIVE_TYPES:
            dtype_dir = deriv_base / dtype
            if not dtype_dir.exists():
                continue
            for fpath in sorted(dtype_dir.iterdir()):
                if fpath.is_file():
                    arc_name = (
                        f"{prefix}/derivatives/{evidence_id}/{dtype}/{fpath.name}"
                    )
                    zf.write(str(fpath), arc_name)
                    fsize = fpath.stat().st_size
                    fhash = _compute_sha256(str(fpath))
                    file_manifest.append({
                        "path": arc_name,
                        "sha256": fhash,
                        "size_bytes": fsize,
                        "type": f"derivative:{dtype}",
                        "evidence_id": evidence_id,
                    })
                    total += fsize
        return total

    # ------------------------------------------------------------------
    # Pack ledger extract
    # ------------------------------------------------------------------

    def _pack_ledger_extract(
        self,
        zf: zipfile.ZipFile,
        prefix: str,
        evidence_ids: List[str],
    ) -> int:
        """Extract ledger entries for the given evidence IDs and pack them."""
        if self._ledger is None:
            return 0

        all_entries = self._ledger.read_all()
        eid_set = set(evidence_ids)
        relevant = [
            e for e in all_entries
            if e.get("evidence_id", "") in eid_set
            or any(eid in e.get("evidence_id", "") for eid in eid_set)
        ]

        if not relevant:
            return 0

        # Write as JSONL (preserving format)
        lines = []
        for entry in relevant:
            lines.append(
                json.dumps(entry, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
            )
        content = "\n".join(lines) + "\n"
        arc_name = f"{prefix}/ledger_extract.jsonl"
        zf.writestr(arc_name, content)
        return len(content.encode("utf-8"))

    # ------------------------------------------------------------------
    # Pack search index snapshot
    # ------------------------------------------------------------------

    def _pack_search_index(
        self,
        zf: zipfile.ZipFile,
        prefix: str,
        evidence_ids: List[str],
    ) -> int:
        """Pack a filtered search index for included evidence only."""
        index_path = self._evidence_base / "search_index.json"
        if not index_path.exists():
            return 0

        try:
            with open(index_path, "r", encoding="utf-8") as f:
                full_index = json.load(f)
        except (json.JSONDecodeError, OSError):
            return 0

        eid_set = set(evidence_ids)
        # Filter documents to only included evidence
        if isinstance(full_index, dict) and "documents" in full_index:
            filtered = {
                k: v for k, v in full_index["documents"].items()
                if k in eid_set
            }
            snapshot = {"documents": filtered, "evidence_ids": evidence_ids}
        else:
            snapshot = full_index

        content = json.dumps(snapshot, indent=2)
        arc_name = f"{prefix}/search_index.json"
        zf.writestr(arc_name, content)
        return len(content.encode("utf-8"))

    # ------------------------------------------------------------------
    # Integrity report
    # ------------------------------------------------------------------

    @staticmethod
    def _generate_integrity_report(
        manifest: Dict[str, Any],
        file_manifest: List[Dict],
        export_time: datetime,
    ) -> str:
        """Generate a human-readable Markdown integrity report."""
        lines = [
            "# Evidence Export Integrity Report",
            "",
            f"**Package:** {manifest['package_name']}",
            f"**Case Reference:** {manifest['case_ref']}",
            f"**Exported At:** {export_time.isoformat()}",
            f"**Exported By:** {manifest['exported_by']}",
            f"**Size Tier:** {manifest['size_tier']}",
            "",
            "## Summary",
            "",
            f"- Evidence items requested: {len(manifest['evidence_ids'])}",
            f"- Evidence items found: {manifest['evidence_found']}",
            f"- Total files: {manifest['file_count']}",
            f"- Total bytes: {manifest['total_bytes']:,}",
            "",
            "## File Inventory",
            "",
            "| # | Path | SHA-256 | Size | Type |",
            "|---|------|---------|------|------|",
        ]

        for idx, entry in enumerate(file_manifest, 1):
            sha_short = entry["sha256"][:16] + "..."
            lines.append(
                f"| {idx} | {entry['path']} | {sha_short} | "
                f"{entry['size_bytes']:,} | {entry['type']} |"
            )

        # Composite hash of all file hashes
        composite = hashlib.sha256()
        for entry in sorted(file_manifest, key=lambda e: e["path"]):
            composite.update(entry["sha256"].encode("utf-8"))
        composite_hash = composite.hexdigest()

        lines.extend([
            "",
            "## Verification",
            "",
            f"- Composite file hash: `{composite_hash}`",
            f"- Manifest SHA-256: `{manifest.get('manifest_sha256', 'N/A')}`",
            "",
            "To verify: recompute SHA-256 for each file and compare against "
            "the manifest. The composite hash is the SHA-256 of all individual "
            "file hashes concatenated in path-sorted order.",
            "",
            "---",
            f"*Generated {export_time.isoformat()} — Evident Technologies*",
        ])
        return "\n".join(lines)
