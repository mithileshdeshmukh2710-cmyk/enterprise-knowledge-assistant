import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv

# Ensure backend is on sys.path
backend_path = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_path))

load_dotenv(backend_path / ".env")

from app.rag_service import RAGService

TEST_QUESTIONS = [
    "Find the exact term manager approval",
    "Who gives permission for working remotely?",
    "What medical coverage does the company provide?",
    "Does the company provide maternity leave?",
]

def main():
    rag = RAGService()
    print("=" * 80)
    print("TESTING RAG SERVICE WITH HYBRID SEARCH")
    print("=" * 80)

    for i, q in enumerate(TEST_QUESTIONS, start=1):
        print(f"\n[{i}/6] Question: {q}")
        response = None
        for attempt in range(4):
            try:
                response = rag.ask_question(q)
                break
            except Exception as e:
                print(f"  Attempt {attempt + 1} encountered: {e}. Retrying in 3s...")
                time.sleep(3)
        if response:
            print(f"Answer: {response['answer']}")
            print(f"Sources: {response['sources']}")
        else:
            print("Failed to get answer after retries.")
        print("-" * 80)
        time.sleep(1)

if __name__ == "__main__":
    main()

