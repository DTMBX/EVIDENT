"""
Tests for services/chat_grounding.py — Phase 5
=================================================
Tests citation validation, grounded tool execution, system prompt building,
and safe-mode gating.
"""

import pytest

from services.chat_grounding import (
    CitationCheck,
    GroundedToolExecutor,
    GROUNDED_SYSTEM_PROMPT,
    GROUNDED_TOOLS,
    SAFE_MODE_PROMPT_SUFFIX,
    build_grounded_system_prompt,
    validate_citations,
)
from services.evidence_indexer import EvidenceIndexer
from services.evidence_store import EvidenceStore
from services.integrity_ledger import IntegrityLedger


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def tmp_env(tmp_path):
    store_dir = tmp_path / "evidence_store"
    store_dir.mkdir()
    return {
        "store": EvidenceStore(root=str(store_dir)),
        "ledger": IntegrityLedger(ledger_path=str(tmp_path / "ledger.jsonl")),
        "indexer": EvidenceIndexer(
            store=EvidenceStore(root=str(store_dir)),
            ledger=IntegrityLedger(ledger_path=str(tmp_path / "ledger2.jsonl")),
            index_path=str(tmp_path / "idx.json"),
        ),
        "tmp_path": tmp_path,
    }


@pytest.fixture
def populated_indexer(tmp_env):
    """Indexer with test evidence."""
    idx = tmp_env["indexer"]
    idx.index_evidence(
        "ev-100", "a" * 64, "bodycam_merritt.mp4",
        "Officer Merritt activated his body camera at 22:57. "
        "Domestic disturbance at 123 Main St. dispatch@police.gov",
    )
    idx.index_evidence(
        "ev-101", "b" * 64, "witness_statement.txt",
        "I saw two people arguing. One wore a red jacket.",
    )
    return idx


# ---------------------------------------------------------------------------
# Citation Validation
# ---------------------------------------------------------------------------


class TestCitationValidation:
    """Test citation validation logic."""

    def test_valid_citation_by_filename(self):
        text = "The footage shows [Evidence: bodycam_merritt.mp4] the officer arriving."
        result = validate_citations(
            text,
            known_evidence_ids=["ev-100"],
            known_filenames=["bodycam_merritt.mp4"],
        )
        assert result.has_citations is True
        assert result.citation_count == 1
        assert len(result.valid_citations) == 1
        assert result.passed is True

    def test_valid_citation_by_evidence_id(self):
        text = "According to [Evidence: ev-100], the incident occurred at 22:57."
        result = validate_citations(
            text,
            known_evidence_ids=["ev-100"],
            known_filenames=["bodycam.mp4"],
        )
        assert result.has_citations is True
        assert len(result.valid_citations) == 1
        assert result.passed is True

    def test_citation_with_timecode(self):
        text = "At [Evidence: bodycam_merritt.mp4, timecode 00:02:34] the subject is visible."
        result = validate_citations(
            text,
            known_evidence_ids=["ev-100"],
            known_filenames=["bodycam_merritt.mp4"],
        )
        assert result.has_citations is True
        assert len(result.valid_citations) == 1

    def test_invalid_citation_unknown_file(self):
        text = "According to [Evidence: nonexistent_file.mp4], something happened."
        result = validate_citations(
            text,
            known_evidence_ids=["ev-100"],
            known_filenames=["bodycam_merritt.mp4"],
        )
        assert len(result.invalid_citations) == 1
        assert result.passed is False

    def test_no_citations(self):
        text = "The evidence clearly shows guilt."
        result = validate_citations(
            text,
            known_evidence_ids=["ev-100"],
            known_filenames=["bodycam.mp4"],
        )
        assert result.has_citations is False
        assert result.citation_count == 0

    def test_multiple_citations(self):
        text = (
            "[Evidence: bodycam_merritt.mp4] shows arrival. "
            "[Evidence: witness_statement.txt] corroborates this."
        )
        result = validate_citations(
            text,
            known_evidence_ids=["ev-100", "ev-101"],
            known_filenames=["bodycam_merritt.mp4", "witness_statement.txt"],
        )
        assert result.citation_count == 2
        assert len(result.valid_citations) == 2
        assert result.passed is True

    def test_fabrication_warning_guilty(self):
        text = "Based on [Evidence: bodycam_merritt.mp4], the subject is clearly guilty."
        result = validate_citations(
            text,
            known_evidence_ids=["ev-100"],
            known_filenames=["bodycam_merritt.mp4"],
        )
        assert any("guilty" in w.lower() for w in result.warnings)

    def test_fabrication_warning_legal_advice(self):
        text = "Based on the evidence, I recommend filing charges immediately."
        result = validate_citations(
            text,
            known_evidence_ids=[],
            known_filenames=[],
        )
        assert any("recommend" in w.lower() for w in result.warnings)

    def test_empty_response(self):
        result = validate_citations("", [], [])
        assert result.passed is False

    def test_filename_references_detected(self):
        text = "The file bodycam_merritt.mp4 contains the footage."
        result = validate_citations(
            text,
            known_evidence_ids=[],
            known_filenames=["bodycam_merritt.mp4"],
        )
        assert len(result.filename_references) >= 1


# ---------------------------------------------------------------------------
# Grounded Tool Executor
# ---------------------------------------------------------------------------


