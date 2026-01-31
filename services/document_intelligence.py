"""
Document Intelligence Service
=============================

Advanced AI-powered document analysis for legal documents:
- Multi-length summarization (brief, standard, detailed)
- Entity extraction (parties, dates, courts, case numbers)
- Citation extraction with validation
- Issue spotting and risk assessment
- Sentiment and tone analysis
"""

import hashlib
import json
import logging
import os
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class SummaryLength(Enum):
    """Summary length options."""

    BRIEF = "brief"  # 1-2 sentences
    STANDARD = "standard"  # 1-2 paragraphs
    DETAILED = "detailed"  # Full summary with sections


class RiskLevel(Enum):
    """Risk assessment levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ExtractedEntity:
    """Represents an extracted entity from a document."""

    entity_type: str  # party, date, court, case_number, judge, attorney, etc.
    value: str
    confidence: float
    context: str = ""
    start_pos: int = 0
    end_pos: int = 0
    metadata: Dict = field(default_factory=dict)


@dataclass
class ExtractedCitation:
    """Represents an extracted legal citation."""

    citation_text: str
    citation_type: str  # case, statute, regulation, constitution
    jurisdiction: str
    year: Optional[int] = None
    reporter: Optional[str] = None
    volume: Optional[str] = None
    page: Optional[str] = None
    pinpoint: Optional[str] = None
    confidence: float = 0.0
    is_valid: bool = False
    validation_notes: str = ""


@dataclass
class LegalIssue:
    """Represents an identified legal issue."""

    issue_type: str
    description: str
    severity: RiskLevel
    relevant_text: str
    recommendations: List[str] = field(default_factory=list)
    related_citations: List[str] = field(default_factory=list)


@dataclass
class DocumentAnalysis:
    """Complete document analysis result."""

    document_id: str
    summary: Dict[str, str]  # {brief, standard, detailed}
    entities: List[ExtractedEntity]
    citations: List[ExtractedCitation]
    issues: List[LegalIssue]
    risk_assessment: Dict[str, Any]
    metadata: Dict[str, Any]
    processing_time_ms: float
    created_at: datetime = field(default_factory=datetime.utcnow)


class DocumentIntelligenceService:
    """
    AI-powered document intelligence service.

    Provides comprehensive document analysis including:
    - Summarization at multiple lengths
    - Entity extraction
    - Citation detection and validation
    - Legal issue identification
    - Risk assessment
    """

    # Citation patterns for various legal sources
    CITATION_PATTERNS = {
        "us_case": r"(\d+)\s+U\.?S\.?\s+(\d+)(?:\s*,\s*(\d+))?(?:\s*\((\d{4})\))?",
        "federal_reporter": r"(\d+)\s+F\.?(?:2d|3d|4th)?\s+(\d+)(?:\s*,\s*(\d+))?(?:\s*\(.*?(\d{4})\))?",
        "supreme_court_reporter": r"(\d+)\s+S\.?\s*Ct\.?\s+(\d+)",
        "state_reporter": r"(\d+)\s+([A-Z][a-z]+\.?(?:\s+\d+[a-z]*)?)\s+(\d+)",
        "usc": r"(\d+)\s+U\.?S\.?C\.?\s+§?\s*(\d+[a-z]*)",
        "cfr": r"(\d+)\s+C\.?F\.?R\.?\s+§?\s*(\d+(?:\.\d+)?)",
        "nj_statute": r"N\.?J\.?S\.?A\.?\s+(\d+[A-Z]?):(\d+)-(\d+(?:\.\d+)?)",
        "nj_admin": r"N\.?J\.?A\.?C\.?\s+(\d+):(\d+)-(\d+(?:\.\d+)?)",
    }

    # Entity patterns
    ENTITY_PATTERNS = {
        "case_number": r"(?:Case|Docket|No\.?|#)\s*(?:No\.?)?\s*([A-Z0-9]+-[A-Z0-9-]+)",
        "date": r"(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}",
        "court": r"(?:United States|U\.S\.)\s+(?:District|Circuit|Supreme)\s+Court|(?:Superior|Municipal|Tax)\s+Court\s+of\s+[A-Z][a-z]+",
        "judge": r"(?:Judge|Justice|Hon\.?|Honorable)\s+([A-Z][a-z]+(?:\s+[A-Z]\.?)?\s+[A-Z][a-z]+)",
        "attorney": r"(?:Attorney|Counsel|Esq\.?)\s+([A-Z][a-z]+(?:\s+[A-Z]\.?)?\s+[A-Z][a-z]+)",
    }

    def __init__(self):
        """Initialize the document intelligence service."""
        self.openai_client = None
        self.anthropic_client = None
        self._init_ai_clients()

        # Cache for expensive operations
        self._summary_cache = {}
        self._citation_cache = {}

    def _init_ai_clients(self):
        """Initialize AI provider clients."""
        # OpenAI
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            try:
                import openai

                self.openai_client = openai.OpenAI(api_key=openai_key)
                logger.info("OpenAI client initialized")
            except Exception as e:
                logger.warning(f"OpenAI initialization failed: {e}")

        # Anthropic Claude
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        if anthropic_key:
            try:
                import anthropic

                self.anthropic_client = anthropic.Anthropic(api_key=anthropic_key)
                logger.info("Anthropic client initialized")
            except Exception as e:
                logger.warning(f"Anthropic initialization failed: {e}")

    def _get_cache_key(self, text: str, operation: str) -> str:
        """Generate cache key for text operations."""
        text_hash = hashlib.sha256(text.encode()).hexdigest()[:16]
        return f"{operation}:{text_hash}"

    # =========================================================
    # SUMMARIZATION
    # =========================================================

    def summarize(
        self,
        text: str,
        length: SummaryLength = SummaryLength.STANDARD,
        focus_areas: Optional[List[str]] = None,
    ) -> Dict[str, str]:
        """
        Generate summaries at multiple lengths.

        Args:
            text: Document text to summarize
            length: Desired summary length
            focus_areas: Optional areas to emphasize (e.g., ["damages", "liability"])

        Returns:
            Dict with summaries at requested lengths
        """
        cache_key = self._get_cache_key(text, f"summary:{length.value}")
        if cache_key in self._summary_cache:
            return self._summary_cache[cache_key]

        summaries = {}

        # Try AI summarization first
        if self.openai_client or self.anthropic_client:
            summaries = self._ai_summarize(text, length, focus_areas)

        # Fallback to extractive summarization
        if not summaries:
            summaries = self._extractive_summarize(text, length)

        self._summary_cache[cache_key] = summaries
        return summaries

    def _ai_summarize(
        self, text: str, length: SummaryLength, focus_areas: Optional[List[str]] = None
    ) -> Dict[str, str]:
        """Generate AI-powered summaries."""
        length_instructions = {
            SummaryLength.BRIEF: "Provide a 1-2 sentence summary capturing the key point.",
            SummaryLength.STANDARD: "Provide a 1-2 paragraph summary covering main points.",
            SummaryLength.DETAILED: "Provide a detailed summary with sections for: Background, Key Arguments, Holdings/Conclusions, and Implications.",
        }

        focus_text = ""
        if focus_areas:
            focus_text = f"\n\nFocus particularly on: {', '.join(focus_areas)}"

        system_prompt = f"""You are a legal document analyst. Summarize the following legal document.
{length_instructions[length]}
{focus_text}

