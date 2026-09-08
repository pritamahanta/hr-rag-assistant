# HR FAQ & Policy Assistant

A small Retrieval-Augmented Generation (RAG) application for answering employee questions from uploaded HR policy documents.

The system retrieves relevant policy content, checks whether the question can be answered from that evidence, and returns a grounded answer with citations. When the available policies do not support the question, it clarifies or safely refuses instead of guessing.

## Features

- Upload Markdown (`.md`), text (`.txt`), and PDF (`.pdf`) HR policies
- Section-aware document parsing and chunking
- Local semantic embeddings
- Chroma vector search
- Natural-language policy questions
- Structured `answer / clarify / refuse` query resolution
- Grounded LLM answers with structured JSON output
- Backend-validated citations
- Safe refusal when evidence is missing or unsupported
- List uploaded documents
- Delete uploaded documents and indexed chunks
- Re-upload a document to replace its existing indexed version
- Minimal browser UI
- Automated tests

## Tech Stack

| Component | Technology |
|---|---|
| Backend API | FastAPI |
| Frontend | HTML, CSS, JavaScript |
| Vector store | Chroma |
| Embeddings | `sentence-transformers` — `all-MiniLM-L6-v2` |
| LLM | Groq — `openai/gpt-oss-20b` |
| PDF parsing | `pypdf` |
| Validation | Pydantic |
| Testing | pytest |

Embeddings are generated locally. Only the final query-resolution and answer-generation calls use the remote LLM provider.

## Project Structure

```text
hr-rag-assistant/
├── app/
│   ├── core/
│   ├── models/
│   ├── routes/
│   └── services/
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── app.js
├── tests/
├── test_documents/
├── data/                 # local runtime data; ignored by Git
├── .env
├── .env.example
├── .gitignore
├── DESIGN.md
└── requirements.txt
```

## Requirements

- Python 3.12 or a compatible recent Python version
- A Groq API key

## Setup

### 1. Clone the repository

```bash
git clone <repository-url>
cd hr-rag-assistant
```

### 2. Create and activate a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
```

On Windows PowerShell:

```powershell
python -m venv venv
venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure the environment

Copy the example environment file:

```bash
cp .env.example .env
```

Set your Groq API key in `.env`:

```env
GROQ_API_KEY=your_actual_groq_api_key
```

Do not commit `.env` or any API key.

## Run the Application

Start the FastAPI server:

```bash
uvicorn app.main:app --reload
```

Open the application in your browser:

```text
http://127.0.0.1:8000/
```

Interactive API documentation is available at:

```text
http://127.0.0.1:8000/docs
```

## Using the Application

### Upload a policy

Upload a `.md`, `.txt`, or `.pdf` file from the web interface.

The document is parsed, chunked, embedded locally, and indexed in Chroma.

### Ask a question

Example:

```text
How many casual leave days do employees receive?
```

A supported question returns an answer with its supporting citation.

### Ambiguous question

Example:

```text
How many leave days do I get?
```

Because multiple leave types may exist, the system can ask for clarification rather than assuming a leave type.

### Unsupported question

Example:

```text
Does the company provide dental insurance?
```

When the uploaded policies do not support the question, the system returns a safe refusal rather than using general knowledge.

## API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/documents/upload` | Upload and index a policy |
| `GET` | `/documents/` | List uploaded documents |
| `DELETE` | `/documents/{filename}` | Delete a document and its indexed chunks |
| `POST` | `/query` | Ask a policy question |
| `GET` | `/health` | Health check |

### Query Request

```json
{
  "question": "How many casual leave days do employees receive?"
}
```

### Query Response

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

## Grounding and Refusal

The query flow is intentionally layered:

```text
Question
   ↓
Embedding
   ↓
Top-5 retrieval
   ↓
Evidence resolver
   ├── answer
   ├── clarify
   └── refuse
          ↓
   Final answer generation
          ↓
   source_ids
          ↓
   Backend citation validation
          ↓
   Answer + citations
```

The final answer generator is instructed to use only the retrieved policy context.

Citations are reconstructed by the backend from the actual retrieved chunks. Model-generated source IDs are accepted only when they match a retrieved chunk.

If retrieval, resolution, generation, or citation validation fails, the system uses a safe refusal response instead of returning an unsupported answer.

## Retrieval Details

- Embedding model: `all-MiniLM-L6-v2`
- Vector store: Chroma
- Distance metric: cosine
- Retrieval size: top 5 chunks
- Maximum chunk size: 1000 characters
- Chunk overlap: 150 characters
- Chunk metadata: document, section, page, chunk ID

The retrieval layer provides candidate evidence. It does not use a single hardcoded embedding-distance threshold as the final answerability gate. Answerability is determined using the retrieved context and the evidence resolver.

## Testing

Run the test suite with:

```bash
pytest -q
```

The current test suite covers document chunking, ingestion, retrieval, citations, vector-store operations, query construction, and grounding/refusal behavior.

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `GROQ_API_KEY` | Yes | API key used for Groq LLM calls |

## Notes and Limitations

- PDF section headings are not always available, so PDF citations may use page metadata without a section heading.
- Chunking is currently character-based rather than token-aware or fully semantic.
- Chroma is used as a local vector store for the prototype.
- Authentication, multi-tenancy, production deployment, and other production infrastructure are outside the scope of this prototype.

For the design rationale, trade-offs, grounding flow, and future hardening ideas, see [`DESIGN.md`](DESIGN.md).
