# 🚀 Autonomous AI Research Agent

<div align="center">

[![Docker](https://img.shields.io/badge/Docker-Published-blue?logo=docker)](https://hub.docker.com/u/mrshibly)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/Frontend-React-61DAFB?logo=react)](https://reactjs.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![HuggingFace](https://img.shields.io/badge/%F0%9F%A4%97%20Space-Live-orange)](https://huggingface.co/spaces/mrshibly/autonomous-research-agent)

**A production-ready multi-agent AI system that autonomously researches topics, analyzes academic papers, and generates structured research reports with verified citations.**

[Overview](#-overview) • [Features](#-features) • [Architecture](#-system-architecture) • [Tech Stack](#-tech-stack) • [Quick Start](#-quick-start)

</div>

---

# 🌟 Overview

The **Autonomous AI Research Agent** is a **multi-agent LLM system** designed to automate the entire research process.

<img width="1913" height="947" alt="image" src="https://github.com/user-attachments/assets/709dc775-7085-406c-b20f-6fe71641974e" />

Instead of simply prompting an LLM, the system coordinates specialized agents that:

1. Generate research queries
2. Discover relevant academic papers
3. Parse PDFs and extract structured text
4. Analyze findings using LLM reasoning
5. Verify technical accuracy through a critic loop
6. Produce structured research reports with citations

The result is a **high-fidelity research synthesis pipeline** that helps reduce information overload.

---

# ✨ Features

## 🤖 Multi-Agent AI Architecture

The system consists of specialized agents collaborating through a centralized orchestrator.

| Agent            | Responsibility                          |
| ---------------- | --------------------------------------- |
| Planner Agent    | Generates research queries              |
| Search Agent     | Retrieves academic papers & web sources |
| Paper Agent      | Downloads and parses PDFs               |
| Summarizer Agent | Extracts technical insights             |
| Critic Agent     | Verifies technical accuracy             |
| Writer Agent     | Generates final research report         |

---

## 🔍 Hybrid Retrieval (RAG)

To improve factual grounding, the system uses **Hybrid Retrieval-Augmented Generation**.

| Method             | Technology             |
| ------------------ | ---------------------- |
| Semantic Retrieval | Sentence Transformers  |
| Vector Search      | FAISS                  |
| Keyword Search     | BM25                   |
| Result Fusion      | Reciprocal Rank Fusion |

This ensures **high-quality retrieval for academic queries and technical papers**.

---

## ⚡ Real-Time Research Pipeline

Users can watch the research pipeline execute live:

* Query generation
* Paper discovery
* Document analysis
* Report synthesis

This is powered by **WebSockets + FastAPI streaming updates**.

---

## 💬 Chat with the Research Report

After generating a report, users can ask follow-up questions using a **localized RAG pipeline** over the analyzed documents.

---

# 🧠 System Architecture

```mermaid
flowchart LR
    A[Planner Agent] -->|Research Queries| B[Search Agent]
    B -->|Paper URLs| C[Paper Agent]
    C -->|Extracted Text| D[Summarizer Agent]
    D -->|Draft Report| E[Critic Agent]
    E -->|Feedback| F[Writer Agent]
    F -->|Revision Loop| E
    F -->|Final Report| G[Research Report]

    style A fill:#4CAF50,color:#fff
    style G fill:#2196F3,color:#fff
    style E fill:#f96
```

The **Critic Agent loop** ensures the final output maintains **technical accuracy and grounded citations**.

---

# 🛠 Tech Stack

### Frontend

* React 18
* Vite
* Framer Motion
* Axios

### Backend

* FastAPI
* Async SQLAlchemy
* Pydantic

### AI / ML

* OpenAI / Groq / Ollama
* Sentence Transformers
* FAISS
* BM25

### Infrastructure

* Docker
* HuggingFace Spaces
* GitHub Actions

---

# 📂 Project Structure

```
autonomous-research-agent
│
├── backend
│   ├── agents
│   ├── pipelines
│   ├── rag
│   └── run.py
│
├── frontend
│   ├── components
│   ├── pages
│   └── ui
│
├── docker
├── docs
└── docker-compose.yml
```

---

# 🎥 Demo

Try the live version:

https://huggingface.co/spaces/mrshibly/autonomous-research-agent

---

# 🐳 Quick Start

Create an `.env` file:

```
OPENAI_API_KEY=your_key
```

or

```
GROQ_API_KEY=your_key
```

---

## Run with Docker (Recommended)

```bash
docker-compose up -d --build
```

Access:

Frontend
http://localhost:8002

API Docs
http://localhost:8001/docs

---

## Run Locally

### Backend

```bash
cd backend
pip install -r requirements.txt
python run.py
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

---

# 🧪 Example Workflow

User query:

```
Latest methods for improving LLM reasoning
```

System pipeline:

<img width="1060" height="181" alt="image" src="https://github.com/user-attachments/assets/d6af9fb1-e911-4146-a889-de6c4f3eb33a" />

Output:

A **structured research report with citations and technical insights**.
<img width="1920" height="5261" alt="image" src="https://github.com/user-attachments/assets/82f699e6-f315-49f5-bba8-bce1c9b4579e" />

---

# 🚀 Roadmap

Future improvements:

* Agent memory
* automatic dataset creation
* citation graphs
* evaluation benchmarks
* streaming report generation
* distributed agent orchestration

---

# ⭐ Support

If you find this project useful, please consider giving it a ⭐ on GitHub.
