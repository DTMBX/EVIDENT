# B30 — Gaps and Risks (Ranked)

**Date:** 2026-02-18

---

## Severity Scale

| Level | Description |
|---|---|
| **CRITICAL** | Blocks pipeline correctness or evidence admissibility |
| **HIGH** | Significant functional gap; workaround possible but fragile |
| **MEDIUM** | Capability missing but pipeline still operational |
| **LOW** | Enhancement opportunity; no current harm |

---

## GAP-01 — No Folder-Dump Batch Ingest (CRITICAL)

**What:** BWC evidence arrives as messy folder dumps — dozens or hundreds of files with inconsistent naming, mixed file types, and device metadata only in filenames. There is no CLI or API for ingesting an entire folder atomically.

**Current state:** Single-file upload via browser only. No batch manifest creation. No device/time clustering.

**Risk:** Manual one-at-a-time upload is impractical for real BWC evidence (7+ files already in `uploads/`). Risk of missed files, broken ordering, and no batch-level audit trail.

**B30 target:** P2 — Folder ingest with manifest, SHA-256 per file, sequence grouping, JSONL integrity ledger.

---

## GAP-02 — No JSONL Integrity Ledger (CRITICAL)

**What:** While the audit stream dual-writes to DB + manifest JSON, there is no flat-file, append-only integrity ledger (JSONL) that can be independently verified without the database.

**Current state:** Audit entries are embedded in per-evidence manifest JSON files and in the ChainOfCustody SQL table. The manifest JSON is rewritten on each append (overwrite, not true append-only at filesystem level).

**Risk:** If the manifest JSON is corrupted or the database is compromised, there is no independent, tamper-evident record. The manifest rewrite (save_manifest) is technically not append-only at the filesystem level even though the list only grows.

**B30 target:** P2 — True append-only JSONL ledger alongside manifest JSON.

---

## GAP-03 — Chat Assistant Not Grounded / No Citation Enforcement (CRITICAL)

**What:** The chat assistant can call tools (search_legal_documents, get_evidence_items, etc.) but there is no enforcement that responses cite sources. The assistant can produce text that is not backed by indexed materials.

**Current state:** OpenAI function-calling is wired up; tools return structured data. But responses are not validated for citation presence or accuracy.

**Risk:** A response that fabricates facts, case names, or timecodes would be catastrophic for a forensic evidence platform.

**B30 target:** P5 — Grounded mode: require citations (file ID, hash, timecode), block uncited claims, audit tool calls.

---

## GAP-04 — No Waveform Generation (HIGH)

**What:** Waveform images (visual audio timeline) are not generated for video/audio evidence. These are essential for quick visual review of audio presence, gaps, and intensity.

**Current state:** Thumbnail and proxy video are generated via ffmpeg. Audio tracks are detected in ffprobe metadata. No waveform image generation.

**Risk:** Reviewers cannot quickly assess audio characteristics without playing entire files.

**B30 target:** P3 — ffmpeg waveform PNG generation, stored as derivative.

---

## GAP-05 — No Timecode Index / Marker System (HIGH)

**What:** There is no data model or API for placing timestamped markers, notes, or annotations on media evidence.

**Current state:** EvidenceAnalysis can store JSON results; ForensicAudioMetadata has edit_markers (JSON text). But no structured AnalysisNote/Marker model with timecodes, tags, confidence scores.

**Risk:** Collaborative review requires placing and sharing markers. Without structured timecodes, search and export cannot reference specific moments.

**B30 target:** P1 — AnalysisNote/Marker model; P4 — Timecode index.

---

## GAP-06 — No Transcript/OCR Index for Search (HIGH)

**What:** While PDF text extraction and OCR exist, extracted text is not indexed in a searchable structure linked to evidence and timecodes.

**Current state:** `ContentExtractionIndex` is referenced by `ReviewSearchService` but the indexing pipeline to populate it from processing results is unclear/incomplete.

**Risk:** Evidence search over document content will return nothing if the index is not populated.

**B30 target:** P4 — Indexer that feeds ContentExtractionIndex from processing results.

---

## GAP-07 — Sequence Grouping Not Implemented (HIGH)

**What:** BWC dumps contain multiple clips from the same incident, spread across multiple officers and devices. There is no logic to group files by time adjacency, device label, or naming heuristics.

**Current state:** `device_label` and `device_type` columns exist on EvidenceItem but are not used for grouping.

**Risk:** Related clips appear as disconnected items, making timeline reconstruction difficult.

**B30 target:** P2 — Sequence grouping algorithm in ingest pipeline.

---

## GAP-08 — No Safe Mode Gating on External API Calls (HIGH)

