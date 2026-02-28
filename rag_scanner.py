# rag_scanner.py - Custom RAG Readiness Scanner for your Evident repo
import os
import sys
from pathlib import Path
from collections import defaultdict
import json

# Your existing deps
from unstructured.partition.auto import partition  # PDFs, docs, etc.
from dedupe import Dedupe  # near-dupe detection
import spacy  # entity extraction, quality check
from sentence_transformers import SentenceTransformer
from rapidfuzz import fuzz, process
import chromadb  # quick embed test storage

nlp = spacy.load("en_core_web_sm", disable=["ner", "parser"])  # fast mode
embedder = SentenceTransformer("all-MiniLM-L6-v2")  # lightweight
chroma_client = chromadb.Client()  # in-memory for scan

def scan_repo(root_dir: str, extensions=(".pdf", ".txt", ".md", ".py", ".docx", ".mp4")):
    report = {"issues": [], "stats": defaultdict(int), "duplicates": []}
    files = []

    for path in Path(root_dir).rglob("*"):
        if path.is_file() and path.suffix.lower() in extensions:
            files.append(str(path))

    report["stats"]["total_files"] = len(files)
    print(f"Scanning {len(files)} files...")

    # Simple dedupe setup (train on filenames/content snippets)
    fields = [{'field': 'content', 'type': 'String'}]
    deduper = Dedupe(fields)
    # For real use: train once on sample data; here we do fuzzy + embed sim

    for file_path in files:
        try:
            size_mb = os.path.getsize(file_path) / (1024 ** 2)
            report["stats"]["total_size_mb"] += size_mb

            if size_mb > 50:
                report["issues"].append({"file": file_path, "issue": f"Large file ({size_mb:.1f} MB) - may choke ingestion"})

            # Extract text (unstructured handles most)
            elements = partition(filename=file_path, strategy="auto")
            text = " ".join(str(el) for el in elements if hasattr(el, 'text'))
            chunk_preview = text[:500]  # first bit

            # Quality checks
            doc = nlp(chunk_preview)
            if len(doc) < 20:
                report["issues"].append({"file": file_path, "issue": "Very short/empty content - poor for RAG"})

            # Embed test
            emb = embedder.encode(chunk_preview)
            collection = chroma_client.get_or_create_collection("scan_test")
            collection.add(documents=[chunk_preview], ids=[file_path], embeddings=[emb.tolist()])

            # Fuzzy dupe check (simple rapidfuzz on preview)
            if report["duplicates"]:
                matches = process.extract(chunk_preview, [d["preview"] for d in report["duplicates"]], scorer=fuzz.token_sort_ratio, limit=1)
                if matches and matches[0][1] > 85:
                    report["duplicates"].append({"file": file_path, "similar_to": matches[0][2], "score": matches[0][1]})

            report["duplicates"].append({"file": file_path, "preview": chunk_preview[:200]})

        except Exception as e:
            report["issues"].append({"file": file_path, "issue": f"Parse failed: {str(e)}"})

    # Final stats
    report["stats"]["unique_embeddings_tested"] = len(chroma_client.get_or_create_collection("scan_test").get()["ids"])

    return report


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python rag_scanner.py /path/to/your/repo")
        sys.exit(1)

    root = sys.argv[1]
    results = scan_repo(root)
    with open("rag_scan_report.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print("\nScan complete. Report saved: rag_scan_report.json")
    print(f"Issues found: {len(results['issues'])}")
    print(f"Files scanned: {results['stats']['total_files']}")