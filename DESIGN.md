# HR FAQ & Policy Assistant — Design

## 1. Overview

This project is a small Retrieval-Augmented Generation (RAG) service for answering employee questions from uploaded HR policies.

The system is designed around three requirements:

1. Answers must come only from uploaded policy documents.
2. Answers should include citations pointing to the supporting document and section/page metadata.
3. When the available policies do not support an answer, the system should clarify or safely refuse instead of guessing.

The prototype uses FastAPI for the backend, Chroma for vector search, local sentence-transformer embeddings, Groq for structured LLM inference, and a small vanilla HTML/CSS/JavaScript frontend.

---

## 2. Architecture

### Components

- **FastAPI API**
  - Handles document upload, listing, deletion, and user queries.
- **Document Parser**
  - Parses Markdown, text, and PDF documents.
  - Markdown headings are preserved as section metadata.
  - PDF parsing preserves page information.
- **Chunking Service**
  - Splits parsed policy sections into bounded text chunks.
- **Embedding Service**
  - Generates embeddings locally using `all-MiniLM-L6-v2`.
- **Chroma Vector Store**
  - Stores chunk text, embeddings, metadata, and deterministic chunk IDs.
  - Uses cosine distance for semantic retrieval.
  - **BM25 Keyword Index**
  - Maintains an in-memory lexical index over indexed chunks.
  - Supports exact-term and keyword-based retrieval.
  - Rebuilt when the indexed corpus changes.
- **Query Service**
  - Coordinates retrieval, evidence resolution, answer generation, and citation validation.
- **LLM Service**
  - Uses Groq with `openai/gpt-oss-20b`.
  - Uses structured JSON schemas for both query resolution and final answers.
- **Citation Service**
  - Maps model-generated source IDs back to retrieved chunks.
  - Only real retrieved chunks can become citations.
- **Frontend**
  - Minimal interface for uploading policies, viewing uploaded documents, deleting documents, and asking questions.

### Data flow

```text
                    DOCUMENT INGESTION

Upload document
      |
      v
Document parser
      |
      v
Section-aware chunks
      |
      v
Local embeddings
      |
      v
Chroma vector store
      |
      v
Indexed policy chunks


                       QUERY FLOW


Employee question
        |
        v
   Query embedding
        |
        +--------------------+
        |                    |
        v                    v
 Vector search            BM25 search
        |                    |
        +---------+----------+
                  |
                  v
     Reciprocal Rank Fusion
                  |
                  v
       Top-k candidate chunks
                  |
                  v
         Evidence resolver
          /       |       \
      answer   clarify   refuse
         |
         v
 Grounded answer generation
         |
         v
 Structured answer + source_ids
         |
         v
 Backend citation validation
         |
         v
     Answer + citations
```

The frontend communicates with the same FastAPI application and does not contain separate business logic for retrieval or grounding.

---

## 3. Chunking & Retrieval

### Document parsing

The parser supports:

- Markdown (`.md`)
- Plain text (`.txt`)
- PDF (`.pdf`)

Markdown documents are parsed using their headings as section boundaries. PDF documents are extracted page-by-page so page numbers can be preserved in citation metadata.

### Chunking

The system uses section-aware, line-aware chunking:

- Maximum chunk size: **1000 characters**
- Overlap target: **150 characters**

A section smaller than the maximum size remains intact.

Long content is split at line boundaries where possible rather than cutting arbitrarily through text. If a single line exceeds the maximum chunk size, it falls back to character-based splitting.

Markdown-style tables receive additional handling. Table rows are preserved as complete lines, and when a table spans multiple chunks, the table header and separator row are repeated in each table chunk. This helps preserve column meaning during retrieval.

Chunking is performed after section extraction instead of splitting the entire document blindly. This keeps policy rules grouped by their logical section whenever possible.

Each chunk receives metadata containing:

```text
document
section
page
chunk_id
```

Chunk IDs are deterministic and document-specific:

```text
<document>-chunk-<index>
```

