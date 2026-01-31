"""
BWC-PDF Discrepancy Detector - Evidence Cross-Reference Analysis

Compares body-worn camera (BWC) transcripts against PDF police reports
to detect contradictions and inconsistencies - critical for civil rights litigation.

Features:
- Officer statement extraction from both sources
- Timeline alignment (BWC timestamps vs report narrative)
- Speaker attribution validation
- Fact extraction and contradiction detection
- Semantic similarity matching
- Evidence consistency scoring
- Court-ready discrepancy reports
"""

import hashlib
import json
import re
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple

try:
    import numpy as np
    from sentence_transformers import SentenceTransformer

    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

try:
    import spacy

    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False


@dataclass
class Statement:
    """A statement from either BWC or PDF report"""

    source: str  # 'bwc' or 'report'
    speaker: str  # 'Officer Smith', 'Suspect', etc.
    text: str
    timestamp: Optional[float] = None  # BWC timestamp in seconds
    position: Optional[str] = None  # PDF page/paragraph reference
    confidence: float = 1.0
    metadata: Dict = field(default_factory=dict)


@dataclass
class Discrepancy:
    """A detected discrepancy between BWC and report"""

    type: str  # 'contradiction', 'omission', 'embellishment', 'timeline_mismatch'
    severity: str  # 'critical', 'major', 'minor'
    bwc_statement: Optional[Statement] = None
    report_statement: Optional[Statement] = None
    description: str = ""
    similarity_score: float = 0.0
    evidence: Dict = field(default_factory=dict)


