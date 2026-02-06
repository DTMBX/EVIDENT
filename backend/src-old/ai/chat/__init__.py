# Copyright © 2024–2026 Faith Frontier Ecclesiastical Trust. All rights reserved.
# PROPRIETARY — See LICENSE.

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
