# Enterprise Knowledge Assistant

An AI-powered document intelligence and question-answering assistant for enterprise documents. Built with **FastAPI**, **React (Vite)**, **ChromaDB**, **SentenceTransformers**, and **Google Gemini**.

---

## Features

- **Automated Document Ingestion & Chunking**: Extracts text from multi-page PDFs using PyMuPDF, chunks content with configurable overlap, and computes normalized dense vector embeddings using `sentence-transformers/all-MiniLM-L6-v2`.
- **Hybrid Retrieval-Augmented Generation (RAG)**: Combines dense semantic vector search with sparse keyword search (BM25) using **Reciprocal Rank Fusion (RRF)**, filtered by distance cutoffs (`MAX_DISTANCE = 0.55`).
- **Conversational Q&A with Source Citations**: Queries Gemini with grounded document context, maintaining sliding-window multi-turn conversation history and returning precise page-level citations.
- **Persistent AI Document Summaries**: Generates executive summaries, key bullet points, dates, numbers, and action items upon upload, cached persistently in a metadata store.
- **Smart Document Comparison & Visual Diff**:
  - Compares two PDF versions semantically using Gemini.
  - Generates text-level sentence diffs powered by `difflib.SequenceMatcher`.
  - **Smart Modified-Content Detection**: Calculates sentence similarity (threshold $\ge 0.60$) to display changes side-by-side (`OLD` vs `NEW`) rather than disjointed deletions and additions.
- **Security & Abuse Protection**:
  - Strict filename sanitization and path-traversal prevention.
  - Tiered IP rate limiting via SlowAPI (`/upload` 5/min, `/compare` 5/min, `/ask` 10/min, `/documents` 30/min).
  - Optional API key authentication via `X-API-Key` header (`APP_API_KEY`).
  - Configurable CORS origins with production environment variable support.

---

## Architecture Overview

```
[ React 18 + Vite ]
       │
       │ HTTP / JSON (VITE_API_URL)
       ▼
[ FastAPI Backend ] ─── (SlowAPI Rate Limiter & Security)
       │
       ├─► [ PyMuPDF + Chunking Engine ]
       │
       ├─► [ SentenceTransformers (all-MiniLM-L6-v2) ]
       │
       ├─► [ ChromaDB (Persistent Vector Store) + BM25Okapi ]
       │
       ├─► [ Document Metadata Store (JSON Cache) ]
       │
       └─► [ Google Gemini Client (google-genai SDK) ]
```

---

## Prerequisites

- **Python**: 3.10 to 3.14
- **Node.js**: 18+ and npm
- **Google Gemini API Key**: Obtain from [Google AI Studio](https://aistudio.google.com/)

---

## Quickstart

### 1. Clone & Set Up Backend

```powershell
# Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1    # On Windows
# source .venv/bin/activate      # On Linux/macOS

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example backend/.env
```

Edit `backend/.env`:
```env
GEMINI_API_KEY=your_actual_gemini_api_key
GEMINI_MODEL=gemini-2.5-flash
FRONTEND_URL=http://localhost:5173
APP_API_KEY=
```

Start the FastAPI backend:
```powershell
uvicorn backend.app.main:app --reload --port 8000
```
API Documentation will be available at `http://localhost:8000/docs`.

---

### 2. Set Up Frontend

```powershell
cd frontend
npm install

# Configure frontend environment (optional for local dev)
cp .env.example .env
```

Start the React development server:
```powershell
npm run dev
```
Open `http://localhost:5173` in your browser.

---

## API Endpoints

| Method | Endpoint | Description | Rate Limit |
|---|---|---|---|
| `GET` | `/health` | Health check endpoint | Unmetered |
| `POST` | `/upload` | Upload & index a PDF document | 5 / minute |
| `POST` | `/ask` | Ask a question across indexed documents | 10 / minute |
| `POST` | `/compare` | Compare two documents (semantic + visual diff) | 5 / minute |
| `GET` | `/documents` | List all indexed documents & metadata | 30 / minute |
| `GET` | `/documents/{filename}/summary` | Retrieve persistent AI summary for a PDF | 30 / minute |
| `DELETE` | `/documents/{filename}` | Delete document and vector index | 10 / minute |

---

## Configuration Reference

### Backend (`.env` or `backend/.env`)

| Variable | Default | Description |
|---|---|---|
| `GEMINI_API_KEY` | *(Required)* | Google Gemini API Key |
| `GEMINI_MODEL` | `gemini-2.5-flash` | Gemini model name (`gemini-2.5-flash`, `gemini-1.5-flash`, etc.) |
| `FRONTEND_URL` | `http://localhost:5173` | Allowed CORS origins (comma-separated for multiple origins) |
| `APP_API_KEY` | `""` | Optional secret token. When set, mutation endpoints require `X-API-Key` |
| `CHROMA_DB_PATH` | `data/chroma_db` | Storage path for ChromaDB vector database |
| `DOCUMENT_METADATA_PATH` | `data/document_metadata.json`| Storage path for persistent summaries |

### Frontend (`frontend/.env`)

| Variable | Default | Description |
|---|---|---|
| `VITE_API_URL` | `http://localhost:8000` | Backend API base URL for deployed environments |

---

## Running Automated Tests

```powershell
# Run the complete test suite (29 tests)
pytest -v
```

Test coverage includes:
- Request validation and chat history constraints (`test_validation.py`)
- Text chunking, overlap calculations, and edge cases (`test_chunking.py`)
- Distance cutoff thresholds and hybrid rank fusion (`test_rag.py`)
- Security validation, path traversal defense, and API key auth (`test_endpoints.py`)
- Sentence-level visual diff, smart modified-content pairing, and truncation (`test_visual_diff.py`)

---

## Production Deployment Notes

1. **CORS & API Base URL**:
   - Set `FRONTEND_URL=https://your-frontend-domain.com` in backend environment variables.
   - Set `VITE_API_URL=https://your-backend-api.com` in frontend build environment.
2. **API Authentication**:
   - Set `APP_API_KEY=a_secure_random_key` to require an `X-API-Key` header on `/upload` and `DELETE /documents/*`.
3. **Memory Optimization**:
   - PyTorch threads are constrained to 1 thread (`torch.set_num_threads(1)`) to operate within low-memory cloud containers (e.g. Render / Cloud Run 512MB RAM limits).

