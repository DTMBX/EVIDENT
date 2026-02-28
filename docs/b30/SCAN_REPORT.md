# B30 — Discovery Scan Report

**Date:** 2026-02-18
**Branch:** `feature/b30-bwc-pipeline-assistant-integration`
**Scope:** BWC analysis pipeline + Chat Assistant + Search/Index/Export/Legal-Analysis tooling

---

## 1. Existing BWC / Media Ingestion

### 1.1 Evidence Store (`services/evidence_store.py`)

- **EvidenceStore** class manages canonical filesystem layout:
  ```
  evidence_store/
    originals/<sha256_prefix>/<sha256>/<original_filename>
    derivatives/<sha256_prefix>/<sha256>/<derivative_type>/<filename>
    manifests/<evidence_id>.json
  ```
- Originals are **immutable** — `store_original()` raises `FileExistsError` on collision.
- SHA-256 hashing via streaming 64 KiB blocks (`compute_file_hash()`).
- Post-copy integrity verification (re-hash after write).
- Duplicate detection by SHA-256 before storing.
- `IngestResult` dataclass returned on every ingest (success/failure, evidence_id, sha256, stored_path).
- Manifests are JSON files per evidence_id containing `IngestMetadata` + `DerivativeRecord[]` + audit entries.
- `append_audit()` appends to manifest JSON — append-only by contract.
- `verify_original()` re-hashes stored file and compares.
- Max ingest size: 3 GiB.
- **Live data:** 2 manifests present, 2 SHA-256 prefix directories in originals, 1 in derivatives.

### 1.2 Hashing Service (`services/hashing_service.py`)

- `compute_sha256_file(Path)` — streaming SHA-256 (4 KiB chunks).
- `compute_sha256_stream(BinaryIO)` — streaming SHA-256 for uploads.
- `verify_file_hash(Path, expected)` — comparison utility.
- Standalone module; no side effects.

### 1.3 Storage Backend (`services/storage_backend.py`)

- Abstract `StorageBackend` (ABC) with `put`, `get`, `exists`, `delete`, `list_keys`, `get_stream`, `put_stream`, `size`.
- Two implementations: `LocalFSStore` (dev), `S3Store` (production, S3-compatible).
- Every write verified by SHA-256.
- Delete method exists but documented as "NEVER delete originals in production."

### 1.4 Upload Routes (`routes/upload_routes.py`)

- Blueprint at `/upload`.
- Allowed extensions: video (mp4/avi/mov/mkv/webm/flv), audio, images, PDF, DOCX.
- Max file size: 2.5 GB (for BWC video).
- Singleton `_evidence_store = EvidenceStore(root="evidence_store")`.
- User-scoped staging directories: `uploads/user_{id}/YYYYMMDD/`.
- Metadata JSON per upload.
- Integrates with `MediaProcessor` + `BatchProcessor`.

### 1.5 Evidence Processor (`services/evidence_processor.py`)

- **PDF extraction:** native text via pdfplumber + OCR fallback (pytesseract).
- **Video metadata:** ffprobe (streams, format, duration, resolution, codec).
- **Thumbnail generation:** ffmpeg (single frame JPEG at t=10s).
- **Proxy video generation:** ffmpeg (720p, libx264, CRF 23, AAC audio).
- **Image OCR:** PIL + pytesseract.
- **DOCX extraction:** python-docx.
- **Plaintext passthrough:** UTF-8/latin-1.
- **Entity extraction:** regex for emails + phone numbers (deterministic).
- **MIME detection:** mimetypes + extension fallback.
- **Unified dispatcher:** `process_evidence_file()` routes by detected type.
- `process_video_evidence()` — full pipeline: metadata → thumbnail → optional proxy → store derivatives.

### 1.6 Forensic Media (`models/forensic_media.py`, `services/forensic_media_service.py`)

- **ForensicAudioMetadata** model: 40+ columns covering file properties, recording metadata, forensic analysis (authenticity, splicing, frequency, speakers), chain of custody.
- **ForensicVideoMetadata** model (referenced in imports).
- **SpeakerIdentification**, **AudioTranscription**, **ForensicChainOfCustody**, **MediaForensicReport** models.
- `ForensicAudioService` class: structured analysis framework (currently stubs for spectral analysis).
- Status enums: `ForensicStatus`, `AuthenticityLevel`.

### 1.7 BWC Files Present