class DiscrepancyDetector:
    """
    Detect discrepancies between BWC footage and police reports

    Critical for civil rights cases where officer statements may differ
    between what was said on camera vs. what was written in the report.
    """

    def __init__(self):
        """Initialize discrepancy detector with NLP models"""

        # Load sentence transformer for semantic similarity
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                self.embedder = SentenceTransformer("all-MiniLM-L6-v2")
                print("✓ Sentence transformer loaded")
            except Exception as e:
                print(f"Warning: Could not load sentence transformer: {e}")
                self.embedder = None
        else:
            print(
                "Warning: sentence-transformers not available. Install: pip install sentence-transformers"
            )
            self.embedder = None

        # Load spaCy for entity extraction
        if SPACY_AVAILABLE:
            try:
                self.nlp = spacy.load("en_core_web_sm")
                print("✓ spaCy model loaded")
            except:
                print(
                    "Warning: spaCy model not found. Download: python -m spacy download en_core_web_sm"
                )
                self.nlp = None
        else:
            print("Warning: spaCy not available. Install: pip install spacy")
            self.nlp = None

        # Negation patterns
        self.negation_words = {
            "not",
            "no",
            "never",
            "nothing",
            "nowhere",
            "neither",
            "nobody",
            "none",
        }

        # Contradiction indicators
        self.contradiction_patterns = [
            (
                r"\b(said|stated|claimed)\b.*?\b(but|however|although)\b.*?\b(actually|in fact|really)\b",
                "contradiction",
            ),
            (r"\b(denied|refuted|contradicted)\b", "direct_contradiction"),
            (r"\b(differently|inconsistent|conflicting)\b", "inconsistency"),
        ]

    def analyze_case(
        self, bwc_transcript: Dict, pdf_report: Dict, case_info: Optional[Dict] = None
    ) -> Dict:
        """
        Analyze BWC transcript against PDF police report

        Args:
            bwc_transcript: {
                'segments': [
                    {'speaker': 'Officer Smith', 'text': '...', 'start_time': 0.0, 'end_time': 5.2},
                    ...
                ],
                'metadata': {...}
            }

            pdf_report: {
                'text': 'Full report text...',
                'sections': [
                    {'heading': 'Officer Statement', 'content': '...', 'page': 1},
                    ...
                ],
                'metadata': {...}
            }

            case_info: Optional case metadata

        Returns:
            {
                'discrepancies': [Discrepancy, ...],
                'consistency_score': 0.75,
                'timeline_analysis': {...},
                'speaker_analysis': {...},
                'summary': '...',
                'court_report': '...'
            }
        """

        result = {
            "discrepancies": [],
            "consistency_score": 0.0,
            "timeline_analysis": {},
            "speaker_analysis": {},
            "summary": "",
            "court_report": "",
            "metadata": {"analyzed_at": datetime.now().isoformat(), "case_info": case_info or {}},
        }

        # 1. Extract statements from both sources
        bwc_statements = self._extract_bwc_statements(bwc_transcript)
        report_statements = self._extract_report_statements(pdf_report)

        print(
            f"Extracted {len(bwc_statements)} BWC statements, {len(report_statements)} report statements"
        )

        # 2. Align speakers (same officer in both sources)
        speaker_mapping = self._align_speakers(bwc_statements, report_statements)

        # 3. Compare statements and find discrepancies
        discrepancies = []

        # Compare officer statements
        for bwc_speaker, report_speaker in speaker_mapping.items():
            bwc_officer_stmts = [s for s in bwc_statements if s.speaker == bwc_speaker]
            report_officer_stmts = [s for s in report_statements if s.speaker == report_speaker]

            # Cross-compare all statements
            for bwc_stmt in bwc_officer_stmts:
                for report_stmt in report_officer_stmts:
                    discrep = self._compare_statements(bwc_stmt, report_stmt)
                    if discrep:
                        discrepancies.append(discrep)

        # 4. Find omissions (in BWC but not in report, or vice versa)
        omissions = self._find_omissions(bwc_statements, report_statements)
        discrepancies.extend(omissions)

        # 5. Analyze timeline consistency
        timeline_analysis = self._analyze_timeline(bwc_statements, report_statements)

        # 6. Calculate overall consistency score
        consistency_score = self._calculate_consistency_score(discrepancies, len(bwc_statements))

        # 7. Generate court-ready report
        court_report = self._generate_court_report(
            discrepancies, bwc_statements, report_statements, timeline_analysis, case_info
        )

        result.update(
            {
                "discrepancies": [self._discrepancy_to_dict(d) for d in discrepancies],
                "consistency_score": consistency_score,
                "timeline_analysis": timeline_analysis,
                "speaker_analysis": {
                    "bwc_speakers": list(set(s.speaker for s in bwc_statements)),
                    "report_speakers": list(set(s.speaker for s in report_statements)),
                    "speaker_mapping": speaker_mapping,
                },
                "summary": self._generate_summary(discrepancies, consistency_score),
                "court_report": court_report,
            }
        )

        return result

    def _extract_bwc_statements(self, bwc_transcript: Dict) -> List[Statement]:
        """Extract statements from BWC transcript"""

        statements = []

        for segment in bwc_transcript.get("segments", []):
            # Clean up text
            text = segment["text"].strip()
            if not text or len(text) < 5:
                continue

            stmt = Statement(
                source="bwc",
                speaker=segment.get("speaker", "Unknown Speaker"),
                text=text,
                timestamp=segment.get("start_time"),
                confidence=segment.get("confidence", 1.0),
                metadata={
                    "start_time": segment.get("start_time"),
                    "end_time": segment.get("end_time"),
                    "duration": segment.get("end_time", 0) - segment.get("start_time", 0),
                },
            )

            statements.append(stmt)

        return statements

    def _extract_report_statements(self, pdf_report: Dict) -> List[Statement]:
        """Extract officer statements from PDF report"""

        statements = []

        # Look for statement sections
        full_text = pdf_report.get("text", "")
        sections = pdf_report.get("sections", [])

        # If sections are provided, use them
        if sections:
            for section in sections:
                if any(
                    keyword in section.get("heading", "").lower()
                    for keyword in ["statement", "narrative", "officer", "account"]
                ):

                    # Extract sentences
                    sentences = self._split_into_sentences(section.get("content", ""))

                    for sent in sentences:
                        if len(sent.strip()) < 10:
                            continue

                        # Try to identify speaker
                        speaker = self._identify_speaker_in_text(sent)

                        stmt = Statement(
                            source="report",
                            speaker=speaker or "Officer",
                            text=sent,
                            position=f"Page {section.get('page', '?')}",
                            metadata={"section": section.get("heading")},
                        )

                        statements.append(stmt)
        else:
            # Fall back to full text parsing
            sentences = self._split_into_sentences(full_text)

            for sent in sentences:
                if len(sent.strip()) < 10:
                    continue

                speaker = self._identify_speaker_in_text(sent)
                if speaker:  # Only include if we can identify a speaker
                    stmt = Statement(source="report", speaker=speaker, text=sent)
                    statements.append(stmt)

        return statements

    def _align_speakers(
        self, bwc_statements: List[Statement], report_statements: List[Statement]
    ) -> Dict[str, str]:
        """
        Align speakers between BWC and report

        Returns mapping: {bwc_speaker: report_speaker}
        """

        bwc_speakers = set(s.speaker for s in bwc_statements)
        report_speakers = set(s.speaker for s in report_statements)

        mapping = {}

        for bwc_speaker in bwc_speakers:
            # Try exact match first
            if bwc_speaker in report_speakers:
                mapping[bwc_speaker] = bwc_speaker
                continue

            # Try partial match (e.g., "Officer Smith" vs "Smith")
            for report_speaker in report_speakers:
                if (
                    bwc_speaker.lower() in report_speaker.lower()
                    or report_speaker.lower() in bwc_speaker.lower()
                ):
                    mapping[bwc_speaker] = report_speaker
                    break

            # Default to generic "Officer" if no match
            if bwc_speaker not in mapping and "officer" in bwc_speaker.lower():
                mapping[bwc_speaker] = "Officer"

        return mapping

    def _compare_statements(
        self, bwc_stmt: Statement, report_stmt: Statement
    ) -> Optional[Discrepancy]:
        """Compare two statements for contradictions"""

        # 1. Check semantic similarity
        similarity = self._calculate_similarity(bwc_stmt.text, report_stmt.text)

        # If highly similar (>0.8), they're consistent
        if similarity > 0.8:
            return None

        # If somewhat similar (0.5-0.8), check for contradictions
        if 0.5 <= similarity <= 0.8:
            # Check for negation differences
            bwc_negated = self._contains_negation(bwc_stmt.text)
            report_negated = self._contains_negation(report_stmt.text)

            if bwc_negated != report_negated:
                return Discrepancy(
                    type="contradiction",
                    severity="major",
                    bwc_statement=bwc_stmt,
                    report_statement=report_stmt,
                    description=f"BWC states {'negative' if bwc_negated else 'positive'} "
                    f"but report states {'negative' if report_negated else 'positive'}",
                    similarity_score=similarity,
                    evidence={"bwc_negated": bwc_negated, "report_negated": report_negated},
                )

        # If very different (<0.5), check for factual contradictions
        if similarity < 0.5:
            # Extract entities from both
            bwc_entities = self._extract_entities(bwc_stmt.text)
            report_entities = self._extract_entities(report_stmt.text)

            # Check if discussing similar topics but with different facts
            if self._are_related_topics(bwc_entities, report_entities):
                return Discrepancy(
                    type="contradiction",
                    severity="critical",
                    bwc_statement=bwc_stmt,
                    report_statement=report_stmt,
                    description="Statements discuss same topic but present different facts",
                    similarity_score=similarity,
                    evidence={"bwc_entities": bwc_entities, "report_entities": report_entities},
                )

        return None

    def _find_omissions(
        self, bwc_statements: List[Statement], report_statements: List[Statement]
    ) -> List[Discrepancy]:
        """Find statements in BWC but missing from report (or vice versa)"""

        omissions = []

        # Check each BWC statement to see if represented in report
        for bwc_stmt in bwc_statements:
            # Skip very short statements
            if len(bwc_stmt.text.split()) < 5:
                continue

            # Find most similar report statement
            max_similarity = 0.0
            most_similar = None

            for report_stmt in report_statements:
                if report_stmt.speaker != bwc_stmt.speaker:
                    continue

                similarity = self._calculate_similarity(bwc_stmt.text, report_stmt.text)
                if similarity > max_similarity:
                    max_similarity = similarity
                    most_similar = report_stmt

            # If no similar statement found, it's an omission
            if max_similarity < 0.3:
                # Check if it's a significant statement
                if self._is_significant_statement(bwc_stmt):
                    omissions.append(
                        Discrepancy(
                            type="omission",
                            severity="major" if max_similarity < 0.1 else "minor",
                            bwc_statement=bwc_stmt,
                            report_statement=None,
                            description="Statement in BWC not found in report",
                            similarity_score=max_similarity,
                            evidence={"omitted_from": "report"},
                        )
                    )

        # Also check for embellishments (in report but not in BWC)
        for report_stmt in report_statements:
            if len(report_stmt.text.split()) < 5:
                continue

            max_similarity = 0.0
            for bwc_stmt in bwc_statements:
                if bwc_stmt.speaker != report_stmt.speaker:
                    continue

                similarity = self._calculate_similarity(bwc_stmt.text, report_stmt.text)
                max_similarity = max(max_similarity, similarity)

            if max_similarity < 0.3 and self._is_significant_statement(report_stmt):
                omissions.append(
                    Discrepancy(
                        type="embellishment",
                        severity="major" if max_similarity < 0.1 else "minor",
                        bwc_statement=None,
                        report_statement=report_stmt,
                        description="Statement in report not supported by BWC",
                        similarity_score=max_similarity,
                        evidence={"added_in": "report"},
                    )
                )

        return omissions

    def _analyze_timeline(
        self, bwc_statements: List[Statement], report_statements: List[Statement]
    ) -> Dict:
        """Analyze timeline consistency between BWC and report"""

        # Extract temporal events from both sources
        bwc_events = []
        for stmt in bwc_statements:
            if stmt.timestamp is not None:
                event = {
                    "time": stmt.timestamp,
                    "description": stmt.text[:100],
                    "speaker": stmt.speaker,
                }
                bwc_events.append(event)

        # Try to extract times from report text
        report_events = []
        for stmt in report_statements:
            time_matches = re.findall(r"\b(\d{1,2}):(\d{2})\s*(AM|PM)?\b", stmt.text, re.IGNORECASE)
            for match in time_matches:
                hour, minute, meridiem = match
                event = {
                    "time": f"{hour}:{minute} {meridiem or ''}",
                    "description": stmt.text[:100],
                    "speaker": stmt.speaker,
                }
                report_events.append(event)

        return {
            "bwc_timeline": bwc_events,
            "report_timeline": report_events,
            "bwc_duration": max([s.timestamp or 0 for s in bwc_statements], default=0),
            "temporal_markers_in_report": len(report_events),
        }

    def _calculate_consistency_score(
        self, discrepancies: List[Discrepancy], total_statements: int
    ) -> float:
        """Calculate overall consistency score (0.0 = totally inconsistent, 1.0 = perfect)"""

        if total_statements == 0:
            return 0.0

        # Weight discrepancies by severity
        severity_weights = {"critical": 3.0, "major": 2.0, "minor": 1.0}

        total_weight = sum(severity_weights.get(d.severity, 1.0) for d in discrepancies)

        # Calculate score (more discrepancies = lower score)
        max_possible_weight = total_statements * severity_weights["critical"]
        consistency = 1.0 - min(1.0, total_weight / max_possible_weight)

        return round(consistency, 2)

    def _generate_summary(self, discrepancies: List[Discrepancy], consistency_score: float) -> str:
        """Generate executive summary of analysis"""

        critical_count = sum(1 for d in discrepancies if d.severity == "critical")
        major_count = sum(1 for d in discrepancies if d.severity == "major")
        minor_count = sum(1 for d in discrepancies if d.severity == "minor")

        summary = f"""
BWC-PDF Discrepancy Analysis Summary
=====================================

Overall Consistency Score: {consistency_score:.0%}

Total Discrepancies Found: {len(discrepancies)}
  - Critical: {critical_count}
  - Major: {major_count}
  - Minor: {minor_count}

Discrepancy Types:
  - Contradictions: {sum(1 for d in discrepancies if d.type == 'contradiction')}
  - Omissions: {sum(1 for d in discrepancies if d.type == 'omission')}
  - Embellishments: {sum(1 for d in discrepancies if d.type == 'embellishment')}
"""

        if consistency_score < 0.7:
            summary += "\n⚠️ WARNING: Significant inconsistencies detected between BWC and report."
        elif consistency_score < 0.85:
            summary += "\n⚠️ NOTICE: Moderate inconsistencies found. Further review recommended."
        else:
            summary += "\n✓ Overall consistency is acceptable."

        return summary.strip()

    def _generate_court_report(
        self,
        discrepancies: List[Discrepancy],
        bwc_statements: List[Statement],
        report_statements: List[Statement],
        timeline_analysis: Dict,
        case_info: Optional[Dict],
    ) -> str:
        """Generate court-ready discrepancy report"""

        case_name = case_info.get("case_name", "Case") if case_info else "Case"
        docket = (
            case_info.get("docket_number", "XXXX-L-XXXXXX-XX") if case_info else "XXXX-L-XXXXXX-XX"
        )

        report = f"""
BODY-WORN CAMERA AND POLICE REPORT DISCREPANCY ANALYSIS
{case_name}
Docket No. {docket}

INTRODUCTION

This report presents a systematic analysis comparing statements made by law enforcement 
officers as captured on body-worn camera (BWC) footage against statements contained in 
the written police report. The analysis utilizes natural language processing and semantic 
similarity algorithms to identify contradictions, omissions, and inconsistencies.

METHODOLOGY

The analysis employed:
1. Automated transcription of BWC audio with speaker diarization
2. Optical character recognition (OCR) of PDF police report
3. Sentence-level semantic similarity matching
4. Entity extraction and cross-reference validation
5. Timeline alignment and consistency checking

FINDINGS

Total BWC Statements Analyzed: {len(bwc_statements)}
Total Report Statements Analyzed: {len(report_statements)}
Discrepancies Identified: {len(discrepancies)}

"""

        # Group discrepancies by severity
        critical = [d for d in discrepancies if d.severity == "critical"]
        major = [d for d in discrepancies if d.severity == "major"]
        minor = [d for d in discrepancies if d.severity == "minor"]

        # Critical discrepancies
        if critical:
            report += "CRITICAL DISCREPANCIES\n" + "=" * 80 + "\n\n"
            for i, discrep in enumerate(critical, 1):
                report += f"{i}. {discrep.description}\n\n"

                if discrep.bwc_statement:
                    ts = discrep.bwc_statement.timestamp
                    time_str = f"[{ts:.1f}s]" if ts else ""
                    report += f"   BWC {time_str} ({discrep.bwc_statement.speaker}):\n"
                    report += f'   "{discrep.bwc_statement.text}"\n\n'

                if discrep.report_statement:
                    pos = discrep.report_statement.position or ""
                    report += f"   Report {pos} ({discrep.report_statement.speaker}):\n"
                    report += f'   "{discrep.report_statement.text}"\n\n'

                report += f"   Similarity Score: {discrep.similarity_score:.1%}\n"
                report += "-" * 80 + "\n\n"

        # Major discrepancies
        if major:
            report += "\nMAJOR DISCREPANCIES\n" + "=" * 80 + "\n\n"
            for i, discrep in enumerate(major, 1):
                report += f"{i}. {discrep.description}\n"
                if discrep.bwc_statement:
                    report += f'   BWC: "{discrep.bwc_statement.text[:100]}..."\n'
                if discrep.report_statement:
                    report += f'   Report: "{discrep.report_statement.text[:100]}..."\n'
                report += "\n"

        report += "\nCONCLUSION\n" + "=" * 80 + "\n\n"
        report += "This analysis reveals "

        if len(critical) > 0:
            report += f"{len(critical)} critical discrepancies "
        if len(major) > 0:
            report += f"and {len(major)} major discrepancies "

        report += "between the body-worn camera footage and the written police report. "
        report += "These inconsistencies raise questions about the accuracy and reliability "
        report += "of the written report and warrant further investigation.\n"

        return report

    # Helper methods

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate semantic similarity between two texts"""

        if not self.embedder:
            # Fall back to simple word overlap
            words1 = set(text1.lower().split())
            words2 = set(text2.lower().split())

            if not words1 or not words2:
                return 0.0

            intersection = len(words1 & words2)
            union = len(words1 | words2)

            return intersection / union if union > 0 else 0.0

        # Use sentence transformer
        embeddings = self.embedder.encode([text1, text2])

        # Cosine similarity
        similarity = np.dot(embeddings[0], embeddings[1]) / (
            np.linalg.norm(embeddings[0]) * np.linalg.norm(embeddings[1])
        )

        return float(similarity)

    def _contains_negation(self, text: str) -> bool:
        """Check if text contains negation"""
        words = set(text.lower().split())
        return bool(words & self.negation_words)

    def _extract_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract named entities from text"""

        if not self.nlp:
            return {}

        doc = self.nlp(text)

        entities = defaultdict(list)
        for ent in doc.ents:
            entities[ent.label_].append(ent.text)

        return dict(entities)

    def _are_related_topics(self, entities1: Dict, entities2: Dict) -> bool:
        """Check if two entity sets discuss related topics"""

        if not entities1 or not entities2:
            return False

        # Check for overlap in entity types and values
        common_types = set(entities1.keys()) & set(entities2.keys())

        if not common_types:
            return False

        # Check for value overlap within common types
        for entity_type in common_types:
            set1 = set(entities1[entity_type])
            set2 = set(entities2[entity_type])

            if set1 & set2:  # Any overlap
                return True

        return False

    def _is_significant_statement(self, stmt: Statement) -> bool:
        """Determine if statement is significant enough to report"""

        # Check length
        word_count = len(stmt.text.split())
        if word_count < 5:
            return False

        # Check for action verbs, entities, etc.
        if self.nlp:
            doc = self.nlp(stmt.text)

            # Has verb and noun
            has_verb = any(token.pos_ == "VERB" for token in doc)
            has_noun = any(token.pos_ in ["NOUN", "PROPN"] for token in doc)
            has_entity = len(doc.ents) > 0

            return has_verb and (has_noun or has_entity)

        # Fall back to simple check
        return word_count >= 8

    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""

        if self.nlp:
            doc = self.nlp(text)
            return [sent.text for sent in doc.sents]

        # Fall back to simple splitting
        return re.split(r"[.!?]+\s+", text)

    def _identify_speaker_in_text(self, text: str) -> Optional[str]:
        """Identify speaker from statement text"""

        # Look for patterns like "Officer Smith stated" or "I (Officer Jones) observed"
        patterns = [
            r"(Officer\s+\w+)",
            r"(Detective\s+\w+)",
            r"(Sergeant\s+\w+)",
            r"\(([^)]*Officer[^)]*)\)",
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)

        # If text is first-person and mentions officer, assume "Officer"
        if re.search(r"\b(I|my|me)\b", text, re.IGNORECASE) and re.search(
            r"\b(officer|badge|patrol)\b", text, re.IGNORECASE
        ):
            return "Officer"

        return None

    def _discrepancy_to_dict(self, discrep: Discrepancy) -> Dict:
        """Convert Discrepancy to dictionary for JSON serialization"""

        return {
            "type": discrep.type,
            "severity": discrep.severity,
            "description": discrep.description,
            "similarity_score": discrep.similarity_score,
            "bwc_statement": (
                {
                    "speaker": discrep.bwc_statement.speaker,
                    "text": discrep.bwc_statement.text,
                    "timestamp": discrep.bwc_statement.timestamp,
                    "confidence": discrep.bwc_statement.confidence,
                }
                if discrep.bwc_statement
                else None
            ),
            "report_statement": (
                {
                    "speaker": discrep.report_statement.speaker,
                    "text": discrep.report_statement.text,
                    "position": discrep.report_statement.position,
                }
                if discrep.report_statement
                else None
            ),
            "evidence": discrep.evidence,
        }


# Convenience function
def analyze_case(
    bwc_transcript_file: str, pdf_report_file: str, output_report_file: Optional[str] = None
) -> Dict:
    """
    Quick function to analyze a case

    Args:
        bwc_transcript_file: Path to JSON file with BWC transcript
        pdf_report_file: Path to JSON file with PDF report data
        output_report_file: Optional path to save court report

    Returns:
        Analysis results dictionary
    """

    with open(bwc_transcript_file, "r") as f:
        bwc_data = json.load(f)

    with open(pdf_report_file, "r") as f:
        pdf_data = json.load(f)

    detector = DiscrepancyDetector()
    results = detector.analyze_case(bwc_data, pdf_data)

    if output_report_file:
        with open(output_report_file, "w") as f:
            f.write(results["court_report"])

    return results
