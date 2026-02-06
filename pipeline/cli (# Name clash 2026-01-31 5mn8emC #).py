# Copyright © 2024–2026 Faith Frontier Ecclesiastical Trust. All rights reserved.
# PROPRIETARY — See LICENSE.

"""Legal Retrieval Pipeline CLI"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from citation_service import CitationService
from legal_library_adapter import LegalLibraryAdapter
from retrieval_service import RetrievalService


def cmd_retrieve(args):
    """Retrieve passages for a query"""
    service = RetrievalService()

    filters = {}
    if args.source:
        filters["source_system"] = args.source

    passages = service.retrieve(query=args.query, filters=filters, top_k=args.top)

    print(f"\n=== Retrieved {len(passages)} passages ===\n")

    for idx, passage in enumerate(passages, 1):
        print(f"[{idx}] Score: {passage.score:.4f}")
        print(f"    Document: {passage.filename}")
        print(f"    Page: {passage.page_number}")
        print(f"    Source: {passage.source_system}")
        print(f"    Snippet: {passage.snippet[:200]}")
        print()

    if args.json:
        print(json.dumps([p.to_dict() for p in passages], indent=2))


def main():
    parser = argparse.ArgumentParser(description="Legal Retrieval Pipeline CLI")
    subparsers = parser.add_subparsers(dest="command")

    retrieve_parser = subparsers.add_parser("retrieve")
    retrieve_parser.add_argument("query")
    retrieve_parser.add_argument("--top", type=int, default=5)
    retrieve_parser.add_argument("--source")
    retrieve_parser.add_argument("--json", action="store_true")

    args = parser.parse_args()

    if args.command == "retrieve":
        cmd_retrieve(args)


if __name__ == "__main__":
    main()
