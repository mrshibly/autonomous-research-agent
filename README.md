# Autonomous AI Research Agent

An AI-powered research assistant that searches the web, reads papers, summarizes findings, and generates structured research reports — all automatically.

## Architecture

```
User → Frontend (React + Vite) → Backend (FastAPI) → Agent Orchestrator
                                                          │
                                                 ┌────────┼────────────┐
                                                 │        │            │
                                            Search   Paper Agent   Summarizer
                                            Agent    (PDF Parse)    Agent
                                                 │        │            │
                                                 └────────┼────────────┘
                                                          │
                                                    Critic Agent → Writer Agent
                                                          │
                                                     Final Report
```

## Quick Start

### Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux

pip install -r requirements.txt

# Copy and configure environment variables
copy .env.example .env       # Windows
# cp .env.example .env       # Mac/Linux

# Edit .env and add your GROQ_API_KEY (free at console.groq.com)

uvicorn app.main:app --reload
```

Backend will be at: http://localhost:8000  
API docs at: http://localhost:8000/docs

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend will be at: http://localhost:5173

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_PROVIDER` | `groq` | LLM provider: `groq`, `openai`, `ollama` |
| `GROQ_API_KEY` | — | Groq API key (free at console.groq.com) |
| `SEARCH_PROVIDER` | `duckduckgo` | Search: `duckduckgo` (free), `serpapi` |
| `EMBEDDING_PROVIDER` | `local` | Embeddings: `local` (free), `openai` |

## Features

- **Multi-Agent Pipeline**: Search → Paper → Summarize → Critic → Writer
- **Multi-Provider LLM**: Groq (free), OpenAI, Ollama (local)
- **Free by Default**: DuckDuckGo search, Arxiv, local embeddings
- **RAG Pipeline**: FAISS vector store with sentence-transformers
- **Real-time Progress**: Polling-based status tracking
- **Structured Reports**: Summary, comparison table, citations
- **Download Reports**: Export as Markdown
