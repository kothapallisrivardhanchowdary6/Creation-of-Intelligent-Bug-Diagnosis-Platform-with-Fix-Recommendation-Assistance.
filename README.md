# DefectMind AI — Intelligent Bug Diagnosis Platform

> AI-powered software defect analysis using RAG, multi-agent orchestration, and semantic search.

**Live Application:** [https://defectmind-frontend.onrender.com/](https://defectmind-frontend.onrender.com/)
**Backend API:** [https://defectmind-ai.onrender.com/](https://defectmind-ai.onrender.com/)
**API Docs (Swagger):** [https://defectmind-ai.onrender.com/docs](https://defectmind-ai.onrender.com/docs)

---

## Overview

DefectMind AI is a full-stack intelligent bug diagnosis platform that accepts bug reports (title, description, stack traces, error logs) and runs them through a five-stage AI agent pipeline to produce:

- **Severity and priority classification** (Triage Agent)
- **Stack trace and exception parsing** (Log Analysis Agent)
- **Root cause hypothesis with supporting evidence** (Root Cause Agent)
- **Semantic duplicate detection** (Duplicate Detection Agent)
- **Actionable remediation recommendations** (Remediation Agent)

The platform uses a Retrieval-Augmented Generation (RAG) pipeline backed by ChromaDB and `sentence-transformers/all-MiniLM-L6-v2` to retrieve relevant historical defects, which agents use as grounding evidence.

---

## Features

| Feature | Description | Status |
|---|---|---|
| Bug Submission | Form with title, description, stack trace, logs, file uploads | ✅ Implemented |
| 5-Agent Pipeline | Triage → Log Analysis → Root Cause → Duplicate Detection → Remediation | ✅ Implemented |
| RAG Knowledge Base | 12 seeded historical defects + user-added resolved bugs | ✅ Implemented |
| Defect Analytics | Severity/priority/component/exception/trend charts with filters | ✅ Implemented |
| KB Growth Mechanism | Add confirmed-resolved bugs to the vector store | ✅ Implemented |
| E2E Testing UI | In-browser test runner for 11 test scenarios | ✅ Implemented |
| Semantic Search | Natural language search over the knowledge base | ✅ Implemented |
| Mock LLM Mode | Fully functional without an OpenAI API key | ✅ Implemented |
| Docker Deployment | Docker Compose stack with PostgreSQL + ChromaDB | ✅ Implemented |
| Render Deployment | Live deployment on Render.com | ✅ Live |

---

## Technology Stack

| Layer | Technology | Version |
|---|---|---|
| Frontend | React + TypeScript + Vite | React 18.2, Vite 6.3 |
| UI Styling | Tailwind CSS 4 | v4.1 |
| Charts | Recharts | v2.10 |
| Icons | Lucide React | v0.294 |
| Backend | Python + FastAPI | Python 3.11, FastAPI 0.104 |
| Data Validation | Pydantic | v2.5 |
| Database | PostgreSQL + SQLAlchemy (async) | PG 15, SQLAlchemy 2.0 |
| Vector Store | ChromaDB | v0.4.18 |
| Embeddings | sentence-transformers/all-MiniLM-L6-v2 | 384 dimensions |
| LLM | OpenAI-compatible API (mock mode available) | gpt-4o-mini default |
| Containerisation | Docker + Docker Compose | - |
| Deployment | Render.com | - |

---

## Quick Start

### Prerequisites

- Node.js 18+
- Python 3.11+
- Docker & Docker Compose (optional but recommended)

### 1 — Clone and configure

```bash
git clone <repository-url>
cd "Intern M2"
cp .env.example .env
# Edit .env — set OPENAI_API_KEY if you have one; leave empty for mock mode
```

### 2 — Docker (recommended, all services)

```bash
docker-compose up --build
```

| Service | URL |
|---|---|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:8000 |
| Swagger Docs | http://localhost:8000/docs |
| PostgreSQL | localhost:5432 |

### 3 — Manual setup (frontend only)

```bash
npm install
npm run dev        # http://localhost:3000
```

### 4 — Manual setup (backend only)

```bash
cd backend
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### 5 — Seed the knowledge base

```bash
cd backend
python ../scripts/seed_data.py
```

---

## AI Agent Pipeline

```
Bug Submission
      │
      ▼
 Bug Processing
      │
  ┌───┴──────────────────┐
  ▼                      ▼
RAG Knowledge         Agent Pipeline
   Base               │
      │         ┌─────┼──────┐
      │         ▼     ▼      ▼
      │      Triage  Log   Root Cause
      │             Analysis
      │                │
      │         Duplicate Detection
      │                │
      │           Remediation
      │                │
      └────────────────┤
                       ▼
              Structured Findings
                       │
       ┌───────────────┴───────────────┐
       ▼                               ▼
 Analytics Dashboard           Knowledge Growth
```

---

## Project Structure

```
DefectMind AI/
├── backend/                    # FastAPI backend
│   ├── main.py                 # Application entry point & router registration
│   ├── requirements.txt        # Python dependencies
│   ├── Dockerfile              # Backend container (Python 3.11-slim)
│   ├── agents/                 # AI agent implementations
│   │   ├── triage_agent.py     # Severity/priority/component classifier
│   │   ├── log_analysis_agent.py  # Stack trace + log parser
│   │   ├── root_cause_agent.py    # RAG + LLM root cause analysis
│   │   ├── duplicate_detection_agent.py  # Semantic similarity search
│   │   ├── remediation_agent.py   # Fix suggestion generator
│   │   ├── orchestrator.py        # Multi-agent pipeline coordinator
│   │   └── definitions.py         # Backward-compat re-exports
│   ├── database/               # Database layer
│   │   ├── connection.py       # Async SQLAlchemy engine & session
│   │   └── models.py           # ORM models (BugReport, AnalysisResult, HistoricalDefect)
│   ├── routers/                # FastAPI route handlers
│   │   ├── bugs.py             # Bug CRUD + analysis pipeline trigger
│   │   ├── analytics.py        # Analytics endpoints (M4.1)
│   │   ├── knowledge.py        # KB growth + status + search (M4.2)
│   │   └── search.py           # Semantic search
│   ├── services/               # Core services
│   │   ├── embedding_service.py  # sentence-transformers wrapper
│   │   ├── chroma_service.py     # ChromaDB operations
│   │   ├── llm_service.py        # OpenAI-compatible LLM client
│   │   └── mock_search.py        # Mock search fallback
│   └── tests/                  # Test suite
│       ├── test_milestone4.py  # Comprehensive 104-test E2E suite
│       ├── test_milestone3.py  # M3 pipeline tests
│       ├── test_milestone2.py  # M2 agent tests
│       ├── test_agents.py      # Agent unit tests
│       ├── test_api.py         # API endpoint tests
│       └── test_embeddings.py  # Embedding math tests
├── src/                        # React + TypeScript frontend
│   ├── App.tsx                 # Root component with routing
│   ├── components/Layout.tsx   # Sidebar + nav + notification
│   ├── pages/
│   │   ├── Dashboard.tsx       # Overview + pipeline diagram
│   │   ├── BugSubmission.tsx   # Bug report form
│   │   ├── BugList.tsx         # Submitted bugs management
│   │   ├── BugAnalysis.tsx     # Full 5-agent results display
│   │   ├── Analytics.tsx       # Defect pattern analytics (M4.1)
│   │   ├── KnowledgeBase.tsx   # Semantic KB search
│   │   ├── KnowledgeGrowth.tsx # Add resolved bugs to KB (M4.2)
│   │   └── E2ETest.tsx         # In-browser E2E test runner (M4.3)
│   ├── services/api.ts         # Backend API client + conversion
│   ├── services/mockData.ts    # Mock fallback data
│   └── types/index.ts          # TypeScript type definitions
├── data/
│   └── historical_defects.csv  # 12 seeded historical defects
├── scripts/
│   ├── seed_data.py            # ChromaDB seeding script
│   ├── evaluate_milestone2.py  # M2 evaluation script
│   └── evaluate_milestone3.py  # M3 evaluation script
├── docs/                       # Full project documentation
│   ├── PROJECT_REPORT.md
│   ├── SYSTEM_ARCHITECTURE.md
│   ├── API_DOCUMENTATION.md
│   ├── DATABASE_DOCUMENTATION.md
│   ├── AGENT_AND_RAG_DOCUMENTATION.md
│   ├── INSTALLATION_AND_DEPLOYMENT.md
│   ├── TESTING_AND_VALIDATION.md
│   ├── USER_MANUAL.md
│   ├── DEVELOPER_GUIDE.md
│   ├── SECURITY_AND_LIMITATIONS.md
│   ├── PROJECT_PRESENTATION_AND_VIVA.md
│   └── CHANGELOG.md
├── docker-compose.yml          # Full stack orchestration
├── Dockerfile.frontend         # Nginx + React build container
├── nginx.conf                  # Nginx reverse proxy config
├── .env.example                # Environment variable template
├── package.json                # Frontend dependencies
└── README.md                   # This file
```

---

## API Endpoints Summary

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/health` | Health check |
| `POST` | `/api/bugs` | Submit a new bug report |
| `GET` | `/api/bugs` | List all bug reports |
| `GET` | `/api/bugs/{id}` | Get a single bug |
| `POST` | `/api/bugs/{id}/analyze` | Run full AI analysis pipeline |
| `GET` | `/api/bugs/{id}/analysis` | Retrieve stored analysis |
| `DELETE` | `/api/bugs/{id}` | Delete a bug |
| `POST` | `/api/bugs/upload` | Upload a file attachment |
| `POST` | `/api/search` | Semantic search |
| `GET` | `/api/knowledge-base/status` | KB document count and status |
| `POST` | `/api/knowledge-base/validate` | Validate a resolved bug |
| `POST` | `/api/knowledge-base/add-resolved` | Add confirmed-resolved bug to KB |
| `GET` | `/api/knowledge-base/recent` | Recently added KB entries |
| `POST` | `/api/knowledge-base/search` | Semantic KB search |
| `GET` | `/api/knowledge-base/verify/{id}` | Verify KB entry retrieval |
| `GET` | `/api/analytics/overview` | Analytics overview |
| `GET` | `/api/analytics/severity` | Severity distribution |
| `GET` | `/api/analytics/priority` | Priority distribution |
| `GET` | `/api/analytics/components` | Component-wise frequency |
| `GET` | `/api/analytics/exceptions` | Exception-type frequency |
| `GET` | `/api/analytics/root-causes` | Most common root causes |
| `GET` | `/api/analytics/duplicates` | Duplicate statistics |
| `GET` | `/api/analytics/trends` | Defect trends over time |
| `GET` | `/api/analytics/clusters` | Semantic bug clusters |

Full API documentation: [`docs/API_DOCUMENTATION.md`](docs/API_DOCUMENTATION.md)

---

## Environment Variables

See [`.env.example`](.env.example) for the complete list. Key variables:

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://...` | PostgreSQL connection string |
| `CHROMA_PERSIST_DIR` | `./chroma_data` | ChromaDB persistence path |
| `OPENAI_API_KEY` | *(empty)* | LLM API key — leave empty for mock mode |
| `LLM_MODEL` | `gpt-4o-mini` | OpenAI model name |
| `LLM_MODE` | `mock` | `mock` or `production` |
| `EMBEDDING_MODEL` | `sentence-transformers/all-MiniLM-L6-v2` | Embedding model |

---

## Testing

```bash
# Run full M4 test suite (104 tests)
cd backend
py -3.11 -m pytest tests/test_milestone4.py -v

# Run all tests
py -3.11 -m pytest tests/ -v

# Frontend build verification
npm run build
```

**Latest test run result:** 104/104 passed (see [`docs/TESTING_AND_VALIDATION.md`](docs/TESTING_AND_VALIDATION.md))

---

## Documentation

| Document | Description |
|---|---|
| [PROJECT_REPORT.md](docs/PROJECT_REPORT.md) | Full academic project report |
| [SYSTEM_ARCHITECTURE.md](docs/SYSTEM_ARCHITECTURE.md) | Architecture diagrams and data flow |
| [API_DOCUMENTATION.md](docs/API_DOCUMENTATION.md) | All API endpoints with examples |
| [DATABASE_DOCUMENTATION.md](docs/DATABASE_DOCUMENTATION.md) | DB schemas and vector store |
| [AGENT_AND_RAG_DOCUMENTATION.md](docs/AGENT_AND_RAG_DOCUMENTATION.md) | All five agents and RAG pipeline |
| [INSTALLATION_AND_DEPLOYMENT.md](docs/INSTALLATION_AND_DEPLOYMENT.md) | Setup, Docker, Render deployment |
| [TESTING_AND_VALIDATION.md](docs/TESTING_AND_VALIDATION.md) | Test cases and results |
| [USER_MANUAL.md](docs/USER_MANUAL.md) | End-user step-by-step guide |
| [DEVELOPER_GUIDE.md](docs/DEVELOPER_GUIDE.md) | Developer setup and conventions |
| [SECURITY_AND_LIMITATIONS.md](docs/SECURITY_AND_LIMITATIONS.md) | Security notes and known limitations |
| [PROJECT_PRESENTATION_AND_VIVA.md](docs/PROJECT_PRESENTATION_AND_VIVA.md) | Presentation script and viva Q&A |
| [CHANGELOG.md](docs/CHANGELOG.md) | Version history from Git |

---

## Milestones

| Milestone | Focus | Status |
|---|---|---|
| M1 | Foundation: Bug submission, mock agents, ChromaDB, frontend | ✅ Complete |
| M2 | Enhanced agents: Pydantic validation, real stack trace parsing, parallel execution | ✅ Complete |
| M3 | Full pipeline: Root cause RAG, duplicate detection, remediation with evidence | ✅ Complete |
| M4 | Analytics, KB growth, E2E testing (104 tests all passing) | ✅ Complete |

---

## License

MIT License — Copyright (c) 2025
