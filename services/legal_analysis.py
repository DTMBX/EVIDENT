"""
B30 Phase 6 — Legal Analysis Tooling
=======================================
Structured legal research helpers for constitutional analysis.

Provides:
  1. IssueMapper — maps evidence to constitutional issues/amendments.
  2. StandardTemplates — produces structured analysis outlines.
  3. CitationRegistry — verifies and formats legal citations.
  4. ArgumentBuilder — organizes evidence into structured arguments.

CRITICAL CONSTRAINT:
  These tools are RESEARCH HELPERS only. They:
  - MUST NOT fabricate cases or statutes.
  - MUST NOT render legal conclusions or advice.
  - MUST cite sources for every claim.
  - MUST flag when a citation cannot be verified.
  - Operate on structured data, not free-form inference.
"""

import json
import logging
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from services.integrity_ledger import IntegrityLedger

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Constitutional issue taxonomy
# ---------------------------------------------------------------------------

CONSTITUTIONAL_ISSUES = {
    "1A": {
        "amendment": "First Amendment",
        "rights": ["Freedom of Speech", "Freedom of Press", "Freedom of Religion",
                    "Freedom of Assembly", "Right to Petition"],
        "keywords": ["speech", "press", "religion", "assembly", "petition",
                      "expression", "protest", "censorship"],
    },
    "2A": {
        "amendment": "Second Amendment",
        "rights": ["Right to Bear Arms"],
        "keywords": ["firearm", "firearms", "weapons", "arms", "gun", "militia"],
    },
    "4A": {
        "amendment": "Fourth Amendment",
        "rights": ["Protection from Unreasonable Search and Seizure",
                    "Warrant Requirement", "Probable Cause"],
        "keywords": ["search", "seizure", "warrant", "probable cause",
                      "privacy", "surveillance", "stop and frisk", "terry stop"],
    },
    "5A": {
        "amendment": "Fifth Amendment",
        "rights": ["Due Process", "Self-Incrimination", "Double Jeopardy",
                    "Eminent Domain", "Grand Jury"],
        "keywords": ["due process", "self-incrimination", "miranda",
                      "double jeopardy", "takings", "grand jury"],
    },
    "6A": {
        "amendment": "Sixth Amendment",
        "rights": ["Right to Counsel", "Speedy Trial", "Jury Trial",
                    "Confrontation Clause", "Compulsory Process"],
        "keywords": ["counsel", "attorney", "lawyer", "speedy trial",
                      "jury", "confrontation", "witness"],
    },
    "8A": {
        "amendment": "Eighth Amendment",
        "rights": ["Excessive Bail", "Cruel and Unusual Punishment",
                    "Excessive Fines"],
        "keywords": ["bail", "cruel", "unusual", "punishment", "excessive",
                      "fines", "sentencing"],
    },
    "14A": {
        "amendment": "Fourteenth Amendment",
        "rights": ["Equal Protection", "Due Process (State)",
                    "Privileges and Immunities", "Citizenship"],
        "keywords": ["equal protection", "discrimination", "due process",
                      "state action", "incorporation", "citizenship"],
    },
}


# ---------------------------------------------------------------------------
# Issue Mapper
# ---------------------------------------------------------------------------


@dataclass
class IssueMappingResult:
    """Result of mapping evidence to constitutional issues."""
    evidence_id: str
    filename: str
    matched_issues: List[Dict] = field(default_factory=list)
    keyword_matches: List[str] = field(default_factory=list)
    confidence_note: str = ""


