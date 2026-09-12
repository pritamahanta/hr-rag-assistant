# HR RAG Assistant: Engineering Design

## 1. Problem and Goals

This application answers employee questions from uploaded HR policy documents. The design goal is controlled, inspectable behavior: retrieve policy evidence, decide whether that evidence is sufficient, and return an answer with document provenance. If the evidence is missing, the system refuses rather than filling the gap with general knowledge.

The project is an assignment-scale prototype. It implements retrieval, grounding, citations, and a small React workflow, but not real authentication, asynchronous ingestion, persistent BM25 storage, OCR, or a deployment pipeline.

It intentionally favors a small number of explicit, testable components over a large orchestration framework, which keeps the assignment's design decisions defensible.

## 2. End-to-End Architecture

The frontend is React/Vite. FastAPI owns validation and policy processing. Supabase Storage and Chroma Cloud are external persisted services; BM25 is process-local and rebuilt from Chroma.

### 2.1 Admin document ingestion

```text
React/Vite
    |
    v
FastAPI POST /documents/upload
    |
    v
Validation: extension, basename, empty file, 10 MiB
    |
    v
Temporary file -----+----> Supabase Storage
    |                    original file, persisted
    v
Parser
  +-- Markdown -> heading hierarchy
  +-- TXT      -> one section
  +-- PDF      -> page-level text extraction
    |
    v
Section-aware chunking
    |
    v
Index text: document + section + content
    |
    +----------------------+----------------------+
    |                                             |
    v                                             v
Local embeddings                                  BM25 rebuild
    |                                             process-local
    v                                             |
Chroma Cloud                                      |
chunks, embeddings,                              |
metadata, IDs                                     |
    |                                             |
    +----------------------+----------------------+
                           v
                    Corpus available for retrieval
```

### 2.2 Employee query

```text
React/Vite
    |
    v
FastAPI POST /query
    |
    v
Validate and trim question
    |
    +-------------------------+-------------------------+
    |                                                   |
    v                                                   v
Query embedding                                      BM25 search
    |                                                   |
    v                                                   |
Chroma vector search                                  |
    |                                                   |
    +-------------------------+-------------------------+
                              v
                    Reciprocal Rank Fusion
                              v
                         Final top-K chunks
                              v
                       Groq query resolver
                    +---------+---------+
                    |         |         |
                 ANSWER    CLARIFY    REFUSE
                    |         |         |
                    v         v         v
             answer LLM   fixed text  fixed text
                    |
                    v
              structured source_ids
                    v
             backend citation validation
                    v
             structured AnswerResponse
                    v
               React AnswerPanel
```

The LLM calls are external. The backend, not the browser, selects context, decides whether generation is allowed, and constructs citations.

## 3. End-to-End Flows

### 3.1 Document Ingestion Flow

`app/routes/documents.py` accepts only `.md`, `.txt`, and `.pdf`, normalizes the filename with `Path(...).name`, rejects empty files, and caps bytes at 10 MiB. It writes a temporary file, uploads it to the configured Supabase bucket, and passes it to `app/services/ingestion.py`; the temporary file is removed afterward. If processing fails, the route attempts to remove the uploaded object.

`document_parser.py` preserves provenance at parse time: Markdown headings become breadcrumb sections such as `Health Insurance > Dental Implant Coverage`; TXT becomes one section; PDF text is extracted page by page with one-based page numbers. PDF headings are not inferred. `chunking.py` then splits each section with a 1,000-character maximum and approximately 150 characters of line-aware overlap. Oversized lines are character-split, while Markdown-style table headers and separators are carried into table chunks.

`ingestion.py` constructs `Document:`, `Section:`, and `Content:` index text, generates local `all-MiniLM-L6-v2` embeddings, and replaces Chroma chunks for the same document. Chunk IDs are deterministic, for example `<document>-chunk-0`. Finally, it reads the resulting Chroma corpus and rebuilds the in-memory BM25 index. Same-name uploads therefore replace old indexed chunks rather than accumulating stale versions.

### 3.2 Query / RAG Flow

`POST /query` validates `QueryRequest`, trims the question, and rejects an empty result with HTTP 400. `retrieval.py` ensures BM25 exists, embeds the query, and asks Chroma and BM25 for candidate rankings. Each path supplies `max(top_k * 2, 10)` candidates. Their IDs are fused with RRF using the default `top_k=8`, then sibling sections are added only when a retrieved chunk belongs to a nested section and those siblings share the same parent section. Retrieval produces the candidate evidence set; the resolver determines whether that evidence is sufficient for the specific question.

`query.py` formats each chunk with an internal source ID, document, section, page, and content. `resolve_query` sends that context to Groq and requires one structured decision: `answer`, `clarify`, or `refuse`. Only `answer` invokes the second Groq call, which returns structured `answer` and `source_ids`. The backend validates those IDs against the chunks retrieved for this request, creates deduplicated citations, and returns `AnswerResponse` to React.

