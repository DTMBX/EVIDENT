# B30 — Current Pipeline Map

**Date:** 2026-02-18

---

## Data Flow Diagram (Box-and-Arrow)

```
┌──────────────────────────────────────────────────────────────────────────┐
│                         INGEST LAYER                                     │
│                                                                          │
│  ┌─────────────┐    ┌──────────────────┐    ┌────────────────────────┐  │
│  │  Web Upload  │───▶│  Upload Routes   │───▶│  Staging Directory     │  │
│  │  (Browser)   │    │  /upload/        │    │  uploads/user_{id}/    │  │
│  └─────────────┘    └──────────────────┘    └───────────┬────────────┘  │
│                                                          │               │
│                                                          ▼               │
│                                              ┌────────────────────────┐  │
│                                              │  EvidenceStore.ingest()│  │
│                                              │  - SHA-256 hash        │  │
│                                              │  - Duplicate check     │  │
│                                              │  - Copy + verify       │  │
│                                              │  - Create manifest     │  │
│                                              └───────────┬────────────┘  │
│                                                          │               │
│                                                          ▼               │
│                                              ┌────────────────────────┐  │
│                                              │  evidence_store/       │  │
│                                              │    originals/{hash}/   │  │
│                                              │    manifests/{uuid}    │  │
│                                              └───────────┬────────────┘  │
└──────────────────────────────────────────────────────────┼───────────────┘
                                                           │
                                                           ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                        DATABASE LAYER                                    │
│                                                                          │
│  ┌─────────────────┐  ┌──────────────────┐  ┌────────────────────────┐  │
│  │  EvidenceItem    │  │ ChainOfCustody   │  │  CaseEvidence          │  │
│  │  - hash_sha256   │  │ - action         │  │  - case_id             │  │
│  │  - file_type     │  │ - actor          │  │  - evidence_id         │  │
│  │  - device_label  │  │ - hash_before    │  │  - link_purpose        │  │
│  │  - evidence_id   │  │ - hash_after     │  │  - linked_at           │  │
│  └────────┬────────┘  └──────────────────┘  └────────────────────────┘  │
│           │                                                              │
│           ▼                                                              │
│  ┌─────────────────┐  ┌──────────────────┐  ┌────────────────────────┐  │
│  │ EvidenceAnalysis │  │ EvidenceTag      │  │ ForensicAudioMetadata  │  │
│  │ - type           │  │ - tag_name       │  │ - authenticity_verdict │  │
│  │ - results_json   │  │ - tag_color      │  │ - speaker_segments     │  │
│  └─────────────────┘  └──────────────────┘  └────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                       PROCESSING LAYER                                   │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │                   evidence_processor.py                             │ │
│  │                                                                     │ │
│  │  detect_file_type() ──▶ process_evidence_file()                    │ │
│  │                             │                                       │ │
│  │        ┌────────────────────┼────────────────────┐                 │ │
│  │        ▼                    ▼                    ▼                  │ │
│  │  ┌──────────┐      ┌──────────────┐     ┌──────────────┐          │ │
│  │  │ PDF      │      │ Video        │     │ Image OCR    │          │ │
│  │  │ extract  │      │ ffprobe meta │     │ pytesseract  │          │ │
│  │  │ + OCR    │      │ + thumbnail  │     └──────────────┘          │ │
│  │  └──────────┘      │ + proxy      │                               │ │
│  │                     └──────┬───────┘                               │ │
│  │                            │                                       │ │
│  │                            ▼                                       │ │
│  │                   evidence_store/                                  │ │
│  │                     derivatives/{hash}/{type}/                     │ │
│  └─────────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                        AUDIT LAYER                                       │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │                    AuditStream.record()                            │  │
│  │                                                                    │  │
│  │    ┌─────────────────────┐     ┌────────────────────────────────┐ │  │
│  │    │  DB: ChainOfCustody │     │  File: manifest.json audit[]   │ │  │
│  │    │  (SQLAlchemy)       │     │  (append-only JSON)            │ │  │
│  │    └─────────────────────┘     └────────────────────────────────┘ │  │
│  └────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                       SEARCH / REVIEW LAYER                              │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │              ReviewSearchService.search()                          │  │
│  │                                                                    │  │
│  │  - Boolean (AND/OR) + phrase matching                             │  │
│  │  - Filters: date, file_type, has_ocr, custodian                   │  │
│  │  - Pagination + deterministic sort                                │  │
│  │  - Query audit logging                                            │  │
│  │  - Depends on: ContentExtractionIndex table                       │  │
│  └────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                       CHAT / ASSISTANT LAYER                             │
│                                                                          │
│  ┌─────────────────┐   ┌──────────────────┐   ┌───────────────────┐    │
│  │  Chat Routes     │──▶│  ChatService     │──▶│  OpenAI API       │    │
│  │  /api/chat/      │   │  - conversations │   │  (tool calling)   │    │
│  │                  │   │  - messages      │   └───────┬───────────┘    │
│  └─────────────────┘   │  - context mgmt  │           │                │
│                         └──────────────────┘           ▼                │
│                                                ┌───────────────────┐    │
│                                                │  EvidentChatTools │    │
│                                                │  - search_legal   │    │
│                                                │  - get_case       │    │
│                                                │  - get_evidence   │    │
│                                                └───────────────────┘    │
└──────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                        EXPORT LAYER                                      │
│                                                                          │
│  ┌────────────────────────┐     ┌───────────────────────────────────┐   │
│  │  EvidenceExporter       │     │  CaseExporter                    │   │
│  │  (single evidence item) │     │  (full case package)             │   │
│  │                         │     │                                   │   │
│  │  ZIP contents:          │     │  ZIP contents:                    │   │
│  │  - originals/           │     │  - originals/                     │   │
│  │  - derivatives/         │     │  - derivatives/                   │   │
│  │  - manifest.json        │     │  - events.json                    │   │
│  │  - audit_log.json       │     │  - sync_groups.json               │   │
│  │  - integrity_report.md  │     │  - timeline.json                  │   │
│  └────────────────────────┘     │  - integrity_statement.txt         │   │
│                                  │  - manifest.json                   │   │
│                                  └───────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                    STORAGE BACKEND ABSTRACTION                            │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │   StorageBackend (ABC)                                            │  │
│  │                                                                    │  │
│  │   ┌──────────────────┐          ┌──────────────────────────────┐  │  │
│  │   │  LocalFSStore    │          │  S3Store                     │  │  │
│  │   │  (development)   │          │  (production, S3-compatible) │  │  │
│  │   └──────────────────┘          └──────────────────────────────┘  │  │
│  └────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## Key Integration Points

| Component | Entry Point | Protocol |
|---|---|---|
| Upload | `routes/upload_routes.py` → `/upload/` | Flask Blueprint, multipart form |
| Evidence Store | `services/evidence_store.py` → `EvidenceStore` | Python class, filesystem |
| DB Models | `models/evidence.py` → `EvidenceItem`, `ChainOfCustody` | SQLAlchemy ORM |
| Processor | `services/evidence_processor.py` → `process_evidence_file()` | Python function |
| Audit | `services/audit_stream.py` → `AuditStream.record()` | Dual-write (DB + JSON) |
| Search | `services/review_search_service.py` → `ReviewSearchService.search()` | Python class |
| Chat | `routes/chat_routes.py` → `/api/chat/` | Flask Blueprint, REST |
| Chat Tools | `services/chat_tools.py` → `EvidentChatTools` | OpenAI function-calling format |
| Tool Execution | `services/tool_implementations.py` → `ToolExecutors` | Python static methods |
| Evidence Export | `services/evidence_export.py` → ZIP generation | Python class |
| Case Export | `services/case_export_service.py` → `CaseExporter` | Python class |
| Integrity Stmt | `services/integrity_statement.py` → deterministic text | Python class |
| Storage Backend | `services/storage_backend.py` → `StorageBackend` ABC | Abstract interface |

---

## Data Model Relationships

```
LegalCase ──1:N──▶ CaseEvidence ◀──N:1── EvidenceItem
                                              │
                                              ├──1:N──▶ ChainOfCustody
                                              ├──1:N──▶ EvidenceAnalysis
                                              ├──N:M──▶ EvidenceTag
                                              ├──1:1──▶ ForensicAudioMetadata
                                              ├──1:1──▶ ForensicVideoMetadata
                                              └──1:N──▶ ProductionItem ──N:1──▶ ProductionSet

LegalCase ──1:N──▶ Event ──1:N──▶ CameraSyncGroup
LegalCase ──1:N──▶ CaseTimelineEntry
LegalCase ──1:N──▶ CaseExportRecord

User ──1:N──▶ Conversation ──1:N──▶ Message
User ──1:N──▶ ChatToolCall
User ──1:N──▶ UserAPIKey
```
