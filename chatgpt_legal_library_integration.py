"""
ChatGPT Integration with Legal Reference Library

Enables ChatGPT assistant to:
- Search user's legal library when answering questions
- Cite cases from the library in responses
- Suggest relevant cases based on conversation context
- Link to full case text in the library
"""

import json
from typing import Dict, List, Optional

from legal_library import CitationParser, LegalLibraryService


class ChatGPTLegalLibraryIntegration:
    """Integrates legal library search into ChatGPT conversations"""

    def __init__(self):
        self.library = LegalLibraryService()
        self.citation_parser = CitationParser()

    def search_library_for_context(self, user_message: str, user_id: int = None) -> List[Dict]:
        """
        Search legal library based on user's question

        Args:
            user_message: User's chat message
            user_id: Optional user ID for private documents

        Returns:
            List of relevant cases to include in ChatGPT context
        """

        # Extract legal keywords
        legal_keywords = self._extract_legal_keywords(user_message)

        if not legal_keywords:
            return []

        # Search library
        results = self.library.search_library(
            query=" ".join(legal_keywords), limit=5  # Top 5 most relevant cases
        )

        # Format for ChatGPT context
        context_cases = []
        for doc in results:
            context_cases.append(
                {
                    "citation": doc.citation,
                    "title": doc.title,
                    "summary": doc.summary[:500] if doc.summary else "",
                    "topics": json.loads(doc.topics) if doc.topics else [],
                    "url": f"/api/legal-library/document/{doc.id}",
                }
            )

        return context_cases

    def enhance_system_prompt(self, base_prompt: str, relevant_cases: List[Dict]) -> str:
        """
        Add relevant cases to ChatGPT system prompt

        Args:
            base_prompt: Original system prompt
            relevant_cases: Cases from search_library_for_context()

        Returns:
            Enhanced prompt with case law context
        """

        if not relevant_cases:
            return base_prompt

        cases_context = "\n\nRELEVANT CASE LAW FROM USER'S LIBRARY:\n"

        for case in relevant_cases:
            cases_context += f"\n{case['citation']} - {case['title']}\n"
            if case["summary"]:
                cases_context += f"Summary: {case['summary']}\n"
            if case["topics"]:
                cases_context += f"Topics: {', '.join(case['topics'])}\n"

        cases_context += "\nWhen relevant, cite these cases in your response. Users can click citations to view full text.\n"

        return base_prompt + cases_context

    def format_citation_links(self, response_text: str) -> str:
        """
        Convert citations in response to clickable links

        Args:
            response_text: ChatGPT's response text

        Returns:
            Response with citations converted to markdown links
        """

        # Find all citations in response
        citations = self.citation_parser.extract_all(response_text)

        # Replace each citation with a link
        for citation in citations:
            # Look up in library
            doc = self.library.search_library(query=citation, limit=1)
            if doc:
                doc_id = doc[0].id
                link = f"[{citation}](/api/legal-library/document/{doc_id})"
                response_text = response_text.replace(citation, link)

        return response_text

    def _extract_legal_keywords(self, text: str) -> List[str]:
        """Extract legal keywords from user message"""

        # Common legal terms
        legal_terms = [
            "amendment",
            "constitutional",
            "supreme court",
            "circuit",
            "search",
            "seizure",
            "warrant",
            "probable cause",
            "miranda",
            "rights",
            "due process",
            "equal protection",
            "excessive force",
            "qualified immunity",
            "section 1983",
            "brady",
            "giglio",
            "discovery",
            "evidence",
            "counsel",
            "trial",
            "appeal",
            "habeas",
            "discrimination",
            "employment",
            "wrongful termination",
        ]

        text_lower = text.lower()
        keywords = []

        for term in legal_terms:
            if term in text_lower:
                keywords.append(term)

        # Also extract any citations mentioned
        citations = self.citation_parser.extract_all(text)
        keywords.extend(citations)

        return keywords


# TODO: Integration points for api/chatgpt.py
"""
Add to chat endpoint in api/chatgpt.py:

from chatgpt_legal_library_integration import ChatGPTLegalLibraryIntegration

library_integration = ChatGPTLegalLibraryIntegration()

@chatgpt_bp.route('/api/v1/chat/message', methods=['POST'])
def send_message():
    data = request.get_json()
    user_message = data.get('message')
    
    # Search library for relevant cases
    relevant_cases = library_integration.search_library_for_context(
        user_message,
        user_id=current_user.id
    )
    
    # Enhance system prompt
    system_prompt = library_integration.enhance_system_prompt(
        base_system_prompt,
        relevant_cases
    )
    
    # Call ChatGPT with enhanced prompt
    response = chatgpt_service.chat(user_message, system_prompt)
    
    # Format citations as links
    response = library_integration.format_citation_links(response)
    
    return jsonify({'response': response})
"""