Real BWC video uploads exist in `uploads/`:
- `BryanMerritt_202511292257_BWL7137497-0.mp4`
- `CristianMartin_202511292312_BWL7139081-0.mp4`
- `EdwardRuiz_202511292251_BWL7139078-0.mp4`
- `EdwardRuiz_202511292318_BWL7139078-0.mp4`
- `GaryClune_202511292317_BWL7139083-0.mp4`
- `KyleMcknight_202511292311_BWL7139063-0.mp4`
- `RachelHare_202511292258_BWL7139108-0.mp4`
- `Barber, Devon T. (2025-41706) Pro Se.pdf`

Naming pattern: `{OfficerName}_{YYYYMMDDHHMI}_{DeviceSerial}-{Clip}.mp4` — confirms BWC device labels (BWL series).

---

## 2. Database Models

### 2.1 EvidenceItem (`models/evidence.py`)

- **Fields:** id, origin_case_id, original_filename, stored_filename, file_type, file_size_bytes, mime_type, evidence_store_id (UUID), evidence_type, media_category, hash_sha256 (unique, indexed), hash_md5, collected_date, collected_by, collection_location, device_label, device_type, duration_seconds, transcript, text_content, processing_status, has_been_transcribed, has_ocr, is_redacted, is_responsive, has_privilege, privilege_type, is_under_legal_hold, retention_date, notes, uploaded_by_id.
- Indexed columns: file_type, collected_date, evidence_type, processing_status.
- Relationships: chain_of_custody, analysis_results, tags, case_evidence_links.

### 2.2 CaseEvidence (`models/evidence.py`)

- Many-to-many link between cases and evidence items.
- Audit fields: linked_at, linked_by_id, link_purpose, unlinked_at, unlinked_by_id.
- Soft-delete (append-only unlink).
- Unique constraint: (case_id, evidence_id).

### 2.3 ChainOfCustody (`models/evidence.py`)

- Immutable audit log per evidence item.
- Fields: evidence_id, action, actor_name, actor_id, action_timestamp, action_details, ip_address, user_agent, hash_before, hash_after.
- No update/delete by design.

### 2.4 EvidenceAnalysis (`models/evidence.py`)

- Per-evidence analysis results (type, confidence, results_json, model_name, processing_time).

### 2.5 EvidenceTag, PrivilegeLog, ProductionSet, ProductionItem

- Full eDiscovery model suite: tags, privilege assertions, production sets with Bates numbers.

### 2.6 LegalCase (`models/legal_case.py`)

- Referenced by CaseEvidence, events, exports.

### 2.7 Case Events (`models/case_event.py`)

- Event, CameraSyncGroup, CaseTimelineEntry, CaseExportRecord.

---

## 3. Audit Stream (`services/audit_stream.py`)

- `AuditStream` class — dual writes to:
  1. SQLAlchemy database (ChainOfCustody table).
  2. Evidence manifest JSON (for export packaging).
- Actions defined as constants in `AuditAction` class: INGEST, INGEST_DUPLICATE, HASH_COMPUTED, DERIVATIVE_CREATED, METADATA_EXTRACTED, THUMBNAIL_GENERATED, PROXY_GENERATED, TRANSCRIPT_CREATED, ACCESSED, DOWNLOADED, EXPORTED, INTEGRITY_VERIFIED, INTEGRITY_FAILED.
- Captures: actor, timestamp, IP, user agent, hash before/after.

---

## 4. Chat / Assistant System

### 4.1 Chat Service (`services/chat_service.py`)

- `ChatService` class per user.
- Supports: create/list/get conversations, add messages, AI completion via OpenAI SDK.
- Model support: GPT-4, GPT-4 Turbo, GPT-3.5, Claude 3 Opus/Sonnet.
- Context strategies: rolling_window, summarize, keep_first_last.
- Token counting via tiktoken.

### 4.2 Chat Tools (`services/chat_tools.py`)

- `EvidentChatTools` class — OpenAI function-calling format.
- Existing tools: search_legal_documents, get_case_details, search_cases, get_case_management_info, get_evidence_items.
- Additional tools likely defined further in the file.

### 4.3 Tool Implementations (`services/tool_implementations.py`)

- `ToolExecutors` class — actual implementations for each chat tool.
- Connects to `LegalLibraryService`, `GovernmentSources`, database models.
- Returns structured dicts with status, results, citations.

### 4.4 Chat Routes (`routes/chat_routes.py`)

