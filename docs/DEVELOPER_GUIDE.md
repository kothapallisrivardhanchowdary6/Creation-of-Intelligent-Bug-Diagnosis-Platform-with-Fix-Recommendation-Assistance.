# Developer Guide

## DefectMind AI — Development Reference

---

## Repository Layout

```
Intern M2/
├── README.md                       # Project overview
├── package.json                    # Frontend dependencies
├── vite.config.js                  # Vite config + dev proxy
├── tsconfig.json                   # TypeScript config
├── docker-compose.yml              # Full-stack container orchestration
├── Dockerfile.frontend             # Multi-stage React → Nginx build
├── nginx.conf                      # Nginx SPA routing + API proxy
├── .env.example                    # Environment variable template
├── index.html                      # Vite HTML entry point
│
├── backend/                        # Python/FastAPI backend
│   ├── main.py                     # App factory, router registration, lifespan
│   ├── requirements.txt            # Pinned Python dependencies
│   ├── Dockerfile                  # python:3.11-slim + CPU torch
│   │
│   ├── agents/                     # AI agent implementations
│   │   ├── __init__.py
│   │   ├── definitions.py          # Backward-compat re-exports (M1)
│   │   ├── mock_analysis.py        # Mock analysis data generator (M1)
│   │   ├── orchestrator.py         # Multi-agent pipeline coordinator
│   │   ├── triage_agent.py         # M2: Severity/priority/component classification
│   │   ├── log_analysis_agent.py   # M2: Stack trace parser (Java/Python/Node.js)
│   │   ├── root_cause_agent.py     # M3: RAG + LLM root cause analysis
│   │   ├── duplicate_detection_agent.py  # M3: Semantic similarity duplicate check
│   │   └── remediation_agent.py    # M3: Fix suggestion generator
│   │
│   ├── database/                   # SQLAlchemy layer
│   │   ├── __init__.py
│   │   ├── connection.py           # Async engine, session factory, init_db()
│   │   └── models.py               # ORM models: BugReport, AnalysisResult, HistoricalDefect
│   │
│   ├── routers/                    # FastAPI APIRouter modules
│   │   ├── __init__.py
│   │   ├── bugs.py                 # Bug CRUD + analysis trigger + service singletons
│   │   ├── analytics.py            # M4.1: 9 analytics endpoints
│   │   ├── knowledge.py            # M4.2: KB growth workflow endpoints
│   │   └── search.py               # Semantic search (mock implementation)
│   │
│   ├── services/                   # Singleton service wrappers
│   │   ├── __init__.py
│   │   ├── embedding_service.py    # sentence-transformers wrapper + mock fallback
│   │   ├── chroma_service.py       # ChromaDB operations + mock fallback + _mock_store
│   │   ├── llm_service.py          # OpenAI-compatible HTTP client + mock mode
│   │   └── mock_search.py          # Mock search for /api/search endpoint
│   │
│   ├── chroma_data/
│   │   └── chroma.sqlite3          # ChromaDB persistent store (gitignored in production)
│   │
│   └── tests/
│       ├── __init__.py
│       ├── test_milestone4.py      # M4 comprehensive 104-test suite
│       ├── test_milestone3.py      # M3 agent tests
│       ├── test_milestone2.py      # M2 triage/log agent tests
│       ├── test_agents.py          # M1 agent unit tests
│       ├── test_api.py             # M1 endpoint tests
│       └── test_embeddings.py      # Embedding math tests
│
├── src/                            # React/TypeScript frontend
│   ├── main.tsx                    # React entry point (creates root, mounts App)
│   ├── App.tsx                     # Root component with routing state
│   ├── index.css                   # Tailwind CSS directives
│   │
│   ├── components/
│   │   └── Layout.tsx              # Sidebar + topbar + notification system
│   │
│   ├── pages/
│   │   ├── Dashboard.tsx           # Home: stats + pipeline diagram + recent bugs
│   │   ├── BugSubmission.tsx       # Bug report form with file upload
│   │   ├── BugList.tsx             # Bug management list
│   │   ├── BugAnalysis.tsx         # 5-agent result display
│   │   ├── Analytics.tsx           # M4.1: Recharts analytics dashboard
│   │   ├── KnowledgeBase.tsx       # Semantic KB search
│   │   ├── KnowledgeGrowth.tsx     # M4.2: Add resolved bugs to KB
│   │   └── E2ETest.tsx             # M4.3: In-browser E2E test runner
│   │
│   ├── services/
│   │   ├── api.ts                  # Complete backend API client + E2E runner
│   │   └── mockData.ts             # Mock fallback data for offline development
│   │
│   └── types/
│       └── index.ts                # All TypeScript type definitions
│
├── data/
│   └── historical_defects.csv      # 12 seed defects (Mozilla, Apache, Eclipse)
│
├── scripts/
│   ├── seed_data.py                # Loads historical_defects.csv → ChromaDB
│   ├── evaluate_milestone2.py      # M2 evaluation runner
│   └── evaluate_milestone3.py      # M3 evaluation runner
│
└── docs/                           # Full project documentation
    ├── PROJECT_REPORT.md
    ├── SYSTEM_ARCHITECTURE.md
    ├── API_DOCUMENTATION.md
    ├── DATABASE_DOCUMENTATION.md
    ├── AGENT_AND_RAG_DOCUMENTATION.md
    ├── INSTALLATION_AND_DEPLOYMENT.md
    ├── TESTING_AND_VALIDATION.md
    ├── USER_MANUAL.md
    ├── DEVELOPER_GUIDE.md           ← this file
    ├── SECURITY_AND_LIMITATIONS.md
    ├── PROJECT_PRESENTATION_AND_VIVA.md
    └── CHANGELOG.md
```