Empty retrieval, resolver refusal, or missing/invalid citations returns the canonical refusal with no citations. A genuine ambiguity returns a fixed clarification with no citations. Unexpected retrieval, resolver, and generation exceptions become HTTP 500 through `QueryServiceError`, while Groq rate-limit failures return HTTP 503; infrastructure failure is not mislabeled as policy refusal.

## 4. Retrieval Architecture

The system uses section-aware, line-aware chunks rather than splitting the whole document blindly. The 1,000-character limit and approximately 150-character overlap keep nearby policy statements together. Table headers and separator rows are repeated across simple Markdown table chunks. Each chunk carries document, section, page, and a deterministic ID. The enriched `document + section + content` text is used for both embeddings and lexical search.

Local `sentence-transformers` embeddings (`all-MiniLM-L6-v2`) are stored in the Chroma Cloud `hr_policies` collection configured for cosine space. This helps with paraphrased questions, such as asking about carrying leave forward without using the policy's exact wording.

The in-memory `rank-bm25` index tokenizes the same enriched text. It helps with exact HR terminology, section numbers, clause wording, policy identifiers, named benefits, and table values. Hybrid retrieval is therefore a deliberate fit for HR policy data: semantic search handles paraphrase, while BM25 protects exact terms and values.

`retrieval.py` requests at least 10 candidates from each path and applies Reciprocal Rank Fusion with `RRF_K = 60`:

```text
RRF score(chunk) = sum(1 / (60 + rank)) for each ranking containing it
```

RRF combines rank positions without pretending Chroma distances and BM25 scores share a scale. It returns the default `top_k=8` chunks for all queries, then adds sibling sections only when a retrieved chunk belongs to a nested section and those siblings share the same parent section. There is no semantic-distance answerability threshold; retrieval produces the candidate evidence set, while the resolver decides whether it is sufficient for the specific question.

## 5. Grounding, Clarification, and Refusal

```text
Retrieved chunks
      v
Backend context: source ID + provenance + content
      v
Query Resolver
  +-- clarify -> fixed clarification, no citations
  +-- refuse  -> fixed refusal, no citations
  `-- answer  -> Answer Generator -> source_ids
                                      v
                         validate IDs against this retrieval
                              +-------+-------+
                              |               |
                           valid        invalid/none
                              v               v
                       final citations  safe refusal
```

Grounding is not a prompt-only claim. The safeguards are layered:

1. Retrieval limits the policy evidence supplied to the LLM.
2. A structured resolver gates answer generation and must reject unsupported material parts.
3. The generator receives only backend-formatted policy context and must return structured source IDs.
4. The backend accepts only IDs belonging to the current retrieved chunks.
5. Unknown IDs are ignored; if no valid ID remains, the answer is refused.
6. Clarification and refusal branches never fabricate citations.

These controls reduce unsupported answers but do not mathematically guarantee that an LLM cannot hallucinate. Weak retrieval is not automatically a clarification case. **Clarify** means the question itself is genuinely ambiguous, for example “How many leave days do I get?” when multiple leave types exist. **Refuse** means the intent is clear but the uploaded policies do not contain enough evidence, for example “Can I expense a personal home gym?” when no such policy exists. A clear question with missing policy evidence should not be sent back for unnecessary rewording.

## 6. Citation and Provenance

```text
chunk_id -> context source ID -> returned source_ids
         -> backend lookup -> deduplicate(document, section, page)
         -> Citation in AnswerResponse
```

Chunk IDs are internal. The user-facing `Citation` contains `document`, `section`, and `page`; Markdown sections and PDF pages can therefore be displayed, while plain text or PDF chunks may have an empty section. The backend performs validation because the LLM is not authoritative about which chunks were retrieved for this request. Invalid IDs are ignored, duplicate provenance is removed, and no valid source means safe refusal rather than an uncited answer.

## 7. State, Storage, and Responsibilities

```text
Supabase Storage (external, persisted)
  -> original uploaded policy files

Chroma Cloud (external, persisted)
  -> chunk documents, embeddings, metadata, IDs

Backend process memory (not persisted)
  -> rank-bm25 KeywordIndex
