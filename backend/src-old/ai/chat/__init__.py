"""
Enhanced Chat Module - AI Assistant with Memory & References

Provides comprehensive chat functionality with:
- Persistent conversation memory
- Document reference tracking
- Citation-based retrieval
- Accessibility features
"""

from .enhanced_assistant import EnhancedChatAssistant
from .memory_store import ConversationMemoryStore
from .reference_manager import ReferenceManager

__all__ = [
    "EnhancedChatAssistant",
    "ConversationMemoryStore",
    "ReferenceManager",
]