---

## Development Setup

See [`INSTALLATION_AND_DEPLOYMENT.md`](INSTALLATION_AND_DEPLOYMENT.md) for full setup instructions. Quick reference:

```bash
# Backend
cd backend
py -3.11 -m venv venv && venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Frontend (separate terminal, project root)
npm install
npm run dev         # http://localhost:3000  (configured in vite.config.js)
```

Both dev servers hot-reload on file save.

---

## Backend Architecture Patterns

### Singleton Services

All three services (LLM, ChromaDB, Embedding) and the Orchestrator are module-level singletons in `routers/bugs.py`:

```python
_llm_service: Optional[LLMService] = None

def get_llm_service() -> LLMService:
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service
```

**Why:** FastAPI starts multiple event loops in tests. Lazy-init ensures services are created in the same event loop that uses them. **Implication for tests:** The `clear_bug_store` fixture must also reset `ChromaService._mock_store` to prevent state bleed between tests.

### In-Memory Store

```python
# routers/bugs.py
bug_store: dict = {}  # { bug_id: bug_dict }
```

This dictionary is the runtime data store. `analytics.py` imports it directly:
```python
from routers.bugs import bug_store, get_chroma_service, get_embedding_service
```

### Agent Wrapper Pattern

Every agent returns a standard wrapper dict:
```python
{
    "agent": "Agent Name",
    "version": "x.y.z",
    "status": "success | error | insufficient_evidence",
    "result": { ... },        # Agent-specific Pydantic model as dict
    "duration": 0.123,
    "timestamp": "...",
    "error": None
}
```

The orchestrator stores these in `results["agents"]` and also promotes the `result` sub-dict to top-level keys for frontend convenience.

### Graceful Degradation

Each agent is called via a safe wrapper:
```python
async def _safe_run(self, agent, bug_data, agent_name):
    try:
        return await agent.analyze(bug_data)
    except Exception as e:
        logger.error(f"Agent '{agent_name}' failed: {e}")
        return self._error_result(agent_name, str(e))
```

This means one agent crashing never prevents other agents from running.

### Pydantic Models

All agent inputs and outputs are validated with Pydantic models. Agents use `model.dict()` to serialise results for JSON. In Pydantic v2, use `.model_dump()` — the `@validator` decorators in M2 agents are v1 syntax and will show deprecation warnings but continue to work.

