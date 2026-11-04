from __future__ import annotations

import logging
import os
import re
import tempfile
from difflib import SequenceMatcher
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, UploadFile, File, Request, Depends, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field, ConfigDict
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

try:
    from app.document_service import DocumentService
    from app.rag_service import RAGService
    from app.gemini_client import GeminiClient
except ImportError:
    from backend.app.document_service import DocumentService
    from backend.app.rag_service import RAGService
    from backend.app.gemini_client import GeminiClient

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
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://localhost:4173",
]
frontend_env = os.getenv("FRONTEND_URL", "")
if frontend_env:
    for origin in frontend_env.split(","):
        trimmed = origin.strip()
        if trimmed and trimmed not in allowed_origins:
            allowed_origins.append(trimmed)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Optional API Key Authentication
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def verify_api_key(api_key: str = Security(api_key_header)) -> bool:
    required_key = os.getenv("APP_API_KEY", "").strip()
    if not required_key:
        return True  # Open dev mode if no key configured
    if api_key != required_key:
        raise HTTPException(
            status_code=401,
            detail="Unauthorized: invalid or missing API key."
        )
    return True


def validate_pdf_filename(filename: str) -> str:
    if not filename:
        raise HTTPException(
            status_code=400,
            detail="Filename cannot be empty."
        )
    if "/" in filename or "\\" in filename or ".." in filename:
        raise HTTPException(
            status_code=400,
            detail="Invalid PDF filename: path traversal is not allowed."
        )
    cleaned = Path(filename).name
    if not re.fullmatch(
        r"[A-Za-z0-9][A-Za-z0-9._ -]{0,99}\.pdf",
        cleaned,
        flags=re.IGNORECASE
    ):
        raise HTTPException(
            status_code=400,
            detail="Invalid PDF filename."
        )
    return cleaned


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


class ChatMessage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=2000)


class QuestionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question: str = Field(min_length=1, max_length=2000)
    top_k: int = Field(default=3, ge=1, le=10)
    history: list[ChatMessage] = Field(
        default_factory=list,
        max_length=10
    )


class DocumentComparisonRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document_a: str = Field(min_length=1, max_length=100)
    document_b: str = Field(min_length=1, max_length=100)
    question: str = Field(
        default="Compare these documents and identify their major differences.",
        max_length=1000
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


def validate_upload_content(filename: str, content: bytes) -> str:
    if not filename or not filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are allowed."
        )

    original_filename = validate_pdf_filename(filename)

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

    return original_filename


@app.post("/upload")
@limiter.limit("5/minute")
async def upload_pdf(
    request: Request,
    file: UploadFile = File(...),
    authenticated: bool = Depends(verify_api_key)
):
    content = await file.read()
    original_filename = validate_upload_content(file.filename, content)

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


def build_visual_diff(chunks_a, chunks_b, max_items=100, similarity_threshold=0.60):
    """Compare sentences and identify additions, removals, modifications and unchanged content."""
    def extract_sentences(chunks):
        sentences = []
        for chunk in sorted(
            chunks,
            key=lambda item: (item["page"], item["chunk"])
        ):
            parts = re.split(
                r"(?<=[.!?])\s+|\n+",
                chunk["text"]
            )
            for part in parts:
                text = " ".join(part.split())
                if not text or not re.search(r"\w", text):
                    continue
                normalized = text.casefold()
                # Remove adjacent duplicate sentences caused by chunk overlap.
                if (
                    sentences
                    and sentences[-1]["normalized"] == normalized
                ):
                    continue
                sentences.append({
                    "text": text,
                    "normalized": normalized,
                    "page": chunk["page"]
                })
        return sentences

    a = extract_sentences(chunks_a)
    b = extract_sentences(chunks_b)

    a_norm = [item["normalized"] for item in a]
    b_norm = [item["normalized"] for item in b]

    matcher = SequenceMatcher(None, a_norm, b_norm)
    diff_items = []

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            for idx_a, idx_b in zip(range(i1, i2), range(j1, j2)):
                page_a = a[idx_a]["page"]
                page_b = b[idx_b]["page"]
                page_label = f"Pages {page_a}/{page_b}" if page_a != page_b else f"Page {page_a}"
                diff_items.append({
                    "type": "unchanged",
                    "text": b[idx_b]["text"],
                    "old_text": a[idx_a]["text"],
                    "new_text": b[idx_b]["text"],
                    "text_a": a[idx_a]["text"],
                    "text_b": b[idx_b]["text"],
                    "page": page_b,
                    "page_a": page_a,
                    "page_b": page_b,
                    "location": f"Document A/B · {page_label}"
                })
        elif tag == "delete":
            for idx in range(i1, i2):
                diff_items.append({
                    "type": "removed",
                    "text": a[idx]["text"],
                    "old_text": a[idx]["text"],
                    "text_a": a[idx]["text"],
                    "page": a[idx]["page"],
                    "page_a": a[idx]["page"],
                    "location": f"Document A · Page {a[idx]['page']}"
                })
        elif tag == "insert":
            for idx in range(j1, j2):
                diff_items.append({
                    "type": "added",
                    "text": b[idx]["text"],
                    "new_text": b[idx]["text"],
                    "text_b": b[idx]["text"],
                    "page": b[idx]["page"],
                    "page_b": b[idx]["page"],
                    "location": f"Document B · Page {b[idx]["page"]}"
                })
        elif tag == "replace":
            used_a = set()
            used_b = set()

            # Identify candidates for modified content using similarity threshold
            candidates = []
            for idx_a in range(i1, i2):
                for idx_b in range(j1, j2):
                    sim = SequenceMatcher(
                        None,
                        a[idx_a]["normalized"],
                        b[idx_b]["normalized"]
                    ).ratio()
                    if sim >= similarity_threshold:
                        candidates.append((sim, idx_a, idx_b))

            # Greedy match by highest similarity first
            candidates.sort(key=lambda item: item[0], reverse=True)
            matched_a_to_b = {}
            for sim, idx_a, idx_b in candidates:
                if idx_a not in used_a and idx_b not in used_b:
                    used_a.add(idx_a)
                    used_b.add(idx_b)
                    matched_a_to_b[idx_a] = (idx_b, sim)

            for idx_a in range(i1, i2):
                if idx_a in matched_a_to_b:
                    idx_b, sim = matched_a_to_b[idx_a]
                    page_a = a[idx_a]["page"]
                    page_b = b[idx_b]["page"]
                    diff_items.append({
                        "type": "modified",
                        "text": b[idx_b]["text"],
                        "old_text": a[idx_a]["text"],
                        "new_text": b[idx_b]["text"],
                        "text_a": a[idx_a]["text"],
                        "text_b": b[idx_b]["text"],
                        "page_a": page_a,
                        "page_b": page_b,
                        "similarity": round(sim, 2),
                        "location": f"Doc A (p. {page_a}) -> Doc B (p. {page_b})"
                    })
                else:
                    diff_items.append({
                        "type": "removed",
                        "text": a[idx_a]["text"],
                        "old_text": a[idx_a]["text"],
                        "text_a": a[idx_a]["text"],
                        "page": a[idx_a]["page"],
                        "page_a": a[idx_a]["page"],
                        "location": f"Document A · Page {a[idx_a]['page']}"
                    })

            for idx_b in range(j1, j2):
                if idx_b not in used_b:
                    diff_items.append({
                        "type": "added",
                        "text": b[idx_b]["text"],
                        "new_text": b[idx_b]["text"],
                        "text_b": b[idx_b]["text"],
                        "page": b[idx_b]["page"],
                        "page_b": b[idx_b]["page"],
                        "location": f"Document B · Page {b[idx_b]["page"]}"
                    })

    total_items = len(diff_items)
    truncated = total_items > max_items
    items = diff_items[:max_items]

    return {
        "items": items,
        "total_items": total_items,
        "truncated": truncated
    }