class IssueMapper:
    """
    Maps evidence text content to constitutional issues using keyword matching.

    This is a DETERMINISTIC helper — keyword match only, no inference.
    Every match is traceable to a specific keyword in the taxonomy.
    """

    def map_evidence(
        self,
        evidence_id: str,
        filename: str,
        text_content: str,
    ) -> IssueMappingResult:
        """
        Map evidence text to constitutional issues via keyword matching.

        Returns matched issues with the specific keywords that triggered them.
        """
        result = IssueMappingResult(
            evidence_id=evidence_id,
            filename=filename,
        )

        if not text_content:
            result.confidence_note = "No text content available for analysis."
            return result

        text_lower = text_content.lower()

        for code, issue_data in CONSTITUTIONAL_ISSUES.items():
            matched_keywords = []
            for kw in issue_data["keywords"]:
                if kw.lower() in text_lower:
                    matched_keywords.append(kw)

            if matched_keywords:
                result.matched_issues.append({
                    "issue_code": code,
                    "amendment": issue_data["amendment"],
                    "rights": issue_data["rights"],
                    "matched_keywords": matched_keywords,
                    "match_count": len(matched_keywords),
                })
                result.keyword_matches.extend(matched_keywords)

        if not result.matched_issues:
            result.confidence_note = (
                "No constitutional keywords detected in evidence text. "
                "Manual review may identify issues not in the keyword taxonomy."
            )
        else:
            result.confidence_note = (
                f"Keyword-based matching only. {len(result.matched_issues)} "
                f"potential issue(s) identified. Manual legal review required."
            )

        return result


# ---------------------------------------------------------------------------
# Standard Templates
# ---------------------------------------------------------------------------

ANALYSIS_TEMPLATES = {
    "fourth_amendment_search": {
        "title": "Fourth Amendment Search Analysis",
        "sections": [
            {"heading": "Facts", "description": "Objective facts from evidence about the search/seizure."},
            {"heading": "Was there a search?", "description": "Did government action intrude on a reasonable expectation of privacy?"},
            {"heading": "Was a warrant obtained?", "description": "If so, was it supported by probable cause and particularity?"},
            {"heading": "Warrant exceptions", "description": "Do any recognized exceptions apply (consent, exigent circumstances, plain view, search incident to arrest, automobile)?"},
            {"heading": "Standing", "description": "Does the party challenging the search have standing (reasonable expectation of privacy)?"},
            {"heading": "Exclusionary rule", "description": "Would evidence be subject to exclusion under the exclusionary rule?"},
            {"heading": "Source citations", "description": "All evidence items and legal authorities referenced."},
        ],
    },
    "due_process_analysis": {
        "title": "Due Process Analysis",
        "sections": [
            {"heading": "Facts", "description": "Objective facts from evidence."},
            {"heading": "Liberty or property interest", "description": "Is a protected interest at stake?"},
            {"heading": "Procedural requirements", "description": "What process was due and what was provided?"},
            {"heading": "Adequacy of process", "description": "Mathews v. Eldridge balancing (private interest, risk of error, government interest)."},
            {"heading": "Substantive due process", "description": "Was the government action rationally related to a legitimate interest?"},
            {"heading": "Source citations", "description": "All evidence items and legal authorities referenced."},
        ],
    },
    "excessive_force_analysis": {
        "title": "Excessive Force Analysis",
        "sections": [
            {"heading": "Facts", "description": "Objective facts about the use of force from evidence."},
            {"heading": "Severity of force", "description": "What level of force was used?"},
            {"heading": "Government interest", "description": "What was the immediate threat, resistance, or flight risk?"},
            {"heading": "Graham v. Connor factors", "description": "Objective reasonableness under the totality of circumstances."},
            {"heading": "BWC evidence", "description": "What does the body camera footage show at each relevant timecode?"},
            {"heading": "Source citations", "description": "All evidence items and legal authorities referenced."},
        ],
    },
    "evidence_integrity_report": {
        "title": "Evidence Integrity Report",
        "sections": [
            {"heading": "Evidence inventory", "description": "List of all evidence items with SHA-256 hashes."},
            {"heading": "Chain of custody", "description": "Complete custody chain from collection through analysis."},
            {"heading": "Integrity verification", "description": "Hash verification results for each item."},
            {"heading": "Processing record", "description": "All derivatives generated and their parameters."},
            {"heading": "Access log", "description": "All access events from the integrity ledger."},
            {"heading": "Certification", "description": "Statement of integrity status."},
        ],
    },
}


