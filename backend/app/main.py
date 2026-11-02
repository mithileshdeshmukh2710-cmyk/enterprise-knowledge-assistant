import os
import tempfile

from fastapi import FastAPI, UploadFile, File, HTTPException

from app.pdf_processor import extract_text_from_pdf


app = FastAPI(
    title="Enterprise Knowledge Assistant",
    description="AI-powered document question answering system",
    version="1.0.0"
)


@app.get("/")
def home():
    return {
        "message": "Welcome to Enterprise Knowledge Assistant",
        "status": "Backend is running"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }


@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):

    # Validate file extension
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are allowed"
        )

    # Read uploaded file
    content = await file.read()

    # Basic file size validation: 10 MB
    if not content:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty"
        )

    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail="File size must not exceed 10 MB"
        )

    temp_path = None

    try:
        # Save PDF temporarily
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".pdf"
        ) as temp_file:

            temp_file.write(content)
            temp_path = temp_file.name

        # Extract PDF text
        extracted_pages = extract_text_from_pdf(temp_path)

        if not any(page["text"].strip() for page in extracted_pages):
            raise HTTPException(
                status_code=422,
                detail="No extractable text found in PDF"
            )

        return {
            "filename": file.filename,
            "total_pages": len(extracted_pages),
            "pages": extracted_pages
        }

    except HTTPException:
        raise

    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Unable to process this PDF"
        )

    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)