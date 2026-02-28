# B30 — Evidence Data Model

**Date:** 2026-02-18
**Phase:** P1 — Unified Evidence Graph + Artifact Model

---

## Overview

B30 extends the existing evidence data model with four new tables, all
backwards-compatible with existing schema. No existing tables are modified.

## New Tables

### `derived_artifact`

Tracks every derivative file (proxy video, thumbnail, waveform, transcript,
OCR text, index shard) with full provenance linking to originals via SHA-256.

| Column | Type | Description |
|---|---|---|
| id | Integer PK | Auto-increment |
| evidence_id | FK → evidence_item | Link to original |
| original_sha256 | String(64) | SHA-256 of the original file |
| artifact_type | String(50) | thumbnail, proxy, waveform, transcript, ocr_text, etc. |
| stored_path | String(1000) | Canonical filesystem path |
| filename | String(500) | Human-readable filename |
| sha256 | String(64) | SHA-256 of this derivative |
| size_bytes | Integer | File size |
| mime_type | String(100) | MIME type |
| parameters_json | Text | JSON: generation parameters for reproducibility |
| is_current | Boolean | True if this is the latest version |
| supersedes_id | FK → derived_artifact | Previous version (if any) |
| created_at | DateTime | UTC timestamp |
| created_by_id | FK → users | Who/what created it |
| is_deleted | Boolean | Soft-delete flag |

### `evidence_marker`

Non-destructive annotations on evidence items (timecodes for media,
pages for documents).

| Column | Type | Description |
|---|---|---|
| id | Integer PK | Auto-increment |
| evidence_id | FK → evidence_item | Target evidence |
| case_id | FK → legal_case | Optional case scope |
| start_seconds | Float | Media start timecode |
| end_seconds | Float | Media end timecode |
| page_number | Integer | Document page |
| char_offset_start | Integer | Text character offset start |
| char_offset_end | Integer | Text character offset end |
| marker_type | String(50) | note, highlight, flag, issue, tag |
| title | String(300) | Short label |
| body | Text | Full annotation text |
| tags_json | Text | JSON array of tag strings |
| confidence | Float | 0.0–1.0 |
| severity | String(20) | info, warning, critical |
| author_id | FK → users | Who created it |
| author_name | String(300) | Human-readable author |
| is_current | Boolean | Latest version flag |
| supersedes_id | FK → evidence_marker | Previous version |
| created_at | DateTime | UTC timestamp |
| is_deleted | Boolean | Soft-delete flag |

### `evidence_sequence_group` + `evidence_sequence_group_member`

Groups related evidence items (e.g., BWC clips from the same incident).

**evidence_sequence_group:**

| Column | Type | Description |
|---|---|---|
| id | Integer PK | — |
| case_id | FK → legal_case | Optional case scope |
| group_name | String(300) | Human-readable label |
| group_type | String(50) | auto, manual, device, time_window |
| start_time | DateTime | Earliest clip start |
| end_time | DateTime | Latest clip end |
| device_labels_json | Text | JSON array of device labels |
| grouping_algorithm | String(100) | Algorithm used |
| grouping_parameters_json | Text | Algorithm parameters |
| created_at | DateTime | UTC |
| created_by_id | FK → users | — |

**evidence_sequence_group_member:**

| Column | Type | Description |
|---|---|---|
| id | Integer PK | — |
| group_id | FK → evidence_sequence_group | — |
| evidence_id | FK → evidence_item | — |
| sequence_index | Integer | Order within group |
| device_label | String(200) | Device label for this clip |
| clip_start_time | DateTime | Individual clip start |

### `b30_audit_event`

Enhanced audit events with correlation IDs for batch operations.

| Column | Type | Description |
|---|---|---|
| id | Integer PK | — |
| correlation_id | String(36) | UUID linking related events |
| action | String(100) | Action constant |
| component | String(100) | Pipeline component name |
| actor_id | FK → users | — |
| actor_name | String(300) | — |
| ip_address | String(45) | — |
| evidence_id | FK → evidence_item | Optional link |
| evidence_sha256 | String(64) | — |
| details_json | Text | Structured metadata |
| timestamp | DateTime | UTC, immutable |

## Relationships to Existing Models

```
EvidenceItem (existing)
  ├── derived_artifacts[]      (new, via DerivedArtifact)
  ├── markers[]                (new, via EvidenceMarker)
  ├── chain_of_custody[]       (existing)
  ├── analysis_results[]       (existing)
  ├── tags[]                   (existing)
  └── case_evidence_links[]    (existing)

EvidenceSequenceGroup (new)
  └── members[]                (via EvidenceSequenceGroupMember)
       └── evidence            (→ EvidenceItem)

B30AuditEvent (new, supplement to ChainOfCustody)
  └── actor                    (→ User)
```

## Migration Notes

- All new tables use `db.Model` from `auth.models` (same as existing).
- No existing columns or constraints are altered.
- Migration is additive only — safe for `CREATE TABLE` without touching existing data.
- Rollback: `DROP TABLE` the four new tables.