This ensures IDs remain unique, including for multi-page PDFs, and allows an uploaded document to be replaced cleanly when the same filename is uploaded again.

### Embeddings

Embeddings are generated locally with:

```text
all-MiniLM-L6-v2
```

This avoids sending policy text to a remote embedding service and avoids additional API usage.

### Hybrid retrieval

The retrieval layer combines semantic vector search with lexical BM25 search.

Chroma performs dense vector retrieval using cosine distance. BM25 provides lexical matching for exact terms, policy identifiers, clause references, benefit names, and structured values.

Both retrieval methods return ranked chunk IDs. The rankings are combined using Reciprocal Rank Fusion (RRF):

```text
Vector ranking ──┐
                 ├──> RRF ──> final ranked candidates
BM25 ranking ────┘
---

## 4. Grounding & Refusal

Grounding is implemented as multiple layers rather than relying only on a prompt.

### Step 1 — retrieve evidence

The user's question is embedded and sent to both the vector and BM25 retrieval paths.

Their ranked results are combined using Reciprocal Rank Fusion (RRF), producing the final top 5 candidate chunks.

If no chunks are available, the system immediately returns the safe refusal response.

### Step 2 — evidence resolution

A dedicated LLM call determines one of three decisions:

```text
answer
clarify
refuse
```

The resolver is explicitly instructed to use only the supplied policy context.

It also distinguishes genuine ambiguity from informal language. For example, a question such as:

```text
How many casual leaves we have
```

can still be treated as answerable when the retrieved policy clearly identifies casual leave.

A question such as:

```text
How many leave days do I get?
```

is ambiguous because the policy contains multiple leave types.

### Step 3 — grounded answer generation

Only when the resolver returns `answer` does the system call the final answer-generation step.

The generation prompt requires:

- policy context only
- no general knowledge
- no unsupported assumptions
- complete natural-language answers
- source IDs corresponding to supporting context entries

The LLM uses structured JSON output:

```json
{
  "answer": "string",
  "source_ids": ["string"]
}
```

Temperature is set to `0.0` to reduce unnecessary variation.

### Step 4 — backend citation validation

The backend does not trust the model's source IDs directly.

Each returned source ID is matched against the actual chunks retrieved for that query.

Unknown source IDs are ignored.

Citations are constructed from the retrieved chunk metadata:

```text
document
section
page
```

Duplicate citations pointing to the same document/section/page are removed.

If the final model returns no valid source IDs, or the backend cannot construct any valid citations, the answer is rejected and the system returns the refusal response.

This makes citation validation a backend responsibility rather than relying entirely on the LLM.

### Failure paths

The system safely refuses when:

- retrieval returns no chunks
- the resolver explicitly returns `refuse`
- the final response has no source IDs
- returned source IDs do not map to retrieved chunks

Unexpected infrastructure or service failures in retrieval, query resolution, or answer generation are logged server-side and surfaced to the API as a safe HTTP 500 response rather than being presented as a policy refusal.

The assignment requires the model not to answer from general knowledge when the policy is silent, so refusal is treated as a first-class outcome.

---

## 5. Schemas & APIs

The backend uses Pydantic models for structured request and response validation.

### Query request

```json
{
  "question": "How many casual leave days do employees receive?"
}
```

### Query response

```json
{
  "answer": "Employees receive 12 casual leave days per calendar year.",
  "citations": [
    {
      "document": "leave-policy.md",
      "section": "2.1 Casual leave (CL)",
      "page": ""
    }
  ]
}
```

### Main API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/documents/upload` | Upload and index a policy |
| `GET` | `/documents/` | List uploaded policy documents |
| `DELETE` | `/documents/{filename}` | Delete a document and its indexed chunks |
| `POST` | `/query` | Ask a policy question |
| `GET` | `/health` | Basic service health check |

Whitespace-only queries are rejected before retrieval.

The API returns structured JSON instead of free-form response text so the frontend and any future client can reliably consume answers and citations.

