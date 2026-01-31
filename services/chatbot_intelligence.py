"""
Chatbot Intelligence Layer - Legal Query Processing

Advanced natural language processing for legal chatbot:
- Query intent classification
- Entity extraction (parties, dates, jurisdictions, citations)
- Multi-turn conversation handling
- Context-aware response generation
- Legal document summarization
- Citation formatting and verification
"""

import json
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from services.legal_reference_engine import LegalReferenceEngine


class LegalChatbotIntelligence:
    """
    AI-powered legal chatbot with natural language understanding

    Capabilities:
    - Intent classification (research, precedent, citation, summary)
    - Entity extraction (names, dates, jurisdictions, citations)
    - Multi-turn conversations with context
    - Smart response generation
    - Citation validation and formatting
    """

    def __init__(self):
        self.reference_engine = LegalReferenceEngine()
        self.conversation_contexts = {}  # Store conversation history

        # Intent patterns
        self.intent_patterns = {
            "find_precedent": [
                r"find (precedent|case law|cases) (for|about|on)",
                r"what precedent supports",
                r"are there cases (about|on|regarding)",
                r"show me cases (where|that)",
            ],
            "cite_check": [
                r"check (this )?citation",
                r"is this citation (valid|correct)",
                r"verify citation",
                r"validate citation",
            ],
            "summarize": [
                r"summarize (this|the) (case|document)",
                r"give me a (brief|summary) of",
                r"what (is|was) (this case|the holding)",
                r"tell me about",
            ],
            "legal_research": [
                r"research",
                r"find (information|sources) (on|about)",
                r"what (is|are) the law(s)? (on|about)",
                r"legal (definition|meaning) of",
            ],
            "build_argument": [
                r"build (an )?argument (for|that)",
                r"how (can|should) i argue",
                r"support (my|the) (position|claim)",
                r"construct (a )?legal argument",
            ],
            "citation_network": [
                r"what cases cite",
                r"show citation network",
                r"citing (cases|authorities)",
                r"citation map",
            ],
        }

        # Entity extraction patterns
        self.entity_patterns = {
            "case_citation": r"\d+ [A-Z][A-Za-z.]+ \d+",  # e.g., "347 U.S. 483"
            "statute": r"\d+\s+[A-Z][A-Za-z.]+\s+§?\s*\d+",  # e.g., "42 U.S.C. § 1983"
            "year": r"\b(19|20)\d{2}\b",
            "jurisdiction": r"\b(federal|supreme court|[A-Z][a-z]+)\b",
            "party_name": r"\b([A-Z][a-z]+)\s+v\.?\s+([A-Z][a-z]+)\b",
        }

    # ==================== QUERY PROCESSING ====================

    def process_query(
        self, query: str, user_id: Optional[int] = None, conversation_id: Optional[str] = None
    ) -> Dict:
        """
        Process a natural language legal query

        Args:
            query: User's question or request
            user_id: User ID for personalization
            conversation_id: ID to track multi-turn conversations

        Returns:
            Response with answer, sources, and follow-up suggestions
        """

        # Get or create conversation context
        if conversation_id:
            context = self.conversation_contexts.get(
                conversation_id,
                {"history": [], "entities": {}, "jurisdiction": None, "current_case": None},
            )
        else:
            context = {"history": [], "entities": {}, "jurisdiction": None}

        # Classify intent
        intent = self._classify_intent(query)

        # Extract entities
        entities = self._extract_entities(query)

        # Merge entities with context
        context["entities"].update(entities)

        # Route to appropriate handler
        if intent == "find_precedent":
            response = self._handle_precedent_search(query, entities, context)
        elif intent == "cite_check":
            response = self._handle_citation_check(query, entities)
        elif intent == "summarize":
            response = self._handle_summarization(query, entities, context)
        elif intent == "legal_research":
            response = self._handle_research(query, entities, context)
        elif intent == "build_argument":
            response = self._handle_argument_construction(query, entities, context)
        elif intent == "citation_network":
            response = self._handle_citation_network(query, entities)
        else:
            response = self._handle_general_query(query, entities, context)

        # Add metadata
        response["intent"] = intent
        response["entities"] = entities
        response["conversation_id"] = conversation_id

        # Update conversation context
        if conversation_id:
            context["history"].append(
                {
                    "timestamp": datetime.now().isoformat(),
                    "query": query,
                    "intent": intent,
                    "response_summary": response.get("answer", "")[:200],
                }
            )
            self.conversation_contexts[conversation_id] = context

        # Add follow-up suggestions
        response["follow_up_suggestions"] = self._generate_follow_ups(intent, entities, response)

        return response

    def _classify_intent(self, query: str) -> str:
        """Classify the user's intent"""
        query_lower = query.lower()

        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, query_lower):
                    return intent

        return "general"

    def _extract_entities(self, query: str) -> Dict:
        """Extract legal entities from query"""
        entities = {}

        # Case citations
        citation_matches = re.findall(self.entity_patterns["case_citation"], query)
        if citation_matches:
            entities["citations"] = citation_matches

        # Statutes
        statute_matches = re.findall(self.entity_patterns["statute"], query)
        if statute_matches:
            entities["statutes"] = statute_matches

        # Years
        year_matches = re.findall(self.entity_patterns["year"], query)
        if year_matches:
            entities["years"] = [int(y) for y in year_matches]

        # Jurisdiction
        jurisdiction_matches = re.findall(
            self.entity_patterns["jurisdiction"], query, re.IGNORECASE
        )
        if jurisdiction_matches:
            entities["jurisdiction"] = jurisdiction_matches[0].lower()

        # Party names
        party_matches = re.findall(self.entity_patterns["party_name"], query)
        if party_matches:
            entities["parties"] = [f"{p[0]} v. {p[1]}" for p in party_matches]

        return entities

    # ==================== INTENT HANDLERS ====================

    def _handle_precedent_search(self, query: str, entities: Dict, context: Dict) -> Dict:
        """Handle precedent search requests"""

        # Extract legal issue from query
        legal_issue = self._extract_legal_issue(query)

        # Get jurisdiction from entities or context
        jurisdiction = entities.get("jurisdiction") or context.get("jurisdiction") or "federal"

        # Search for precedents
        precedents = self.reference_engine.find_precedents(
            legal_issue=legal_issue, jurisdiction=jurisdiction, limit=10
        )

        # Format response
        if precedents:
            answer = f"I found {len(precedents)} relevant precedents for '{legal_issue}' in {jurisdiction} law:\n\n"

            for i, precedent in enumerate(precedents[:5], 1):
                answer += f"{i}. **{precedent['citation']}** - {precedent['title']}\n"
                answer += f"   Strength: {precedent['precedent_strength']:.0%}\n"
                if precedent.get("summary"):
                    answer += f"   {precedent['summary'][:200]}...\n"
                answer += "\n"

            if len(precedents) > 5:
                answer += f"*... and {len(precedents) - 5} more cases*\n"
        else:
            answer = f"I couldn't find strong precedents for '{legal_issue}' in {jurisdiction} law. Try broadening your search or checking a different jurisdiction."

        return {
            "answer": answer,
            "precedents": precedents,
            "legal_issue": legal_issue,
            "jurisdiction": jurisdiction,
            "source_count": len(precedents),
        }

    def _handle_citation_check(self, query: str, entities: Dict) -> Dict:
        """Handle citation validation requests"""

        citations = entities.get("citations", [])

        if not citations:
            return {
                "answer": "I don't see a citation in your query. Please provide a citation in standard format (e.g., '347 U.S. 483').",
                "valid": False,
            }

        results = []
        for citation in citations:
            # Check if citation exists in database
            doc = self.reference_engine.comprehensive_search(query=citation, limit=1)

            if doc:
                results.append(
                    {
                        "citation": citation,
                        "valid": True,
                        "full_cite": doc[0].get("citation"),
                        "title": doc[0].get("title"),
                        "year": (
                            doc[0].get("decision_date", "")[:4]
                            if doc[0].get("decision_date")
                            else "Unknown"
                        ),
                    }
                )
            else:
                results.append(
                    {
                        "citation": citation,
                        "valid": False,
                        "message": "Citation not found in database",
                    }
                )

        # Format answer
        answer = "**Citation Check Results:**\n\n"
        for result in results:
            if result["valid"]:
                answer += f"✅ **{result['citation']}**\n"
                answer += f"   Full: {result.get('full_cite', 'N/A')}\n"
                answer += f"   Title: {result.get('title', 'N/A')}\n"
                answer += f"   Year: {result.get('year', 'N/A')}\n\n"
            else:
                answer += f"❌ **{result['citation']}**\n"
                answer += f"   {result['message']}\n\n"

        return {
            "answer": answer,
            "citations_checked": results,
            "all_valid": all(r["valid"] for r in results),
        }

    def _handle_summarization(self, query: str, entities: Dict, context: Dict) -> Dict:
        """Handle case/document summarization requests"""

        # Try to identify which case to summarize
        citations = entities.get("citations")
        parties = entities.get("parties")

        if citations:
            # Search by citation
            results = self.reference_engine.comprehensive_search(query=citations[0], limit=1)
        elif parties:
            # Search by party names
            results = self.reference_engine.comprehensive_search(query=parties[0], limit=1)
        elif context.get("current_case"):
            # Use case from context
            results = [context["current_case"]]
        else:
            return {
                "answer": "Please specify which case you'd like me to summarize (provide citation or party names).",
                "needs_clarification": True,
            }

        if not results:
            return {
                "answer": "I couldn't find that case in the database. Please check the citation or try a different search.",
                "found": False,
            }

        case = results[0]

        # Generate summary
        answer = f"**Summary of {case['citation']}**\n\n"
        answer += f"**Title:** {case['title']}\n"
        answer += f"**Court:** {case.get('court', 'N/A')}\n"
        answer += f"**Date:** {case.get('decision_date', 'N/A')[:10] if case.get('decision_date') else 'N/A'}\n\n"

        if case.get("summary"):
            answer += f"**Holding:**\n{case['summary']}\n\n"

        if case.get("legal_issues"):
            answer += f"**Legal Issues:**\n"
            for issue in case["legal_issues"][:3]:
                answer += f"• {issue}\n"
            answer += "\n"

        if case.get("topics"):
            answer += f"**Topics:** {', '.join(case['topics'][:5])}\n"

        # Store in context
        context["current_case"] = case

        return {"answer": answer, "case": case, "summarized": True}

    def _handle_research(self, query: str, entities: Dict, context: Dict) -> Dict:
        """Handle general legal research queries"""

        # Extract research topic
        topic = self._extract_legal_issue(query)
        jurisdiction = entities.get("jurisdiction") or context.get("jurisdiction")

        # Comprehensive search
        results = self.reference_engine.comprehensive_search(
            query=topic, jurisdiction=jurisdiction, limit=15
        )

        if not results:
            return {
                "answer": f"No results found for '{topic}'. Try rephrasing or broadening your search.",
                "results": [],
            }

        # Format response
        answer = f"**Research Results for '{topic}'**\n"
        if jurisdiction:
            answer += f"*Jurisdiction: {jurisdiction}*\n\n"

        answer += f"Found {len(results)} relevant sources:\n\n"

        # Group by document type
        cases = [r for r in results if r.get("doc_type") == "case"]
        statutes = [r for r in results if r.get("doc_type") == "statute"]

        if cases:
            answer += "**Case Law:**\n"
            for case in cases[:5]:
                answer += f"• {case.get('citation')} - {case.get('title')}\n"
                answer += f"  Relevance: {case.get('relevance_score', 0):.0%}\n"
            answer += "\n"

        if statutes:
            answer += "**Statutes:**\n"
            for statute in statutes[:3]:
                answer += f"• {statute.get('citation')} - {statute.get('title')}\n"
            answer += "\n"

        return {"answer": answer, "results": results, "topic": topic, "total_results": len(results)}

    def _handle_argument_construction(self, query: str, entities: Dict, context: Dict) -> Dict:
        """Handle legal argument construction requests"""

        # Extract position and issue
        legal_issue = self._extract_legal_issue(query)
        jurisdiction = entities.get("jurisdiction") or context.get("jurisdiction") or "federal"

        # Determine position (simplified - would use NLP)
        position = (
            "plaintiff"
            if any(word in query.lower() for word in ["plaintiff", "for", "support"])
            else "defendant"
        )

        # Construct argument
        argument = self.reference_engine.construct_legal_argument(
            position=position,
            legal_issue=legal_issue,
            jurisdiction=jurisdiction,
            facts=[],  # Would extract from context
        )

        # Format response
        answer = f"**Legal Argument Construction**\n\n"
        answer += f"**Position:** {argument['position']}\n"
        answer += f"**Issue:** {argument['legal_issue']}\n"
        answer += f"**Jurisdiction:** {argument['jurisdiction']}\n"
        answer += f"**Argument Strength:** {argument['strength_score']:.0%}\n\n"

        answer += f"**Introduction:**\n{argument['introduction']}\n\n"

        if argument["precedents"]:
            answer += f"**Supporting Precedents:**\n"
            for prec in argument["precedents"]:
                answer += f"{prec['rank']}. {prec.get('citation', 'N/A')}\n"
                answer += f"   Strength: {prec['strength']:.0%}\n"
                answer += f"   {prec.get('holding', '')[:150]}...\n\n"

        answer += f"**Conclusion:**\n{argument['conclusion']}\n"

        return {"answer": answer, "argument": argument, "strength": argument["strength_score"]}

    def _handle_citation_network(self, query: str, entities: Dict) -> Dict:
        """Handle citation network mapping requests"""

        citations = entities.get("citations")

        if not citations:
            return {
                "answer": "Please provide a case citation to map its citation network.",
                "needs_clarification": True,
            }

        citation = citations[0]

        # Map network
        network = self.reference_engine.map_citation_network(case_citation=citation, depth=2)

        if "error" in network:
            return {"answer": f"Error: {network['error']}", "error": True}

        # Format response
        answer = f"**Citation Network for {citation}**\n\n"
        answer += f"**Root Case:** {network['root'].get('title')}\n"
        answer += f"**Total Network Nodes:** {network['total_nodes']}\n\n"

        answer += f"**Cited By ({len(network['cited_by'])} cases):**\n"
        for case in network["cited_by"][:5]:
            answer += f"• {case.get('citation')} - {case.get('title')}\n"

        answer += f"\n**Cites ({len(network['cites'])} cases):**\n"
        for case in network["cites"][:5]:
            answer += f"• {case.get('citation')} - {case.get('title')}\n"

        return {
            "answer": answer,
            "network": network,
            "visualization_data": network,  # For graph visualization
        }

    def _handle_general_query(self, query: str, entities: Dict, context: Dict) -> Dict:
        """Handle general queries with comprehensive search"""

        results = self.reference_engine.comprehensive_search(query=query, limit=10)

        if results:
            answer = f"I found {len(results)} relevant results:\n\n"
            for i, result in enumerate(results[:5], 1):
                answer += f"{i}. **{result.get('citation', 'N/A')}**\n"
                answer += f"   {result.get('title', 'N/A')}\n"
                answer += f"   Relevance: {result.get('relevance_score', 0):.0%}\n\n"
        else:
            answer = "I couldn't find specific results for your query. Could you rephrase or provide more details?"

        return {"answer": answer, "results": results}

    # ==================== UTILITY METHODS ====================

    def _extract_legal_issue(self, query: str) -> str:
        """Extract the core legal issue from a query"""
        # Remove common question words
        cleaned = re.sub(
            r"\b(find|show|what|how|when|where|who|precedent|case|law|cases|about|on|regarding)\b",
            "",
            query,
            flags=re.IGNORECASE,
        )
        cleaned = cleaned.strip()

        # If still too long, take first 100 chars
        if len(cleaned) > 100:
            cleaned = cleaned[:100].rsplit(" ", 1)[0]

        return cleaned or query

    def _generate_follow_ups(self, intent: str, entities: Dict, response: Dict) -> List[str]:
        """Generate contextual follow-up suggestions"""

        suggestions = []

        if intent == "find_precedent":
            suggestions.append("Show me the citation network for the top case")
            suggestions.append("Summarize the strongest precedent")
            suggestions.append("Find precedents in a different jurisdiction")

        elif intent == "summarize":
            suggestions.append("What cases cite this one?")
            suggestions.append("Find similar cases")
            suggestions.append("Show me related precedents")

        elif intent == "legal_research":
            suggestions.append("Find precedents supporting this issue")
            suggestions.append("Build an argument based on these results")
            suggestions.append("Check the citations in these cases")

        elif intent == "build_argument":
            suggestions.append("Show me counterarguments")
            suggestions.append("Find additional supporting precedents")
            suggestions.append("Summarize the strongest case cited")

        else:
            suggestions.append("Find precedents for this issue")
            suggestions.append("Summarize the most relevant case")
            suggestions.append("Show me related legal research")

        return suggestions[:3]

    def clear_conversation(self, conversation_id: str):
        """Clear conversation context"""
        if conversation_id in self.conversation_contexts:
            del self.conversation_contexts[conversation_id]

    def get_conversation_history(self, conversation_id: str) -> List[Dict]:
        """Get conversation history"""
        context = self.conversation_contexts.get(conversation_id, {})
        return context.get("history", [])
