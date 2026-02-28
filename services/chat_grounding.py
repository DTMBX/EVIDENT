"""
B30 Phase 5 — Chat Assistant Grounding Service
=================================================
Enforces evidence-grounded chat responses with mandatory citations.

This module provides:
  1. Grounded system prompts that enforce citation requirements.
  2. Evidence-context tools that bring indexed evidence into chat context.
  3. Citation validation — checks that assistant responses reference real evidence.
  4. Tool call audit — every tool invocation is logged to the integrity ledger.
  5. Safe-mode gating — blocks fabrication of evidence or legal conclusions.

Design principles:
  - The assistant MUST cite evidence by filename, timecode, or document ID.
  - The assistant MUST NOT fabricate cases, statutes, or evidence metadata.
  - All tool calls are logged to the integrity ledger (append-only).
  - The assistant MUST NOT infer guilt, liability, or intent.
  - Responses that fail citation validation are flagged before delivery.
"""

import json
import logging
import re
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from services.evidence_indexer import EvidenceIndexer, SearchResponse
from services.integrity_ledger import IntegrityLedger

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Grounded system prompts
# ---------------------------------------------------------------------------

GROUNDED_SYSTEM_PROMPT = """You are the Evident Evidence Assistant — a forensic evidence analysis tool.

MANDATORY RULES:
1. CITE EVIDENCE: Every factual claim MUST reference specific evidence by filename, evidence ID, or timecode.
   Format citations as [Evidence: filename] or [Evidence: evidence_id, timecode HH:MM:SS].

2. NO FABRICATION: Never invent, assume, or hallucinate:
   - Case names, statutes, or legal citations
   - Evidence metadata (dates, times, locations) not present in provided evidence
   - Conclusions about guilt, liability, or intent

3. STATE LIMITATIONS: If evidence is insufficient to answer a question, explicitly say so.
   Use phrases like "Based on the available evidence..." or "The indexed evidence does not contain..."

4. NO LEGAL ADVICE: You are an evidence analysis tool, not legal counsel.
   You may describe what evidence shows; you may NOT advise on legal strategy or conclusions.

5. DETERMINISTIC: Your analysis must be reproducible. Do not speculate beyond what the evidence shows.

6. CHAIN OF CUSTODY: When discussing evidence, note its integrity status if available.

When using tools:
- Use search_evidence_index to find relevant evidence before answering.
- Use get_evidence_context to retrieve specific evidence details.
- Always report the source of your information.

If asked to do something that violates these rules, decline with an explanation."""

SAFE_MODE_PROMPT_SUFFIX = """

SAFE MODE ACTIVE:
- All responses are limited to factual descriptions of evidence content.
- No interpretive analysis is permitted.
- No legal conclusions of any kind.
- Citations are strictly required for every statement."""


# ---------------------------------------------------------------------------
# Grounded tool definitions (for OpenAI function calling)
# ---------------------------------------------------------------------------

