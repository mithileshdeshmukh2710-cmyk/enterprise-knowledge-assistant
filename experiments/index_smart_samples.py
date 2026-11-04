import os
import sys
from pathlib import Path
from unittest.mock import MagicMock

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir / "backend"))

from app.document_service import DocumentService

def main():
    service = DocumentService()
    # Mock Gemini summarization so indexing is instant and offline
    service.gemini.generate_document_summary = MagicMock(return_value="Automated sample summary")
    
    for filename in ["company_policy_v1.pdf", "company_policy_v2.pdf"]:
        pdf_path = root_dir / "sample_documents" / filename
        print(f"Indexing {filename}...")
        result = service.index_pdf(str(pdf_path), filename)
        print(f"Result for {filename}: pages={result['pages']}, chunks={result['chunks_indexed']}")
        
    print("\nRetrieving chunks for both:")
    chunks_a = service.vector_store.get_source_content("company_policy_v1.pdf")
    chunks_b = service.vector_store.get_source_content("company_policy_v2.pdf")
    
    print(f"Chunks A: {len(chunks_a)}")
    print(f"Chunks B: {len(chunks_b)}")
    
    from app.main import build_visual_diff
    diff = build_visual_diff(chunks_a, chunks_b)
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    
    print("\nVisual Diff Total Items:", diff["total_items"])
    for idx, item in enumerate(diff["items"], 1):
        print(f"{idx}. [{item['type'].upper()}] - {item['location']}")
        if item["type"] == "modified":
            print(f"   OLD: {item['old_text']}")
            print(f"   NEW: {item['new_text']}")
            print(f"   Similarity: {item.get('similarity')}")
        else:
            print(f"   Text: {item.get('text')}")

if __name__ == "__main__":
    main()
