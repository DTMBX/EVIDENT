"""
Legal Library Adapter - Wraps existing legal_library.py system

Responsibilities:
1. Sync legal_documents into unified pipeline
2. Split full_text into pages (or pseudo-pages)
3. Route searches through unified retrieval
4. Preserve existing API for backward compatibility
"""

import logging

logger = logging.getLogger(__name__)


class LegalLibraryAdapter:
    """
    Adapter for legacy legal_library.py system

    Wraps existing code without breaking it.
    """

    def __init__(self, orchestrator):
        self.orchestrator = orchestrator
        logger.info("LegalLibraryAdapter initialized")

    def sync_document(self, legal_doc_id: int):
        """
        Sync a document from legal_documents table into unified pipeline

        Steps:
        1. Load LegalDocument by ID
        2. Check if already synced (by sha256 or citation)
        3. If not synced:
           a. Save full_text to temp file
           b. Call orchestrator.ingest_document()
           c. Split text into pseudo-pages
           d. Call orchestrator.extract_document() with pre-split pages
           e. Call orchestrator.index_document()
        4. Store mapping: legal_documents.id -> documents.id

        Args:
            legal_doc_id: ID from legal_documents table
        """
        logger.info(f"Syncing legal_library doc_id={legal_doc_id}")

        # TODO: Implement
        # 1. from legal_library import LegalDocument
        # 2. doc = LegalDocument.query.get(legal_doc_id)
        # 3. Create temp file with full_text
        # 4. Call orchestrator to ingest/extract/index
        # 5. Update legal_documents.unified_doc_id = result.doc_id

        raise NotImplementedError("sync_document() - coming in next commit")
