from backend.app.rag_service import RAGService


def main():

    rag = RAGService()

    while True:

        question = input(
            "\nAsk a question (or type exit): "
        )

        if question.lower() == "exit":
            break

        if not question.strip():
            print("Please enter a question.")
            continue

        try:

            result = rag.ask_question(question)

            print("\nAI ANSWER:")
            print(result["answer"])

            print("\nSOURCES:")

            for source in result["sources"]:

                print(
                    f"- {source['source']}, "
                    f"Page {source['page']}"
                )

        except Exception as error:

            print("Error:", error)


if __name__ == "__main__":
    main()