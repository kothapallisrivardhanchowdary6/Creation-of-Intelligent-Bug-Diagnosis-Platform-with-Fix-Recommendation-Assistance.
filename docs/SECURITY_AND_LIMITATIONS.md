# Security and Limitations

## DefectMind AI — Security Considerations and Known Limitations

---

## 1. Security Considerations

### 1.1 Authentication and Authorisation

**Current state:** The API has **no authentication**. Any caller with network access to the backend can:
- Submit, read, analyze, and delete all bug reports
- Add entries to the knowledge base
- Call all analytics endpoints

**Risk:** Medium for internal/demo use; High for internet-exposed production use.

**Recommendation:** Implement JWT-based authentication before any production deployment handling real proprietary bug data. The `python-jose[cryptography]` library is already in `requirements.txt`.

---

### 1.2 CORS Configuration

**Current state:**
```python
app.add_middleware(CORSMiddleware, allow_origins=["*"], ...)
```

All origins are allowed. This is appropriate for a demo but should be restricted in production.

**Recommendation:**
```python
allow_origins=[
    "https://defectmind-frontend.onrender.com",
    "http://localhost:3000",   # local dev (vite.config.js port)
    "http://localhost:5173"    # Docker Compose mapped port
]
```

---

### 1.3 In-Memory Data Store

**Current state:** Bug reports are stored in a process-level Python dictionary (`bug_store`). This means:
- No persistence across server restarts
- No encryption at rest
- No access logging

**Risk:** Any data in bug reports (including potentially sensitive stack traces, internal error messages, API keys accidentally pasted) is held in plain memory and lost on restart.

**Recommendation:** Migrate to the existing PostgreSQL ORM models with proper connection encryption and access controls before handling sensitive production data.

---

### 1.4 File Upload Handling

**Current state:** File uploads are accepted, read as text, and returned to the caller. They are not persisted server-side.

```python
@router.post("/bugs/upload")
async def upload_file(file: UploadFile = File(...)):
    content = await file.read()
    return {"name": file.filename, "content": content.decode("utf-8", errors="replace"), "size": len(content)}
```

**Risks:**
- No file size limit — a very large file could exhaust server memory
- No file type validation beyond the frontend JavaScript check
- File content is returned to the client verbatim — potential for reflected injection if rendered unsafely

**Recommendation:** Add `max_size` enforcement in the endpoint, validate MIME types server-side, and never render file content as HTML.

---

### 1.5 LLM Prompt Injection

**Risk:** User-supplied bug descriptions and stack traces are injected directly into LLM prompts. A malicious user could craft input designed to manipulate the LLM's behaviour (e.g., "Ignore previous instructions and...").

**Current mitigations:**
- Evidence and signals are injected in clearly-labelled sections (`=== CURRENT BUG ===`, `=== RETRIEVED HISTORICAL EVIDENCE ===`)
- LLM responses are parsed as structured JSON — free-text injection in the response is discarded
- Mock mode is entirely deterministic and not affected

**Recommendation:** Add input length limits (title ≤ 500 chars, description ≤ 5000 chars, stack trace ≤ 10000 chars). Consider sanitising input to remove common injection patterns.

---

### 1.6 LLM API Key Security

**Current state:** `OPENAI_API_KEY` is read from environment variables, never logged, and never returned in API responses.

**Checklist:**
- ✅ Not hardcoded in source
- ✅ Not included in `.env.example`
- ✅ Not returned in any API endpoint
- ✅ `.gitignore` should exclude `.env` (verify before committing)
- ⚠️ The key is accessible to any code running in the backend process — ensure third-party dependencies are trusted

---

### 1.7 SQL Injection

**Risk:** Low. SQLAlchemy with parameterised queries is used for all database operations. No raw SQL string interpolation is present.

---

### 1.8 Dependency Security

Production dependencies should be monitored for known vulnerabilities. Key packages to watch:

| Package | CVE monitoring |
|---|---|
| `fastapi` | https://github.com/tiangolo/fastapi/security/advisories |
| `pydantic` | https://github.com/pydantic/pydantic/security |
| `chromadb` | https://github.com/chroma-core/chroma/security |
| `httpx` | https://github.com/encode/httpx/security |
| `python-jose` | https://github.com/mpdavis/python-jose/issues |

Run `pip audit` periodically to scan for vulnerabilities.

---

### 1.9 HTTPS

**Current state:** Render.com provides HTTPS by default for both the frontend and backend. All live traffic is encrypted in transit.

For local Docker deployments behind a load balancer or reverse proxy, ensure HTTPS termination is configured.

---

## 2. Known Limitations

### 2.1 Data Persistence

**Limitation:** The in-memory `bug_store` dictionary loses all data on server restart. The PostgreSQL ORM models (`BugReport`, `AnalysisResult`, `HistoricalDefect`) exist and tables are created on startup, but no write operations go to the database at runtime.

**Impact:** All submitted bugs are lost when the Render.com service is redeployed or spun down. ChromaDB data in the persistent volume survives restarts.

