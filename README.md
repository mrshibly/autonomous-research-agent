---
title: Autonomous AI Research Agent
emoji: 🚀
colorFrom: indigo
colorTo: blue
sdk: docker
pinned: false
---

# 🚀 Autonomous AI Research Agent

[![Docker](https://img.shields.io/badge/Docker-Published-blue?logo=docker)](https://hub.docker.com/u/mrshibly)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/Frontend-React-61DAFB?logo=react)](https://reactjs.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An intelligent, multi-agent autonomous system designed to combat information overload by synthesizing academic papers and web data into structured, actionable research reports.

---

## 🌟 Overview

The **Autonomous AI Research Agent** is a sophisticated 6-stage pipeline that automates the entire research process—from query generation and paper discovery to deep PDF analysis and final synthesis. Unlike standard LLM wrappers, this system employs a **Multi-Agent Orchestrator** with a built-in **Critic Loop** to ensure high-fidelity, hallucination-free output.

### 🎥 Visual Tour

```carousel
![Dashboard Overview](C:\Users\mrshibly\.gemini\antigravity\brain\efd400fc-787c-4fab-95c4-3d940c882adb\research_progress_searching_1773250772555.png)
<!-- slide -->
![Mobile Experience](C:\Users\mrshibly\.gemini\antigravity\brain\efd400fc-787c-4fab-95c4-3d940c882adb\mobile_view_report_1773252776439.png)
<!-- slide -->
![Technical Report](C:\Users\mrshibly\.gemini\antigravity\brain\efd400fc-787c-4fab-95c4-3d940c882adb\final_verification_responsiveness_search_1773252137893.webp)
```

---

## 🏗️ Technical Architecture

The platform is built on a distributed micro-agent architecture where specialized AI agents collaborate through a centralized orchestrator.

```mermaid
flowchart TD
    %% Styling
    classDef user fill:#6366f1,stroke:#4f46e5,stroke-width:2px,color:#fff,rx:8px,ry:8px
    classDef frontend fill:#14b8a6,stroke:#0d9488,stroke-width:2px,color:#fff,rx:8px,ry:8px
    classDef backend fill:#f59e0b,stroke:#d97706,stroke-width:2px,color:#fff,rx:8px,ry:8px
    classDef agent fill:#ec4899,stroke:#db2777,stroke-width:2px,color:#fff,rx:8px,ry:8px
    classDef db fill:#8b5cf6,stroke:#7c3aed,stroke-width:2px,color:#fff,rx:8px,ry:8px
    classDef external fill:#64748b,stroke:#475569,stroke-width:2px,color:#fff,rx:8px,ry:8px

    %% Nodes
    User(("🧑‍💻 User")):::user
    UI["💻 React/Vite Frontend<br>(Dashboard & Chat)"]:::frontend

    subgraph FastAPI_Backend ["FastAPI Backend"]
        API["📡 REST API & WebSockets"]:::backend
        Orchestrator["🎯 Pipeline Orchestrator"]:::backend

        subgraph Multi_Agent_System ["Multi-Agent System"]
            Planner["🧠 Planner Agent<br>(Generates Queries)"]:::agent
            Search["🌐 Search Agent<br>(Web & Academic)"]:::agent
            Paper["📄 Paper Agent<br>(PDF Parsing)"]:::agent
            Summarizer["📝 Summarizer Agent<br>(Info Extraction)"]:::agent
            Critic["⚖️ Critic Agent<br>(Quality Control)"]:::agent
            Writer["✍️ Writer Agent<br>(Synthesis)"]:::agent
        end

        subgraph RAG_Pipeline ["RAG Pipeline"]
            Embeddings["🔢 Local Embeddings<br>(sentence-transformers)"]:::db
            FAISS[("🗄️ FAISS Vector Store<br>+ BM25 (Hybrid)")]:::db
        end

        SQLite[("💿 SQLite Database<br>(Async SQLAlchemy)")]:::db
    end

    Provider["☁️ Groq / OpenAI / Ollama<br>(LLM Core)"]:::external
    Sources["📚 Arxiv / PubMed / Web"]:::external

    %% Edges
    User -- "Requests Research" --> UI
    UI -- "HTTP/WS" --> API
    API -- "Triggers" --> Orchestrator

    Orchestrator --> Planner
    Planner -- "Directs" --> Search
    Search -- "Fetches" --> Paper
    Paper -- "Feeds" --> Embeddings
    Paper -- "Analyzes" --> Summarizer
    Summarizer -- "Drafts" --> Critic

    Critic -- "Verified Feedback Loop" --> Writer
    Writer -- "Refines" --> Critic

    Writer -- "Finalizes" --> Orchestrator
    Orchestrator -- "Real-time Updates" --> UI

    %% Storage
    Orchestrator -. "Persists" .-> SQLite
```

---

## 🔥 Key Technical Highlights

### 1. Unified Hybrid RAG

Utilizes a dual-indexing strategy:

- **Dense Retrieval**: `all-MiniLM-L6-v2` embeddings stored in a FAISS vector store for semantic similarity.
- **Sparse Retrieval**: `BM25` keyword indexing for precise term matching.
- **Result Reranking**: Intelligently combines and ranks results for superior context retrieval during the "Chat with Report" phase.

### 2. Multi-Agent Critic Loop

Features an iterative refinement process where the **Critic Agent** evaluates the **Writer's** output against source documents. If technical accuracy falls below thresholds, the report is autonomously sent back for correction.

### 3. Production-Grade Resilience

- **Smart Retries**: Built-in exponential backoff with jitter for handling LLM rate limits.
- **Real-Time Visibility**: Full-duplex WebSocket communication provides users with live stage updates and agent reasoning logs.
- **Optimized Containers**: Backend image reduced from **4.4GB to 599MB** using multi-stage builds and CPU-optimized machine learning libraries.

---

## 🐳 Getting Started (3-Minute Setup)

### 1. Deploy with Docker (Recommended)

The fastest way to get up and running is via Docker Compose:

```bash
docker-compose up -d
```

- **Web UI**: [http://localhost:8002](http://localhost:8002)
- **API Docs**: [http://localhost:8001/docs](http://localhost:8001/docs)

### 2. Manual Image Pull (Docker Hub)

You can also pull the official pre-built images directly:
*   **Backend**: `docker pull mrshibly/autonomous-research-agent-backend:latest`
*   **Frontend**: `docker pull mrshibly/autonomous-research-agent-frontend:latest`

### 3. Standard Local Setup


If you prefer running natively:

**Backend**:

```bash
cd backend
python -m venv venv
# Activate & Install
pip install -r requirements.txt
cp .env.example .env # Add your GROQ_API_KEY
uvicorn app.main:app --port 8001
```

**Frontend**:

```bash
cd frontend
npm install
npm run dev -- --port 8002
```

---

## 🛠️ Tech Stack

- **Foundations**: React 18, Vite, FastAPI (Python 3.11+)
- **AI/Agents**: Groq, OpenAI API, Ollama, LangGraph-inspired Orchestration
- **RAG/ML**: FAISS, Sentence-Transformers, BM25, PyMuPDF
- **DevOps**: Docker, Multi-stage Builds, GitHub Actions Ready

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.