GROUNDED_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_evidence_index",
            "description": (
                "Search the evidence index for items matching a query. "
                "Returns evidence filenames, content snippets, and metadata. "
                "Use this before answering any question about evidence content."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query (keywords or exact phrases in quotes)",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum results to return (default: 10)",
                        "default": 10,
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_evidence_context",
            "description": (
                "Get the full indexed text content and metadata for a specific "
                "evidence item by its evidence ID. Use after search to get details."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "evidence_id": {
                        "type": "string",
                        "description": "The evidence ID to retrieve context for",
                    },
                },
                "required": ["evidence_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_evidence_summary",
            "description": (
                "List all indexed evidence items with basic metadata "
                "(filename, word count, content type). Use to understand "
                "what evidence is available."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },
]


# ---------------------------------------------------------------------------
# Citation validation
# ---------------------------------------------------------------------------

# Pattern: [Evidence: ...] — standard citation format
CITATION_PATTERN = re.compile(
    r"\[Evidence:\s*([^\]]+)\]",
    re.IGNORECASE,
)

# Pattern: references to filenames with extensions
FILENAME_PATTERN = re.compile(
    r"\b[\w\-]+\.\b(?:mp4|avi|mov|pdf|docx|txt|jpg|png|wav|mp3)\b",
    re.IGNORECASE,
)


@dataclass
class CitationCheck:
    """Result of validating citations in an assistant response."""
    has_citations: bool
    citation_count: int
    valid_citations: List[str] = field(default_factory=list)
    invalid_citations: List[str] = field(default_factory=list)
    filename_references: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    passed: bool = True


def validate_citations(
    response_text: str,
    known_evidence_ids: List[str],
    known_filenames: List[str],
) -> CitationCheck:
    """
    Validate that an assistant response properly cites evidence.

    Checks:
      1. Presence of [Evidence: ...] citations.
      2. That cited evidence IDs or filenames exist in the index.
      3. Absence of fabrication indicators.

    Args:
        response_text: The assistant's response text.
        known_evidence_ids: List of valid evidence IDs.
        known_filenames: List of valid evidence filenames.

    Returns:
        CitationCheck with validation results.
    """
    result = CitationCheck(
        has_citations=False,
        citation_count=0,
    )

    if not response_text:
        result.passed = False
        result.warnings.append("Empty response")
        return result

    # Extract formal citations
    citations = CITATION_PATTERN.findall(response_text)
    result.citation_count = len(citations)
    result.has_citations = len(citations) > 0

    # Validate each citation
    ids_lower = {eid.lower() for eid in known_evidence_ids}
    names_lower = {fn.lower() for fn in known_filenames}

    for cite in citations:
        cite_stripped = cite.strip()
        cite_lower = cite_stripped.lower()

        # Check against known evidence
        matched = False
        if cite_lower in ids_lower:
            matched = True
        elif cite_lower in names_lower:
            matched = True
        else:
            # Partial match (citation might include timecode)
            for eid in known_evidence_ids:
                if eid.lower() in cite_lower:
                    matched = True
                    break
            if not matched:
                for fn in known_filenames:
                    if fn.lower() in cite_lower:
                        matched = True
                        break

        if matched:
            result.valid_citations.append(cite_stripped)
        else:
            result.invalid_citations.append(cite_stripped)

    # Extract filename references (may be informal citations)
    result.filename_references = FILENAME_PATTERN.findall(response_text)

    # Check for fabrication indicators
    fabrication_phrases = [
        "i believe", "i think", "it seems likely",
        "guilty", "not guilty", "liable", "negligent",
        "you should", "i recommend", "my advice",
    ]
    for phrase in fabrication_phrases:
        if phrase in response_text.lower():
            result.warnings.append(
                f"Potential policy violation: response contains '{phrase}'"
            )

    # Determine pass/fail
    if result.invalid_citations:
        result.passed = False
        result.warnings.append(
            f"{len(result.invalid_citations)} citation(s) reference unknown evidence"
        )

    return result


# ---------------------------------------------------------------------------
# Grounded tool executor
# ---------------------------------------------------------------------------


class GroundedToolExecutor:
    """
    Executes grounded evidence tools and logs every call to the integrity ledger.
    """

    def __init__(
        self,
        indexer: Optional[EvidenceIndexer] = None,
        ledger: Optional[IntegrityLedger] = None,
        case_evidence_ids: Optional[List[str]] = None,
    ):
        self._indexer = indexer or EvidenceIndexer()
        self._ledger = ledger or IntegrityLedger()
        self._case_evidence_ids = case_evidence_ids

    def execute(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        actor: str = "system",
        conversation_id: str = "",
    ) -> Dict[str, Any]:
        """
        Execute a grounded tool call.

        Every call is logged to the integrity ledger.

        Args:
            tool_name: Name of the tool to execute.
            arguments: Tool arguments.
            actor: Actor identifier.
            conversation_id: Conversation context.

        Returns:
            Tool result dict.
        """
        start = time.time()

        # Log tool invocation
        self._ledger.append(
            action="chat.tool_invoked",
            evidence_id=conversation_id,
            actor=actor,
            details={
                "tool_name": tool_name,
                "arguments": arguments,
            },
        )

        try:
            if tool_name == "search_evidence_index":
                result = self._search_evidence_index(arguments)
            elif tool_name == "get_evidence_context":
                result = self._get_evidence_context(arguments)
            elif tool_name == "list_evidence_summary":
                result = self._list_evidence_summary()
            else:
                result = {"error": f"Unknown tool: {tool_name}"}

            elapsed = time.time() - start

            # Log tool result
            self._ledger.append(
                action="chat.tool_result",
                evidence_id=conversation_id,
                actor=actor,
                details={
                    "tool_name": tool_name,
                    "success": "error" not in result,
                    "elapsed_ms": round(elapsed * 1000, 2),
                    "result_keys": list(result.keys()) if isinstance(result, dict) else [],
                },
            )

            return result

        except Exception as exc:
            elapsed = time.time() - start
            self._ledger.append(
                action="chat.tool_error",
                evidence_id=conversation_id,
                actor=actor,
                details={
                    "tool_name": tool_name,
                    "error": str(exc),
                    "elapsed_ms": round(elapsed * 1000, 2),
                },
            )
            return {"error": str(exc)}

    def _search_evidence_index(self, args: Dict) -> Dict:
        """Execute search_evidence_index tool."""
        query = args.get("query", "")
        max_results = args.get("max_results", 10)

        response = self._indexer.search(
            query=query,
            case_evidence_ids=self._case_evidence_ids,
            max_results=max_results,
        )

        return {
            "query": response.query,
            "total_results": response.total_results,
            "results": [
                {
                    "evidence_id": r.evidence_id,
                    "filename": r.filename,
                    "snippet": r.snippet,
                    "match_count": r.match_count,
                    "content_type": r.content_type,
                }
                for r in response.results
            ],
        }

    def _get_evidence_context(self, args: Dict) -> Dict:
        """Execute get_evidence_context tool."""
        evidence_id = args.get("evidence_id", "")
        entry = self._indexer.get_entry(evidence_id)

        if not entry:
            return {"error": f"Evidence '{evidence_id}' not found in index"}

        return {
            "evidence_id": entry.evidence_id,
            "filename": entry.filename,
            "sha256": entry.original_sha256,
            "content_type": entry.content_type,
            "full_text": entry.full_text,
            "word_count": entry.word_count,
            "email_addresses": entry.email_addresses,
            "phone_numbers": entry.phone_numbers,
            "indexed_at": entry.indexed_at,
        }

    def _list_evidence_summary(self) -> Dict:
        """Execute list_evidence_summary tool."""
        entries = self._indexer.get_all_entries()

        if self._case_evidence_ids is not None:
            entries = [e for e in entries if e.evidence_id in self._case_evidence_ids]

        return {
            "total_items": len(entries),
            "items": [
                {
                    "evidence_id": e.evidence_id,
                    "filename": e.filename,
                    "content_type": e.content_type,
                    "word_count": e.word_count,
                    "entities": len(e.email_addresses) + len(e.phone_numbers),
                }
                for e in entries
            ],
        }


# ---------------------------------------------------------------------------
# System prompt builder
# ---------------------------------------------------------------------------


def build_grounded_system_prompt(
    case_context: Optional[str] = None,
    safe_mode: bool = False,
    evidence_count: int = 0,
) -> str:
    """
    Build the grounded system prompt with optional case context.

    Args:
        case_context: Optional case description to include.
        safe_mode: If True, append safe mode restrictions.
        evidence_count: Number of indexed evidence items (for context).

    Returns:
        Complete system prompt string.
    """
    prompt = GROUNDED_SYSTEM_PROMPT

    if case_context:
        prompt += f"\n\nCASE CONTEXT:\n{case_context}"

    if evidence_count > 0:
        prompt += (
            f"\n\nEVIDENCE AVAILABLE: {evidence_count} items indexed. "
            "Use search_evidence_index to find relevant evidence before answering."
        )

    if safe_mode:
        prompt += SAFE_MODE_PROMPT_SUFFIX

    return prompt
