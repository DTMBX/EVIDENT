"""
B30 Phase 2 — Integrity Ledger (Append-Only JSONL)
====================================================
True append-only integrity ledger backed by a JSONL flat file.

Each entry is a single JSON line appended to the file — never rewritten.
This provides crash-safe, tamper-evident logging independent of the
database and manifest JSON files.

Design principles:
  - Append only: file is opened in 'a' mode; never truncated.
  - Each line is self-contained JSON with SHA-256 chain link.
  - Each entry includes the SHA-256 of the previous entry (hash chain).
  - File can be independently verified without the database.

Verification:
  To verify the ledger:
    1. Read line by line.
    2. For each line, compute SHA-256 of the raw bytes.
    3. Verify the next line's `prev_hash` matches.
    4. First entry's `prev_hash` must be the zero hash (64 zeros).
"""

import hashlib
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

ZERO_HASH = "0" * 64  # Genesis prev_hash


class IntegrityLedger:
    """
    Append-only JSONL ledger for evidence integrity tracking.

    Each appended entry is a single JSON line containing:
      - seq: monotonically increasing sequence number
      - timestamp: ISO-8601 UTC
      - action: what happened
      - evidence_id: UUID of the evidence item
      - sha256: hash of the evidence/artifact this entry concerns
      - actor: who/what performed the action
      - details: arbitrary metadata dict
      - prev_hash: SHA-256 of the previous entry's raw JSON bytes
      - entry_hash: SHA-256 of this entry (computed before writing)
    """

    def __init__(self, ledger_path: str = "evidence_store/integrity_ledger.jsonl"):
        self._path = Path(ledger_path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._seq = self._count_entries()
        self._prev_hash = self._last_entry_hash()

    @property
    def entry_count(self) -> int:
        """Return the current number of entries in the ledger."""
        return self._seq

    def _count_entries(self) -> int:
        """Count existing entries in the ledger file."""
        if not self._path.exists():
            return 0
        count = 0
        with open(self._path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    count += 1
        return count

    def _last_entry_hash(self) -> str:
        """Compute hash of last entry, or return ZERO_HASH if empty."""
        if not self._path.exists() or self._seq == 0:
            return ZERO_HASH
        last_line = ""
        with open(self._path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    last_line = line.strip()
        if not last_line:
            return ZERO_HASH
        return hashlib.sha256(last_line.encode("utf-8")).hexdigest()

    def append(
        self,
        action: str,
        evidence_id: str = "",
        sha256: str = "",
        actor: str = "system",
        details: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Append a new entry to the integrity ledger.

        Returns the entry dict (including computed hashes).
        """
        self._seq += 1
        now = datetime.now(timezone.utc).isoformat()

        entry = {
            "seq": self._seq,
            "timestamp": now,
            "action": action,
            "evidence_id": evidence_id,
            "sha256": sha256,
            "actor": actor,
            "details": details or {},
            "prev_hash": self._prev_hash,
        }

        # Compute entry hash (exclude entry_hash field itself)
        entry_bytes = json.dumps(entry, sort_keys=True, separators=(",", ":")).encode("utf-8")
        entry_hash = hashlib.sha256(entry_bytes).hexdigest()
        entry["entry_hash"] = entry_hash

        # Serialize to single line
        line = json.dumps(entry, sort_keys=True, separators=(",", ":"), ensure_ascii=True)

        # Append to file (atomic at OS level for single-line writes)
        with open(self._path, "a", encoding="utf-8") as f:
            f.write(line + "\n")
            f.flush()
            os.fsync(f.fileno())

        # Update chain state
        self._prev_hash = hashlib.sha256(line.encode("utf-8")).hexdigest()

        logger.info(
            "Ledger entry #%d: %s evidence=%s sha256=%s",
            self._seq, action, evidence_id[:12] if evidence_id else "-", sha256[:12] if sha256 else "-",
        )
        return entry

    def verify(self) -> List[Dict[str, Any]]:
        """
        Verify the integrity of the entire ledger.

        Returns a list of error dicts. An empty list means the ledger is intact.
        """
        errors = []
        if not self._path.exists():
            return errors  # Empty ledger is valid

        prev_hash = ZERO_HASH
        with open(self._path, "r", encoding="utf-8") as f:
            for line_num, raw_line in enumerate(f, start=1):
                raw_line = raw_line.strip()
                if not raw_line:
                    continue

                try:
                    entry = json.loads(raw_line)
                except json.JSONDecodeError as e:
                    errors.append({
                        "line": line_num,
                        "error": f"Invalid JSON: {e}",
                    })
                    continue

                # Check prev_hash chain
                if entry.get("prev_hash") != prev_hash:
                    errors.append({
                        "line": line_num,
                        "seq": entry.get("seq"),
                        "error": (
                            f"Chain broken: expected prev_hash={prev_hash[:16]}..., "
                            f"got {entry.get('prev_hash', '?')[:16]}..."
                        ),
                    })

                # Check entry_hash
                stored_entry_hash = entry.pop("entry_hash", None)
                recomputed = json.dumps(entry, sort_keys=True, separators=(",", ":")).encode("utf-8")
                recomputed_hash = hashlib.sha256(recomputed).hexdigest()
                if stored_entry_hash and stored_entry_hash != recomputed_hash:
                    errors.append({
                        "line": line_num,
                        "seq": entry.get("seq"),
                        "error": (
                            f"Entry hash mismatch: stored={stored_entry_hash[:16]}..., "
                            f"computed={recomputed_hash[:16]}..."
                        ),
                    })

                # Update chain
                prev_hash = hashlib.sha256(raw_line.encode("utf-8")).hexdigest()

        return errors

    def read_all(self) -> List[Dict[str, Any]]:
        """Read all entries from the ledger."""
        if not self._path.exists():
            return []
        entries = []
        with open(self._path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    entries.append(json.loads(line))
        return entries

    @property
    def entry_count(self) -> int:
        return self._seq

    @property
    def path(self) -> str:
        return str(self._path)
