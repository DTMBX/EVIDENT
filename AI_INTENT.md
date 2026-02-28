# AI Intent — EVIDENT (Repo-Aware RAG)

## Current objective
Build and harden the BWC pipeline assistant integration on branch:
feature/b30-bwc-pipeline-assistant-integration

## Non-negotiables
- Never overwrite originals.
- All derivatives must reference original SHA-256 + have their own hashes.
- Append-only audit log (no silent access).
- Small diffs; no unrelated refactors.
- Keep tests green; add tests for new behavior.

## What “done” looks like
- Ingest BWC/dashcam folder dumps reliably
- Hash originals and store immutably
- Generate proxies/thumbnails/waveforms
- Index metadata for timeline search
- Export package with manifest + hashes + audit events