```

The BM25 index is rebuilt after ingestion and deletion and can be rebuilt from Chroma when empty. It is not persistent or shared between backend processes.

The frontend is responsible for role selection, question input, upload/delete controls, loading/status states, and rendering answers/citations. `App.jsx`, `QueryPanel`, `AnswerPanel`, and `DocumentManager` implement this boundary. The backend owns validation, prototype authorization, storage, parsing, chunking, embeddings, retrieval, RRF, LLM calls, grounding, citation construction, and structured responses.

## 8. API and Schema Design

| Method/path | Request | Response and errors |
| --- | --- | --- |
| `GET /health` | None | `{ "status": "ok" }` |
| `GET /documents/` | None | `{ "documents": [...] }`; storage failures are server errors |
| `POST /documents/upload` | Multipart `file`; `X-User-Role: admin` | Message, filename, `chunks_indexed`; `400` invalid/empty/type, `403` non-admin, `413` over 10 MiB, `500` ingestion failure |
| `DELETE /documents/{filename}` | Path filename; `X-User-Role: admin` | Message, filename, `chunks_deleted`; `403`, `404` if no indexed chunks, or `500` storage failure |
| `POST /query` | `{ "question": "..." }` | `AnswerResponse`; `400` empty after trim, `500` unexpected query-service failure, or `503` Groq rate-limit failure |

`AnswerResponse` contains `answer` and `citations`. `Citation` contains `document`, `section`, and `page`. Internal structured models restrict resolution to `answer`, `clarify`, or `refuse`, and LLM output to `answer` plus `source_ids`. Pydantic and Groq JSON schemas make the client boundary predictable; free-form LLM output is not returned directly.

## 9. Authorization

`app/core/auth.py` defines `require_admin`, which accepts only a trimmed, lower-cased `X-User-Role: admin`. Upload and delete use it; listing, querying, and health do not. The default role is `employee`.

This is prototype authorization, not authentication, SSO, secure RBAC, identity verification, or production security. The client controls the header, so it is spoofable and provides no tenant isolation. The minimal mechanism matches the assignment's admin/employee workflow but must be replaced for real HR data.

## 10. Trade-offs

- **Hybrid vector + BM25 vs vector-only:** chosen because HR questions mix paraphrases with exact clause terms, section numbers, identifiers, and table values. The cost is a second, process-local index and rebuilds.
- **Two LLM stages vs one:** the resolver makes answer/clarify/refuse explicit before generation, improving control and testability. The cost is another provider call and latency.
- **Synchronous vs asynchronous ingestion:** synchronous processing is easy to reason about and returns `chunks_indexed` immediately. It blocks uploads during parsing, embedding, and external calls.
- **Line/section chunks vs token/semantic chunks:** the current strategy preserves headings and simple tables with little tuning. It is less optimal for arbitrary documents and is not token-aware.
- **Chroma Cloud vs local persistence:** Cloud matches the external indexed-corpus design, but adds provider credentials and dependency on an external service. Application code uses `CloudClient`; local Chroma clients appear in tests.
- **Local embeddings vs remote embeddings:** local embeddings avoid sending policy text to an embedding provider and avoid embedding API cost, at the cost of local model resources.
- **Simple table handling vs heavy extraction:** repeated Markdown headers help simple policy tables, but there is no OCR or layout-aware PDF/table extractor.
- **In-memory BM25 vs persistent lexical search:** rebuilding from Chroma is simple for this corpus, but the index is not durable or shared across processes.

## 11. Testing and Assignment Stretch Features

The backend tests cover parser dispatch, Markdown hierarchy, PDF page metadata, chunk limits and table handling, ingestion replacement, Chroma add/search/delete/replace, BM25 ranking and rebuilds, RRF, BM25-only retrieval candidates, route validation, upload limits/types, admin authorization, citation filtering/deduplication, query failures, and answer/clarify/refuse orchestration.

`test_eval.py` is a small mocked set covering supported and informal supported questions, an ambiguous leave question, and an unsupported benefit question. It validates orchestration, not live Groq quality, retrieval recall, or factual model accuracy. There is no browser, load, security, or deployment test.

Implemented assignment stretch behaviors are hybrid search, improved Markdown/PDF/table provenance handling, the small mocked evaluation set, and same-name policy replacement/re-indexing. They are useful because they address retrieval coverage, provenance, and stale-index risk without introducing a larger framework.

## 12. Deployment, Limitations, and Two-Week Plan

The current prototype is deployed on Vercel as separate frontend and backend projects. The deployment topology is:

```text
Vercel React/Vite frontend
    | VITE_API_URL
    v
Vercel FastAPI backend
    +--> Groq (LLM)
    +--> Chroma Cloud (indexed chunks)
    `--> Supabase Storage (uploaded policies)
```

The frontend uses `VITE_API_URL` to call the deployed FastAPI backend. Backend CORS uses `FRONTEND_ORIGIN` to allow the deployed frontend origin. Backend configuration also includes `GROQ_API_KEY`, `CHROMA_API_KEY`, `CHROMA_TENANT`, and `CHROMA_DATABASE`. `storage.py` reads `SUPABASE_URL`, `SUPABASE_SECRET_KEY`, and `SUPABASE_STORAGE_BUCKET` for uploaded policies.

Current limitations include spoofable authorization, synchronous ingestion, process-local BM25, text-only PDF extraction, external provider dependency, and no live-model evaluation or observability. The highest-value two-week hardening order would be:

1. real authentication/RBAC and tenant/data-access boundaries;
2. asynchronous ingestion with provider timeouts, retries, status, and failure observability;
3. live-model regression evaluation for answer support, refusal correctness, retrieval recall, and citation correctness;
4. stronger PDF/OCR/table extraction, then evidence-based consideration of reranking or persistent lexical search.

These are future improvements, not current capabilities.
