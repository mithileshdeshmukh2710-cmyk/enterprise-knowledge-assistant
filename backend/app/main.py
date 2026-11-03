import logging
import os
import re
import tempfile
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, UploadFile, File, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, ConfigDict
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.document_service import DocumentService
from app.rag_service import RAGService

logger = logging.getLogger(__name__)


app = FastAPI(
    title="Enterprise Knowledge Assistant",
    description="AI-powered document question answering system",
    version="1.0.0"
)

limiter = Limiter(key_func=get_remote_address)

app.state.limiter = limiter

app.add_exception_handler(
    RateLimitExceeded,
    _rate_limit_exceeded_handler
)

allowed_origins = [
    "http://localhost:5173",
    os.getenv("FRONTEND_URL", "")
]
allowed_origins = [
    origin for origin in allowed_origins if origin
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Initialize service only when first needed
rag_service = None


def get_rag_service():

    global rag_service

    if rag_service is None:
        rag_service = RAGService()

    return rag_service


document_service = None


def get_document_service():
    global document_service

    if document_service is None:
        document_service = DocumentService()

    return document_service


class QuestionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question: str = Field(min_length=1, max_length=2000)
    top_k: int = Field(default=3, ge=1, le=10)
    history: list[ChatMessage] = Field(
        default_factory=list,
        max_length=10
    )

class ChatMessage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=2000)


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


@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):

    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are allowed."
        )

    original_filename = Path(file.filename).name
    if not re.fullmatch(
        r"[A-Za-z0-9][A-Za-z0-9._ -]{0,99}\.pdf",
        original_filename,
        flags=re.IGNORECASE
    ):
        raise HTTPException(
            status_code=400,
            detail="Invalid PDF filename."
        )

    content = await file.read()

    if not content:
        raise HTTPException(
            status_code=400,
            detail="The uploaded file is empty."
        )

    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail="File size must be 10 MB or less."
        )

    if not content.startswith(b"%PDF-"):
        raise HTTPException(
            status_code=400,
            detail="The uploaded file is not a valid PDF."
        )

    temp_path = None

    try:
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".pdf"
        ) as temp_file:

            temp_file.write(content)
            temp_path = temp_file.name

        result = get_document_service().index_pdf(
            temp_path,
            original_filename
        )

        return {
            "message": "PDF indexed successfully.",
            **result
        }

    except ValueError as error:
        logger.warning("PDF processing validation error: %s", error)
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    except Exception:
        logger.exception("Failed to process and index the PDF")
        raise HTTPException(
            status_code=500,
            detail="Failed to process and index the PDF."
        )

    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)


@app.post("/ask")
@limiter.limit("10/minute")
def ask_question(request: Request, body: QuestionRequest):

    try:

        service = get_rag_service()

        history = [
            message.model_dump()
            for message in body.history
        ]

        result = service.ask_question(
            body.question,
            body.top_k,
            history
        )

        return result

    except Exception:
        logger.exception("Question answering failed")
        raise HTTPException(
            status_code=500,
            detail="Unable to process your question. Please try again."
        )

@app.get("/documents")
def get_documents():
    try:
        service = get_document_service()

        documents = service.vector_store.list_sources()

        return {
            "total_documents": len(documents),
            "documents": documents
        }

    except Exception:
        logger.exception("Failed to retrieve documents")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve documents."
        )

@app.delete("/documents/{filename}")
def delete_document(filename: str):
    try:
        service = get_document_service()

        existing = service.vector_store.list_sources()

        if not any(
            doc["filename"] == filename
            for doc in existing
        ):
            raise HTTPException(
                status_code=404,
                detail="Document not found."
            )

        service.vector_store.delete_source(filename)

        return {
            "message": "Document deleted successfully.",
            "filename": filename
        }

    except HTTPException:
        raise

    except Exception:
        logger.exception("Failed to delete document")
        raise HTTPException(
            status_code=500,
            detail="Failed to delete document."
        )
