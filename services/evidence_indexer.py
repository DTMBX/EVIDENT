"""
B30 Phase 4 — Evidence Indexing & Search Service
==================================================
Populates ContentExtractionIndex from P3 normalization derivatives
and provides a unified search API for evidence content.

Pipeline:
  1. After normalization, read text_extract derivatives from the store.
  2. Extract entities (emails, phones) deterministically.
  3. Populate ContentExtractionIndex row per evidence item.
  4. Log indexing operations to IntegrityLedger.
  5. Provide search methods that work without the DB (filesystem-only mode).

Design principles:
  - Deterministic: same text → same index content.
  - No AI/LLM interpretation of content.
  - Entity extraction is regex-only (no hallucination).
  - Every index operation is audited.
"""

import json
import logging
import os
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from services.evidence_processor import extract_entities
from services.evidence_store import EvidenceStore
from services.integrity_ledger import IntegrityLedger

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------


@dataclass
class IndexEntry:
    """A search index entry for a single evidence item."""
    evidence_id: str
    original_sha256: str
    filename: str
    content_type: str  # text, ocr, transcript, video_metadata
    full_text: str = ""
    word_count: int = 0
    character_count: int = 0
    line_count: int = 0
    email_addresses: List[str] = field(default_factory=list)
    phone_numbers: List[str] = field(default_factory=list)
    indexed_at: str = ""


@dataclass
class SearchResult:
    """A single search result."""
    evidence_id: str
    filename: str
    sha256: str
    snippet: str = ""
    match_count: int = 0
    content_type: str = ""
    score: float = 0.0


@dataclass
class SearchResponse:
    """Response from a search query."""
    query: str
    total_results: int = 0
    results: List[SearchResult] = field(default_factory=list)
    search_time_ms: float = 0.0


# ---------------------------------------------------------------------------
# Filesystem-based index (no DB required)
# ---------------------------------------------------------------------------