class StandardTemplates:
    """Provides structured analysis templates."""

    @staticmethod
    def list_templates() -> List[Dict]:
        """List all available analysis templates."""
        return [
            {
                "template_id": tid,
                "title": tdata["title"],
                "section_count": len(tdata["sections"]),
            }
            for tid, tdata in ANALYSIS_TEMPLATES.items()
        ]

    @staticmethod
    def get_template(template_id: str) -> Optional[Dict]:
        """Get a specific template by ID."""
        tdata = ANALYSIS_TEMPLATES.get(template_id)
        if not tdata:
            return None
        return {
            "template_id": template_id,
            "title": tdata["title"],
            "sections": tdata["sections"],
        }

    @staticmethod
    def generate_outline(
        template_id: str,
        case_title: str = "",
        evidence_items: Optional[List[Dict]] = None,
    ) -> Optional[Dict]:
        """
        Generate a structured analysis outline from a template.

        This populates the template structure with placeholders for the analyst.

        Args:
            template_id: Template to use.
            case_title: Optional case title.
            evidence_items: Optional list of evidence items to reference.

        Returns:
            Structured outline dict, or None if template not found.
        """
        tdata = ANALYSIS_TEMPLATES.get(template_id)
        if not tdata:
            return None

        outline = {
            "template_id": template_id,
            "title": tdata["title"],
            "case_title": case_title,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "sections": [],
            "evidence_items": evidence_items or [],
            "note": "This is a structured outline template. All sections require human analysis and completion.",
        }

        for section in tdata["sections"]:
            outline["sections"].append({
                "heading": section["heading"],
                "description": section["description"],
                "content": "",  # To be filled by analyst
                "citations": [],  # To be filled by analyst
            })

        return outline


# ---------------------------------------------------------------------------
# Citation Registry
# ---------------------------------------------------------------------------

# Well-known landmark cases (verified, not fabricated)
KNOWN_CITATIONS = {
    "terry_v_ohio": {
        "citation": "Terry v. Ohio, 392 U.S. 1 (1968)",
        "holding": "Police may stop and frisk based on reasonable suspicion.",
        "amendment": "4A",
    },
    "miranda_v_arizona": {
        "citation": "Miranda v. Arizona, 384 U.S. 436 (1966)",
        "holding": "Suspects must be informed of rights before custodial interrogation.",
        "amendment": "5A",
    },
    "mapp_v_ohio": {
        "citation": "Mapp v. Ohio, 367 U.S. 643 (1961)",
        "holding": "Exclusionary rule applies to states through 14th Amendment.",
        "amendment": "4A",
    },
    "graham_v_connor": {
        "citation": "Graham v. Connor, 490 U.S. 386 (1989)",
        "holding": "Excessive force claims analyzed under objective reasonableness standard.",
        "amendment": "4A",
    },
    "mathews_v_eldridge": {
        "citation": "Mathews v. Eldridge, 424 U.S. 319 (1976)",
        "holding": "Three-factor balancing test for procedural due process.",
        "amendment": "5A",
    },
    "katz_v_united_states": {
        "citation": "Katz v. United States, 389 U.S. 347 (1967)",
        "holding": "Fourth Amendment protects reasonable expectations of privacy.",
        "amendment": "4A",
    },
    "gideon_v_wainwright": {
        "citation": "Gideon v. Wainwright, 372 U.S. 335 (1963)",
        "holding": "Right to counsel applies in state felony proceedings.",
        "amendment": "6A",
    },
    "marbury_v_madison": {
        "citation": "Marbury v. Madison, 5 U.S. 137 (1803)",
        "holding": "Established judicial review of legislation.",
        "amendment": "Article III",
    },
}


