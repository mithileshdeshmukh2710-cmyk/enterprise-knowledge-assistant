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
    print("TEST 1: Compare the same document twice (Should return HTTP 400)")
    print("=" * 80)
    r1 = client.post("/compare", json={
        "document_a": "company_policy.pdf",
        "document_b": "company_policy.pdf",
        "question": "Compare these."
    })
    print(f"Status: {r1.status_code}")
    print(f"Response: {r1.json()}")
    assert r1.status_code == 400

    print("\n" + "=" * 80)
    print("TEST 2: Compare with nonexistent document (Should return HTTP 404)")
    print("=" * 80)
    r2 = client.post("/compare", json={
        "document_a": "company_policy.pdf",
        "document_b": "nonexistent_file.pdf",
        "question": "Compare these."
    })
    print(f"Status: {r2.status_code}")
    print(f"Response: {r2.json()}")
    assert r2.status_code == 404

    print("\n" + "=" * 80)
    print("TEST 3: Compare company_policy.pdf and DWM_MiniProject_Report.pdf (Should return HTTP 200)")
    print("=" * 80)
    r3 = client.post("/compare", json={
        "document_a": "company_policy.pdf",
        "document_b": "DWM_MiniProject_Report.pdf",
        "question": "Compare the purpose, structure, methodology, and key information in these documents."
    })
    print(f"Status: {r3.status_code}")
    data = r3.json()
    print(f"Document A: {data.get('document_a')} (Pages: {data.get('pages_document_a')})")
    print(f"Document B: {data.get('document_b')} (Pages: {data.get('pages_document_b')})")
    print("\nComparison Output:\n")
    print(data.get("comparison"))

if __name__ == "__main__":
    main()