@app.post("/compare")
@limiter.limit("5/minute")
def compare_documents(
    request: Request,
    body: DocumentComparisonRequest
):
    try:
        doc_a = validate_pdf_filename(body.document_a)
        doc_b = validate_pdf_filename(body.document_b)

        if doc_a == doc_b:
            raise HTTPException(
                status_code=400,
                detail="Please select two different documents."
            )

        service = get_document_service()

        # Retrieve complete indexed content for both documents.
        chunks_a = service.vector_store.get_source_content(doc_a)
        chunks_b = service.vector_store.get_source_content(doc_b)

        if not chunks_a:
            raise HTTPException(
                status_code=404,
                detail=f"Document not found: {doc_a}"
            )

        if not chunks_b:
            raise HTTPException(
                status_code=404,
                detail=f"Document not found: {doc_b}"
            )

        text_a = "\n\n".join([f"[Page {c['page']}] {c['text']}" for c in chunks_a])
        text_b = "\n\n".join([f"[Page {c['page']}] {c['text']}" for c in chunks_b])

        pages_a = len(set(c["page"] for c in chunks_a))
        pages_b = len(set(c["page"] for c in chunks_b))

        gemini_client = GeminiClient()
        comparison_result = gemini_client.compare_documents(
            document_a=text_a,
            document_b=text_b,
            question=body.question
        )

        visual_diff = build_visual_diff(
            chunks_a,
            chunks_b
        )

        return {
            "document_a": body.document_a,
            "document_b": body.document_b,
            "comparison": comparison_result,
            "pages_document_a": pages_a,
            "pages_document_b": pages_b,
            "visual_diff": visual_diff["items"],
            "visual_diff_total": visual_diff["total_items"],
            "visual_diff_truncated": visual_diff["truncated"]
        }

    except HTTPException:
        raise

    except Exception:
        logger.exception("Document comparison failed")
        raise HTTPException(
            status_code=500,
            detail="Failed to compare the documents."
        )

@app.get("/documents")
@limiter.limit("30/minute")
def get_documents(request: Request):
    try:
        service = get_document_service()

        documents = service.list_documents()

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


@app.get("/documents/{filename}/summary")
@limiter.limit("30/minute")
def get_document_summary(request: Request, filename: str):
    valid_filename = validate_pdf_filename(filename)
    try:
        service = get_document_service()
        summary_data = service.get_summary(valid_filename)
        if summary_data is None:
            raise HTTPException(
                status_code=404,
                detail="Summary not found."
            )
        return summary_data

    except HTTPException:
        raise
    except Exception:
        logger.exception("Failed to retrieve document summary")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve document summary."
        )


@app.delete("/documents/{filename}")
@limiter.limit("10/minute")
def delete_document(
    request: Request,
    filename: str,
    authenticated: bool = Depends(verify_api_key)
):
    valid_filename = validate_pdf_filename(filename)
    try:
        service = get_document_service()

        existing = service.vector_store.list_sources()

        if not any(
            doc["filename"] == valid_filename
            for doc in existing
        ):
            raise HTTPException(
                status_code=404,
                detail="Document not found."
            )

        service.delete_document(valid_filename)

        return {
            "message": "Document deleted successfully.",
            "filename": valid_filename
        }

    except HTTPException:
        raise

    except Exception:
        logger.exception("Failed to delete document")
        raise HTTPException(
            status_code=500,
            detail="Failed to delete document."
        )
