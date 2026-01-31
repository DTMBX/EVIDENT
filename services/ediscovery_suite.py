"""
E-Discovery Analysis Suite - Advanced Document Intelligence

Professional-grade e-discovery with:
- Batch document processing
- Relevance scoring and categorization
- Predictive coding (Technology Assisted Review)
- Email threading and deduplication
- Timeline construction
- Named entity recognition (parties, dates, locations)
- Key document identification
- Privilege detection
- Production set generation
"""

import hashlib
import json
import re
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple

import numpy as np
from services.legal_reference_engine import LegalReferenceEngine
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB


class EDiscoverySuite:
    """
    Enterprise-grade e-discovery analysis suite

    Features:
    - Document relevance prediction (TAR)
    - Email threading and deduplication
    - Timeline and chronology generation
    - Named entity extraction
    - Privilege screening
    - Production set management
    - Similarity clustering
    """

    def __init__(self):
        self.reference_engine = LegalReferenceEngine()
        self.vectorizer = TfidfVectorizer(max_features=5000, stop_words="english")
        self.relevance_model = None  # Will be trained with user feedback
        self.doc_cache = {}

        # Legal term dictionaries
        self.privilege_terms = [
            "attorney-client",
            "work product",
            "privileged",
            "confidential",
            "legal advice",
            "in confidence",
            "attorney communication",
            "prepared for litigation",
            "in anticipation of",
            "counsel",
        ]

        self.responsive_indicators = [
            "contract",
            "agreement",
            "settlement",
            "negotiation",
            "claim",
            "lawsuit",
            "litigation",
            "dispute",
            "damages",
            "liability",
            "breach",
            "violation",
            "allegation",
            "complaint",
        ]

    # ==================== DOCUMENT PROCESSING ====================

    def process_document_batch(
        self,
        documents: List[Dict],
        case_issues: List[str],
        relevant_precedents: List[str] = None,
        apply_tar: bool = False,
    ) -> Dict:
        """
        Process a batch of documents for e-discovery

        Args:
            documents: List of documents with 'id', 'text', 'metadata'
            case_issues: Legal issues in the case
            relevant_precedents: Optional list of relevant citations
            apply_tar: Apply predictive coding (TAR) if trained

        Returns:
            Processed results with relevance scores and categories
        """

        results = {
            "total_documents": len(documents),
            "processed": [],
            "statistics": {
                "highly_relevant": 0,
                "relevant": 0,
                "marginal": 0,
                "not_relevant": 0,
                "privileged": 0,
                "duplicates": 0,
            },
            "key_documents": [],
            "timeline_events": [],
            "entities": {
                "people": set(),
                "organizations": set(),
                "locations": set(),
                "dates": set(),
            },
        }

        # Deduplicate first
        unique_docs, duplicate_map = self._deduplicate_documents(documents)
        results["statistics"]["duplicates"] = len(documents) - len(unique_docs)

        # Process each unique document
        for doc in unique_docs:
            analysis = self._analyze_document(doc, case_issues, relevant_precedents or [])

            # Apply TAR if available
            if apply_tar and self.relevance_model:
                analysis["tar_prediction"] = self._predict_relevance(doc["text"])

            # Extract entities
            entities = self._extract_entities(doc["text"])
            results["entities"]["people"].update(entities["people"])
            results["entities"]["organizations"].update(entities["organizations"])
            results["entities"]["dates"].update(entities["dates"])

            # Extract timeline events
            if entities["dates"]:
                for date in entities["dates"]:
                    results["timeline_events"].append(
                        {"date": date, "document_id": doc["id"], "snippet": doc["text"][:200]}
                    )

            # Categorize
            if analysis["privilege_risk"] > 0.7:
                results["statistics"]["privileged"] += 1
                analysis["category"] = "privileged"
            elif analysis["overall_relevance"] >= 0.7:
                results["statistics"]["highly_relevant"] += 1
                analysis["category"] = "highly_relevant"
                results["key_documents"].append(analysis)
            elif analysis["overall_relevance"] >= 0.4:
                results["statistics"]["relevant"] += 1
                analysis["category"] = "relevant"
            elif analysis["overall_relevance"] >= 0.2:
                results["statistics"]["marginal"] += 1
                analysis["category"] = "marginal"
            else:
                results["statistics"]["not_relevant"] += 1
                analysis["category"] = "not_relevant"

            results["processed"].append(analysis)

        # Convert sets to lists for JSON serialization
        results["entities"] = {k: sorted(list(v)) for k, v in results["entities"].items()}

        # Sort timeline
        results["timeline_events"].sort(key=lambda x: x["date"])

        # Rank key documents
        results["key_documents"].sort(key=lambda x: x["overall_relevance"], reverse=True)

        return results

    def _analyze_document(
        self, doc: Dict, case_issues: List[str], relevant_precedents: List[str]
    ) -> Dict:
        """Analyze individual document"""

        text = doc.get("text", "")

        analysis = {
            "document_id": doc.get("id"),
            "filename": doc.get("metadata", {}).get("filename"),
            "overall_relevance": 0.0,
            "privilege_risk": 0.0,
            "issue_matches": [],
            "precedent_mentions": [],
            "key_terms": [],
            "excerpts": [],
            "recommended_action": "review",
        }

        # Check for case issues
        for issue in case_issues:
            if issue.lower() in text.lower():
                count = text.lower().count(issue.lower())
                # Extract context
                pattern = re.compile(f".{{0,100}}{re.escape(issue)}.{{0,100}}", re.IGNORECASE)
                excerpts = pattern.findall(text)

                analysis["issue_matches"].append(
                    {"issue": issue, "count": count, "excerpts": excerpts[:2]}
                )
                analysis["overall_relevance"] += min(0.3, count * 0.1)

        # Check for precedent mentions
        for precedent in relevant_precedents:
            if precedent.lower() in text.lower():
                count = text.lower().count(precedent.lower())
                pattern = re.compile(f".{{0,100}}{re.escape(precedent)}.{{0,100}}", re.IGNORECASE)
                excerpts = pattern.findall(text)

                analysis["precedent_mentions"].append(
                    {"citation": precedent, "count": count, "excerpts": excerpts[:2]}
                )
                analysis["overall_relevance"] += min(0.4, count * 0.15)

        # Check for responsive indicators
        responsive_score = 0
        for term in self.responsive_indicators:
            if term in text.lower():
                responsive_score += 0.05
                analysis["key_terms"].append(term)
        analysis["overall_relevance"] += min(0.3, responsive_score)

        # Check for privilege
        privilege_score = 0
        for term in self.privilege_terms:
            if term in text.lower():
                privilege_score += 0.15
        analysis["privilege_risk"] = min(1.0, privilege_score)

        # Cap overall relevance
        analysis["overall_relevance"] = min(1.0, analysis["overall_relevance"])

        # Determine action
        if analysis["privilege_risk"] > 0.7:
            analysis["recommended_action"] = "privilege_review"
        elif analysis["overall_relevance"] >= 0.7:
            analysis["recommended_action"] = "high_priority_review"
        elif analysis["overall_relevance"] >= 0.4:
            analysis["recommended_action"] = "standard_review"
        else:
            analysis["recommended_action"] = "low_priority"

        return analysis

    # ==================== DEDUPLICATION ====================

    def _deduplicate_documents(self, documents: List[Dict]) -> Tuple[List[Dict], Dict]:
        """
        Deduplicate documents using content hashing

        Returns:
            (unique_documents, duplicate_map)
        """

        seen_hashes = {}
        unique_docs = []
        duplicate_map = {}

        for doc in documents:
            # Create content hash
            text = doc.get("text", "")
            content_hash = hashlib.md5(text.encode()).hexdigest()

            if content_hash in seen_hashes:
                # Duplicate found
                original_id = seen_hashes[content_hash]
                duplicate_map[doc["id"]] = original_id
            else:
                # Unique document
                seen_hashes[content_hash] = doc["id"]
                unique_docs.append(doc)

        return unique_docs, duplicate_map

    # ==================== NAMED ENTITY EXTRACTION ====================

    def _extract_entities(self, text: str) -> Dict[str, Set[str]]:
        """Extract named entities from text"""

        entities = {"people": set(), "organizations": set(), "locations": set(), "dates": set()}

        # Extract dates (various formats)
        date_patterns = [
            r"\d{1,2}/\d{1,2}/\d{2,4}",  # MM/DD/YYYY
            r"\d{4}-\d{2}-\d{2}",  # YYYY-MM-DD
            r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}",
            r"\d{1,2}\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{4}",
        ]

        for pattern in date_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            entities["dates"].update(matches)

        # Extract people (simplified - look for capitalized names)
        people_pattern = r"\b([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b"
        people_matches = re.findall(people_pattern, text)

        # Filter out common non-names
        exclude_words = {"Supreme Court", "United States", "District Court", "Court of Appeals"}
        entities["people"].update(
            name for name in people_matches if name not in exclude_words and len(name.split()) <= 3
        )

        # Extract organizations (simplified - Inc., LLC, Corp., etc.)
        org_pattern = r"\b([A-Z][A-Za-z\s&]+(?:Inc\.|LLC|Corp\.|Corporation|Company|Ltd\.))\b"
        org_matches = re.findall(org_pattern, text)
        entities["organizations"].update(org_matches)

        # Extract locations (simplified - common patterns)
        location_pattern = r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*,\s*[A-Z]{2})\b"  # City, STATE
        location_matches = re.findall(location_pattern, text)
        entities["locations"].update(location_matches)

        return entities

    # ==================== PREDICTIVE CODING (TAR) ====================

    def train_relevance_model(
        self, training_docs: List[Dict], labels: List[int]  # 1 for relevant, 0 for not relevant
    ):
        """
        Train TAR model with user-coded documents

        Args:
            training_docs: Documents with 'text' field
            labels: 1 for relevant, 0 for not relevant
        """

        # Extract text
        texts = [doc["text"] for doc in training_docs]

        # Vectorize
        X = self.vectorizer.fit_transform(texts)

        # Train Naive Bayes classifier
        self.relevance_model = MultinomialNB()
        self.relevance_model.fit(X, labels)

        # Calculate accuracy on training set
        predictions = self.relevance_model.predict(X)
        accuracy = np.mean(predictions == labels)

        return {
            "model_trained": True,
            "training_docs": len(training_docs),
            "training_accuracy": accuracy,
            "message": f"TAR model trained on {len(training_docs)} documents with {accuracy:.1%} accuracy",
        }

    def _predict_relevance(self, text: str) -> Dict:
        """Predict document relevance using TAR model"""

        if not self.relevance_model:
            return {"error": "Model not trained"}

        # Vectorize
        X = self.vectorizer.transform([text])

        # Predict
        prediction = self.relevance_model.predict(X)[0]
        probability = self.relevance_model.predict_proba(X)[0]

        return {
            "relevant": bool(prediction),
            "confidence": float(max(probability)),
            "probability_relevant": float(probability[1]) if len(probability) > 1 else 0.0,
        }

    # ==================== EMAIL THREADING ====================

    def thread_emails(self, emails: List[Dict]) -> List[Dict]:
        """
        Thread email conversations

        Args:
            emails: List of emails with 'subject', 'from', 'to', 'date', 'text'

        Returns:
            List of email threads
        """

        threads = []
        processed_ids = set()

        for email in emails:
            if email["id"] in processed_ids:
                continue

            # Start new thread
            thread = {
                "root_subject": self._normalize_subject(email.get("subject", "")),
                "participants": set([email.get("from", "")]),
                "date_range": {"start": email.get("date"), "end": email.get("date")},
                "emails": [email],
                "email_count": 1,
            }

            processed_ids.add(email["id"])

            # Find related emails
            for other_email in emails:
                if other_email["id"] in processed_ids:
                    continue

                # Check if subjects match (ignoring Re:, Fwd:, etc.)
                if (
                    self._normalize_subject(other_email.get("subject", ""))
                    == thread["root_subject"]
                ):
                    thread["emails"].append(other_email)
                    thread["participants"].add(other_email.get("from", ""))
                    thread["email_count"] += 1
                    processed_ids.add(other_email["id"])

                    # Update date range
                    email_date = other_email.get("date")
                    if email_date:
                        if (
                            not thread["date_range"]["start"]
                            or email_date < thread["date_range"]["start"]
                        ):
                            thread["date_range"]["start"] = email_date
                        if (
                            not thread["date_range"]["end"]
                            or email_date > thread["date_range"]["end"]
                        ):
                            thread["date_range"]["end"] = email_date

            # Sort emails in thread by date
            thread["emails"].sort(key=lambda x: x.get("date", ""))
            thread["participants"] = list(thread["participants"])

            threads.append(thread)

        # Sort threads by most recent email
        threads.sort(key=lambda x: x["date_range"]["end"], reverse=True)

        return threads

    def _normalize_subject(self, subject: str) -> str:
        """Normalize email subject for threading"""
        # Remove Re:, Fwd:, FW:, etc.
        normalized = re.sub(r"^(Re|RE|Fwd|FW|Fw):\s*", "", subject, flags=re.IGNORECASE)
        normalized = normalized.strip().lower()
        return normalized

    # ==================== SIMILARITY CLUSTERING ====================

    def cluster_similar_documents(
        self, documents: List[Dict], num_clusters: int = 10
    ) -> List[Dict]:
        """
        Cluster documents by similarity

        Args:
            documents: Documents with 'text' field
            num_clusters: Number of clusters to create

        Returns:
            List of clusters with documents
        """

        # Extract text
        texts = [doc.get("text", "") for doc in documents]

        # Vectorize
        X = self.vectorizer.fit_transform(texts)

        # Cluster
        kmeans = KMeans(n_clusters=min(num_clusters, len(documents)), random_state=42)
        cluster_labels = kmeans.fit_predict(X)

        # Organize into clusters
        clusters = defaultdict(list)
        for doc, label in zip(documents, cluster_labels):
            clusters[int(label)].append(doc)

        # Format output
        result = []
        for cluster_id, docs in clusters.items():
            result.append(
                {
                    "cluster_id": cluster_id,
                    "document_count": len(docs),
                    "documents": docs,
                    "representative_terms": self._get_cluster_terms(docs),
                }
            )

        # Sort by size
        result.sort(key=lambda x: x["document_count"], reverse=True)

        return result

    def _get_cluster_terms(self, documents: List[Dict], top_n: int = 5) -> List[str]:
        """Extract representative terms for a cluster"""

        # Combine all text in cluster
        combined_text = " ".join(doc.get("text", "") for doc in documents)

        # Count word frequencies (simplified)
        words = re.findall(r"\b[a-z]{4,}\b", combined_text.lower())
        word_counts = defaultdict(int)
        for word in words:
            word_counts[word] += 1

        # Return top terms
        top_terms = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
        return [term for term, count in top_terms[:top_n]]

    # ==================== PRODUCTION SETS ====================

    def generate_production_set(
        self, documents: List[Dict], include_categories: List[str] = None
    ) -> Dict:
        """
        Generate production set from processed documents

        Args:
            documents: Processed documents with category field
            include_categories: Which categories to include (default: highly_relevant, relevant)

        Returns:
            Production set metadata and document list
        """

        if include_categories is None:
            include_categories = ["highly_relevant", "relevant"]

        production_docs = [doc for doc in documents if doc.get("category") in include_categories]

        # Exclude privileged
        production_docs = [doc for doc in production_docs if doc.get("category") != "privileged"]

        return {
            "production_set_id": f"PROD_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "created": datetime.now().isoformat(),
            "total_documents": len(production_docs),
            "categories_included": include_categories,
            "documents": production_docs,
            "bates_range": self._assign_bates_numbers(production_docs),
        }

    def _assign_bates_numbers(self, documents: List[Dict], prefix: str = "BATES") -> Dict:
        """Assign Bates numbers to documents"""

        start = 1
        for i, doc in enumerate(documents, start):
            doc["bates_number"] = f"{prefix}{i:06d}"

        return {
            "start": f"{prefix}{start:06d}",
            "end": f"{prefix}{len(documents):06d}",
            "count": len(documents),
        }