- Blueprint at `/api/chat`.
- CRUD for conversations, messages.
- Rate limiting (placeholder for Redis-backed production impl).
- Session token management.

### 4.5 Chat Models (`models/chat_system.py`)

- Additional models: Project, Chat, ChatMessage, ChatMemory.
- Project-scoped chats with storage limits.

### 4.6 Additional Chat Models (`auth/chat_models.py`)

- Conversation, Message, UserAPIKey, ChatSession, ChatToolCall.

---

## 5. Export System

### 5.1 Evidence Export (`services/evidence_export.py`)

- Court-ready ZIP archive generator.
- Contents: originals, derivatives, manifest.json (hashes+sizes), audit_log.json, integrity_report.md.
- Deterministic and self-verifying.

### 5.2 Case Export (`services/case_export_service.py`)

- `CaseExporter` class for case-level ZIP packages.
- Includes: originals, derivatives, events.json, sync_groups.json, timeline.json.
- Generates Evidence Integrity Statement (deterministic text + optional PDF).
- Pre-manifest SHA-256 recorded.

### 5.3 Integrity Statement (`services/integrity_statement.py`)

- Deterministic text generator — byte-identical for same inputs.
- Template-driven (field interpolation, not AI-generated).
- Separate text SHA-256 and PDF SHA-256 tracking.

### 5.4 Existing Export

- `exports/evidence_package_64a8dfb0_20260210T052707Z.zip` — real export already generated.

---

## 6. Search / Review

### 6.1 Review Search Service (`services/review_search_service.py`)

- Full-text search within a case.
- Boolean operators (AND/OR), phrase matching, filters (date, file_type, has_ocr, custodian).
- Pagination with deterministic sort.
- Query audit logging.
- Depends on `ContentExtractionIndex` model (in `models/document_processing.py`).

---

## 7. Supporting Infrastructure

### 7.1 Tasks / Workers

- `tasks/algorithm_tasks.py`, `tasks/processing_tasks.py` — Celery tasks.
- `worker/worker.js` — Node.js worker (semantic docket).

### 7.2 CI/CD (`.github/workflows/`)

- 40+ workflow files; active ones include: ci.yml, law-tests.yml, media-validate.yml, video-transcode.yml, security-scan.yml, web-ci.yml, etc.

### 7.3 Config

- `config/ai_ml_config.py` — AI/ML configuration.
- `config/fastapi_integration.py` — FastAPI integration points.
- `app_config.py` — Flask configuration.

### 7.4 Governance

- `governance/` — security scans, design decisions, dependency tracking, governance tracker.

---

## 8. Summary Statistics

| Category | Status |
|---|---|
| Evidence store (immutable originals) | **Implemented** |
| SHA-256 hashing on ingest | **Implemented** |
| Duplicate detection | **Implemented** |
| Post-copy verification | **Implemented** |
| Append-only audit (dual write) | **Implemented** |
| Video metadata (ffprobe) | **Implemented** |
| Thumbnail generation (ffmpeg) | **Implemented** |
| Proxy video generation (ffmpeg) | **Implemented** |
| PDF text/OCR extraction | **Implemented** |
| Image OCR | **Implemented** |
| DOCX text extraction | **Implemented** |
| Entity extraction (regex) | **Implemented** |
| Forensic media models | **Implemented (analysis logic stubbed)** |
| Chat assistant with tool calling | **Implemented** |
| Legal document search tools | **Implemented** |
| Evidence search (boolean, filtered) | **Implemented** |
| Case-level export (ZIP + manifest) | **Implemented** |
| Evidence-level export (ZIP) | **Implemented** |
| Integrity statement (deterministic) | **Implemented** |
| Storage backend abstraction (local/S3) | **Implemented** |
| Folder-dump batch ingest (BWC messy dumps) | **Not implemented** |
| Sequence grouping (time/device clustering) | **Not implemented** |
| Waveform generation | **Not implemented** |
| Transcript/OCR indexing for full-text search | **Partial (ContentExtractionIndex exists)** |
| Timecode index for markers/notes | **Not implemented** |
| Chat grounded-mode (citation-required) | **Not implemented** |
| Legal analysis tooling (structured) | **Not implemented** |
| ToolHub manifests for BWC pipeline | **Not implemented** |
| JSONL integrity ledger (append-only flat file) | **Not implemented** |
| Safe Mode gating on external calls | **Not implemented** |
