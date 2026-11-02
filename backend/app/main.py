from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.rag_service import RAGService


app = FastAPI(
    title="Enterprise Knowledge Assistant",
    description="AI-powered document question answering system",
    version="1.0.0"
)


# Initialize service only when first needed
rag_service = None


def get_rag_service():

    global rag_service

    if rag_service is None:
        rag_service = RAGService()

    return rag_service


class QuestionRequest(BaseModel):

    question: str = Field(
        min_length=1,
        max_length=2000
    )

    top_k: int = Field(
        default=3,
        ge=1,
        le=10
    )


@app.get("/")
def home():

    return {
        "message": "Welcome to Enterprise Knowledge Assistant",
        "status": "running"
    }


@app.get("/health")
def health_check():

    return {
        "status": "healthy"
    }


@app.post("/ask")
def ask_question(request: QuestionRequest):

    try:

        rag = get_rag_service()

        result = rag.ask_question(
            question=request.question.strip(),
            top_k=request.top_k
        )

        return result

    except Exception:

        raise HTTPException(
            status_code=502,
            detail="Unable to generate an answer. Please try again."
        )