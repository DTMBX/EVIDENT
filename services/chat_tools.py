"""
Chat Tool Definitions for Evident
Tools that connect chat to backend services (legal library, media, cases, evidence, etc.)
"""

import json
from typing import Dict, List, Any, Callable, Optional

# Tool registry - maps tool names to executor functions
TOOL_REGISTRY: Dict[str, Callable] = {}


class EvidentChatTools:
    """Defines all available tools for the chat interface"""
    
    @staticmethod
    def get_all_tools() -> List[Dict]:
        """Get all available tools in OpenAI function format"""
        return [
            {
                "type": "function",
                "function": {
                    "name": "search_legal_documents",
                    "description": "Search the legal library for case law, founding documents, amendments. Searches across Supreme Court cases, Constitution, Bill of Rights, and precedent.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query (keywords, case names, etc.)"
                            },
                            "category": {
                                "type": "string",
                                "enum": ["supreme_court", "founding_documents", "amendments", "bill_of_rights", "precedent", "all"],
                                "description": "Document category to search in"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Max results to return (default: 10, max: 50)",
                                "default": 10
                            },
                            "year_from": {
                                "type": "integer",
                                "description": "Filter by year from (for historical searches)"
                            },
                            "year_to": {
                                "type": "integer",
                                "description": "Filter by year to"
                            }
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_case_details",
                    "description": "Get full details of a specific legal case including opinion, justices, holdings, and related cases",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "case_id": {
                                "type": "string",
                                "description": "Case ID or name (e.g., 'roe-v-wade', 'marbury-v-madison')"
                            }
                        },
                        "required": ["case_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "search_cases",
                    "description": "Search for legal cases with advanced filters (justices, date range, topics, precedent)",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "keywords": {
                                "type": "string",
                                "description": "Search keywords"
                            },
                            "justices": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Filter by justice names (e.g., ['Marshall', 'Brennan'])"
                            },
                            "date_from": {
                                "type": "string",
                                "description": "Start date (YYYY-MM-DD)"
                            },
                            "date_to": {
                                "type": "string",
                                "description": "End date (YYYY-MM-DD)"
                            },
                            "topics": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Legal topics to filter by"
                            }
                        },
                        "required": ["keywords"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_case_management_info",
                    "description": "Get information about a specific e-discovery case including parties, evidence, and status",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "case_id": {
                                "type": "string",
                                "description": "E-discovery case ID"
                            }
                        },
                        "required": ["case_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_evidence_items",
                    "description": "Get evidence items in a case with chain of custody and privilege information",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "case_id": {
                                "type": "string",
                                "description": "E-discovery case ID"
                            },
                            "evidence_type": {
                                "type": "string",
                                "enum": ["document", "video", "audio", "image", "chat", "email", "all"],
                                "description": "Filter by evidence type"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Max results to return",
                                "default": 20
                            }
                        },
                        "required": ["case_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "search_evidence",
                    "description": "Search evidence items across cases",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query"
                            },
                            "case_id": {
                                "type": "string",
                                "description": "Optional: search within specific case"
                            },
                            "date_from": {
                                "type": "string",
                                "description": "Start date (YYYY-MM-DD)"
                            },
                            "date_to": {
                                "type": "string",
                                "description": "End date (YYYY-MM-DD)"
                            }
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "check_privilege",
                    "description": "Check privilege status of evidence items (attorney-client, work product, etc.)",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "evidence_id": {
                                "type": "string",
                                "description": "Evidence item ID"
                            }
                        },
                        "required": ["evidence_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "upload_media",
                    "description": "Initiate media upload (video, PDF, images) for analysis and processing",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_type": {
                                "type": "string",
                                "enum": ["video", "pdf", "image", "audio", "document"],
                                "description": "Type of media to upload"
                            },
                            "description": {
                                "type": "string",
                                "description": "Description of the media"
                            },
                            "case_id": {
                                "type": "string",
                                "description": "Optional: associate with e-discovery case"
                            }
                        },
                        "required": ["file_type", "description"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_media_processing_status",
                    "description": "Check status of media processing jobs (transcription, OCR, analysis)",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "process_id": {
                                "type": "string",
                                "description": "Media processing job ID"
                            }
                        },
                        "required": ["process_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "analyze_document",
                    "description": "Analyze a document (extract text via OCR, identify key sections, legal terms)",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "evidence_id": {
                                "type": "string",
                                "description": "Evidence item ID (document)"
                            },
                            "analysis_type": {
                                "type": "string",
                                "enum": ["full_text", "key_sections", "legal_terms", "entities", "summary"],
                                "description": "Type of analysis"
                            }
                        },
                        "required": ["evidence_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "create_case_collection",
                    "description": "Create a collection to group related documents and evidence",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "Collection name"
                            },
                            "case_id": {
                                "type": "string",
                                "description": "E-discovery case ID"
                            },
                            "description": {
                                "type": "string",
                                "description": "Collection description"
                            }
                        },
                        "required": ["name", "case_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_statistics",
                    "description": "Get statistics about legal library and case management (document counts, coverage, etc.)",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "stat_type": {
                                "type": "string",
                                "enum": ["legal_library", "cases", "evidence", "media", "all"],
                                "description": "Type of statistics"
                            }
                        }
                    }
                }
            }
        ]
    
    @staticmethod
    def get_tool_descriptions() -> Dict[str, str]:
        """Get simple descriptions of all tools"""
        return {
            "search_legal_documents": "Search Supreme Court cases, founding documents, and legal precedent",
            "get_case_details": "Get detailed information about a specific legal case",
            "search_cases": "Advanced search for cases by justice, date, or topic",
            "get_case_management_info": "Get e-discovery case information",
            "get_evidence_items": "Retrieve evidence items with chain of custody",
            "search_evidence": "Search evidence across cases",
            "check_privilege": "Check attorney-client privilege and work product status",
            "upload_media": "Upload and process media files",
            "get_media_processing_status": "Check media processing job status",
            "analyze_document": "Analyze documents (OCR, key sections, legal terms)",
            "create_case_collection": "Create collections for organizing evidence",
            "get_statistics": "Get statistics about the legal library and cases",
        }


def register_tool_executor(name: str, executor: Callable) -> None:
    """
    Register a tool executor function
    
    Args:
        name: Tool name
        executor: Function that executes the tool
    """
    TOOL_REGISTRY[name] = executor
    print(f"Registered tool executor: {name}")


def get_tool_executor(name: str) -> Optional[Callable]:
    """Get executor for a tool by name"""
    return TOOL_REGISTRY.get(name)


def execute_tool(name: str, **kwargs) -> Dict[str, Any]:
    """
    Execute a tool by name
    
    Args:
        name: Tool name
        **kwargs: Tool arguments
        
    Returns:
        Tool result dict
    """
    executor = get_tool_executor(name)
    
    if not executor:
        return {
            'success': False,
            'error': f"Unknown tool: {name}"
        }
    
    try:
        result = executor(**kwargs)
        return {
            'success': True,
            'result': result
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }
