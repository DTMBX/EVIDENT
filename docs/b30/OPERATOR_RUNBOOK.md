# B30 BWC Pipeline — Operator Runbook

## Overview

The B30 BWC Analysis Pipeline processes body-worn camera evidence through seven
stages: ingest, normalize, index, search, chat grounding, legal analysis, and
export. Every operation is recorded in an append-only integrity ledger.

---

## Pipeline Stages

### 1. Integrity Ledger

**Service:** `services/integrity_ledger.py`

```python
from services.integrity_ledger import IntegrityLedger

ledger = IntegrityLedger("evidence_store/integrity_ledger.jsonl")
ledger.append(action="INGEST", evidence_id="ev-001", sha256="abc...")
errors = ledger.verify()  # Returns [] if intact
```

- Append-only JSONL with SHA-256 hash chain
- Genesis entry uses zero hash (`"0" * 64`)
- Verify with `ledger.verify()` — returns list of errors

### 2. Batch Ingest

**Service:** `services/batch_ingest.py`

```python
from services.batch_ingest import ingest_folder

result = ingest_folder(
    folder_path="/path/to/bwc/files",
    evidence_store=store,
    ledger=ledger,
    case_ref="CASE-2025-001",
)
# result["files"] — list of ingested file records
# result["sequence_groups"] — auto-detected BWC sequences
```

- Parses BWC filenames: `{Officer}_{YYYYMMDDHHMI}_{Device}-{Clip}.ext`
- Groups adjacent clips by officer + device + time window
- Detects duplicates by SHA-256
- Skips unsupported extensions

### 3. Normalization Pipeline

**Service:** `services/normalization_pipeline.py`

```python
from services.normalization_pipeline import normalize_evidence

result = normalize_evidence(
    evidence_id="ev-001",
    original_path="/path/to/file.mp4",
    mime_type="video/mp4",
    derivatives_dir="/path/to/derivatives",
    ledger=ledger,
)
# result["derivatives"] — list of generated files
```

- Video: metadata + thumbnail + waveform + optional proxy
- Audio: metadata + waveform
- Image: metadata + thumbnail
- Document (PDF/DOCX/TXT): text extraction
- Waveform: 1800×140px blue-on-dark via ffmpeg `showwavespic`

### 4. Evidence Indexer

**Service:** `services/evidence_indexer.py`

```python
from services.evidence_indexer import EvidenceIndexer

indexer = EvidenceIndexer("evidence_store")
indexer.index_evidence("ev-001", "Full text content...", metadata={...})
results = indexer.search("search terms")
```

- Filesystem-based JSON index
- Keyword, phrase, and AND search
- Entity extraction (emails, phones)
- Persists to `evidence_store/search_index.json`

### 5. Chat Grounding

**Service:** `services/chat_grounding.py`

```python
from services.chat_grounding import (
    build_grounded_system_prompt,
    validate_citations,
    GroundedToolExecutor,
    GROUNDED_TOOLS,
)

prompt = build_grounded_system_prompt(case_context="Case 2025-001")
# Use GROUNDED_TOOLS as OpenAI function-call tool definitions
# Validate responses with validate_citations(response_text, known_ids)
```

- Mandatory citation format: `[Evidence: filename]`
- Fabrication detection (warns on hallucination phrases)
- Three grounded tools: search_evidence_index, get_evidence_context, list_evidence_summary
- Every tool call logged to integrity ledger

### 6. Legal Analysis

**Service:** `services/legal_analysis.py`

```python
from services.legal_analysis import (
    IssueMapper,
    StandardTemplates,
    CitationRegistry,
    ArgumentBuilder,
)

mapper = IssueMapper()
result = mapper.map_evidence("ev-001", "filename.mp4", text_content)

citations = CitationRegistry()
verified = citations.get_citation("terry_v_ohio")

builder = ArgumentBuilder(ledger=ledger)
outline = builder.build_argument("ev-001", "filename.mp4", text_content)
```

- Maps text to 7 constitutional amendments (1A, 2A, 4A, 5A, 6A, 8A, 14A)
- 4 analysis templates: 4th Amendment search, due process, excessive force, evidence integrity
- 8 verified landmark citations (never fabricates)
- Structured argument outlines with counter-considerations

### 7. BWC Export

**Service:** `services/bwc_export.py`

```python
from services.bwc_export import BWCCaseExporter

exporter = BWCCaseExporter(
    evidence_base="evidence_store",
    export_dir="exports/bwc",
    ledger=ledger,
)
result = exporter.export(
    evidence_ids=["ev-001", "ev-002"],
    case_ref="CASE-2025-001",
    exported_by="analyst@example.com",
)
# result.export_path — path to ZIP
# result.package_sha256 — package hash
# result.size_tier — "small" / "medium" / "large"
```

- Deterministic naming: `BWC_EXPORT_{case_ref}_{timestamp}.zip`
- Size tiers: small (<100 MB), medium (<1 GB), large (1 GB+)
- Includes: originals, derivatives, ledger extract, search index, manifest, integrity report
- Package SHA-256 recorded in ledger

---

## Tool Registry

**Service:** `services/tool_manifest.py`

```python
from services.tool_manifest import build_bwc_registry

registry = build_bwc_registry()
registry.validate_dependencies()  # Returns [] if valid
plan = registry.execution_plan("bwc_export")  # Topological order
registry.save("tools/bwc_tools.json")
```

- 7 registered tools with typed schemas
- Dependency validation and cycle detection
- Execution plan generation (topological sort)
- JSON export for external systems

---

## Verification Procedures

### Ledger Integrity Check

```bash
python -c "
from services.integrity_ledger import IntegrityLedger
ledger = IntegrityLedger()
errors = ledger.verify()
print(f'Entries: {ledger.entry_count}')
print(f'Errors: {len(errors)}')
for e in errors: print(e)
"
```

### Full Test Suite

```bash
python -m pytest tests/test_b30_evidence_graph.py \
    tests/test_integrity_ledger.py \
    tests/test_batch_ingest.py \
    tests/test_normalization_pipeline.py \
    tests/test_evidence_indexer.py \
    tests/test_chat_grounding.py \
    tests/test_legal_analysis.py \
    tests/test_bwc_export.py \
    tests/test_tool_manifest.py \
    -v --tb=short
```

Expected: **189 passed, 0 failed**

### Package Verification

After export, verify any package:

```python
from services.bwc_export import _compute_sha256
pkg_hash = _compute_sha256("exports/bwc/BWC_EXPORT_CASE_20250115.zip")
# Compare against ledger entry
```

---

## Constraints

- **Originals are immutable** — never overwritten or modified
- **Ledger is append-only** — never deleted or rewritten
- **SHA-256 everywhere** — 64 KiB streaming blocks
- **Deterministic processing** — same inputs produce same outputs (except chat LLM)
- **Fail closed** — errors halt processing, never skip silently
- **No secrets committed** — API keys via environment variables only

---

## Architecture Diagram

```
BWC Files → [Batch Ingest] → [Evidence Store]
                                    ↓
                            [Normalization]
                                    ↓
                             [Indexer/Search]
                                    ↓
                        [Chat Grounding] ← [Legal Analysis]
                                    ↓
                            [BWC Export] → Court-Ready ZIP
                                    
            ← Integrity Ledger (append-only JSONL) →
```

---

*Evident Technologies — B30 BWC Pipeline v1.0.0*
