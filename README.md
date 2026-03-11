# 🚀 Autonomous AI Research Agent

<div align="center">

[![Docker](https://img.shields.io/badge/Docker-Published-blue?logo=docker)](https://hub.docker.com/u/mrshibly)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/Frontend-React-61DAFB?logo=react)](https://reactjs.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![HuggingFace](https://img.shields.io/badge/%F0%9F%A4%97%20Space-Live-orange)](https://huggingface.co/spaces/mrshibly/autonomous-research-agent)
[![Maintained](https://img.shields.io/badge/Maintained%3F-yes-green.svg)](https://github.com/mrshibly/autonomous-research-agent/graphs/commit-activity)

**An Autonomous Multi-Agent AI System that produces high-fidelity, citation-aware research reports automatically.**

[Overview](#-overview) • [Premium Features](#-premium-features) • [Architecture](#-system-architecture) • [Demo](#-demo) • [Quick Start](#-quick-start)

</div>

---

# 🌟 Overview

The **Autonomous AI Research Agent** isn't just another LLM wrapper. It's a coordinated system of specialized agents that orchestrates a full research lifecycle:

1.  **Orchestration**: Plans and breaks down complex topics into searchable technical queries.
2.  **Retrieval**: Searches academic databases (ArXiv, Scholar) and the broader web.
3.  **Extraction**: Downloads, parses, and cleans content from PDFs and web pages.
4.  **Verification**: A dedicated Critic Agent audits findings for technical accuracy.
5.  **Synthesis**: Produces a structured report with cross-referenced citations.

---

# ✨ Premium Features

### 🎨 High-Fidelity UI/UX
- **Motion Architecture**: Seamless layout transitions and entrance animations powered by `framer-motion`.
- **Dynamic Research View**: Real-time progress tracking with high-contrast status indicators.
- **Glassmorphism Design**: A modern, sleek aesthetic with dark-mode optimization and premium typography.

### 💬 Intelligent Research Assistant
- **Context-Aware Chat**: Ask specific questions about the analyzed papers using localized RAG.
- **Markdown Support**: Rich message rendering for comparison tables, code snippets, and lists.
- **Session Persistence**: Chat history persists locally, ensuring your findings are never lost.

### 🔗 Utility & Sharing
- **Instant Sharing**: One-click "Copy Link" feature for sharing research insights.
- **Multi-Format Export**: Download reports as high-quality Markdown or structured PDF-ready text.
- **Author Filtering**: Intelligent author parsing (et al. support) for clean academic citations.

---

# 🏗️ System Architecture

### Multi-Agent Pipeline
The system uses a sequential orchestration model with a verification loop:

```mermaid
flowchart LR
    A[Planner] -->|Queries| B[Search]
    B -->|URLs| C[Paper Agent]
    C -->|Text| D[Summarizer]
    D -->|Draft| E[Critic]
    E -->|Feedback| F[Writer]
    F -->|Revision| E
    F -->|Final Report| G[Result]
    
    style E fill:#f96,stroke:#333
    style A fill:#4CAF50,color:#fff
    style G fill:#2196F3,color:#fff
```

### Hybrid RAG Deep Dive
Our retrieval system fuses **Dense (Semantic)** and **Sparse (Keyword)** search to capture both conceptual meaning and exact technical terms.

| Component | Technology | Purpose |
| :--- | :--- | :--- |
| **Dense Search** | Sentence-Transformers + FAISS | Understanding semantic intent & synonyms |
| **Sparse Search** | BM25 Ranking | Matching exact IDs, acronyms, and names |
| **Fusion Layer** | Reciprocal Rank Fusion | Combining best results for high-precision context |

---

# 🛠 Tech Stack

**Frontend**: React 18, Vite, Framer Motion, Axios  
**Backend**: FastAPI, SQLAlchemy (Async), Pydantic  
**AI Core**: OpenAI/Groq/Ollama, FAISS, Sentence Transformers, BM25  
**Infrastructure**: Docker, Hugging Face Spaces, GitHub Actions  

---

# 🐳 Quick Start

Prepare your environment with an `.env` file containing your `OPENAI_API_KEY` or `GROQ_API_KEY`.

### Using Docker (Recommended)
```bash
docker-compose up -d --build
```
- **Dashboard**: [http://localhost:8002](http://localhost:8002)
- **API Docs**: [http://localhost:8001/docs](http://localhost:8001/docs)

### Local Development
1. **Backend**: `cd backend && pip install -r requirements.txt && python run.py`
2. **Frontend**: `cd frontend && npm install && npm run dev`

---

# 👤 Author & Links

**Developed by Shibly**

- **GitHub**: [github.com/mrshibly](https://github.com/mrshibly)
- **HuggingFace**: [mrshibly@HF](https://huggingface.co/mrshibly)
- **Portfolio**: [Join the Research Revolution](https://huggingface.co/spaces/mrshibly/autonomous-research-agent)

---

<div align="center">
  <sub>Built with ❤️ for the AI Research Community</sub>
</div>
