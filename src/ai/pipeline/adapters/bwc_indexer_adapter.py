"""
BWC Indexer Adapter - Wraps existing barber-cam/py/bwc_index.py system

Responsibilities:
1. Mirror BWC-indexed pages into main database
2. Preserve BWC's own database (.bwc/index.db)
3. Enable unified retrieval across BWC + legal library
4. Maintain BWC's repair/OCR logic
"""

import logging

logger = logging.getLogger(__name__)


class BWCIndexerAdapter:
    """
    Adapter for BWC evidence indexer system

    The BWC indexer is already well-designed with:
    - SHA-256 hashing
    - PDF repair pipeline
    - OCR for thin text
    - FTS5 search

    This adapter doesn't replace it; it mirrors its results
    into the main app database for unified retrieval.
    """

    def __init__(self, orchestrator):
        self.orchestrator = orchestrator
        logger.info("BWCIndexerAdapter initialized")

    def sync_evidence(self, bwc_evidence_id: int):
        """
        Sync BWC evidence into unified pipeline

        Steps:
        1. Load evidence_item from .bwc/index.db
        2. Check if already synced
        3. If not synced:
           a. Call orchestrator.ingest_document() with original path
           b. Load pdf_pages from BWC DB
           c. Mirror pages into main DB (document_pages)
           d. Update document_fts with BWC page text
        4. Store mapping: evidence_items.id -> documents.id

        Args:
            bwc_evidence_id: ID from .bwc/index.db evidence_items table
        """
        logger.info(f"Syncing BWC evidence_id={bwc_evidence_id}")

        # TODO: Implement
        # 1. Connect to .bwc/index.db
        # 2. Load evidence_item + pdf_pages
        # 3. Call orchestrator to sync into main DB
        # 4. Store cross-reference

        raise NotImplementedError("sync_evidence() - coming in next commit")
