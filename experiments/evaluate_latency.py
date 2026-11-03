import time

from backend.app.rag_service import RAGService


QUESTIONS = [
    "How many days can employees work remotely?",
    "Who approves annual leave?",
    "What health insurance benefits are available?",
]


def evaluate_latency():

    service = RAGService()
    latencies = []

    for question in QUESTIONS:

        start = time.perf_counter()

        result = service.ask_question(
            question,
            top_k=3
        )

        end = time.perf_counter()

        latency = end - start
        latencies.append(latency)

        print(f"\nQuestion: {question}")
        print(f"Answer: {result['answer']}")
        print(f"Latency: {latency:.2f} seconds")

    average_latency = sum(latencies) / len(latencies)

    print("\n========== LATENCY RESULTS ==========")
    print(f"Average latency: {average_latency:.2f} seconds")
    print(f"Minimum latency: {min(latencies):.2f} seconds")
    print(f"Maximum latency: {max(latencies):.2f} seconds")


if __name__ == "__main__":
    evaluate_latency()