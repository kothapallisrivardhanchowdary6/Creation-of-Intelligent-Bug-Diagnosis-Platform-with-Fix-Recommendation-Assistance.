# Changelog

## DefectMind AI — Version History

All changes are sourced from verified Git commit history.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [4.0.0-M4] — 2026-10-13 (Current)

Final milestone. Adds defect pattern analytics, knowledge base growth, and comprehensive end-to-end testing.

### Added — M4.1 Defect Pattern Analytics
- `backend/routers/analytics.py` — nine analytics endpoints:
  - `GET /api/analytics/overview` — severity, priority, component, exception summaries
  - `GET /api/analytics/severity` — severity distribution with component breakdown
  - `GET /api/analytics/priority` — priority distribution
  - `GET /api/analytics/components` — component-wise bug frequency
  - `GET /api/analytics/exceptions` — exception-type frequency
  - `GET /api/analytics/root-causes` — most common root causes
  - `GET /api/analytics/duplicates` — duplicate detection statistics
  - `GET /api/analytics/trends` — defect trends (day/week/month granularity)
  - `GET /api/analytics/clusters` — semantic bug clusters via ChromaDB
  - `GET /api/analytics/remediation-patterns` — fix source and risk distributions
- All analytics support query-parameter filtering (component, severity, priority, exception_type, date range, is_duplicate)
- `src/pages/Analytics.tsx` — full Recharts dashboard (pie, bar, line, radar charts) with live filter bar

### Added — M4.2 Knowledge Base Growth
- `backend/routers/knowledge.py` — extended with:
  - `POST /api/knowledge-base/validate` — structured validation result (not raw 422)
  - `POST /api/knowledge-base/add-resolved` — validate → embed → store → verify pipeline
  - `GET /api/knowledge-base/recent` — recently added KB entries
  - `POST /api/knowledge-base/search` — semantic KB search using same embedding model
  - `GET /api/knowledge-base/verify/{doc_id}` — retrieval verification
  - `GET /api/knowledge-base/status` — wired to real ChromaDB (replaces hardcoded mock)
- `backend/services/chroma_service.py` — added `get_all_documents()`, `get_document_by_id()`, `document_exists()`, and `_mock_store` class dict for consistent mock-mode add/get/exists operations
- `src/pages/KnowledgeGrowth.tsx` — six-step workflow UI (fill → validate → dup check → embed → index → verify)

### Added — M4.3 End-to-End Testing
- `backend/tests/test_milestone4.py` — 104-test comprehensive suite (104/104 passing):
  - TestBugSubmission (10), TestTriageAgent (7), TestLogAnalysisAgent (6)
  - TestRootCauseAgent (7), TestDuplicateDetectionAgent (7), TestRemediationAgent (6)
  - TestRAGPipeline (7), TestAnalyticsEndpoints (14), TestKnowledgeBaseGrowth (15)
  - TestErrorHandling (12), TestPerformance (5), TestStructuredFindings (8)
- `src/pages/E2ETest.tsx` — in-browser test runner for 11 scenarios with suite summary, performance metrics, and JSON export
- `src/services/api.ts` — `runE2ETests()` function with 8 bug scenarios + 3 error-handling cases

### Changed
- `backend/agents/root_cause_agent.py` — sparse-report confidence cap: vague bugs (no stack trace, no error_logs, description < 80 chars) are capped at ≤ 0.50 confidence to prevent overconfident results
- `backend/main.py` — version bumped to `4.0.0-M4`; analytics router registered
- `src/App.tsx` — three new routes: `analytics`, `kb-growth`, `e2e-test`
- `src/components/Layout.tsx` — three new navigation items (Analytics, KB Growth, E2E Testing)
- `src/types/index.ts` — all M4 TypeScript types appended
- `vite.config.js` — dev server configured with `port: 3000`, `strictPort: true`

### Fixed (during audit)
- `backend/agents/root_cause_agent.py` — `NoneType.strip()` crash when bug has `None` stack_trace or error_logs fields
- `backend/routers/knowledge.py` — `ResolvedBugSubmission` Pydantic fields changed from hard `min_length` to defaults, so validation errors are returned as structured JSON (`{valid, errors}`) instead of raw 422

---

## Render Deployment — 2026-10-12 to 2026-10-13

### Changed — `fe060e2` (2026-10-12)
- `backend/Dockerfile` — configured `PORT` env var injection for Render deployment (`uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}`)

### Fixed — `f2c7881` (2026-10-13)
- `src/services/api.ts` — fixed frontend API base URL for Render.com deployment

---

## README Updates — 2026-10-09

