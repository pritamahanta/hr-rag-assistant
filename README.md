# HR RAG Assistant

## 1. Project Overview

HR RAG Assistant helps employees find answers in the HR policy documents currently uploaded by an administrator. It addresses a common problem: policy information can be difficult to search, and an answer that sounds plausible is not useful if it cannot be traced back to the policy.

**Employee workflow**

- Open Employee mode and ask a question about an HR policy.
- Review an answer grounded in the retrieved policy text, along with its source document, section, and PDF page when available.
- If the question is genuinely ambiguous, the assistant asks for clarification. If the policies do not contain enough evidence, it refuses instead of filling the gap with general knowledge.

**Admin workflow**

- Open Admin mode to list the policy files currently available.
- Upload a new policy, replace a policy by uploading the same filename, or delete a policy.
- Ask questions against the updated policy set after indexing finishes.

The backend validates every citation against the chunks retrieved for the current question. Answers without valid supporting source IDs are refused. The role selector in the browser only sends an `X-User-Role` header; it is a prototype workflow and is not real authentication or role-based access control.

This is an assignment-scale prototype. Retrieval, grounding, citations, and the main employee/admin workflow are implemented and tested, but authorization, operational resilience, and deployment are not production-grade.

## 2. How to Kick Start

1. Open the deployed frontend: **https://hr-rag-assistant-ksbf.vercel.app**
2. Use **Employee** mode to ask a question about an HR policy.
3. Review the answer and its citation.
4. Switch to **Admin** mode to upload, replace, or delete policy documents.
5. Ask questions against the updated policy set.

Supported policy files are Markdown (`.md`), text (`.txt`), and PDF (`.pdf`).

## 3. Tech Stack

| Layer | Technology |
| --- | --- |
| Frontend | React + Vite |
| Backend | FastAPI + Python |
| LLM | Groq - `openai/gpt-oss-20b` |
| Embeddings | sentence-transformers - `all-MiniLM-L6-v2` |
| Retrieval | Chroma Cloud + BM25 + Reciprocal Rank Fusion |
| Storage | Supabase Storage |
| Deployment | Vercel |

## 4. Local Setup

The repository contains separate backend and frontend projects.

### Prerequisites

- Python 3.x
- Node.js and npm
- Groq API key
- Chroma Cloud credentials
- Supabase credentials

### Backend setup

From the repository root:

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Set the provider, storage, and frontend-origin variables in `backend/.env` before using upload or query functionality.

### Frontend setup

In a second terminal:

```bash
cd frontend
npm install
cp .env.example .env
```

Set `VITE_API_URL` if the backend is not at its default local URL.

### Environment variables

The backend uses:

| Variable | Used for |
| --- | --- |
| `GROQ_API_KEY` | Groq resolver and answer-generation calls |
| `CHROMA_API_KEY` | Chroma Cloud client |
| `CHROMA_TENANT` | Chroma Cloud tenant |
| `CHROMA_DATABASE` | Chroma Cloud database |
| `FRONTEND_ORIGIN` | The single allowed frontend origin in FastAPI CORS |
| `SUPABASE_URL` | Supabase project URL |
| `SUPABASE_SECRET_KEY` | Supabase server-side storage client credential |
| `SUPABASE_STORAGE_BUCKET` | Supabase Storage bucket for policy files |

The frontend uses `VITE_API_URL` as the FastAPI base URL. Keep actual credentials out of source control.

### Running the application

Start the backend:

```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload
```

The API runs at `http://127.0.0.1:8000`. In another terminal, start the frontend:

```bash
cd frontend
npm run dev
```

The Vite development server normally runs at `http://localhost:5173`.

### Running tests

Run the backend suite from `backend`:

```bash
pytest -q
```

The frontend can also be checked with:

```bash
npm run lint
npm run build
```

## 5. Communication Flow

```text
User
  |
  v
React / Vite
  |
  v
FastAPI
  |
  v
Hybrid Retrieval --------------------> Chroma Cloud
  |                                      (vector search)
  +-----------------------------------> BM25
                                         (keyword search)
  |
  v
RRF (top_k=8)
  |
  v
Structural sibling expansion
  |
  v
Query Resolver ----------------------> Groq
  |                                      (answerability)
  +--> Answer
  +--> Clarify: short policy-grounded question
  `--> Refuse
  |
  v
Answer Generator --------------------> Groq
  |
  v
Citation Validation
  |
  v
React UI

Policy files -------------------------> Supabase Storage
                                       (uploaded originals)