**Workaround:** For important bugs, export the analysis JSON via the API before the server restarts.

---

### 2.2 Mock LLM Accuracy

**Limitation:** Without an OpenAI API key, the mock LLM returns a single pre-written JSON template per agent type, regardless of the actual bug content:

- **Triage:** Always returns `severity: "high"`, `category: "Null Reference"`, `component: "Core Module"` — deterministic classification based on keyword matching is the actual primary mechanism
- **Root Cause:** Always returns the same "null/bounds check" probable cause template  
- **Remediation:** Always returns the same null-reference fix template

This means root cause and remediation output is not semantically tailored to the specific bug when running in mock mode.

**Impact:** For demonstrations and structural validation, mock mode is fully functional. For accurate semantic analysis, a real LLM is required.

---

### 2.3 Knowledge Base Size

**Limitation:** The seeded knowledge base contains only 12 historical defects (36 document chunks). Effective RAG-based retrieval typically requires hundreds to thousands of records.

**Impact:**
- Duplicate detection will not classify many real-world bugs as duplicates
- Root cause retrieval evidence may not match the bug's specific technology stack
- The semantic clusters in analytics are limited

**Workaround:** Use the KB Growth mechanism to add more resolved bugs, or extend `seed_data.py` to load from a larger defect dataset.

---

### 2.4 Mock Search Endpoint

**Limitation:** `POST /api/search` uses `mock_search.py` which returns hardcoded results regardless of the query text. Real ChromaDB + embeddings are used in agent pipelines (via `get_chroma_service()`/`get_embedding_service()`) but not wired to this endpoint.

**Impact:** The Knowledge Base search page returns the same five results for any query.

**Fix:** Wire the search endpoint to the real `ChromaService.search()` using the `get_embedding_service()` singleton. This is a one-function change in `routers/search.py`.

---

### 2.5 Mock Duplicate Detection

**Limitation:** When ChromaDB is not installed, `chroma_service._mock_search()` returns the same five hardcoded bugs with fixed similarity scores (0.89, 0.82, 0.75, 0.71, 0.68) for every query.

**Impact:** Every bug will be classified as `related_issue` or `likely_duplicate` regardless of content, because the top mock score (0.89) exceeds both thresholds.

**This is expected mock behaviour** and noted in test comments. Real duplicate detection requires ChromaDB and sentence-transformers.

---

### 2.6 Concurrency

**Limitation:** The `bug_store` dictionary is not protected by locks. Under simultaneous requests, race conditions could corrupt the store.

**Impact:** Low risk for demo/development use with one or two concurrent users. Not suitable for production multi-user concurrent access.

**Recommendation:** Replace with the PostgreSQL backend for any multi-user production deployment.

---

### 2.7 No User Sessions

**Limitation:** All bugs submitted are visible to all users of the application. There is no concept of user accounts, sessions, or data isolation.

---

### 2.8 English-Only Analysis

**Limitation:** The `all-MiniLM-L6-v2` embedding model is optimised for English. The triage keyword lists, stack trace parsers, and LLM prompts are English-only.

**Impact:** Non-English bug descriptions will produce lower-quality triage, retrieval, and analysis results.

---

### 2.9 Stack Trace Language Coverage

**Limitation:** The `LogAnalysisAgent` has dedicated parsers for Java, Python, and Node.js. Other languages (Rust, Go, C++, C#, Ruby, PHP) fall back to the generic `ERROR|FATAL|CRITICAL` regex parser, which produces lower-quality exception extraction.

---

### 2.10 React Router Not Used

**Limitation:** Despite `react-router-dom` being installed, the application uses manual string-based routing via `currentPage` state. This means:
- Browser back/forward navigation does not work as expected
- Deep-linking to specific pages is not possible
- URLs do not change when navigating between pages

---

### 2.11 Large Bundle Size

**Limitation:** The Vite build produces a 742 KB JavaScript bundle (gzip: 200 KB). Recharts and other dependencies contribute significantly.

**Impact:** Initial page load may be slow on slow connections.

**Recommendation:** Implement code splitting with `React.lazy()` and `Suspense` for the Analytics, KnowledgeGrowth, and E2ETest pages.

---

## 3. Future Improvements

Ordered by impact:

| Priority | Improvement | Effort |
|---|---|---|
| High | Connect PostgreSQL ORM models to runtime — persistent bug storage | Medium |
| High | JWT authentication + RBAC | Medium |
| High | Wire `/api/search` to real ChromaDB | Low (1 function) |
| High | Seed larger knowledge base (1000+ defects from public trackers) | Medium |
| Medium | WebSocket streaming for analysis progress | Medium |
| Medium | React Router for proper URL-based navigation | Low |
| Medium | Code splitting for large page components | Low |
| Medium | Playwright E2E browser tests | Medium |
| Medium | Multi-language stack trace support (Rust, Go, C#) | Medium |
| Low | LLM model selection per agent | Low |
| Low | PDF/Markdown analysis export | Low |
| Low | Bug edit functionality | Low |
| Low | Multi-tenancy / project isolation | High |