---

## Frontend Architecture Patterns

### String-Based Routing

`App.tsx` uses a `currentPage: string` state for navigation instead of React Router:

```typescript
const renderPage = () => {
    switch (currentPage) {
        case 'analytics': return <Analytics />;
        case 'kb-growth': return <KnowledgeGrowth />;
        // ...
    }
};
```

To add a new page: add a case here, a `navItem` entry in `Layout.tsx`, and create the page component.

### API Layer (`api.ts`)

All backend calls go through `apiFetch<T>`:
```typescript
async function apiFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 60_000);
    const res = await fetch(`/api${path}`, { signal: controller.signal, ...options });
    if (!res.ok) throw new Error(`HTTP ${res.status}: ...`);
    return res.json();
}
```

- All responses go through snake_case → camelCase converters (`convertBug`, `convertAnalysis`, etc.)
- Use dual-key lookups (`raw.stack_trace ?? raw.stackTrace`) for backward compatibility

### Adding a New Page

1. Create `src/pages/NewPage.tsx`
2. Add `import NewPage from './pages/NewPage';` to `App.tsx`
3. Add `case 'new-page': return <NewPage />;` to `renderPage()` in `App.tsx`
4. Add `{ id: 'new-page', label: 'New Page', icon: SomeIcon }` to `navItems` in `Layout.tsx`

### Adding New Types

Add interfaces to `src/types/index.ts`. If adding M4-style types, append to the end of the file.

---

## Adding a New Backend Endpoint

1. Choose or create the appropriate router file in `backend/routers/`
2. Add the endpoint function with Pydantic request/response models
3. If it's a new router module, register it in `main.py`:
   ```python
   from routers.new_module import router as new_router
   app.include_router(new_router, prefix="/api")
   ```
4. Add the corresponding API function to `src/services/api.ts`
5. Add TypeScript types to `src/types/index.ts`
6. Write tests in `backend/tests/test_milestone4.py` (or a new test file)

---

## Adding a New Agent

1. Create `backend/agents/new_agent.py`
2. Define Pydantic models for input/output
3. Implement the `analyze(self, bug_data, ...) -> Dict` async method
4. Register in `orchestrator.py`:
   - Add lazy-init getter `_get_new_agent()`
   - Add step in `run_m3_pipeline()`
   - Add safe-call wrapper
5. Update `agents/definitions.py` re-exports for backward compat
6. Add to the frontend `AnalysisResult` type in `src/types/index.ts`
7. Add display card to `src/pages/BugAnalysis.tsx`

---

## Coding Conventions

### Python

- **Async everywhere:** All route handlers and service methods are `async def`
- **Pydantic for I/O:** All structured data in/out of agents uses Pydantic models
- **Logging:** Use `logger = logging.getLogger(__name__)` per module
- **Imports:** Absolute imports from the `backend/` root (`from agents.triage_agent import ...`)
- **Type hints:** All functions have parameter and return type annotations
- **Error handling:** Agents must catch all exceptions and return structured error results — never raise

### TypeScript/React

- **All types in `src/types/index.ts`:** No inline `any` in component files
- **API in `api.ts` only:** No `fetch()` calls in component files
- **camelCase in frontend:** All snake_case API fields converted in `api.ts` converters
- **Functional components:** All components are function components with typed props
- **Tailwind only:** No inline style objects except for dynamic values (chart colours)

### Naming Conventions

| Thing | Convention | Example |
|---|---|---|
| Bug ID | `BUG-{12 hex uppercase}` | `BUG-A3F12B9C04E8` |
| KB document ID | `KB-{12 hex uppercase}` | `KB-3B9E3085A512` |
| Historical defect ID | `{PROJECT}-{number}` | `MOZ-1001`, `APC-2003` |
| Agent version | `{milestone}.0.0-M{n}` | `3.0.0-M3` |
| App version | `{major}.{minor}.{patch}-M{milestone}` | `4.0.0-M4` |

