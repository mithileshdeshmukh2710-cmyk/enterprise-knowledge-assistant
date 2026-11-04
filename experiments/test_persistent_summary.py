import sys
import json
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir / "backend"))

from starlette.testclient import TestClient
from app.main import app

def main():
    client = TestClient(app)

    print("=" * 80)
    print("STEP 1: UPLOAD company_policy.pdf")
    print("=" * 80)
    pdf_path = root_dir / "sample_documents" / "company_policy.pdf"
    with open(pdf_path, "rb") as f:
        upload_resp = client.post(
            "/upload",
            files={"file": ("company_policy.pdf", f, "application/pdf")}
        )
    print(f"Upload Status Code: {upload_resp.status_code}")
    upload_data = upload_resp.json()
    print(f"Upload Result: chunks_indexed={upload_data.get('chunks_indexed')}, summary_status={upload_data.get('summary_status')}")

    print("\n" + "=" * 80)
    print("STEP 2: GET /documents")
    print("=" * 80)
    docs_resp = client.get("/documents")
    print(f"Status Code: {docs_resp.status_code}")
    print(json.dumps(docs_resp.json(), indent=2))

    print("\n" + "=" * 80)
    print("STEP 3: GET /documents/company_policy.pdf/summary")
    print("=" * 80)
    summary_resp = client.get("/documents/company_policy.pdf/summary")
    print(f"Status Code: {summary_resp.status_code}")
    print(json.dumps(summary_resp.json(), indent=2))

    print("\n" + "=" * 80)
    print("STEP 4: VERIFY FILE PERSISTENCE data/document_metadata.json")
    print("=" * 80)
    metadata_file = root_dir / "data" / "document_metadata.json"
    print(f"File exists: {metadata_file.exists()}")
    if metadata_file.exists():
        with open(metadata_file, "r", encoding="utf-8") as f:
            content = json.load(f)
            print(f"Entries in file: {list(content.keys())}")
            entry = content.get("company_policy.pdf", {})
            print(f"Saved Status: {entry.get('summary_status')}")
            print(f"Updated At: {entry.get('updated_at')}")

if __name__ == "__main__":
    main()