---

## 6. Key Trade-offs

### 6.1 Line-aware chunking vs. more complex semantic or token-aware chunking

A more advanced semantic or token-aware chunking strategy could produce better retrieval boundaries, but it would add complexity and more tuning for a small policy corpus.

The current approach preserves document sections and splits long content at line boundaries where possible. If a single line exceeds the chunk limit, it falls back to character-based splitting. This is intentionally simple and helps avoid breaking structured content such as table rows unnecessarily.

### 6.2 Chroma vs. a production database such as pgvector

PostgreSQL with pgvector would be a stronger choice for a production multi-user deployment, but it introduces additional database setup and operational complexity.

Chroma is sufficient for this prototype because the assignment emphasizes retrieval and grounding design rather than production infrastructure.

### 6.3 Fixed retrieval threshold vs. evidence-based resolution

A single embedding-distance threshold was considered as a hard answer/refusal gate.

It was rejected because semantic distance varies across query types. Ambiguous, supported, and unsupported queries do not separate cleanly at one fixed value.

The final design therefore uses top-k retrieval as candidate evidence and a separate grounded resolver for the semantic decision.

### 6.4 Two LLM calls vs. a single generation call

The query pipeline uses two LLM calls: one grounded resolver first decides whether the query should be answered, clarified, or refused, and a second call generates the final answer with source IDs.

This adds latency and LLM cost compared with using a single generation call. The trade-off is stronger control over refusal and clarification behavior because the decision to answer is separated from answer generation.

For a small assignment-scale corpus, the additional call is acceptable because reliability and grounded behavior are more important than minimizing latency.


### 6.5 Hybrid retrieval vs. vector-only retrieval

Vector search is strong at semantic similarity, but exact policy terms, identifiers, clause references, and structured values can benefit from lexical matching.

The final design therefore combines vector retrieval with BM25 and merges their rankings using RRF.

This improves retrieval robustness at the cost of maintaining an additional lexical index and rebuilding that index when the document corpus changes.

For the prototype, the BM25 index is maintained in memory rather than persisted separately. A production implementation could use a persistent lexical index or a database-backed search engine.

---

## 7. What I Would Harden With Two More Weeks

### 7.1 Evaluation harness

A small regression scenario set is already included to exercise representative answer, clarification, and refusal paths.

With additional time, I would extend this into a real model evaluation harness that runs a fixed policy corpus through the actual LLM and measures answer correctness, refusal correctness, retrieval quality, and citation correctness automatically.

### 7.2 Better PDF and table extraction

The current PDF pipeline successfully handles simple structured policy tables, but arbitrary real-world PDFs can have complex layouts.

The next hardening step would be stronger table-aware extraction and preservation of relationships between rows, columns, headings, and cells.

### 7.3 Hybrid retrieval

The current system combines vector and BM25 retrieval using RRF. A next step would be to add a dedicated reranker over the fused candidate set.

A reranker could improve ordering when multiple semantically related chunks are retrieved, especially as the policy corpus grows.

### 7.4 Authentication and asynchronous ingestion

For a production system, I would add real admin/employee authorization and move larger document ingestion to an asynchronous job flow so uploads do not block request handling.

These are intentionally outside the prototype scope.

---

## 8. Current Limitations


- PDF section headings are not always available, so PDF citations may use page metadata with `section` reported as unavailable.
- Chunking is line-aware rather than token-aware or fully semantic.
- PDF extraction does not use dedicated table reconstruction; structured-table handling has been validated on simple table-formatted policy content.
- The BM25 lexical index is maintained in memory and rebuilt when the indexed corpus changes, so it is not independently persistent across application restarts.
- The vector store is local Chroma rather than a production database.
- The prototype does not implement real authentication or multi-tenant isolation.
- Document replacement is implemented as delete-and-reinsert, so transactional rollback around indexing would be a future hardening area.

These limitations are acceptable for the assignment scope and can be addressed in a production version.
