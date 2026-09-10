# HR RAG Assistant

HR RAG Assistant is a small FastAPI and React application for answering employee questions from uploaded HR policy documents. It retrieves relevant policy evidence, decides whether the question is answerable, and returns a grounded answer with citations. If the policy evidence is missing or the question is genuinely ambiguous, the service refuses or asks for clarification rather than filling gaps with general knowledge.

This is an assignment-scale prototype. Its retrieval and grounding behavior is implemented and tested, but its authorization, operational resilience, and deployment process are not production-grade.

## What It Does

**Employee workflow**

- Select the Employee view in the browser.
- Ask a question about the policies currently indexed.
- Receive an answer, a clarification request, or a canonical refusal.
- Review citations containing the source document, section when available, and PDF page when available.

**Admin workflow**

- Select the Admin view.
- List policy files in the configured Supabase Storage bucket.
- Upload `.md`, `.txt`, or `.pdf` files.
- Replace an existing indexed document by uploading another file with the same filename.
- Delete a document from storage and remove its indexed chunks.

The browser role selector is only a convenience for sending `X-User-Role`. It is not a login system.

## Architecture

The backend lives under `backend/app`:

- `routes/documents.py` validates upload names and size, applies admin checks, and coordinates storage and ingestion.
- `routes/query.py` validates questions and exposes the query endpoint.
- `services/storage.py` uses Supabase Storage for uploaded files.
- `services/document_parser.py` extracts Markdown, text, or PDF page content.
- `services/chunking.py` creates section-aware, line-aware chunks.
- `services/embedding.py` generates local `all-MiniLM-L6-v2` embeddings.
- `services/vector_store.py` stores chunks in the Chroma Cloud collection `hr_policies` using cosine space.
- `services/keyword_search.py` maintains an in-memory BM25 index.
- `services/retrieval.py` combines Chroma and BM25 rankings with Reciprocal Rank Fusion (RRF).
- `services/query.py` coordinates retrieval, resolution, answer generation, and citation validation.
- `services/llm.py` uses Groq and the `openai/gpt-oss-20b` model with structured JSON responses.
- `services/citations.py` converts valid retrieved source IDs into deduplicated citation metadata.

The frontend is a Vite React application in `frontend/src`. `App.jsx` provides the employee/admin views; `QueryPanel`, `AnswerPanel`, and `DocumentManager` call the FastAPI API and render results.

Groq is the LLM provider. The current model is `openai/gpt-oss-20b`, used for query resolution and grounded answer generation. Embeddings are generated locally with `sentence-transformers` using `all-MiniLM-L6-v2`; policy text is not sent to a separate embedding provider.

## End-to-End Flow

### Document ingestion

1. An admin uploads a file through `POST /documents/upload`.
2. The API accepts only `.md`, `.txt`, and `.pdf` files, strips path components from the filename, rejects empty files, and limits the upload to 10 MiB.
3. The file is written to a temporary local file, uploaded to the configured Supabase Storage bucket, and parsed.
4. Markdown headings become section paths such as `Health Insurance > Dental Implant Coverage`. Text files are treated as one section. PDFs are extracted page by page and retain page numbers; PDF headings are not inferred.
5. `chunking.py` creates chunks with a 1,000-character maximum and approximately 150 characters of line overlap. Long lines fall back to character splitting. Markdown-style table headers and separator rows are carried into table chunks.
6. The indexed text includes document and section context. Local sentence-transformer embeddings are generated and the chunks replace any prior Chroma entries for the same document.
7. The complete Chroma corpus is read to rebuild the in-memory BM25 index.

### Query resolution

1. `POST /query` trims and validates the question.
2. The query is embedded for Chroma vector search. BM25 searches indexed document, section, and content text. Both paths retrieve up to a candidate set of 10 or more items, then RRF combines their IDs; the normal final set is 5 chunks. Enumeration questions use 8 final chunks.
3. A Groq structured-output call classifies the retrieved context as `answer`, `clarify`, or `refuse`.
4. Only an `answer` decision triggers the second Groq call. The answer generator must use only the supplied context and return source IDs for directly supporting chunks.
5. The backend accepts only source IDs belonging to the chunks retrieved for this request. It converts them to unique `{document, section, page}` citations. Missing or invalid source IDs cause a refusal.

The canonical refusal is returned when retrieval is empty, the resolver refuses, or a generated answer has no valid citations. A genuinely ambiguous question receives a generic clarification response without citations. Unexpected retrieval or LLM failures are returned as HTTP 500 rather than being mislabeled as policy refusals.

## Supported Files and Storage

