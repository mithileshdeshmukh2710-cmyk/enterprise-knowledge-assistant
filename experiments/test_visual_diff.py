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
    print("TEST: Compare company_policy.pdf vs company_policy_v2.pdf")
    print("=" * 80)

    resp = client.post("/compare", json={
        "document_a": "company_policy.pdf",
        "document_b": "company_policy_v2.pdf",
        "question": "What policies changed between version 1 and version 2?"
    })

    print(f"Status: {resp.status_code}")
    data = resp.json()
    print(f"Document A: {data.get('document_a')}")
    print(f"Document B: {data.get('document_b')}")
    print(f"Visual Diff Total Items: {data.get('visual_diff_total')}")
    print(f"Visual Diff Truncated: {data.get('visual_diff_truncated')}")

    diff_items = data.get("visual_diff", [])
    added = [d for d in diff_items if d["type"] == "added"]
    removed = [d for d in diff_items if d["type"] == "removed"]
    unchanged = [d for d in diff_items if d["type"] == "unchanged"]

    print(f"\nDiff Counts: + {len(added)} added, - {len(removed)} removed, {len(unchanged)} unchanged")

    print("\nVisual Diff Sample Items:")
    for item in diff_items:
        prefix = "+" if item["type"] == "added" else ("-" if item["type"] == "removed" else "=")
        print(f"  [{prefix}] ({item['type'].upper()}) {item['location']}: {item['text']}")

    print("\nGemini Comparison Summary:")
    print(data.get("comparison")[:500] + "...")

if __name__ == "__main__":
    main()

