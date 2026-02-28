"""
Tests for services/legal_analysis.py — Phase 6
=================================================
Tests issue mapping, templates, citation registry, and argument builder.
"""

from dataclasses import asdict

import pytest

from services.integrity_ledger import IntegrityLedger
from services.legal_analysis import (
    CONSTITUTIONAL_ISSUES,
    KNOWN_CITATIONS,
    ArgumentBuilder,
    ArgumentPoint,
    CitationRegistry,
    IssueMapper,
    StandardTemplates,
    StructuredArgument,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def ledger(tmp_path):
    return IntegrityLedger(ledger_path=str(tmp_path / "ledger.jsonl"))


# ---------------------------------------------------------------------------
# Issue Mapper
# ---------------------------------------------------------------------------


class TestIssueMapper:
    """Test constitutional issue keyword mapping."""

    def test_fourth_amendment_keywords(self):
        mapper = IssueMapper()
        result = mapper.map_evidence(
            "ev-1", "report.txt",
            "The officer conducted a search of the vehicle without a warrant."
        )
        codes = [i["issue_code"] for i in result.matched_issues]
        assert "4A" in codes

    def test_fifth_amendment_miranda(self):
        mapper = IssueMapper()
        result = mapper.map_evidence(
            "ev-2", "statement.txt",
            "The suspect was not given Miranda warnings before the interrogation."
        )
        codes = [i["issue_code"] for i in result.matched_issues]
        assert "5A" in codes

    def test_multiple_issues(self):
        mapper = IssueMapper()
        result = mapper.map_evidence(
            "ev-3", "memo.txt",
            "The warrantless search produced a firearm. The suspect invoked their "
            "right to counsel but interrogation continued."
        )
        codes = [i["issue_code"] for i in result.matched_issues]
        assert "4A" in codes  # search, warrant
        assert "2A" in codes  # firearm
        assert "6A" in codes  # counsel

    def test_no_issues_detected(self):
        mapper = IssueMapper()
        result = mapper.map_evidence(
            "ev-4", "receipt.pdf",
            "Invoice for office supplies. Total: $42.50."
        )
        assert len(result.matched_issues) == 0
        assert "No constitutional keywords" in result.confidence_note

    def test_empty_text(self):
        mapper = IssueMapper()
        result = mapper.map_evidence("ev-5", "blank.txt", "")
        assert len(result.matched_issues) == 0
        assert "No text content" in result.confidence_note

    def test_matched_keywords_tracked(self):
        mapper = IssueMapper()
        result = mapper.map_evidence(
            "ev-6", "report.txt",
            "The search was conducted with probable cause."
        )
        fourth = next(i for i in result.matched_issues if i["issue_code"] == "4A")
        assert "search" in fourth["matched_keywords"]
        assert "probable cause" in fourth["matched_keywords"]

    def test_confidence_note_present(self):
        mapper = IssueMapper()
        result = mapper.map_evidence(
            "ev-7", "doc.txt",
            "The warrant was properly executed."
        )
        assert result.confidence_note
        assert "Manual legal review required" in result.confidence_note or "No constitutional" in result.confidence_note


# ---------------------------------------------------------------------------
# Standard Templates
# ---------------------------------------------------------------------------


class TestStandardTemplates:
    """Test analysis template system."""

    def test_list_templates(self):
        templates = StandardTemplates.list_templates()
        assert len(templates) >= 3
        ids = [t["template_id"] for t in templates]
        assert "fourth_amendment_search" in ids
        assert "due_process_analysis" in ids
        assert "excessive_force_analysis" in ids

    def test_get_template(self):
        t = StandardTemplates.get_template("fourth_amendment_search")
        assert t is not None
        assert t["title"] == "Fourth Amendment Search Analysis"
        assert len(t["sections"]) >= 5

    def test_template_not_found(self):
        t = StandardTemplates.get_template("nonexistent")
        assert t is None

    def test_generate_outline(self):
        outline = StandardTemplates.generate_outline(
            template_id="fourth_amendment_search",
            case_title="Test Case",
            evidence_items=[{"evidence_id": "ev-1", "filename": "cam.mp4"}],
        )
        assert outline is not None
        assert outline["case_title"] == "Test Case"
        assert len(outline["sections"]) >= 5
        # All sections should have empty content (to be filled)
        for s in outline["sections"]:
            assert s["content"] == ""

    def test_generate_outline_has_analyst_note(self):
        outline = StandardTemplates.generate_outline("due_process_analysis")
        assert "human analysis" in outline["note"].lower()


# ---------------------------------------------------------------------------
# Citation Registry
# ---------------------------------------------------------------------------


class TestCitationRegistry:
    """Test legal citation verification and search."""

    def test_verify_known_citation(self):
        data = CitationRegistry.verify_citation("terry_v_ohio")
        assert data is not None
        assert "392 U.S. 1" in data["citation"]

    def test_verify_unknown_citation(self):
        data = CitationRegistry.verify_citation("fake_v_case")
        assert data is None

    def test_verify_with_spaces(self):
        data = CitationRegistry.verify_citation("terry v ohio")
        assert data is not None

    def test_search_by_keyword(self):
        results = CitationRegistry.search_citations("exclusionary")
        assert len(results) >= 1
        assert any("mapp" in r["key"] for r in results)

    def test_search_by_amendment(self):
        results = CitationRegistry.search_citations("", amendment="4A")
        assert len(results) >= 2  # Terry, Mapp, Graham, Katz

    def test_format_citation(self):
        fmt = CitationRegistry.format_citation("miranda_v_arizona")
        assert fmt is not None
        assert "384 U.S. 436" in fmt

    def test_format_unknown_returns_none(self):
        assert CitationRegistry.format_citation("nonexistent") is None

    def test_list_all(self):
        all_cites = CitationRegistry.list_all()
        assert len(all_cites) >= 5
        assert all("citation" in c for c in all_cites)
        assert all("holding" in c for c in all_cites)

    def test_no_fabricated_citations(self):
        """Every citation in the registry must have a real U.S. Reports format."""
        for key, data in KNOWN_CITATIONS.items():
            citation = data["citation"]
            assert "U.S." in citation or "S.Ct." in citation, (
                f"Citation {key} doesn't appear to be a real citation: {citation}"
            )


# ---------------------------------------------------------------------------
# Argument Builder
# ---------------------------------------------------------------------------


class TestArgumentBuilder:
    """Test structured argument outline generation."""

    def test_build_basic_argument(self, ledger):
        builder = ArgumentBuilder(ledger=ledger)
        arg = builder.build_argument(
            title="Fourth Amendment Search Issue",
            issue_code="4A",
            evidence_items=[
                {"evidence_id": "ev-1", "filename": "bodycam.mp4", "summary": "Shows vehicle search."},
                {"evidence_id": "ev-2", "filename": "report.pdf", "summary": "Incident report."},
            ],
            relevant_citations=["terry_v_ohio", "katz_v_united_states"],
        )
        assert isinstance(arg, StructuredArgument)
        assert arg.title == "Fourth Amendment Search Issue"
        assert arg.amendment == "Fourth Amendment"
        assert len(arg.points) == 2

    def test_argument_points_have_placeholders(self, ledger):
        builder = ArgumentBuilder(ledger=ledger)
        arg = builder.build_argument(
            title="Test", issue_code="5A",
            evidence_items=[{"evidence_id": "ev-1", "filename": "doc.txt"}],
        )
        point = arg.points[0]
        assert "TO BE COMPLETED" in point.claim
        assert "TO BE COMPLETED" in point.counter_considerations[0]

    def test_argument_includes_legal_authority(self, ledger):
        builder = ArgumentBuilder(ledger=ledger)
        arg = builder.build_argument(
            title="Test", issue_code="4A",
            evidence_items=[{"evidence_id": "ev-1", "filename": "cam.mp4"}],
            relevant_citations=["graham_v_connor"],
        )
        assert len(arg.points[0].legal_authority) == 1
        assert "490 U.S. 386" in arg.points[0].legal_authority[0]

    def test_argument_logged_to_ledger(self, ledger):
        builder = ArgumentBuilder(ledger=ledger)
        builder.build_argument(
            title="Audit Test", issue_code="6A",
            evidence_items=[{"evidence_id": "ev-1", "filename": "statement.txt"}],
            actor="analyst",
        )
        entries = ledger.read_all()
        actions = [e["action"] for e in entries]
        assert "legal.argument_outline_created" in actions

    def test_argument_without_citations(self, ledger):
        builder = ArgumentBuilder(ledger=ledger)
        arg = builder.build_argument(
            title="No Citations Test", issue_code="8A",
            evidence_items=[{"evidence_id": "ev-1", "filename": "doc.txt"}],
        )
        assert len(arg.points) == 1
        assert len(arg.points[0].legal_authority) == 0

    def test_argument_note_present(self, ledger):
        builder = ArgumentBuilder(ledger=ledger)
        arg = builder.build_argument(
            title="Test", issue_code="4A",
            evidence_items=[{"evidence_id": "ev-1", "filename": "cam.mp4"}],
        )
        assert "human review" in arg.note.lower()