---

## Testing Conventions

### Test isolation

```python
@pytest.fixture(autouse=True)
def clear_bug_store():
    bug_store.clear()
    ChromaService._mock_store.clear()
    yield
    bug_store.clear()
    ChromaService._mock_store.clear()
```

### Assertions pattern

- **Structural:** Always assert schema validity first (types, required fields, allowed values)
- **Semantic:** Optional assertions on values with clear `allow_*` flags for cases where mock mode prevents exact matching
- **Error handling:** Test both happy path and error path for every endpoint

### Running tests

```bash
# Run all tests with verbose output
py -3.11 -m pytest tests/test_milestone4.py -v -p no:warnings

# Run a single class
py -3.11 -m pytest tests/test_milestone4.py::TestKnowledgeBaseGrowth -v

# Run a single test
py -3.11 -m pytest tests/test_milestone4.py::TestAnalyticsEndpoints::test_analytics_overview_empty -v
```

---

## Key Files Reference

| File | Lines | Purpose |
|---|---|---|
| `backend/main.py` | 98 | App factory, all router registration |
| `backend/routers/bugs.py` | 160 | Core bug API + singleton services + bug_store |
| `backend/routers/analytics.py` | 450 | All 9 analytics endpoints with filters |
| `backend/routers/knowledge.py` | 460 | KB growth workflow (validate/add/verify) |
| `backend/agents/orchestrator.py` | 330 | Pipeline coordination + safe-call wrappers |
| `backend/agents/triage_agent.py` | 280 | Keyword matching + LLM refinement |
| `backend/agents/log_analysis_agent.py` | 430 | Multi-language regex parser |
| `backend/agents/root_cause_agent.py` | 540 | RAG + LLM + sparse-signal guard |
| `backend/agents/duplicate_detection_agent.py` | 270 | Embedding search + threshold classification |
| `backend/agents/remediation_agent.py` | 450 | Fix generation + evidence labelling |
| `backend/services/chroma_service.py` | 230 | ChromaDB + mock store |
| `backend/services/llm_service.py` | 160 | HTTP client + mock generator |
| `backend/services/embedding_service.py` | 55 | sentence-transformers + mock |
| `backend/tests/test_milestone4.py` | 1240 | 104-test E2E suite |
| `src/App.tsx` | 120 | Root + router + global state |
| `src/services/api.ts` | 900+ | Complete API client + E2E runner |
| `src/types/index.ts` | 450 | All TypeScript types |
| `src/pages/Analytics.tsx` | 460 | Recharts analytics dashboard |
| `src/pages/KnowledgeGrowth.tsx` | 500 | KB growth workflow UI |
| `src/pages/E2ETest.tsx` | 480 | E2E test UI + suite results |

---

## Environment Detection

**Backend detects mock mode automatically:**
```python
# llm_service.py
self.mock_mode = not bool(os.getenv("OPENAI_API_KEY", ""))

# embedding_service.py — fallback when import fails
try:
    from sentence_transformers import SentenceTransformer
    self.model = SentenceTransformer(self.model_name)
except ImportError:
    self.model = None  # → mock embeddings

# chroma_service.py — fallback when import fails
try:
    import chromadb
    self.client = chromadb.PersistentClient(path=persist_dir)
except ImportError:
    self.client = None  # → mock search + _mock_store
```

**Frontend detects backend availability:**
```typescript
// api.ts — falls back to mock data on network error
export async function searchBugs(query, topK): Promise<SearchResult[]> {
    try {
        return await apiFetch('/search', { method: 'POST', ... });
    } catch {
        return sampleHistoricalBugs.filter(...);  // mockData.ts fallback
    }
}
```

---

## Linting and Type Checking

```bash
# TypeScript type checking (no emit)
npm run typecheck

# Production build (includes type check)
npm run build

# Python syntax check (all files)
cd backend
python -c "import py_compile, os; [py_compile.compile(f) for ...]"
```

There is no ESLint or Black configuration currently in the repository. Consider adding these for production quality.
