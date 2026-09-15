# AI-Based Software Defect Analysis System — Milestones 1 & 2

## Overview

An intelligent software defect analysis system that uses AI agents, RAG (Retrieval-Augmented Generation), and semantic search to automatically triage, analyze, and provide remediation recommendations for software bugs.

### Milestone 2 Update
M2 adds production-grade Triage and Log Analysis agents with:
- Pydantic-validated structured output
- Deterministic regex-based stack trace parsing (Java, Python, Node.js)
- Parallel agent execution via async orchestrator
- Combined bug context for downstream agents
- Graceful handling of missing/messy data

## Architecture

```
Bug Submission UI → FastAPI Backend → Bug Processing → PostgreSQL
                                                        ↓
                              RAG Pipeline ← Embeddings ← ChromaDB
                                                        ↓
                              Semantic Retrieval → Agent Orchestrator
                                                        ↓
                    ┌───────────────────────────────────────────────────┐
                    │  Triage → Log Analysis → Root Cause → Duplicate  │
                    │  → Remediation                                     │
                    └───────────────────────────────────────────────────┘
                                                        ↓
                              Results & Recommendations UI
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React + TypeScript + Vite + Tailwind CSS |
| Backend | Python + FastAPI |
| Database | PostgreSQL + SQLAlchemy |
| Vector DB | ChromaDB |
| Embeddings | sentence-transformers/all-MiniLM-L6-v2 |
| LLM | OpenAI-compatible API (mock mode available) |
| Containerization | Docker + Docker Compose |

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Docker & Docker Compose (optional)

### Setup

1. **Clone and configure:**
```bash
cp .env.example .env
# Edit .env with your configuration
```

2. **Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8000
```

3. **Frontend:**
```bash
cd frontend  # (root directory in this project)
npm install
npm run dev
```

4. **Docker (all-in-one):**
```bash
docker-compose up --build
```

### Using Docker Compose

```bash
docker-compose up --build
```

This starts:
- Frontend on http://localhost:5173
- Backend API on http://localhost:8000
- PostgreSQL on port 5432
- API docs at http://localhost:8000/docs

## Project Structure

```
├── backend/                 # FastAPI backend
│   ├── main.py             # Application entry point
│   ├── agents/             # AI agent definitions
│   │   ├── definitions.py  # Agent implementations
│   │   ├── orchestrator.py # Pipeline orchestrator
│   │   └── mock_analysis.py# Mock analysis generator
│   ├── database/           # Database layer
│   │   ├── connection.py   # DB connection management
│   │   └── models.py       # SQLAlchemy models
│   ├── routers/            # API route handlers
│   │   ├── bugs.py         # Bug CRUD endpoints
│   │   ├── search.py       # Semantic search
│   │   └── knowledge.py    # Knowledge base management
│   ├── services/           # Business logic services
│   │   ├── embedding_service.py  # Text embeddings
│   │   ├── chroma_service.py     # Vector DB operations
│   │   ├── llm_service.py        # LLM integration
│   │   └── mock_search.py        # Mock search
│   └── requirements.txt
├── data/                   # Sample datasets
│   └── historical_defects.csv
├── docs/                   # Documentation
│   ├── ARCHITECTURE.md
│   ├── RAG_PIPELINE.md
│   ├── AGENTS.md
│   └── DATASETS.md
├── scripts/                # Utility scripts
│   └── seed_data.py
├── tests/                  # Test suite
│   ├── test_agents.py
│   ├── test_api.py
│   └── test_embeddings.py
├── src/                    # React frontend
│   ├── App.tsx
│   ├── components/
│   ├── pages/
│   ├── services/
│   └── types/
├── docker-compose.yml
├── .env.example
├── BUILD_REPORT.md
└── README.md
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/bugs` | Submit a new bug report |
| POST | `/api/bugs/upload` | Upload file attachment |
| GET | `/api/bugs/{id}` | Get bug by ID |
| POST | `/api/bugs/{id}/analyze` | Run AI analysis pipeline |
| POST | `/api/search` | Semantic search knowledge base |
| GET | `/api/bugs/{id}/analysis` | Get analysis results |
| GET | `/api/knowledge-base/status` | Knowledge base status |
| GET | `/api/health` | Health check |

## AI Agents

### 1. Triage Agent
Classifies bug severity, priority, category, and component assignment.

### 2. Log Analysis Agent
Parses error logs, stack traces, and identifies exception patterns.

### 3. Root Cause Agent
Identifies probable root cause using RAG-powered historical analysis.

### 4. Duplicate Detection Agent
Detects potential duplicates using semantic similarity (cosine similarity).

### 5. Remediation Agent
Suggests fixes, debugging steps, validation, and regression tests.

## RAG Pipeline

1. **Ingestion**: Raw defects → Cleaning → Chunking → Embeddings → ChromaDB
2. **Retrieval**: Query → Embedding → Vector search → Top-K results
3. **Generation**: Context + Query → LLM → Structured analysis

## Sample Data

The project includes 12 realistic sample defects from:
- **Mozilla Firefox** (4 defects): Networking, Layout, Graphics, CSS
- **Apache HTTP Server/Tomcat** (4 defects): Core, Thread Pool, Parser, Connection Pool
- **Eclipse JDT/Platform** (4 defects): Compiler, UI, Content Assist, Plugin Framework

## Environment Variables

See `.env.example` for all configuration options.

## Known Limitations (Milestone 1)

1. **Mock LLM Mode**: Without an OpenAI API key, the system uses deterministic mock responses
2. **Embedding Model**: Without `sentence-transformers` installed, uses random mock embeddings
3. **ChromaDB**: Without ChromaDB installed, uses in-memory mock vector store
4. **Database**: Frontend demo uses localStorage; backend requires PostgreSQL
5. **File Processing**: Large file uploads may need size limits in production
6. **Concurrency**: Agent pipeline runs sequentially; parallel execution planned for M2

## Testing

```bash
# Backend tests
cd backend
pytest tests/ -v

# Frontend build
npm run build
```

## License

MIT License - See LICENSE file for details.
