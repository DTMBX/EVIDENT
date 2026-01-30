"""Pipeline adapters for legacy systems"""

from .bwc_indexer_adapter import BWCIndexerAdapter
from .legal_library_adapter import LegalLibraryAdapter
from .pdf_discovery_adapter import PDFDiscoveryAdapter

__all__ = [
    "LegalLibraryAdapter",
    "BWCIndexerAdapter",
    "PDFDiscoveryAdapter",
]
