# RAG Personal Knowledge Assistant

A privacy-first document chat system built with RAG (Retrieval-Augmented Generation).
Chat with your PDFs, text files, and markdown documents using a fully local LLM — no data leaves your machine.

## Architecture
┌─────────────────────────────────────────────────────┐
│                    React Frontend                    │
│         Upload UI + Chat UI + Citations UI          │
└──────────────────────┬──────────────────────────────┘
                       │ HTTP
┌──────────────────────▼──────────────────────────────┐
│                 FastAPI Backend                      │
│  /upload          /chat          /evaluate           │
│     │               │                               │
│  Ingestion       Query Pipeline                      │
│  Service         Service                            │
│     │               │                               │
│  Parser→        Embedder→                           │
│  Chunker→       ChromaDB→                           │
│  Embedder→      BM25→                               │
│  ChromaDB       RRF Fusion→                         │
│                 Prompt Builder→                      │
│                 Qwen3 (Ollama)                       │
└──────────────────────────────────────────────────────┘
         │                        │
┌────────▼────────┐    ┌──────────▼────────┐
│   ChromaDB      │    │   Ollama           │
│ (Vector Store)  │    │ (Local LLM)        │
│ Persisted to    │    │ qwen2.5:1.5b       │
│ disk via volume │    │ running on host    │
└─────────────────┘    └────────────────────┘

## Tech Stack

- **Frontend:** React, Tailwind CSS
- **Backend:** Python, FastAPI
- **AI:** Ollama, Qwen2.5, Sentence Transformers
- **Retrieval:** ChromaDB, BM25, Hybrid Search, Reciprocal Rank Fusion
- **Deployment:** Docker, Docker Compose

## Features

- Upload PDF, TXT, and Markdown files
- Intelligent chunking with overlap
- Hybrid search (semantic + keyword)
- Conversational memory
- Citations and source tracking
- Evaluation metrics
- Fully local — no external API calls

## Setup

### Prerequisites
- Python 3.11+
- Node.js 18+
- Ollama (https://ollama.ai)
- Docker Desktop (optional)

### Run locally

**1. Pull the LLM:**
```bash
ollama pull qwen2.5:1.5b
ollama serve
```

**2. Backend:**
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**3. Frontend:**
```bash
cd frontend
npm install
npm start
```

Open http://localhost:3000

### Run with Docker

```bash
docker-compose up --build
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/v1/upload | Upload a document |
| POST | /api/v1/chat | Chat with documents |
| POST | /api/v1/evaluate | Evaluate retrieval quality |
| GET | /health | Health check |