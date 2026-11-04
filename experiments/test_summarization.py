import sys
import json
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir / "backend"))

from app.document_service import DocumentService

def main():
    service = DocumentService()
    pdf_path = root_dir / "sample_documents" / "company_policy.pdf"
    print(f"Indexing {pdf_path}...")
    result = service.index_pdf(str(pdf_path), "company_policy.pdf")
    print("\nRESULT:")
    print("=" * 60)
    for k, v in result.items():
        if k == "summary":
            print(f"{k}:\n{v}")
        else:
            print(f"{k}: {v}")

if __name__ == "__main__":
    main()

