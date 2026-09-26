# 🕉️ Gita AI Guide — Retrieval-Grounded Wisdom Assistant

> A production-oriented Generative AI application that grounds modern-life guidance in the Bhagavad Gita using hybrid Retrieval-Augmented Generation (RAG).

## Overview

**Gita AI Guide** combines an LLM with a searchable corpus of the Bhagavad Gita so responses are grounded in retrieved scripture rather than generated from model memory alone.

The system supports natural-language questions, direct chapter/verse references, semantic retrieval, lexical retrieval, structured responses, and streaming output through a FastAPI backend.

## Why This Project?

A general-purpose LLM can produce fluent answers but may invent references or provide unsupported claims. This project demonstrates how to build a **knowledge-grounded AI application** where retrieval supplies relevant source material before response generation.

## Architecture

```text
User Query
    │
    ▼
FastAPI API
    │
    ▼
Query Understanding
    │
    ├──────────────► Exact Chapter / Verse Lookup
    │
    ▼
Hybrid Retrieval
    ├── Dense Vector Search
    └── BM25 Lexical Search
    │
    ▼
Relevant Gita Verses
    │
    ▼
LLM Response Generation
    │
    ▼
Grounded Structured Answer + References
```

## Key Engineering Features

- **Hybrid RAG** — combines dense vector retrieval with BM25 lexical search.
- **Scripture grounding** — retrieves relevant verses before generating guidance.
- **Precomputed embeddings** — stores normalized verse embeddings for fast local retrieval.
- **Exact reference parsing** — supports inputs such as `2:47`, `Chapter 2 Verse 47`, and `BG 18.66`.
- **Offline retrieval fallback** — BM25 remains available when the embedding API is unavailable.
- **Streaming responses** — FastAPI/SSE provides incremental response delivery.
- **Scripture Explorer** — search chapters, concepts, and individual verses.
- **Structured output** — separates situation, teaching, principle, modern example, actions, and reflection.

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python |
| API | FastAPI |
| LLM | Google Gemini |
| Retrieval | Dense Embeddings + BM25 |
| Embeddings | `gemini-embedding-001` |
| Data | JSON + NumPy |
| Frontend | HTML, CSS, JavaScript |
| Streaming | Server-Sent Events (SSE) |
| Testing | Pytest |
| Deployment | Docker / cloud hosting |

## Project Structure

```text
gita-ai-guide/
├── app.py                         # FastAPI application and API routes
├── rag.py                         # Hybrid retrieval and RAG pipeline
├── requirements.txt               # Python dependencies
├── data/
│   ├── gita_verses.json           # Verse corpus
│   ├── chapters.json              # Chapter metadata
│   └── gita_embeddings.npz        # Precomputed embedding index
├── scripts/
│   ├── build_gita_dataset.py      # Dataset preparation
│   └── generate_embeddings.py     # Embedding generation
├── tests/
│   └── test_rag.py                # Retrieval tests
├── templates/
│   └── index.html                  # Web interface
├── static/
│   ├── css/style.css               # UI styling
│   └── js/app.js                   # Client-side logic
└── Dockerfile
```

## Run Locally

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure environment variables

Create `.env` from `.env.example` and provide your Gemini API key:

```env
GEMINI_API_KEY=your_api_key
MODEL_NAME=gemini-3.6-flash
PORT=8000
```

### 3. Start the API

```bash
python -m uvicorn app:app --reload --port 8000
```

Then open `http://localhost:8000`.

## API Surface

- `POST /api/chat` — generate a streamed, retrieval-grounded response.
- `GET /api/verses/search?q=karma&limit=5` — search verses.
- `GET /api/verses/{chapter}/{verse}` — retrieve a specific verse.
- `GET /api/chapters` — list all chapters.
- `GET /api/config` — inspect model and RAG status.

## Engineering Takeaways

This project demonstrates practical GenAI engineering concepts:

1. **RAG reduces unsupported generation** by supplying relevant source context.
2. **Hybrid retrieval** handles both semantic questions and exact terminology.
3. **Precomputed embeddings** reduce startup work and improve retrieval latency.
4. **Deterministic reference parsing** is preferable to asking an LLM to resolve an exact citation.
5. **Fallback retrieval** improves resilience when an external embedding service is unavailable.

## Future Improvements

- Add retrieval evaluation metrics such as Recall@K and MRR.
- Add citation-level answer evaluation.
- Add multilingual semantic retrieval.
- Add observability for retrieval latency and model latency.
- Add automated CI tests and deployment checks.

---

Built as a hands-on exploration of **RAG, LLM application architecture, retrieval systems, and AI product engineering**.
