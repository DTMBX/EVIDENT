# Copyright © 2024–2026 Faith Frontier Ecclesiastical Trust. All rights reserved.
# PROPRIETARY — See LICENSE.

"""Pipeline adapters for legacy systems"""

from .bwc_indexer_adapter import BWCIndexerAdapter
from .legal_library_adapter import LegalLibraryAdapter
from .pdf_discovery_adapter import PDFDiscoveryAdapter

__all__ = [
    "LegalLibraryAdapter",
    "BWCIndexerAdapter",
    "PDFDiscoveryAdapter",
]