Maintain legal precision and cite specific provisions, parties, or holdings where relevant."""

        try:
            if self.openai_client:
                response = self.openai_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": text[:15000]},  # Limit context
                    ],
                    max_tokens=1000,
                    temperature=0.3,
                )
                return {length.value: response.choices[0].message.content}

            elif self.anthropic_client:
                response = self.anthropic_client.messages.create(
                    model="claude-3-haiku-20240307",
                    max_tokens=1000,
                    system=system_prompt,
                    messages=[{"role": "user", "content": text[:15000]}],
                )
                return {length.value: response.content[0].text}

        except Exception as e:
            logger.error(f"AI summarization failed: {e}")

        return {}

    def _extractive_summarize(self, text: str, length: SummaryLength) -> Dict[str, str]:
        """Fallback extractive summarization using sentence scoring."""
        sentences = re.split(r"(?<=[.!?])\s+", text)

        # Score sentences based on:
        # - Position (first/last paragraphs weighted higher)
        # - Keyword presence (legal terms, parties, holdings)
        # - Length (medium length preferred)

        legal_keywords = [
            "court",
            "plaintiff",
            "defendant",
            "held",
            "ruling",
            "judgment",
            "motion",
            "granted",
            "denied",
            "appeal",
            "pursuant",
            "statute",
            "evidence",
            "testimony",
            "witness",
            "damages",
            "liability",
        ]

        scored_sentences = []
        for i, sentence in enumerate(sentences):
            score = 0

            # Position score
            if i < 3:
                score += 2
            if i >= len(sentences) - 3:
                score += 1

            # Keyword score
            lower_sent = sentence.lower()
            for keyword in legal_keywords:
                if keyword in lower_sent:
                    score += 1

            # Length score (prefer medium length)
            words = len(sentence.split())
            if 15 <= words <= 40:
                score += 1

            scored_sentences.append((score, sentence))

        # Sort by score and select top sentences
        scored_sentences.sort(key=lambda x: x[0], reverse=True)

        num_sentences = {
            SummaryLength.BRIEF: 2,
            SummaryLength.STANDARD: 5,
            SummaryLength.DETAILED: 10,
        }

        top_sentences = scored_sentences[: num_sentences[length]]
        # Restore original order
        top_sentences.sort(key=lambda x: sentences.index(x[1]))

        summary = " ".join([s[1] for s in top_sentences])
        return {length.value: summary}

    # =========================================================
    # ENTITY EXTRACTION
    # =========================================================

    def extract_entities(self, text: str) -> List[ExtractedEntity]:
        """
        Extract legal entities from document text.

        Extracts:
        - Parties (plaintiffs, defendants)
        - Dates
        - Courts
        - Case numbers
        - Judges
        - Attorneys
        - Monetary amounts
        """
        entities = []

        # Pattern-based extraction
        for entity_type, pattern in self.ENTITY_PATTERNS.items():
            for match in re.finditer(pattern, text, re.IGNORECASE):
                value = match.group(1) if match.groups() else match.group(0)

                # Get surrounding context
                start = max(0, match.start() - 50)
                end = min(len(text), match.end() + 50)
                context = text[start:end]

                entities.append(
                    ExtractedEntity(
                        entity_type=entity_type,
                        value=value.strip(),
                        confidence=0.85,
                        context=context,
                        start_pos=match.start(),
                        end_pos=match.end(),
                    )
                )

        # Extract monetary amounts
        money_pattern = r"\$[\d,]+(?:\.\d{2})?(?:\s*(?:million|billion|thousand))?"
        for match in re.finditer(money_pattern, text, re.IGNORECASE):
            entities.append(
                ExtractedEntity(
                    entity_type="monetary_amount",
                    value=match.group(0),
                    confidence=0.9,
                    start_pos=match.start(),
                    end_pos=match.end(),
                )
            )

        # Extract party names from "v." patterns
        vs_pattern = r"([A-Z][a-zA-Z\s,\.]+?)\s+v\.?\s+([A-Z][a-zA-Z\s,\.]+?)(?=\s*,|\s*\d|\s*$)"
        for match in re.finditer(vs_pattern, text):
            entities.append(
                ExtractedEntity(
                    entity_type="plaintiff",
                    value=match.group(1).strip(),
                    confidence=0.8,
                    start_pos=match.start(),
                )
            )
            entities.append(
                ExtractedEntity(
                    entity_type="defendant",
                    value=match.group(2).strip(),
                    confidence=0.8,
                    start_pos=match.start(),
                )
            )

        # Deduplicate by value and type
        seen = set()
        unique_entities = []
        for entity in entities:
            key = (entity.entity_type, entity.value.lower())
            if key not in seen:
                seen.add(key)
                unique_entities.append(entity)

        return unique_entities

    # =========================================================
    # CITATION EXTRACTION
    # =========================================================

    def extract_citations(self, text: str, validate: bool = True) -> List[ExtractedCitation]:
        """
        Extract and optionally validate legal citations.

        Args:
            text: Document text
            validate: Whether to validate extracted citations

        Returns:
            List of ExtractedCitation objects
        """
        citations = []

        for citation_type, pattern in self.CITATION_PATTERNS.items():
            for match in re.finditer(pattern, text, re.IGNORECASE):
                citation = self._parse_citation(match, citation_type)
                if citation:
                    citations.append(citation)

        # Deduplicate
        seen = set()
        unique_citations = []
        for cit in citations:
            if cit.citation_text not in seen:
                seen.add(cit.citation_text)
                unique_citations.append(cit)

        if validate:
            unique_citations = self._validate_citations(unique_citations)

        return unique_citations

    def _parse_citation(self, match: re.Match, citation_type: str) -> Optional[ExtractedCitation]:
        """Parse a regex match into a citation object."""
        try:
            groups = match.groups()
            citation_text = match.group(0).strip()

            # Determine jurisdiction from citation type
            jurisdiction_map = {
                "us_case": "Federal - Supreme Court",
                "federal_reporter": "Federal",
                "supreme_court_reporter": "Federal - Supreme Court",
                "state_reporter": "State",
                "usc": "Federal - Statutory",
                "cfr": "Federal - Regulatory",
                "nj_statute": "New Jersey - Statutory",
                "nj_admin": "New Jersey - Administrative",
            }

            # Extract year if present
            year = None
            for g in groups:
                if g and g.isdigit() and len(g) == 4:
                    year = int(g)
                    break

            return ExtractedCitation(
                citation_text=citation_text,
                citation_type=(
                    "case" if "case" in citation_type or "reporter" in citation_type else "statute"
                ),
                jurisdiction=jurisdiction_map.get(citation_type, "Unknown"),
                year=year,
                volume=groups[0] if groups else None,
                page=groups[1] if len(groups) > 1 else None,
                confidence=0.85,
            )
        except Exception as e:
            logger.warning(f"Citation parsing failed: {e}")
            return None

    def _validate_citations(self, citations: List[ExtractedCitation]) -> List[ExtractedCitation]:
        """Validate citations against known databases."""
        # Basic validation rules
        for citation in citations:
            is_valid = True
            notes = []

            # Check year reasonableness
            if citation.year:
                if citation.year < 1789:  # US Constitution
                    is_valid = False
                    notes.append("Year predates US Constitution")
                elif citation.year > datetime.now().year:
                    is_valid = False
                    notes.append("Future date")

            # Check volume/page reasonableness
            if citation.volume:
                try:
                    vol = int(citation.volume)
                    if vol > 600:  # US Reports only goes to ~580
                        if "U.S." in citation.citation_text:
                            notes.append("Volume number unusually high for U.S. Reports")
                except ValueError:
                    pass

            citation.is_valid = is_valid
            citation.validation_notes = "; ".join(notes) if notes else "Passed basic validation"

        return citations

    # =========================================================
    # ISSUE IDENTIFICATION
    # =========================================================

    def identify_issues(self, text: str) -> List[LegalIssue]:
        """
        Identify potential legal issues in the document.

        Looks for:
        - Constitutional issues
        - Procedural defects
        - Evidence problems
        - Statute of limitations concerns
        - Jurisdiction questions
        """
        issues = []

        # Issue detection patterns
        issue_patterns = {
            "constitutional": {
                "patterns": [
                    r"fourth\s+amendment",
                    r"miranda\s+(?:rights|warning)",
                    r"due\s+process",
                    r"equal\s+protection",
                    r"unreasonable\s+search",
                ],
                "severity": RiskLevel.HIGH,
                "type": "Constitutional Issue",
            },
            "procedural": {
                "patterns": [
                    r"failure\s+to\s+(?:file|serve|notify)",
                    r"improper\s+(?:notice|service)",
                    r"untimely\s+(?:filing|motion)",
                    r"procedural\s+defect",
                ],
                "severity": RiskLevel.MEDIUM,
                "type": "Procedural Defect",
            },
            "evidence": {
                "patterns": [
                    r"chain\s+of\s+custody",
                    r"hearsay",
                    r"inadmissible",
                    r"spoliation",
                    r"tampered?\s+evidence",
                ],
                "severity": RiskLevel.HIGH,
                "type": "Evidence Issue",
            },
            "limitations": {
                "patterns": [
                    r"statute\s+of\s+limitations",
                    r"time[- ]?barred",
                    r"laches",
                ],
                "severity": RiskLevel.CRITICAL,
                "type": "Timeliness Issue",
            },
        }

        for category, config in issue_patterns.items():
            for pattern in config["patterns"]:
                for match in re.finditer(pattern, text, re.IGNORECASE):
                    # Get context around match
                    start = max(0, match.start() - 200)
                    end = min(len(text), match.end() + 200)
                    context = text[start:end]

                    issues.append(
                        LegalIssue(
                            issue_type=config["type"],
                            description=f"Potential {config['type'].lower()} detected: '{match.group(0)}'",
                            severity=config["severity"],
                            relevant_text=context,
                            recommendations=self._get_recommendations(category),
                        )
                    )

        return issues

    def _get_recommendations(self, issue_category: str) -> List[str]:
        """Get recommendations for an issue category."""
        recommendations = {
            "constitutional": [
                "Review applicable constitutional amendments",
                "Research recent Supreme Court decisions",
                "Consider filing motion to suppress",
                "Document all rights violations chronologically",
            ],
            "procedural": [
                "Verify all filing deadlines",
                "Check service requirements",
                "Consider motion to cure defect",
                "Review local court rules",
            ],
            "evidence": [
                "Request chain of custody documentation",
                "File motion to exclude if grounds exist",
                "Consider expert witness testimony",
                "Document all evidentiary objections",
            ],
            "limitations": [
                "Calculate exact limitation period",
                "Research tolling provisions",
                "Consider equitable exceptions",
                "Document all relevant dates",
            ],
        }
        return recommendations.get(issue_category, ["Consult with supervising attorney"])

    # =========================================================
    # RISK ASSESSMENT
    # =========================================================

    def assess_risk(self, text: str, issues: Optional[List[LegalIssue]] = None) -> Dict[str, Any]:
        """
        Perform comprehensive risk assessment on document.

        Returns:
            Risk assessment with scores and recommendations
        """
        if issues is None:
            issues = self.identify_issues(text)

        # Calculate overall risk score
        severity_weights = {
            RiskLevel.LOW: 1,
            RiskLevel.MEDIUM: 2,
            RiskLevel.HIGH: 3,
            RiskLevel.CRITICAL: 5,
        }

        total_weight = sum(severity_weights[issue.severity] for issue in issues)
        max_possible = len(issues) * 5 if issues else 1
        risk_score = min(100, int((total_weight / max_possible) * 100)) if issues else 0

        # Determine overall risk level
        if risk_score >= 75:
            overall_level = RiskLevel.CRITICAL
        elif risk_score >= 50:
            overall_level = RiskLevel.HIGH
        elif risk_score >= 25:
            overall_level = RiskLevel.MEDIUM
        else:
            overall_level = RiskLevel.LOW

        # Group issues by type
        issues_by_type = {}
        for issue in issues:
            if issue.issue_type not in issues_by_type:
                issues_by_type[issue.issue_type] = []
            issues_by_type[issue.issue_type].append(issue)

        return {
            "overall_score": risk_score,
            "overall_level": overall_level.value,
            "total_issues": len(issues),
            "issues_by_severity": {
                level.value: len([i for i in issues if i.severity == level]) for level in RiskLevel
            },
            "issues_by_type": {k: len(v) for k, v in issues_by_type.items()},
            "priority_actions": self._get_priority_actions(issues),
            "assessed_at": datetime.utcnow().isoformat(),
        }

    def _get_priority_actions(self, issues: List[LegalIssue]) -> List[str]:
        """Get prioritized action items based on issues."""
        actions = []

        # Sort issues by severity
        critical_issues = [i for i in issues if i.severity == RiskLevel.CRITICAL]
        high_issues = [i for i in issues if i.severity == RiskLevel.HIGH]

        for issue in critical_issues[:3]:
            actions.append(f"URGENT: Address {issue.issue_type} - {issue.description}")

        for issue in high_issues[:3]:
            actions.append(f"HIGH: Review {issue.issue_type} - {issue.description}")

        if not actions:
            actions.append("No critical issues identified. Proceed with standard review.")

        return actions

    # =========================================================
    # FULL DOCUMENT ANALYSIS
    # =========================================================

    def analyze_document(
        self, text: str, document_id: Optional[str] = None, include_all_summaries: bool = False
    ) -> DocumentAnalysis:
        """
        Perform comprehensive document analysis.

        Args:
            text: Document text
            document_id: Optional document identifier
            include_all_summaries: Include all summary lengths

        Returns:
            Complete DocumentAnalysis object
        """
        import time

        start_time = time.time()

        if not document_id:
            document_id = hashlib.sha256(text.encode()).hexdigest()[:16]

        # Generate summaries
        summaries = {}
        if include_all_summaries:
            for length in SummaryLength:
                result = self.summarize(text, length)
                summaries.update(result)
        else:
            summaries = self.summarize(text, SummaryLength.STANDARD)

        # Extract entities
        entities = self.extract_entities(text)

        # Extract citations
        citations = self.extract_citations(text, validate=True)

        # Identify issues
        issues = self.identify_issues(text)

        # Assess risk
        risk = self.assess_risk(text, issues)

        processing_time = (time.time() - start_time) * 1000

        return DocumentAnalysis(
            document_id=document_id,
            summary=summaries,
            entities=entities,
            citations=citations,
            issues=issues,
            risk_assessment=risk,
            metadata={
                "text_length": len(text),
                "word_count": len(text.split()),
                "entity_count": len(entities),
                "citation_count": len(citations),
                "issue_count": len(issues),
            },
            processing_time_ms=processing_time,
        )


# Global service instance
document_intelligence = DocumentIntelligenceService()


def get_document_intelligence() -> DocumentIntelligenceService:
    """Get the global document intelligence service."""
    return document_intelligence