Supported upload extensions are `.md`, `.txt`, and `.pdf`; the maximum request file size is 10 MiB. Markdown gives the best section citations because headings are preserved. Plain text has no section metadata. PDF page numbers are retained when text extraction succeeds, but scanned PDFs and complex layouts are not handled by OCR or a dedicated table extractor.

Supabase Storage is the source for uploaded files. Chroma Cloud stores the searchable chunks and metadata in the `hr_policies` collection. The BM25 index is process memory and is rebuilt after ingestion and deletion; it is not a separately persisted search service.

## API

| Method | Path | Behavior |
| --- | --- | --- |
| `GET` | `/health` | Returns `{"status":"ok"}`. |
| `GET` | `/documents/` | Lists supported document filenames from Supabase Storage. |
| `POST` | `/documents/upload` | Admin-only multipart upload and indexing. |
| `DELETE` | `/documents/{filename}` | Admin-only storage deletion and indexed-chunk deletion. |
| `POST` | `/query` | Accepts `{"question":"..."}` and returns an answer plus citations. |

Interactive OpenAPI documentation is exposed by FastAPI at `/docs` when the backend is running.

Upload and delete require `X-User-Role: admin`. The header defaults to `employee`, and any other value is rejected with HTTP 403. Query, document listing, and health checks do not use this dependency. This is prototype authorization, not authentication, identity verification, SSO, or production-grade access control.

## Configuration

The application uses these environment variables:

| Variable | Used for |
| --- | --- |
| `GROQ_API_KEY` | Groq resolver and answer-generation calls. |
| `CHROMA_API_KEY` | Chroma Cloud client. |
| `CHROMA_TENANT` | Chroma Cloud tenant. |
| `CHROMA_DATABASE` | Chroma Cloud database. |
| `FRONTEND_ORIGIN` | The single allowed frontend origin in FastAPI CORS configuration. |
| `SUPABASE_URL` | Supabase project URL used by `storage.py`. |
| `SUPABASE_SECRET_KEY` | Supabase server-side storage client credential used by `storage.py`. |
| `SUPABASE_STORAGE_BUCKET` | Supabase Storage bucket used for policy files. |
| `VITE_API_URL` | Frontend base URL for FastAPI requests. |

The backend requires the provider and storage values for the corresponding integrations to initialize; `VITE_API_URL` configures the frontend. Keep actual credentials out of source control.

## Example API Response

`POST /query` returns the structured `AnswerResponse` model:

```json
{
	"answer": "Employees receive 12 casual leave days.",
	"citations": [
		{
			"document": "leave-policy.md",
			"section": "Leave Policy > Leave types > 2.1 Casual leave (CL)",
			"page": ""
		}
	]
}
```

### Prerequisites

- Python 3.x
- Node.js and npm
- Groq API key
- Chroma Cloud credentials
- Supabase credentials

## Local Development (under 10 minutes)

The repository has separate backend and frontend projects.

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Set the provider, storage, and frontend-origin variables in .env.
uvicorn app.main:app --reload
```

The API is available at `http://127.0.0.1:8000`. Configure the required provider and storage variables before using upload or query functionality.

### Frontend

In another terminal:

```bash
cd frontend
npm install
cp .env.example .env
# Set VITE_API_URL if the backend is not at its default URL.
npm run dev
```

The Vite development server normally runs at `http://localhost:5173`. Set `VITE_API_URL` if the backend uses another URL. The frontend can also be checked with `npm run lint` and built with `npm run build`.

## Tests

Run the backend suite from `backend`:

```bash
pytest -q
```

The repository tests cover parsing, section-aware and table-aware chunking, ingestion and replacement, vector operations, BM25 behavior, RRF retrieval, citation validation, route validation/authorization, and mocked answer/clarify/refuse evaluation cases. They do not constitute a live provider, browser, load, or deployment test.

## Deployment Status, Limitations, and Future Work

There is no deployment configuration or completed deployment workflow in this repository. A deployment would need a backend process with access to Groq, Chroma Cloud, and Supabase Storage, plus a separately built/hosted Vite frontend whose origin is configured in `FRONTEND_ORIGIN`. This document does not claim that deployment is complete.

Important current trade-offs and limitations:

- The `X-User-Role` header is spoofable and provides no real authentication or tenant isolation.
- Upload ingestion is synchronous and runs within the request.
- BM25 state is in memory and each process maintains its own copy.
- PDF extraction is text-only and does not provide OCR or robust layout/table handling.
- The resolver and answer generator add latency and provider dependency, but separate answerability from generation and make refusal behavior explicit.

Reasonable future work is real authentication and RBAC, asynchronous ingestion, stronger PDF extraction, persistent lexical indexing, automated live-model evaluation, and operational observability. These are not implemented features.

See [DESIGN.md](DESIGN.md) for the engineering rationale and architecture decisions.