class TestGroundedToolExecutor:
    """Test the grounded tool executor."""

    def test_search_evidence_index(self, tmp_env, populated_indexer):
        executor = GroundedToolExecutor(
            indexer=populated_indexer,
            ledger=tmp_env["ledger"],
        )
        result = executor.execute(
            tool_name="search_evidence_index",
            arguments={"query": "officer"},
            actor="test_user",
            conversation_id="conv-001",
        )
        assert "results" in result
        assert result["total_results"] >= 1

    def test_get_evidence_context(self, tmp_env, populated_indexer):
        executor = GroundedToolExecutor(
            indexer=populated_indexer,
            ledger=tmp_env["ledger"],
        )
        result = executor.execute(
            tool_name="get_evidence_context",
            arguments={"evidence_id": "ev-100"},
            actor="test_user",
        )
        assert result["evidence_id"] == "ev-100"
        assert result["filename"] == "bodycam_merritt.mp4"
        assert "officer" in result["full_text"].lower()

    def test_get_evidence_context_not_found(self, tmp_env, populated_indexer):
        executor = GroundedToolExecutor(
            indexer=populated_indexer,
            ledger=tmp_env["ledger"],
        )
        result = executor.execute(
            tool_name="get_evidence_context",
            arguments={"evidence_id": "nonexistent"},
        )
        assert "error" in result

    def test_list_evidence_summary(self, tmp_env, populated_indexer):
        executor = GroundedToolExecutor(
            indexer=populated_indexer,
            ledger=tmp_env["ledger"],
        )
        result = executor.execute(
            tool_name="list_evidence_summary",
            arguments={},
        )
        assert result["total_items"] == 2
        assert len(result["items"]) == 2

    def test_unknown_tool(self, tmp_env, populated_indexer):
        executor = GroundedToolExecutor(
            indexer=populated_indexer,
            ledger=tmp_env["ledger"],
        )
        result = executor.execute(
            tool_name="nonexistent_tool",
            arguments={},
        )
        assert "error" in result

    def test_tool_calls_logged_to_ledger(self, tmp_env, populated_indexer):
        executor = GroundedToolExecutor(
            indexer=populated_indexer,
            ledger=tmp_env["ledger"],
        )
        executor.execute(
            tool_name="search_evidence_index",
            arguments={"query": "test"},
            actor="auditor",
            conversation_id="conv-audit",
        )
        entries = tmp_env["ledger"].read_all()
        actions = [e["action"] for e in entries]
        assert "chat.tool_invoked" in actions
        assert "chat.tool_result" in actions

    def test_scoped_search(self, tmp_env, populated_indexer):
        """Executor should respect case_evidence_ids scope."""
        executor = GroundedToolExecutor(
            indexer=populated_indexer,
            ledger=tmp_env["ledger"],
            case_evidence_ids=["ev-101"],  # Only witness statement
        )
        result = executor.execute(
            tool_name="search_evidence_index",
            arguments={"query": "officer"},
        )
        # Officer is only in ev-100, which is out of scope
        assert result["total_results"] == 0

    def test_scoped_list_summary(self, tmp_env, populated_indexer):
        executor = GroundedToolExecutor(
            indexer=populated_indexer,
            ledger=tmp_env["ledger"],
            case_evidence_ids=["ev-100"],
        )
        result = executor.execute(
            tool_name="list_evidence_summary",
            arguments={},
        )
        assert result["total_items"] == 1


# ---------------------------------------------------------------------------
# System Prompt Building
# ---------------------------------------------------------------------------


class TestSystemPromptBuilder:
    """Test system prompt construction."""

    def test_default_prompt(self):
        prompt = build_grounded_system_prompt()
        assert "CITE EVIDENCE" in prompt
        assert "NO FABRICATION" in prompt
        assert "NO LEGAL ADVICE" in prompt

    def test_with_case_context(self):
        prompt = build_grounded_system_prompt(
            case_context="Domestic disturbance incident, November 2025",
        )
        assert "Domestic disturbance" in prompt
        assert "CASE CONTEXT" in prompt

    def test_with_evidence_count(self):
        prompt = build_grounded_system_prompt(evidence_count=15)
        assert "15 items indexed" in prompt

    def test_safe_mode(self):
        prompt = build_grounded_system_prompt(safe_mode=True)
        assert "SAFE MODE ACTIVE" in prompt
        assert "No interpretive analysis" in prompt

    def test_grounded_tools_well_formed(self):
        """All grounded tools should have required OpenAI function format."""
        for tool in GROUNDED_TOOLS:
            assert tool["type"] == "function"
            assert "function" in tool
            assert "name" in tool["function"]
            assert "description" in tool["function"]
            assert "parameters" in tool["function"]


# ---------------------------------------------------------------------------
# Ledger chain integrity after tool operations
# ---------------------------------------------------------------------------


class TestLedgerIntegrity:
    """Ensure ledger remains chain-valid after tool operations."""

    def test_ledger_valid_after_multiple_calls(self, tmp_env, populated_indexer):
        executor = GroundedToolExecutor(
            indexer=populated_indexer,
            ledger=tmp_env["ledger"],
        )
        executor.execute("search_evidence_index", {"query": "a"}, actor="u1")
        executor.execute("get_evidence_context", {"evidence_id": "ev-100"}, actor="u2")
        executor.execute("list_evidence_summary", {}, actor="u3")
        executor.execute("nonexistent_tool", {}, actor="u4")

        errors = tmp_env["ledger"].verify()
        assert errors == [], f"Ledger chain broken: {errors}"
