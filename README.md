# Autonomous AI Research Agent

A full-stack, production-ready AI research assistant that autonomously searches the web and academic databases, reads papers, summarizes findings, and generates structured, highly technical research reports. 

Built with **FastAPI**, **React/Vite**, and **LangChain** concepts, featuring a premium dark-theme UI and real-time WebSocket communication.

## 🌟 Key Features

### 🧠 6-Stage Autonomous AI Pipeline
The backend features a robust orchestrator that flows through six specialized agents:
1. **Search Planner Agent**: Analyzes the topic and generates 3-5 diverse search queries to ensure comprehensive coverage.
2. **Search Agent**: Executes queries against **DuckDuckGo** (web) and **Arxiv**, **PubMed**, and **Semantic Scholar** (academic).
3. **Paper Agent**: Downloads PDFs and extracts clean text using `PyMuPDF`.
4. **Summarizer Agent**: Uses LLMs to generate structured summaries for each paper.
5. **Critic Agent**: Cross-references summaries against source text, scores relevance (0-1), and provides constructive JSON feedback.
6. **Writer Agent**: Compiles the final report, utilizing a **Self-Correction Loop** to iterate based on Critic feedback until high technical quality is achieved.

### 🔍 Hybrid RAG & Interactive Chat
- **Hybrid RAG**: Combines exact-match keyword search (**BM25**) with semantic vector search (**FAISS** + local `sentence-transformers`) for highly accurate document retrieval.
- **Interactive Chat**: Includes an off-canvas sidebar where users can chat directly with the research report. The AI provides answers grounded purely in the analyzed papers, complete with inline citations.

### ⚡ Real-Time & Polished UX
- **WebSockets**: Real-time progress tracking of the entire 6-stage pipeline.
- **Premium UI**: Glassmorphism, fluid animations, and a responsive dark theme built with Vite and React.
- **Multi-Format Export**: Robust backend-driven exports force reliable downloads for **PDF**, **Markdown**, and **BibTeX** citation files.

### 🛠️ Flexible & Free-Tier Friendly
- **Multi-Provider LLM**: Easily switch between **Groq** (free, default), **OpenAI**, or **Ollama** (100% local).
- **Free APIs**: Defaults to free services (DuckDuckGo, Arxiv, local embeddings) meaning you only need a free Groq API key to start.
- **Async SQLite**: Lightweight, persistent database using SQLAlchemy for task and paper history.

---

## 🏗️ Architecture

```text
User → Frontend (React + Vite) → Backend (FastAPI) → Agent Orchestrator (WebSockets)
                                                          │
   ┌──────────────────────────────────────────────────────┴───────────────────────┐
   │                                                                              │
 Planner → Search  → Paper Agent → Summarizer → Critic Agent ↺ Writer Agent  → Final
 Agent     Agent     (PDF Parse)     Agent      (Scoring &      (Drafting)     Report
           (Arxiv/                              Feedback)
           Pubmed)
```

---

## 🚀 Quick Start

### 1. Backend Setup (FastAPI)

```bash
cd backend
python -m venv venv

# Activate virtual environment
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux

# Install dependencies including PyMuPDF and fpdf2
pip install -r requirements.txt

# Configure environment
cp .env.example .env

# REQUIRED: Edit .env and add your GROQ_API_KEY (Get one free at console.groq.com)
```

Run the backend server:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8001
```
* Backend runs at: `http://localhost:8001`
* Swagger API Docs: `http://localhost:8001/docs`

### 2. Frontend Setup (React/Vite)

```bash
cd frontend
npm install
npm run dev
```
* Frontend runs at: `http://localhost:5173`

---

## ⚙️ Environment Configuration (`.env`)

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_PROVIDER` | `groq` | Choose `groq`, `openai`, or `ollama`. |
| `GROQ_API_KEY` | — | Required if using Groq. |
| `GROQ_MODEL` | `llama-3.3-70b-versatile` | Recommended Groq model for complex tasks. |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Point to your local Ollama instance. |
| `EMBEDDING_PROVIDER` | `local` | `local` uses free CPU embeddings. `openai` uses paid API. |
| `SEARCH_PROVIDER` | `duckduckgo` | Free web search. Alternative: `serpapi`. |
| `MAX_PAPERS` | `5` | Maximum number of papers to parse per task. |

---

## 🛡️ Security & Performance
- **Rate Limiting**: Integrated `SlowAPI` to prevent abuse (e.g., 5 tasks per minute).
- **CORS Configuration**: Explicitly configured to expose necessary headers (`Content-Disposition`) for robust file downloads.
- **Input Sanitization**: Topic strings are sanitized to prevent path traversal and database injection issues.
