# B30 Phase 2 — Ingest & Integrity Specification

## Overview

Phase 2 hardens the evidence ingest pipeline with:

1. **Append-only integrity ledger** (JSONL with SHA-256 hash chain)
2. **Batch folder ingest** (messy BWC dump → structured evidence store)
3. **BWC filename parsing** (officer, timestamp, device, clip index)
4. **Sequence grouping** (time-adjacent clips from same incident)
5. **Duplicate detection** (content-addressed, idempotent re-runs)

---

## Components

### 1. IntegrityLedger (`services/integrity_ledger.py`)

Append-only JSONL flat file providing tamper-evident logging independent of the
database.

**Entry format (one JSON line per entry):**

```json
{
  "seq": 1,
  "timestamp": "2025-06-16T12:00:00+00:00",
  "action": "file.ingested",
  "evidence_id": "uuid-v4",
  "sha256": "abc123...",
  "actor": "system",
  "details": {},
  "prev_hash": "0000...0000",
  "entry_hash": "def456..."
}
```

**Hash chain rule:**

- Entry N's `prev_hash` = SHA-256 of the raw JSON bytes of entry N-1's line.
- Entry 1's `prev_hash` = `"0" * 64` (genesis/zero hash).
- `entry_hash` = SHA-256 of the entry *without* the `entry_hash` field.

**Verification:**

```python
from services.integrity_ledger import IntegrityLedger

ledger = IntegrityLedger()
errors = ledger.verify()  # Returns [] if intact
```

An empty list means every chain link and entry hash is valid. Any tampering
(modification, insertion, deletion) breaks the chain and produces error entries.

**Storage:** `evidence_store/integrity_ledger.jsonl` (default path).

### 2. Batch Folder Ingest (`services/batch_ingest.py`)

Ingests a folder of BWC files (including nested subdirectories) into the
evidence store.

**Pipeline per file:**

1. Walk folder → discover files with supported extensions.
2. SHA-256 hash each file (streaming, 64 KiB blocks).
3. Check for duplicates (same hash already stored → flag, don't re-copy).
4. Ingest into `EvidenceStore` (immutable copy + post-copy verification).
5. Parse BWC filename → extract officer, timestamp, device, clip index.
6. Record every action in the IntegrityLedger.
7. Group files by time adjacency + device label.
8. Write batch manifest JSON.

**Supported extensions:**

| Category | Extensions |
|----------|-----------|
| Video | `.mp4`, `.avi`, `.mov`, `.mkv`, `.webm`, `.flv` |
| Audio | `.mp3`, `.wav`, `.flac`, `.aac`, `.m4a` |
| Images | `.jpg`, `.jpeg`, `.png`, `.tiff`, `.bmp`, `.webp`, `.gif` |
| Documents | `.pdf`, `.docx`, `.doc`, `.txt` |

**Usage:**

```python
from services.batch_ingest import ingest_folder
from services.evidence_store import EvidenceStore
from services.integrity_ledger import IntegrityLedger

result = ingest_folder(
    folder_path="/path/to/bwc/dump",
    evidence_store=EvidenceStore(),
    ledger=IntegrityLedger(),
    ingested_by="analyst_name",
    case_id="case-uuid",
    time_window_minutes=30,
)

print(f"Found: {result.total_files_found}")
print(f"Ingested: {result.total_files_ingested}")
print(f"Duplicates: {result.total_duplicates}")
print(f"Errors: {result.total_errors}")
print(f"Groups: {len(result.sequence_groups)}")
```

### 3. BWC Filename Parser

Parses BWC-standard naming patterns:

```
{OfficerName}_{YYYYMMDDHHMI}_{DeviceSerial}-{ClipIndex}.ext
```

Example: `BryanMerritt_202511292257_BWL7137497-0.mp4`

Extracts:

| Field | Value |
|-------|-------|
| `officer_name` | `BryanMerritt` |
| `timestamp` | `2025-11-29 22:57` |
| `device_label` | `BWL7137497` |
| `clip_index` | `0` |
| `extension` | `mp4` |

Falls back to regex heuristics for non-standard filenames—extracts whatever
fields it can.

### 4. Sequence Grouping

Groups ingested files into incident sequences based on:

- **Time adjacency:** files whose timestamps fall within `time_window_minutes`
  of the previous file in the sorted sequence.
- **Device labels:** tracked per group but not used as a grouping constraint
  (an incident may involve multiple cameras).

Default window: 30 minutes.

Groups are named `BWC_{device_labels}_{start_time}` when device labels are
available.

---

## Batch Manifest

Written to `evidence_store/manifests/batch_{batch_id}.json`.

Contains:

- `batch_id` — UUID
- `source_folder` — path ingested
- `started_at` / `completed_at` — ISO-8601 UTC
- `total_files_found` / `total_files_ingested` / `total_duplicates` / `total_errors`
- `files[]` — per-file metadata (SHA-256, evidence_id, device, officer, etc.)
- `errors[]` — per-file error details
- `sequence_groups[]` — grouped file lists

---

## Ledger Actions

| Action | When |
|--------|------|
| `batch.ingest_start` | Batch begins |
| `file.ingested` | File successfully ingested |
| `file.ingest_duplicate` | File hash already exists |
| `file.ingest_error` | File ingest returned success=false |
| `file.ingest_exception` | Unexpected exception during ingest |
| `batch.sequence_group_created` | Sequence group formed |
| `batch.ingest_complete` | Batch finished |
| `batch.ingest_error` | Folder not found / invalid |

---

## Invariants

1. **Originals are immutable.** No file in `evidence_store/originals/` is ever
   overwritten or modified.
2. **Ledger is append-only.** The JSONL file is only opened in append mode.
   Hash chain links every entry to its predecessor.
3. **Idempotent.** Running the same ingest twice produces duplicate flags, not
   duplicate files.
4. **Fail-open for batch, fail-closed per file.** A single file error does not
   abort the batch. But each file that fails is recorded in both the result and
   the ledger.
5. **Deterministic hashing.** SHA-256, streaming, 64 KiB blocks. Same file →
   same hash. Always.

---

## Test Coverage

| Test File | Tests | Coverage |
|-----------|-------|----------|
| `tests/test_integrity_ledger.py` | 13 | Append, chain, verify, tamper detection, persistence |
| `tests/test_batch_ingest.py` | 23 | Filename parsing, grouping, full ingest, dedup, ledger integrity |

---

## Files Created/Modified in Phase 2

| File | Status |
|------|--------|
| `services/integrity_ledger.py` | NEW |
| `services/batch_ingest.py` | NEW |
| `tests/test_integrity_ledger.py` | NEW |
| `tests/test_batch_ingest.py` | NEW |
| `docs/b30/INGEST_SPEC.md` | NEW (this file) |