class CitationRegistry:
    """
    Verifies and formats legal citations.

    CRITICAL: Only returns citations from the KNOWN_CITATIONS registry.
    Never fabricates or invents citations.
    """

    @staticmethod
    def verify_citation(citation_key: str) -> Optional[Dict]:
        """
        Verify a citation exists in the registry.

        Returns the citation data if found, None if not found.
        """
        return KNOWN_CITATIONS.get(citation_key.lower().replace(" ", "_"))

    @staticmethod
    def search_citations(
        query: str,
        amendment: Optional[str] = None,
    ) -> List[Dict]:
        """
        Search the citation registry by keyword.

        Args:
            query: Search keyword.
            amendment: Optional amendment code to filter by (e.g., "4A").

        Returns:
            List of matching citation dicts.
        """
        results = []
        query_lower = query.lower()

        for key, data in KNOWN_CITATIONS.items():
            # Check amendment filter
            if amendment and data.get("amendment") != amendment:
                continue

            # Check keyword match
            if (query_lower in key
                    or query_lower in data["citation"].lower()
                    or query_lower in data["holding"].lower()):
                results.append({
                    "key": key,
                    **data,
                })

        return results

    @staticmethod
    def format_citation(citation_key: str) -> Optional[str]:
        """Format a citation in standard legal format. Returns None if not found."""
        data = KNOWN_CITATIONS.get(citation_key.lower().replace(" ", "_"))
        if not data:
            return None
        return data["citation"]

    @staticmethod
    def list_all() -> List[Dict]:
        """List all known citations."""
        return [{"key": k, **v} for k, v in KNOWN_CITATIONS.items()]


# ---------------------------------------------------------------------------
# Argument Builder
# ---------------------------------------------------------------------------


@dataclass
class ArgumentPoint:
    """A single point in a structured legal argument."""
    point_number: int
    claim: str
    evidence_support: List[Dict] = field(default_factory=list)
    legal_authority: List[str] = field(default_factory=list)
    counter_considerations: List[str] = field(default_factory=list)


@dataclass
class StructuredArgument:
    """A complete structured argument."""
    title: str
    issue_code: str
    amendment: str
    points: List[ArgumentPoint] = field(default_factory=list)
    generated_at: str = ""
    note: str = (
        "This is a structured outline. Claims, counter-considerations, "
        "and legal analysis require human review and completion."
    )


class ArgumentBuilder:
    """
    Organizes evidence and legal authorities into structured argument outlines.

    Produces outlines only — does not generate substantive legal analysis.
    """

    def __init__(self, ledger: Optional[IntegrityLedger] = None):
        self._ledger = ledger

    def build_argument(
        self,
        title: str,
        issue_code: str,
        evidence_items: List[Dict],
        relevant_citations: Optional[List[str]] = None,
        actor: str = "system",
    ) -> StructuredArgument:
        """
        Build a structured argument outline.

        Args:
            title: Argument title.
            issue_code: Constitutional issue code (e.g., "4A").
            evidence_items: List of evidence dicts with 'evidence_id', 'filename',
                            'summary' fields.
            relevant_citations: Optional list of citation keys from CitationRegistry.
            actor: Actor for audit.

        Returns:
            StructuredArgument outline.
        """
        issue_data = CONSTITUTIONAL_ISSUES.get(issue_code, {})
        amendment = issue_data.get("amendment", issue_code)

        arg = StructuredArgument(
            title=title,
            issue_code=issue_code,
            amendment=amendment,
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

        # Create a point for each evidence item
        for i, ev in enumerate(evidence_items, 1):
            legal_authorities = []
            if relevant_citations:
                for ckey in relevant_citations:
                    formatted = CitationRegistry.format_citation(ckey)
                    if formatted:
                        legal_authorities.append(formatted)

            point = ArgumentPoint(
                point_number=i,
                claim="[TO BE COMPLETED BY ANALYST]",
                evidence_support=[{
                    "evidence_id": ev.get("evidence_id", ""),
                    "filename": ev.get("filename", ""),
                    "summary": ev.get("summary", "[Summary to be completed]"),
                }],
                legal_authority=legal_authorities,
                counter_considerations=["[TO BE COMPLETED BY ANALYST]"],
            )
            arg.points.append(point)

        # Audit
        if self._ledger:
            self._ledger.append(
                action="legal.argument_outline_created",
                actor=actor,
                details={
                    "title": title,
                    "issue_code": issue_code,
                    "evidence_count": len(evidence_items),
                    "citation_count": len(relevant_citations or []),
                },
            )

        return arg
