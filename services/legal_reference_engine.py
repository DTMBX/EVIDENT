"""
Legal Reference Engine - Advanced Legal Research & Analysis

Comprehensive legal reference system combining:
- Multi-source legal database aggregation
- AI-powered case analysis and citation mapping
- Automated legal research workflows
- E-discovery document analysis
- Precedent identification and ranking
- Legal argument construction

Designed for professional-grade legal research and chatbot integration.
"""

import json
import os
import re
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import numpy as np
import requests
from bs4 import BeautifulSoup
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from legal_library import Citation, LegalDocument
from models_auth import db
from verified_legal_sources import VerifiedLegalSources


class LegalReferenceEngine:
    """
    Advanced legal reference engine for chatbot and e-discovery

    Features:
    - Multi-jurisdictional case law search
    - Precedent strength analysis
    - Citation network mapping
    - Legal issue extraction
    - Argument construction support
    - Document relevance ranking
    """

    def __init__(self):
        self.verified_sources = VerifiedLegalSources()
        self.vectorizer = TfidfVectorizer(
            max_features=1000, stop_words="english", ngram_range=(1, 3)
        )
        self._precedent_cache = {}

    # ==================== CORE SEARCH ====================

    def comprehensive_search(
        self,
        query: str,
        jurisdiction: Optional[str] = None,
        practice_area: Optional[str] = None,
        date_range: Optional[Tuple[datetime, datetime]] = None,
        include_federal: bool = True,
        min_relevance: float = 0.3,
        limit: int = 50,
    ) -> List[Dict]:
        """
        Comprehensive legal search across all verified sources

        Args:
            query: Natural language query or legal issue
            jurisdiction: Specific state/federal jurisdiction
            practice_area: Area of law (constitutional, criminal, civil, etc.)
            date_range: (start_date, end_date) tuple
            include_federal: Include federal cases
            min_relevance: Minimum relevance score (0-1)
            limit: Maximum results

        Returns:
            List of ranked legal documents with relevance scores
        """

        # Step 1: Search local database
        local_results = self._search_local_library(
            query, jurisdiction, practice_area, date_range, limit * 2
        )

        # Step 2: Search external verified sources (if needed)
        if len(local_results) < limit:
            external_results = self._search_verified_sources(
                query, jurisdiction, limit - len(local_results)
            )
            all_results = local_results + external_results
        else:
            all_results = local_results

        # Step 3: Calculate relevance scores
        scored_results = self._calculate_relevance(query, all_results)

        # Step 4: Filter by minimum relevance
        filtered_results = [r for r in scored_results if r["relevance_score"] >= min_relevance]

        # Step 5: Rank by relevance + citation count + recency
        ranked_results = self._rank_results(filtered_results)

        return ranked_results[:limit]

    def _search_local_library(
        self,
        query: str,
        jurisdiction: Optional[str],
        practice_area: Optional[str],
        date_range: Optional[Tuple[datetime, datetime]],
        limit: int,
    ) -> List[Dict]:
        """Search local legal library database"""

        query_obj = LegalDocument.query.filter(LegalDocument.public == True)

        # Full-text search
        search_filter = db.or_(
            LegalDocument.title.ilike(f"%{query}%"),
            LegalDocument.full_text.ilike(f"%{query}%"),
            LegalDocument.summary.ilike(f"%{query}%"),
            LegalDocument.legal_issues.ilike(f"%{query}%"),
        )
        query_obj = query_obj.filter(search_filter)

        # Jurisdiction filter
        if jurisdiction:
            query_obj = query_obj.filter(
                db.or_(
                    LegalDocument.jurisdiction == jurisdiction,
                    LegalDocument.jurisdiction == "Federal",  # Always include federal
                )
            )

        # Practice area filter (via topics JSON)
        if practice_area:
            query_obj = query_obj.filter(LegalDocument.topics.ilike(f"%{practice_area}%"))

        # Date range filter
        if date_range:
            start_date, end_date = date_range
            query_obj = query_obj.filter(
                LegalDocument.decision_date >= start_date, LegalDocument.decision_date <= end_date
            )

        # Execute query
        results = query_obj.order_by(LegalDocument.decision_date.desc()).limit(limit).all()

        # Convert to dict format
        return [self._document_to_dict(doc) for doc in results]

    def _search_verified_sources(
        self, query: str, jurisdiction: Optional[str], limit: int
    ) -> List[Dict]:
        """Search external verified legal sources"""

        results = []

        # CourtListener search
        try:
            courtlistener_results = self.verified_sources.search_courtlistener(
                query, jurisdiction, limit
            )
            results.extend(courtlistener_results)
        except Exception as e:
            print(f"CourtListener search failed: {e}")

        # Justia search (if still need more)
        if len(results) < limit:
            try:
                justia_results = self.verified_sources.search_justia(
                    query, jurisdiction, limit - len(results)
                )
                results.extend(justia_results)
            except Exception as e:
                print(f"Justia search failed: {e}")

        return results

    def _calculate_relevance(self, query: str, documents: List[Dict]) -> List[Dict]:
        """Calculate relevance scores using TF-IDF and cosine similarity"""

        if not documents:
            return []

        # Extract text for vectorization
        doc_texts = [
            f"{doc.get('title', '')} {doc.get('summary', '')} {doc.get('full_text', '')[:500]}"
            for doc in documents
        ]

        # Add query to corpus
        all_texts = [query] + doc_texts

        # Vectorize
        try:
            tfidf_matrix = self.vectorizer.fit_transform(all_texts)

            # Calculate cosine similarity with query
            query_vector = tfidf_matrix[0:1]
            doc_vectors = tfidf_matrix[1:]

            similarities = cosine_similarity(query_vector, doc_vectors)[0]

            # Add relevance scores to documents
            for doc, score in zip(documents, similarities):
                doc["relevance_score"] = float(score)
                doc["search_query"] = query

        except Exception as e:
            print(f"Relevance calculation failed: {e}")
            # Fallback: all documents get neutral score
            for doc in documents:
                doc["relevance_score"] = 0.5

        return documents

    def _rank_results(self, documents: List[Dict]) -> List[Dict]:
        """
        Rank results by composite score:
        - Relevance (40%)
        - Citation count (30%)
        - Recency (20%)
        - Court level (10%)
        """

        # Normalize citation counts
        max_citations = max((doc.get("citation_count", 0) for doc in documents), default=1)

        # Calculate composite scores
        for doc in documents:
            relevance = doc.get("relevance_score", 0.5)
            citations = doc.get("citation_count", 0) / max_citations if max_citations > 0 else 0

            # Recency score (newer is better, decay over 10 years)
            decision_date = doc.get("decision_date")
            if decision_date:
                if isinstance(decision_date, str):
                    decision_date = datetime.fromisoformat(decision_date.replace("Z", "+00:00"))
                years_old = (datetime.now() - decision_date).days / 365.25
                recency = max(0, 1 - (years_old / 10))
            else:
                recency = 0.5

            # Court level score
            court = doc.get("court", "").lower()
            if "supreme court" in court and "u.s." in court:
                court_score = 1.0
            elif "supreme court" in court or "court of appeals" in court:
                court_score = 0.8
            elif "circuit" in court or "appellate" in court:
                court_score = 0.6
            else:
                court_score = 0.4

            # Composite score
            doc["composite_score"] = (
                relevance * 0.40 + citations * 0.30 + recency * 0.20 + court_score * 0.10
            )

        # Sort by composite score
        return sorted(documents, key=lambda x: x["composite_score"], reverse=True)

    # ==================== PRECEDENT ANALYSIS ====================

    def find_precedents(
        self,
        legal_issue: str,
        jurisdiction: str,
        favor: str = "plaintiff",
        min_strength: float = 0.7,
        limit: int = 20,
    ) -> List[Dict]:
        """
        Find precedent cases for a legal issue

        Args:
            legal_issue: Legal question or issue
            jurisdiction: Jurisdiction to search
            favor: 'plaintiff' or 'defendant'
            min_strength: Minimum precedent strength (0-1)
            limit: Maximum precedents

        Returns:
            List of precedent cases with strength scores
        """

        # Check cache
        cache_key = f"{legal_issue}:{jurisdiction}:{favor}"
        if cache_key in self._precedent_cache:
            return self._precedent_cache[cache_key]

        # Search for relevant cases
        results = self.comprehensive_search(
            query=legal_issue, jurisdiction=jurisdiction, min_relevance=0.5, limit=limit * 2
        )

        # Analyze precedent strength
        precedents = []
        for case in results:
            strength = self._calculate_precedent_strength(case, legal_issue, jurisdiction)

            if strength >= min_strength:
                case["precedent_strength"] = strength
                case["favorable_to"] = self._determine_favorable_party(case, favor)
                precedents.append(case)

        # Sort by strength
        precedents.sort(key=lambda x: x["precedent_strength"], reverse=True)
        precedents = precedents[:limit]

        # Cache results
        self._precedent_cache[cache_key] = precedents

        return precedents

    def _calculate_precedent_strength(
        self, case: Dict, legal_issue: str, jurisdiction: str
    ) -> float:
        """
        Calculate precedent strength (0-1) based on:
        - Relevance to issue
        - Court hierarchy
        - Citation count
        - Age (fresher is stronger)
        - Jurisdiction match
        """

        # Base score from relevance
        strength = case.get("relevance_score", 0.5)

        # Court hierarchy multiplier
        court = case.get("court", "").lower()
        if "supreme court" in court and "u.s." in court:
            strength *= 1.5
        elif "supreme court" in court:
            strength *= 1.3
        elif "appellate" in court or "circuit" in court:
            strength *= 1.1

        # Citation count boost (capped at 20%)
        citation_count = case.get("citation_count", 0)
        citation_boost = min(0.2, citation_count / 100)
        strength += citation_boost

        # Recency factor (cases >20 years old lose strength)
        decision_date = case.get("decision_date")
        if decision_date:
            if isinstance(decision_date, str):
                decision_date = datetime.fromisoformat(decision_date.replace("Z", "+00:00"))
            years_old = (datetime.now() - decision_date).days / 365.25
            if years_old > 20:
                strength *= 0.7
            elif years_old > 10:
                strength *= 0.85

        # Jurisdiction match bonus
        case_jurisdiction = case.get("jurisdiction", "")
        if case_jurisdiction == jurisdiction:
            strength *= 1.2
        elif case_jurisdiction == "Federal":
            strength *= 1.1  # Federal cases apply everywhere

        # Cap at 1.0
        return min(1.0, strength)

    def _determine_favorable_party(self, case: Dict, favor: str) -> str:
        """Determine which party the case favors"""
        # This would use NLP analysis of the case text
        # For now, simplified heuristic
        summary = case.get("summary", "").lower()
        title = case.get("title", "").lower()

        plaintiff_keywords = ["plaintiff", "petitioner", "appellant", "granted", "affirmed"]
        defendant_keywords = ["defendant", "respondent", "appellee", "denied", "reversed"]

        plaintiff_score = sum(1 for kw in plaintiff_keywords if kw in summary or kw in title)
        defendant_score = sum(1 for kw in defendant_keywords if kw in summary or kw in title)

        if plaintiff_score > defendant_score:
            return "plaintiff"
        elif defendant_score > plaintiff_score:
            return "defendant"
        else:
            return "neutral"

    # ==================== CITATION NETWORK ====================

    def map_citation_network(self, case_citation: str, depth: int = 2) -> Dict:
        """
        Map citation network for a case

        Args:
            case_citation: Citation of the root case
            depth: How many levels deep to map (1-3)

        Returns:
            Citation network graph
        """

        # Get root case
        root_case = LegalDocument.query.filter(LegalDocument.citation == case_citation).first()

        if not root_case:
            return {"error": "Case not found"}

        network = {
            "root": self._document_to_dict(root_case),
            "cited_by": [],
            "cites": [],
            "depth": depth,
            "total_nodes": 1,
        }

        # Level 1: Direct citations
        cited_by = self._get_citing_cases(root_case.id)
        cites = self._get_cited_cases(root_case.id)

        network["cited_by"] = cited_by
        network["cites"] = cites
        network["total_nodes"] += len(cited_by) + len(cites)

        # Level 2: Citations of citations
        if depth >= 2:
            for case in cited_by[:10]:  # Limit to avoid explosion
                case["cited_by"] = self._get_citing_cases(case["id"])
                network["total_nodes"] += len(case["cited_by"])

            for case in cites[:10]:
                case["cites"] = self._get_cited_cases(case["id"])
                network["total_nodes"] += len(case["cites"])

        return network

    def _get_citing_cases(self, doc_id: int, limit: int = 20) -> List[Dict]:
        """Get cases that cite this document"""
        citations = Citation.query.filter(Citation.cited_doc_id == doc_id).limit(limit).all()

        citing_cases = []
        for citation in citations:
            doc = LegalDocument.query.get(citation.citing_doc_id)
            if doc:
                case_dict = self._document_to_dict(doc)
                case_dict["citation_context"] = citation.context
                citing_cases.append(case_dict)

        return citing_cases

    def _get_cited_cases(self, doc_id: int, limit: int = 20) -> List[Dict]:
        """Get cases that this document cites"""
        citations = Citation.query.filter(Citation.citing_doc_id == doc_id).limit(limit).all()

        cited_cases = []
        for citation in citations:
            doc = LegalDocument.query.get(citation.cited_doc_id)
            if doc:
                case_dict = self._document_to_dict(doc)
                case_dict["citation_context"] = citation.context
                cited_cases.append(case_dict)

        return cited_cases

    # ==================== E-DISCOVERY ANALYSIS ====================

    def analyze_document_relevance(
        self, document_text: str, case_issues: List[str], relevant_precedents: List[str]
    ) -> Dict:
        """
        Analyze document relevance for e-discovery

        Args:
            document_text: Full text of document to analyze
            case_issues: List of legal issues in the case
            relevant_precedents: List of relevant case citations

        Returns:
            Relevance analysis with scores and excerpts
        """

        analysis = {
            "overall_relevance": 0.0,
            "issue_matches": [],
            "precedent_mentions": [],
            "key_excerpts": [],
            "legal_terms": [],
            "recommended_action": "review",
        }

        # Check for case issues
        for issue in case_issues:
            if issue.lower() in document_text.lower():
                # Find context around issue
                pattern = re.compile(f".{{0,100}}{re.escape(issue)}.{{0,100}}", re.IGNORECASE)
                matches = pattern.findall(document_text)

                analysis["issue_matches"].append(
                    {"issue": issue, "count": len(matches), "excerpts": matches[:3]}
                )
                analysis["overall_relevance"] += 0.3

        # Check for precedent mentions
        for precedent in relevant_precedents:
            if precedent.lower() in document_text.lower():
                pattern = re.compile(f".{{0,100}}{re.escape(precedent)}.{{0,100}}", re.IGNORECASE)
                matches = pattern.findall(document_text)

                analysis["precedent_mentions"].append(
                    {"citation": precedent, "count": len(matches), "excerpts": matches[:2]}
                )
                analysis["overall_relevance"] += 0.4

        # Extract legal terms (simplified)
        legal_terms = [
            "jurisdiction",
            "precedent",
            "statute",
            "regulation",
            "plaintiff",
            "defendant",
            "appellant",
            "appellee",
            "motion",
            "brief",
            "discovery",
            "evidence",
            "testimony",
            "deposition",
            "affidavit",
            "sworn",
        ]

        found_terms = []
        for term in legal_terms:
            count = len(re.findall(rf"\b{term}\b", document_text, re.IGNORECASE))
            if count > 0:
                found_terms.append({"term": term, "count": count})

        analysis["legal_terms"] = sorted(found_terms, key=lambda x: x["count"], reverse=True)

        # Determine action based on relevance
        if analysis["overall_relevance"] >= 0.7:
            analysis["recommended_action"] = "high_priority_review"
        elif analysis["overall_relevance"] >= 0.4:
            analysis["recommended_action"] = "standard_review"
        else:
            analysis["recommended_action"] = "low_priority_or_discard"

        # Cap overall relevance at 1.0
        analysis["overall_relevance"] = min(1.0, analysis["overall_relevance"])

        return analysis

    # ==================== ARGUMENT CONSTRUCTION ====================

    def construct_legal_argument(
        self, position: str, legal_issue: str, jurisdiction: str, facts: List[str]
    ) -> Dict:
        """
        Construct a legal argument with supporting precedents

        Args:
            position: The legal position to argue
            legal_issue: The legal issue at hand
            jurisdiction: Relevant jurisdiction
            facts: List of case facts

        Returns:
            Structured legal argument with precedents
        """

        # Find supporting precedents
        precedents = self.find_precedents(
            legal_issue=legal_issue,
            jurisdiction=jurisdiction,
            favor="plaintiff" if "plaintiff" in position.lower() else "defendant",
            limit=10,
        )

        # Construct argument structure
        argument = {
            "position": position,
            "legal_issue": legal_issue,
            "jurisdiction": jurisdiction,
            "introduction": f"The {position} is supported by well-established precedent in {jurisdiction} and federal law.",
            "precedents": [],
            "fact_applications": [],
            "conclusion": "",
            "strength_score": 0.0,
        }

        # Add top precedents
        for i, precedent in enumerate(precedents[:5], 1):
            argument["precedents"].append(
                {
                    "rank": i,
                    "citation": precedent.get("citation"),
                    "holding": precedent.get("summary", ""),
                    "strength": precedent["precedent_strength"],
                    "application": f"Similar to {precedent.get('title', '')}, where...",
                }
            )

        # Calculate argument strength
        if precedents:
            argument["strength_score"] = sum(p["precedent_strength"] for p in precedents[:5]) / len(
                precedents[:5]
            )

        # Generate conclusion
        if argument["strength_score"] >= 0.7:
            argument["conclusion"] = f"Based on strong precedent, {position} should prevail."
        elif argument["strength_score"] >= 0.5:
            argument["conclusion"] = f"The precedent moderately supports {position}."
        else:
            argument["conclusion"] = (
                f"The precedent weakly supports {position}; additional research needed."
            )

        return argument

    # ==================== UTILITY METHODS ====================

    def _document_to_dict(self, doc: LegalDocument) -> Dict:
        """Convert LegalDocument to dictionary"""
        return {
            "id": doc.id,
            "title": doc.title,
            "citation": doc.citation,
            "court": doc.court,
            "jurisdiction": doc.jurisdiction,
            "decision_date": doc.decision_date.isoformat() if doc.decision_date else None,
            "summary": doc.summary,
            "full_text": (
                doc.full_text[:1000] + "..."
                if doc.full_text and len(doc.full_text) > 1000
                else doc.full_text
            ),
            "topics": json.loads(doc.topics) if doc.topics else [],
            "legal_issues": json.loads(doc.legal_issues) if doc.legal_issues else [],
            "citation_count": len(doc.citations_received) if doc.citations_received else 0,
            "url": doc.url,
            "verified": doc.verified,
        }

    def get_statistics(self) -> Dict:
        """Get library statistics"""
        total_docs = LegalDocument.query.count()
        total_citations = Citation.query.count()

        # Count by document type
        doc_types = (
            db.session.query(LegalDocument.doc_type, db.func.count(LegalDocument.id))
            .group_by(LegalDocument.doc_type)
            .all()
        )

        # Count by jurisdiction
        jurisdictions = (
            db.session.query(LegalDocument.jurisdiction, db.func.count(LegalDocument.id))
            .group_by(LegalDocument.jurisdiction)
            .all()
        )

        return {
            "total_documents": total_docs,
            "total_citations": total_citations,
            "by_type": dict(doc_types),
            "by_jurisdiction": dict(jurisdictions),
            "cache_size": len(self._precedent_cache),
        }