```

## End-to-End Flow

### Document ingestion

1. An admin uploads a file through `POST /documents/upload`.
2. The API accepts only `.md`, `.txt`, and `.pdf` files, strips path components from the filename, rejects empty files, and limits the upload to 10 MiB.
3. The file is written to a temporary local file, uploaded to the configured Supabase Storage bucket, and parsed.
4. Markdown headings become section paths such as `Health Insurance > Dental Implant Coverage`. Text files are treated as one section. PDFs are extracted page by page and retain page numbers; PDF headings are not reliably inferred.
5. `chunking.py` creates chunks with a 1,000-character maximum and approximately 150 characters of line overlap. Long lines fall back to character splitting. Markdown-style table headers and separator rows are carried into table chunks.
6. The indexed text includes document and section context. Local sentence-transformer embeddings are generated and the chunks replace any prior Chroma entries for the same document.
7. The complete Chroma corpus is read to rebuild the in-memory BM25 index.

### Query resolution

1. `POST /query` trims and validates the question.
2. Retrieval uses `top_k=8`, combines Chroma vector search and BM25 with RRF, then structurally expands retrieved nested sections with their sibling sections when applicable.
3. A Groq structured-output query resolver receives the user question and retrieved policy context, then returns `answer`, `clarify`, or `refuse`. For a genuine ambiguity, it generates a short clarification using only that context and question; it cannot introduce unsupported policy facts or options.
4. Only an `answer` decision triggers the second Groq call. The answer generator must use only the supplied context and return source IDs for directly supporting chunks.
5. The backend accepts only source IDs belonging to the chunks retrieved for this request. It converts them to unique `{document, section, page}` citations. Missing or invalid source IDs cause a refusal.

The canonical refusal is returned when retrieval is empty, the resolver refuses, or a generated answer has no valid citations. A genuinely ambiguous question receives a concise clarification generated by the query resolver from the retrieved policy context and user question, without citations. The clarification does not use conversation history or persistent memory and cannot introduce unsupported policy facts or options. Unexpected retrieval or LLM failures return HTTP 500, while Groq rate-limit failures return HTTP 503.

## Supported Files and Storage

Supported upload extensions are `.md`, `.txt`, and `.pdf`; the maximum request file size is 10 MiB. Markdown gives the best section citations because headings are preserved. Plain text has no section metadata. PDF page numbers are retained when text extraction succeeds, but headings are not reliably inferred; scanned PDFs and complex layouts are not handled by OCR or a dedicated table extractor.

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

See the [Environment variables](#environment-variables) table in Local Setup. The backend requires the provider and storage values for the corresponding integrations to initialize; `VITE_API_URL` configures the frontend.

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

## Tests

The backend tests cover parsing, section-aware and table-aware chunking, ingestion and replacement, vector operations, BM25 behavior, RRF retrieval, citation validation, route validation/authorization, and mocked answer/clarify/refuse resolver cases. They do not constitute a live provider, browser, load, security, or deployment test.

## Deployment

The application is deployed as two separate Vercel projects from the same repository: one for the FastAPI backend and one for the Vite frontend. Deploy the backend first so its public URL is available when configuring the frontend.

### Backend: Vercel

Create a Vercel project with `backend` as the Root Directory. Add the provider and storage credentials from the [Local Setup - Environment variables](#environment-variables) section as Vercel environment variables, and set `FRONTEND_ORIGIN` to the deployed frontend URL.

The backend endpoint is available at `/health`, which returns `{"status":"ok"}` when the service is running.

### Frontend: Vercel

Create a second Vercel project for the `frontend` directory with these settings:

| Setting | Value |
| --- | --- |
| Root Directory | `frontend` |
| Build Command | `npm run build` |
| Publish Directory | `dist` |

Set the frontend environment variable `VITE_API_URL` to the deployed FastAPI backend URL. Because this value is read during the Vite build, trigger a new frontend deploy after changing it.

After both projects are deployed, verify the backend at `/health`, open the frontend URL, and confirm that browser requests reach the backend without a CORS error. Keep all provider credentials in Vercel environment variables rather than committing them to the repository. Supabase Storage stores uploaded policy files, Chroma Cloud stores indexed chunks, and Groq provides the LLM.

## Limitations and Future Work

Important current trade-offs and limitations:

- The `X-User-Role` header is spoofable and provides no real authentication or tenant isolation.
- Upload ingestion is synchronous and runs within the request.
- BM25 state is in memory and each process maintains its own copy.
- PDF extraction is text-only and does not provide OCR or robust layout/table handling. Page numbers are retained, but headings are not reliably inferred.
- The resolver and answer generator add latency and provider dependency, but separate answerability from generation and make refusal behavior explicit.

Reasonable future work is real authentication and RBAC, asynchronous ingestion, stronger PDF extraction, persistent lexical indexing, automated live-model evaluation, and operational observability. These are not implemented features.

See [DESIGN.md](DESIGN.md) for the engineering rationale and architecture decisions.