### Changed — `9fbc0e3` + `8d74430` (2026-10-09)
- `README.md` — revised license information and updated project title to "DefectMind AI"

---

## [3.0.0-M3] — 2026-09-15

Full five-agent pipeline with real RAG retrieval, evidence/reasoning separation, and LLM integration.

### Added — M3 Agents
- `backend/agents/root_cause_agent.py` — RAG + LLM root cause analysis with `retrieved_evidence` / `agent_reasoning` separation; returns "Insufficient Evidence" when confidence < 0.25
- `backend/agents/duplicate_detection_agent.py` — real cosine similarity duplicate detection with configurable thresholds (0.82 likely_duplicate / 0.55 related_issue)
- `backend/agents/remediation_agent.py` — fix suggestions with `fix_source` labelling (historical_evidence / best_practice / agent_reasoning); `is_speculative` flag on implementation steps

### Added — M3 Infrastructure
- `backend/tests/test_milestone3.py` — M3 agent test suite
- `data/milestone3_test_cases.json` — M3 test case data
- `scripts/evaluate_milestone3.py` — M3 evaluation runner
- `src/pages/BugAnalysis.tsx` — full five-agent results display (significantly expanded)
- `src/services/api.ts` — complete snake_case → camelCase conversion layer for all M3 result types

### Changed
- `backend/agents/orchestrator.py` — full M3 pipeline: Wave 1 (Triage + Log, parallel) → Wave 2 (Root Cause + Duplicate, parallel) → Wave 3 (Remediation, sequential)
- `backend/services/llm_service.py` — `_mock_generate()` with per-agent deterministic JSON responses
- `backend/main.py` — version `3.0.0-M3`

---

## [2.0.0-M2] — 2026-09-15

Production-grade Triage and Log Analysis agents with Pydantic validation.

### Added
- `backend/agents/triage_agent.py` — deterministic keyword classification with 14 component patterns, 10 category patterns, confidence scoring, and optional LLM refinement
- `backend/agents/log_analysis_agent.py` — multi-language stack trace parser (Java, Python, Node.js) using regex; extracts exception type, file, class, method, line number
- `scripts/evaluate_milestone2.py` — M2 evaluation script
- `src/pages/BugAnalysis.tsx` — initial analysis result display
- `src/types/index.ts` — M2/M3 TypeScript types

### Changed
- `backend/agents/orchestrator.py` — `run_m2_pipeline()` running Triage + Log Analysis in parallel via `asyncio.gather`
- `src/services/api.ts` — M2 API client with result converters

---

## [1.0.0-M1] — 2026-09-07

Foundation: bug submission, mock agents, ChromaDB schema, seed data, full frontend.

### Added
- `backend/main.py` — FastAPI app with CORS, lifespan, health endpoint
- `backend/routers/bugs.py` — bug CRUD (in-memory store), file upload
- `backend/routers/search.py` — semantic search endpoint (mock)
- `backend/routers/knowledge.py` — KB status and ingest endpoints
- `backend/database/connection.py` — async SQLAlchemy engine + session
- `backend/database/models.py` — `BugReport`, `AnalysisResult`, `HistoricalDefect` ORM models
- `backend/services/embedding_service.py` — `all-MiniLM-L6-v2` wrapper with mock fallback
- `backend/services/chroma_service.py` — ChromaDB `defect_knowledge_base` collection
- `backend/services/llm_service.py` — OpenAI-compatible client with mock mode
- `backend/agents/definitions.py` — initial agent stubs
- `backend/agents/mock_analysis.py` — mock pipeline data generator
- `data/historical_defects.csv` — 12 historical defects (Mozilla, Apache, Eclipse)
- `scripts/seed_data.py` — ChromaDB seeding script
- `backend/tests/test_agents.py`, `test_api.py`, `test_embeddings.py`
- `src/App.tsx` — React SPA with string-based routing
- `src/components/Layout.tsx` — sidebar navigation
- `src/pages/Dashboard.tsx`, `BugSubmission.tsx`, `BugList.tsx`, `KnowledgeBase.tsx`
- `src/services/mockData.ts` — fallback mock data
- `docker-compose.yml` — PostgreSQL + backend + frontend stack
- `backend/Dockerfile`, `Dockerfile.frontend`, `nginx.conf`
- `.env.example` — full environment variable template

---

## Notes

- Commit messages beginning with "task snapshot" are automated development snapshots; their content is summarised under the milestone they fall within.
- All test results referenced (104/104 passing) were verified on Python 3.11.9, pytest 9.1.1, pytest-asyncio 1.4.0 against mock services.
- No tags exist in this repository. Versions are tracked by milestone labels in commit messages.
