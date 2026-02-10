"""
Court-Ready Evidence Export
============================
Produces a self-contained ZIP archive suitable for court submission.

Package contents:
  evidence_package_<evidence_id>/
    originals/          — Immutable originals
    derivatives/        — Thumbnails, proxies, transcripts
    manifest.json       — Hashes, sizes, relationships, metadata
    audit_log.json      — Full append-only audit trail
    integrity_report.md — Human-readable integrity summary

Design principles:
  - Deterministic: Same inputs → same logical outputs.
  - Self-verifying: Manifest contains hashes for ALL included files.
  - Human-readable: Integrity report is plain Markdown.
  - No external dependencies at read time.
"""

import hashlib
import json
import logging
import os
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from services.evidence_store import (
    EvidenceStore,
    compute_file_hash,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Export data structure
# ---------------------------------------------------------------------------


class EvidenceExportResult:
    """Result of an evidence export operation."""

    def __init__(
        self,
        success: bool,
        export_path: str = "",
        evidence_id: str = "",
        file_count: int = 0,
        total_bytes: int = 0,
        package_sha256: str = "",
        error: Optional[str] = None,
    ):
        self.success = success
        self.export_path = export_path
        self.evidence_id = evidence_id
        self.file_count = file_count
        self.total_bytes = total_bytes
        self.package_sha256 = package_sha256
        self.error = error

    def to_dict(self) -> Dict:
        return {
            "success": self.success,
            "export_path": self.export_path,
            "evidence_id": self.evidence_id,
            "file_count": self.file_count,
            "total_bytes": self.total_bytes,
            "package_sha256": self.package_sha256,
            "error": self.error,
        }


# ---------------------------------------------------------------------------
# Export builder
# ---------------------------------------------------------------------------


class EvidenceExporter:
    """
    Builds court-ready evidence packages from the evidence store.

    Each package is a ZIP file containing originals, derivatives,
    manifest, audit log, and a human-readable integrity report.
    """

    def __init__(self, evidence_store: EvidenceStore, export_dir: str = "exports"):
        self._store = evidence_store
        self._export_dir = Path(export_dir).resolve()
        self._export_dir.mkdir(parents=True, exist_ok=True)

    def export(
        self,
        evidence_id: str,
        include_derivatives: bool = True,
        exported_by: Optional[str] = None,
    ) -> EvidenceExportResult:
        """
        Build and write a court-ready evidence export package.

        Args:
            evidence_id: UUID of the evidence to export.
            include_derivatives: Whether to include thumbnails/proxies.
            exported_by: Name of the user performing the export.

        Returns:
            EvidenceExportResult with path to the ZIP file.
        """
        manifest = self._store.load_manifest(evidence_id)
        if manifest is None:
            return EvidenceExportResult(
                success=False,
                evidence_id=evidence_id,
                error=f"Manifest not found for evidence_id={evidence_id}",
            )

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        package_name = f"evidence_package_{evidence_id[:8]}_{timestamp}"
        zip_path = self._export_dir / f"{package_name}.zip"

        try:
            file_count = 0
            total_bytes = 0
            # Track files added for the integrity report
            included_files: List[Dict] = []

            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
                prefix = package_name

                # -- 1. Original file --
                original_path = self._store.get_original_path(
                    manifest.ingest.sha256
                )
                if original_path and os.path.exists(original_path):
                    arcname = f"{prefix}/originals/{manifest.ingest.original_filename}"
                    zf.write(original_path, arcname)
                    fsize = os.path.getsize(original_path)
                    file_count += 1
                    total_bytes += fsize
                    included_files.append({
                        "path": arcname,
                        "sha256": manifest.ingest.sha256,
                        "size_bytes": fsize,
                        "type": "original",
                    })

                # -- 2. Derivatives --
                if include_derivatives:
                    for deriv in manifest.derivatives:
                        deriv_path = self._store.get_derivative_path(
                            manifest.ingest.sha256,
                            deriv.derivative_type,
                            deriv.filename,
                        )
                        if deriv_path and os.path.exists(deriv_path):
                            arcname = (
                                f"{prefix}/derivatives/"
                                f"{deriv.derivative_type}/{deriv.filename}"
                            )
                            zf.write(deriv_path, arcname)
                            fsize = os.path.getsize(deriv_path)
                            file_count += 1
                            total_bytes += fsize
                            included_files.append({
                                "path": arcname,
                                "sha256": deriv.sha256,
                                "size_bytes": fsize,
                                "type": f"derivative:{deriv.derivative_type}",
                            })

                # -- 3. Manifest JSON --
                manifest_json = json.dumps(
                    {
                        "evidence_id": manifest.evidence_id,
                        "ingest": {
                            "original_filename": manifest.ingest.original_filename,
                            "mime_type": manifest.ingest.mime_type,
                            "size_bytes": manifest.ingest.size_bytes,
                            "sha256": manifest.ingest.sha256,
                            "ingested_at": manifest.ingest.ingested_at,
                            "ingested_by": manifest.ingest.ingested_by,
                            "device_label": manifest.ingest.device_label,
                        },
                        "derivatives": [
                            {
                                "type": d.derivative_type,
                                "filename": d.filename,
                                "sha256": d.sha256,
                                "size_bytes": d.size_bytes,
                                "created_at": d.created_at,
                            }
                            for d in manifest.derivatives
                        ],
                        "included_files": included_files,
                        "export_metadata": {
                            "exported_at": timestamp,
                            "exported_by": exported_by,
                            "include_derivatives": include_derivatives,
                        },
                    },
                    indent=2,
                    ensure_ascii=False,
                )
                zf.writestr(f"{prefix}/manifest.json", manifest_json)
                file_count += 1
                total_bytes += len(manifest_json.encode("utf-8"))

                # -- 4. Audit log JSON --
                audit_json = json.dumps(
                    {
                        "evidence_id": manifest.evidence_id,
                        "audit_entries": manifest.audit_entries,
                        "entry_count": len(manifest.audit_entries),
                    },
                    indent=2,
                    default=str,
                    ensure_ascii=False,
                )
                zf.writestr(f"{prefix}/audit_log.json", audit_json)
                file_count += 1
                total_bytes += len(audit_json.encode("utf-8"))

                # -- 5. Integrity report (Markdown) --
                report_md = self._build_integrity_report(
                    manifest, included_files, exported_by, timestamp
                )
                zf.writestr(f"{prefix}/integrity_report.md", report_md)
                file_count += 1
                total_bytes += len(report_md.encode("utf-8"))

            # Hash the final package
            package_digest = compute_file_hash(str(zip_path))

            # Record export in audit if possible
            self._store.append_audit(
                evidence_id=evidence_id,
                action="exported",
                actor=exported_by,
                details={
                    "package_path": str(zip_path),
                    "package_sha256": package_digest.sha256,
                    "file_count": file_count,
                    "total_bytes": total_bytes,
                },
            )

            logger.info(
                "Exported evidence %s: %s (%d files, %d bytes, sha256=%s)",
                evidence_id,
                zip_path.name,
                file_count,
                total_bytes,
                package_digest.sha256[:16],
            )

            return EvidenceExportResult(
                success=True,
                export_path=str(zip_path),
                evidence_id=evidence_id,
                file_count=file_count,
                total_bytes=total_bytes,
                package_sha256=package_digest.sha256,
            )

        except Exception as exc:
            logger.error(
                "Export failed for %s: %s", evidence_id, exc, exc_info=True
            )
            # Clean up partial ZIP
            if zip_path.exists():
                zip_path.unlink()
            return EvidenceExportResult(
                success=False,
                evidence_id=evidence_id,
                error=str(exc),
            )

    # -- integrity report generation -----------------------------------------

    @staticmethod
    def _build_integrity_report(
        manifest,
        included_files: List[Dict],
        exported_by: Optional[str],
        timestamp: str,
    ) -> str:
        """Generate a human-readable Markdown integrity report."""
        lines = [
            "# Evidence Integrity Report",
            "",
            f"**Evidence ID:** {manifest.evidence_id}",
            f"**Export Timestamp:** {timestamp}",
            f"**Exported By:** {exported_by or 'system'}",
            "",
            "---",
            "",
            "## Original File",
            "",
            f"- **Filename:** {manifest.ingest.original_filename}",
            f"- **MIME Type:** {manifest.ingest.mime_type}",
            f"- **Size:** {manifest.ingest.size_bytes:,} bytes",
            f"- **SHA-256:** `{manifest.ingest.sha256}`",
            f"- **Ingested At:** {manifest.ingest.ingested_at}",
            f"- **Ingested By:** {manifest.ingest.ingested_by or 'system'}",
        ]

        if manifest.ingest.device_label:
            lines.append(f"- **Device:** {manifest.ingest.device_label}")

        lines.extend([
            "",
            "---",
            "",
            "## Derivatives",
            "",
        ])

        if manifest.derivatives:
            lines.append("| Type | Filename | SHA-256 | Size |")
            lines.append("|------|----------|---------|------|")
            for d in manifest.derivatives:
                lines.append(
                    f"| {d.derivative_type} | {d.filename} | "
                    f"`{d.sha256[:16]}...` | {d.size_bytes:,} bytes |"
                )
        else:
            lines.append("No derivatives included in this export.")

        lines.extend([
            "",
            "---",
            "",
            "## Audit Trail",
            "",
            f"Total entries: {len(manifest.audit_entries)}",
            "",
        ])

        for entry in manifest.audit_entries:
            ts = entry.get("timestamp", "N/A")
            action = entry.get("action", "N/A")
            actor = entry.get("actor", "system")
            lines.append(f"- **{ts}** — {action} (by {actor})")

        lines.extend([
            "",
            "---",
            "",
            "## Package Contents",
            "",
            "| File | Type | SHA-256 | Size |",
            "|------|------|---------|------|",
        ])

        for f in included_files:
            sha_display = f["sha256"][:16] + "..." if f["sha256"] else "N/A"
            lines.append(
                f"| {f['path']} | {f['type']} | `{sha_display}` | "
                f"{f['size_bytes']:,} bytes |"
            )

        lines.extend([
            "",
            "---",
            "",
            "## Verification Instructions",
            "",
            "To verify the integrity of the original file:",
            "",
            "```",
            f"certutil -hashfile <original_file> SHA256",
            "```",
            "",
            f"Expected hash: `{manifest.ingest.sha256}`",
            "",
            "Any deviation from this hash indicates the file has been "
            "altered since intake.",
            "",
            "---",
            "",
            f"*Report generated {timestamp} by Evident Technologies*",
        ])

        return "\n".join(lines)
