"""
Tests for services/evidence_indexer.py — Phase 4
==================================================
Tests indexing, entity extraction, and search functionality.
"""

import json
from pathlib import Path

import pytest

from services.evidence_indexer import (
    EvidenceIndexer,
    IndexEntry,
    SearchResponse,
    SearchResult,
)
from services.evidence_store import EvidenceStore
from services.integrity_ledger import IntegrityLedger


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def tmp_env(tmp_path):
    store_dir = tmp_path / "evidence_store"
    store_dir.mkdir()
    ledger_path = str(tmp_path / "ledger.jsonl")
    index_path = str(tmp_path / "search_index.json")
    return {
        "store": EvidenceStore(root=str(store_dir)),
        "ledger": IntegrityLedger(ledger_path=ledger_path),
        "index_path": index_path,
        "tmp_path": tmp_path,
    }


@pytest.fixture
def indexer(tmp_env):
    return EvidenceIndexer(
        store=tmp_env["store"],
        ledger=tmp_env["ledger"],
        index_path=tmp_env["index_path"],
    )


# ---------------------------------------------------------------------------
# Indexing tests
# ---------------------------------------------------------------------------


class TestIndexEvidence:
    """Test indexing operations."""

    def test_index_single_item(self, indexer):
        entry = indexer.index_evidence(
            evidence_id="ev-001",
            original_sha256="a" * 64,
            filename="report.pdf",
            text_content="This is a test document about evidence processing.",
            content_type="text",
        )
        assert isinstance(entry, IndexEntry)
        assert entry.evidence_id == "ev-001"
        assert entry.word_count == 8
        assert entry.character_count > 0
        assert entry.line_count == 1

    def test_index_with_entities(self, indexer):
        text = "Contact john@example.com or call 555-123-4567 for details."
        entry = indexer.index_evidence(
            evidence_id="ev-002",
            original_sha256="b" * 64,
            filename="contact_info.txt",
            text_content=text,
        )
        assert "john@example.com" in entry.email_addresses
        assert any("555" in p and "4567" in p for p in entry.phone_numbers)

    def test_index_persists_to_disk(self, tmp_env):
        indexer1 = EvidenceIndexer(
            store=tmp_env["store"],
            ledger=tmp_env["ledger"],
            index_path=tmp_env["index_path"],
        )
        indexer1.index_evidence(
            evidence_id="ev-persist",
            original_sha256="c" * 64,
            filename="doc.txt",
            text_content="Persistent content.",
        )

        # Re-open index
        indexer2 = EvidenceIndexer(
            store=tmp_env["store"],
            ledger=tmp_env["ledger"],
            index_path=tmp_env["index_path"],
        )
        assert indexer2.entry_count == 1
        entry = indexer2.get_entry("ev-persist")
        assert entry is not None
        assert entry.filename == "doc.txt"

    def test_index_entry_count(self, indexer):
        assert indexer.entry_count == 0
        indexer.index_evidence("ev-1", "a" * 64, "a.txt", "aaa")
        assert indexer.entry_count == 1
        indexer.index_evidence("ev-2", "b" * 64, "b.txt", "bbb")
        assert indexer.entry_count == 2

    def test_index_logs_to_ledger(self, tmp_env, indexer):
        indexer.index_evidence("ev-audit", "d" * 64, "audit.txt", "Audit test.")
        entries = tmp_env["ledger"].read_all()
        actions = [e["action"] for e in entries]
        assert "index.evidence_indexed" in actions

    def test_index_empty_text(self, indexer):
        entry = indexer.index_evidence(
            evidence_id="ev-empty",
            original_sha256="e" * 64,
            filename="blank.txt",
            text_content="",
        )
        assert entry.word_count == 0
        assert entry.character_count == 0


# ---------------------------------------------------------------------------
# Search tests
# ---------------------------------------------------------------------------


class TestSearch:
    """Test search functionality."""

    @pytest.fixture(autouse=True)
    def _populate(self, indexer):
        """Populate the index with test data."""
        indexer.index_evidence(
            "ev-100", "a" * 64, "incident_report.pdf",
            "On November 29 2025, Officer Bryan Merritt responded to a "
            "domestic disturbance call at 123 Main Street. The officer "
            "activated his body-worn camera upon arrival. Contact: "
            "dispatch@police.gov or 555-111-2222.",
        )
        indexer.index_evidence(
            "ev-101", "b" * 64, "witness_statement.txt",
            "I saw two people arguing in the parking lot. One person was "
            "wearing a red jacket. The other was wearing dark clothing. "
            "I called the police at approximately 10:45 PM.",
        )
        indexer.index_evidence(
            "ev-102", "c" * 64, "evidence_log.docx",
            "Evidence item 47: Body camera footage from Officer Merritt. "
            "Duration 12 minutes 34 seconds. Badge number 4521. "
            "Chain of custody maintained by Sergeant Wilson.",
        )
        self.indexer = indexer

    def test_simple_keyword_search(self):
        response = self.indexer.search("officer")
        assert isinstance(response, SearchResponse)
        assert response.total_results >= 1
        filenames = [r.filename for r in response.results]
        assert "incident_report.pdf" in filenames

    def test_phrase_search(self):
        response = self.indexer.search('"body-worn camera"')
        assert response.total_results == 1
        assert response.results[0].filename == "incident_report.pdf"

    def test_multi_term_and_search(self):
        """Multiple terms should use AND logic."""
        response = self.indexer.search("officer merritt")
        assert response.total_results >= 1
        # Both terms must be present
        for r in response.results:
            entry = self.indexer.get_entry(r.evidence_id)
            assert "officer" in entry.full_text.lower()
            assert "merritt" in entry.full_text.lower()

    def test_no_results(self):
        response = self.indexer.search("xyznonexistent123")
        assert response.total_results == 0
        assert response.results == []

    def test_empty_query(self):
        response = self.indexer.search("")
        assert response.total_results == 0

    def test_search_snippet(self):
        response = self.indexer.search("parking lot")
        assert response.total_results >= 1
        snippet = response.results[0].snippet
        assert "parking lot" in snippet.lower()

    def test_search_case_insensitive(self):
        response = self.indexer.search("OFFICER BRYAN")
        assert response.total_results >= 1

    def test_search_scoped_by_evidence_ids(self):
        """Search should respect evidence ID scope."""
        response = self.indexer.search(
            "officer", case_evidence_ids=["ev-100"]
        )
        assert response.total_results == 1
        assert response.results[0].evidence_id == "ev-100"

    def test_search_returns_match_count(self):
        response = self.indexer.search("officer")
        for r in response.results:
            assert r.match_count > 0

    def test_search_time_recorded(self):
        response = self.indexer.search("camera")
        assert response.search_time_ms >= 0

    def test_search_results_sorted_by_score(self):
        """Results should be sorted by relevance (match count)."""
        response = self.indexer.search("merritt")
        if len(response.results) >= 2:
            for i in range(len(response.results) - 1):
                assert response.results[i].score >= response.results[i + 1].score