**What:** Chat assistant calls OpenAI API directly. There is no Safe Mode flag that can disable external calls, restrict to local-only processing, or enforce an allowlist.

**Current state:** OpenAI API key is configured; calls go out without gating.

**Risk:** In demo or air-gapped deployments, external calls must be blocked. In production, an allowlist prevents unauthorized egress.

**B30 target:** P5 — Safe Mode flag; external call gating; local-only fallback.

---

## GAP-09 — Legal Analysis Tooling Does Not Exist (MEDIUM)

**What:** No structured legal analysis helpers (issue mapping, argument building, citation registry) are implemented.

**Current state:** Chat tools search legal documents and return case details. No structured tool that maps facts to legal standards or builds arguments from cited sources.

**Risk:** Without guardrails, users may ask the chat assistant for legal analysis and receive unstructured responses that do not distinguish facts from standards from argument.

**B30 target:** P6 — issue_mapper, standard_templates, citation_registry, argument_builder.

---

## GAP-10 — No ToolHub Manifests for BWC Pipeline (MEDIUM)

**What:** No tool manifest files declaring BWC pipeline tools (ingest, review, export) with risk levels, auth requirements, and audit events.

**Current state:** `apps/` directory contains subdirectories for other tools but no BWC-specific manifests.

**Risk:** Pipeline tools cannot be discovered, gated, or audited by a shared tool platform.

**B30 target:** P8 — tool.manifest.json files for bwc-ingest, bwc-review, bwc-export, legal-analysis.

---

## GAP-11 — Forensic Analysis Logic is Stubbed (MEDIUM)

**What:** `ForensicAudioService` and related services define the framework but analysis functions (spectral analysis, splice detection, speaker identification) are stubs.

**Current state:** Models are complete; service methods set default values and return.

**Risk:** Forensic analysis results will always show "unknown" until stubs are replaced with real implementations. This is a known technical debt, not a B30 blocker.

**B30 target:** Out of scope for B30 (document as known limitation).

---

## GAP-12 — Manifest JSON Rewrite is Not True Append-Only (MEDIUM)

**What:** `EvidenceStore.save_manifest()` overwrites the manifest JSON file on every append_audit() call. While the audit_entries list only grows, the file itself is rewritten.

**Current state:** The rewrite is atomic (Python's file write) but not crash-safe (no fsync, no temp-file-rename pattern).

**Risk:** A crash during rewrite could corrupt the manifest. Mitigation: JSONL ledger (GAP-02) provides independent backup.

**B30 target:** P2 — JSONL ledger as crash-safe backup; optionally improve manifest write to use temp-file-rename.

---

## GAP-13 — Export Compression Tiers Not Implemented (LOW)

**What:** Export packages do not offer size tier options (small/standard/full) or compression level selection.

**Current state:** ZIP_DEFLATED compression used; all files included unconditionally.

**Risk:** Large exports may be impractical for transmission. Low risk: ZIP already compresses.

**B30 target:** P7 — Size tier options, optional original exclusion, deterministic naming.

---

## GAP-14 — No Demo Dataset or Fixture Pack (LOW)

**What:** No synthetic/mock dataset for testing the full pipeline without real evidence files.

**Current state:** Real BWC files exist in `uploads/` but cannot be committed. Test fixtures exist in `tests/fixtures/` but coverage of the full pipeline is unclear.

**Risk:** Developers and reviewers cannot exercise the full pipeline without real data.

**B30 target:** P9 — Demo dataset with placeholder files and mocked fixtures.

---

## Risk Summary

| Gap | Severity | B30 Phase |
|---|---|---|
| GAP-01: No folder-dump batch ingest | CRITICAL | P2 |
| GAP-02: No JSONL integrity ledger | CRITICAL | P2 |
| GAP-03: Chat not grounded | CRITICAL | P5 |
| GAP-04: No waveform generation | HIGH | P3 |
| GAP-05: No timecode index/markers | HIGH | P1, P4 |
| GAP-06: No transcript/OCR index | HIGH | P4 |
| GAP-07: No sequence grouping | HIGH | P2 |
| GAP-08: No Safe Mode gating | HIGH | P5 |
| GAP-09: No legal analysis tooling | MEDIUM | P6 |
| GAP-10: No ToolHub manifests | MEDIUM | P8 |
| GAP-11: Forensic analysis stubs | MEDIUM | Out of scope |
| GAP-12: Manifest rewrite not atomic | MEDIUM | P2 |
| GAP-13: No compression tiers | LOW | P7 |
| GAP-14: No demo dataset | LOW | P9 |