class EvidenceIndexer:
    """
    Builds and queries a search index from evidence store derivatives.

    Operates entirely on the filesystem — no database dependency.
    The index is a JSON file at evidence_store/search_index.json.
    """

    def __init__(
        self,
        store: Optional[EvidenceStore] = None,
        ledger: Optional[IntegrityLedger] = None,
        index_path: Optional[str] = None,
    ):
        self._store = store or EvidenceStore()
        self._ledger = ledger or IntegrityLedger()
        self._index_path = Path(
            index_path or str(self._store.root / "search_index.json")
        )
        self._entries: Dict[str, IndexEntry] = {}
        self._load_index()

    def _load_index(self) -> None:
        """Load existing index from disk."""
        if self._index_path.exists():
            try:
                with open(self._index_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for key, entry_data in data.get("entries", {}).items():
                    self._entries[key] = IndexEntry(**entry_data)
            except (json.JSONDecodeError, TypeError) as exc:
                logger.error("Failed to load search index: %s", exc)

    def _save_index(self) -> None:
        """Persist index to disk."""
        self._index_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "version": 1,
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "entry_count": len(self._entries),
            "entries": {k: asdict(v) for k, v in self._entries.items()},
        }
        with open(self._index_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def index_evidence(
        self,
        evidence_id: str,
        original_sha256: str,
        filename: str,
        text_content: str,
        content_type: str = "text",
        actor: str = "system",
    ) -> IndexEntry:
        """
        Index a single evidence item's text content.

        Args:
            evidence_id: UUID or identifier of the evidence.
            original_sha256: SHA-256 of the original file.
            filename: Original filename.
            text_content: Full extracted text to index.
            content_type: Type of content (text, ocr, transcript, etc.).
            actor: Actor identifier for audit.

        Returns:
            IndexEntry that was created/updated.
        """
        now = datetime.now(timezone.utc).isoformat()

        # Extract entities deterministically (regex only — no AI)
        emails, phones = extract_entities(text_content)

        words = text_content.split() if text_content else []
        lines = text_content.splitlines() if text_content else []

        entry = IndexEntry(
            evidence_id=evidence_id,
            original_sha256=original_sha256,
            filename=filename,
            content_type=content_type,
            full_text=text_content,
            word_count=len(words),
            character_count=len(text_content),
            line_count=len(lines),
            email_addresses=emails,
            phone_numbers=phones,
            indexed_at=now,
        )

        self._entries[evidence_id] = entry
        self._save_index()

        self._ledger.append(
            action="index.evidence_indexed",
            evidence_id=evidence_id,
            sha256=original_sha256,
            actor=actor,
            details={
                "filename": filename,
                "content_type": content_type,
                "word_count": entry.word_count,
                "entities_found": len(emails) + len(phones),
            },
        )

        logger.info(
            "Indexed evidence %s: %d words, %d entities",
            evidence_id, entry.word_count, len(emails) + len(phones),
        )
        return entry

    def index_from_derivatives(
        self,
        evidence_id: str,
        original_sha256: str,
        filename: str,
        actor: str = "system",
    ) -> Optional[IndexEntry]:
        """
        Index an evidence item by reading its text_extract derivative.

        Looks for the derivative at the standard path in the evidence store.

        Returns IndexEntry if text was found, None otherwise.
        """
        # Look for text extract derivative
        derivatives = self._store.list_derivatives(original_sha256)
        text_derivatives = [
            d for d in derivatives if d.startswith("text_extract/")
        ]

        if not text_derivatives:
            logger.info("No text derivative found for %s", evidence_id)
            return None

        # Read the first text extract
        deriv_path_parts = text_derivatives[0].split("/")
        if len(deriv_path_parts) >= 2:
            full_path = self._store.get_derivative_path(
                original_sha256, deriv_path_parts[0], deriv_path_parts[1],
            )
            if full_path and os.path.exists(full_path):
                text = Path(full_path).read_text(encoding="utf-8", errors="replace")
                content_type = "ocr" if "ocr" in deriv_path_parts[1].lower() else "text"
                return self.index_evidence(
                    evidence_id=evidence_id,
                    original_sha256=original_sha256,
                    filename=filename,
                    text_content=text,
                    content_type=content_type,
                    actor=actor,
                )

        return None

    # ---------------------------------------------------------------------------
    # Search
    # ---------------------------------------------------------------------------

    def search(
        self,
        query: str,
        case_evidence_ids: Optional[List[str]] = None,
        max_results: int = 50,
    ) -> SearchResponse:
        """
        Search the index for evidence matching the query.

        Supports:
          - Simple keyword search (case-insensitive)
          - Exact phrase matching (quoted strings)
          - Multiple terms (AND logic by default)

        Args:
            query: Search query string.
            case_evidence_ids: Optional list of evidence IDs to restrict search to.
            max_results: Maximum results to return.

        Returns:
            SearchResponse with matching results.
        """
        import time
        start = time.time()

        if not query or not query.strip():
            return SearchResponse(query=query)

        # Parse query: extract quoted phrases and plain terms
        phrases = re.findall(r'"([^"]+)"', query)
        remaining = re.sub(r'"[^"]*"', "", query).strip()
        terms = [t.lower() for t in remaining.split() if t.strip()]

        results: List[SearchResult] = []

        for eid, entry in self._entries.items():
            # Skip if not in scope
            if case_evidence_ids is not None and eid not in case_evidence_ids:
                continue

            text_lower = entry.full_text.lower() if entry.full_text else ""
            if not text_lower:
                continue

            # Check phrases (exact match)
            phrase_matches = all(p.lower() in text_lower for p in phrases)
            if phrases and not phrase_matches:
                continue

            # Check terms (AND logic)
            term_matches = all(t in text_lower for t in terms)
            if terms and not term_matches:
                continue

            # Both empty means match everything
            if not phrases and not terms:
                continue

            # Count total matches for scoring
            match_count = 0
            for p in phrases:
                match_count += text_lower.count(p.lower())
            for t in terms:
                match_count += text_lower.count(t)

            # Extract snippet
            snippet = self._extract_snippet(
                entry.full_text, phrases[0] if phrases else (terms[0] if terms else "")
            )

            results.append(SearchResult(
                evidence_id=entry.evidence_id,
                filename=entry.filename,
                sha256=entry.original_sha256,
                snippet=snippet,
                match_count=match_count,
                content_type=entry.content_type,
                score=float(match_count),
            ))

        # Sort by score descending
        results.sort(key=lambda r: r.score, reverse=True)
        results = results[:max_results]

        elapsed_ms = (time.time() - start) * 1000

        return SearchResponse(
            query=query,
            total_results=len(results),
            results=results,
            search_time_ms=round(elapsed_ms, 2),
        )

    def _extract_snippet(self, text: str, term: str, context_chars: int = 100) -> str:
        """Extract a text snippet around the first occurrence of term."""
        if not text or not term:
            return text[:200] if text else ""

        idx = text.lower().find(term.lower())
        if idx == -1:
            return text[:200]

        start = max(0, idx - context_chars)
        end = min(len(text), idx + len(term) + context_chars)
        snippet = text[start:end]

        if start > 0:
            snippet = "..." + snippet
        if end < len(text):
            snippet = snippet + "..."

        return snippet

    # ---------------------------------------------------------------------------
    # Utility
    # ---------------------------------------------------------------------------

    @property
    def entry_count(self) -> int:
        return len(self._entries)

    def get_entry(self, evidence_id: str) -> Optional[IndexEntry]:
        return self._entries.get(evidence_id)

    def get_all_entries(self) -> List[IndexEntry]:
        return list(self._entries.values())
