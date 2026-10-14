# System Architecture

## DefectMind AI — Architecture Documentation

**Version:** 4.0.0-M4
**Backend:** https://defectmind-ai.onrender.com/
**Frontend:** https://defectmind-frontend.onrender.com/

---

## 1. High-Level Architecture

```mermaid
graph TB
    subgraph Browser["User Browser"]
        UI[React + TypeScript SPA]
    end

    subgraph Frontend_Server["Frontend Server (Nginx / Render)"]
        NGINX[Nginx — Static + SPA Routing]
    end

    subgraph Backend["FastAPI Backend (Python 3.11)"]
        MAIN[main.py — App Entry Point]
        BR[bugs router]
        AR[analytics router]
        KR[knowledge router]
        SR[search router]
    end

    subgraph Services["Core Services"]
        EMB[EmbeddingService<br/>all-MiniLM-L6-v2<br/>384-dim]
        CHR[ChromaService<br/>defect_knowledge_base<br/>cosine similarity]
        LLM[LLMService<br/>OpenAI-compat<br/>mock mode]
    end

    subgraph Agents["AI Agent Pipeline"]
        ORCH[AgentOrchestrator]
        T[Triage Agent]
        L[Log Analysis Agent]
        RC[Root Cause Agent]
        DD[Duplicate Detection Agent]
        REM[Remediation Agent]
    end

    subgraph Data["Data Layer"]
        PG[(PostgreSQL<br/>ORM models)]
        CHDB[(ChromaDB<br/>chroma.sqlite3)]
        MEM[In-Memory<br/>bug_store dict]
    end

    UI -->|HTTP REST /api| NGINX
    NGINX -->|proxy_pass| MAIN
    MAIN --> BR
    MAIN --> AR
    MAIN --> KR
    MAIN --> SR

    BR --> ORCH
    ORCH --> T
    ORCH --> L
    ORCH --> RC
    ORCH --> DD
    ORCH --> REM

    RC --> EMB
    RC --> CHR
    RC --> LLM
    DD --> EMB
    DD --> CHR
    REM --> EMB
    REM --> CHR
    REM --> LLM

    CHR --> CHDB
    BR --> MEM
    MAIN --> PG
```

---

## 2. Agent Pipeline Data Flow

```mermaid
sequenceDiagram
    participant U as User
    participant API as FastAPI
    participant ORCH as Orchestrator
    participant T as Triage Agent
    participant L as Log Analysis Agent
    participant RC as Root Cause Agent
    participant DD as Duplicate Detection Agent
    participant REM as Remediation Agent
    participant EMB as EmbeddingService
    participant CHR as ChromaDB

    U->>API: POST /api/bugs (title, description, stack_trace, error_logs)
    API-->>U: { id: "BUG-xxx", status: "submitted" }

    U->>API: POST /api/bugs/{id}/analyze
    API->>ORCH: run_m3_pipeline(bug_data)

    note over ORCH,L: Step 1+2: Parallel
    ORCH->>T: analyze(bug_data)
    ORCH->>L: analyze(bug_data)
    T-->>ORCH: { severity, priority, component, category, confidence }
    L-->>ORCH: { exceptions[], error_patterns[], failure_point }

    note over ORCH,DD: Step 3+4: Parallel
    ORCH->>RC: analyze(bug_data, triage_result, log_result)
    ORCH->>DD: analyze(bug_data)

    RC->>EMB: embed_text(query)
    EMB-->>RC: [384-dim vector]
    RC->>CHR: search(embedding, top_k=5)
    CHR-->>RC: [{id, document, score, metadata}]
    RC-->>ORCH: { probable_cause, hypotheses[], retrieved_evidence[] }

    DD->>EMB: embed_text(title + description)
    EMB-->>DD: [384-dim vector]
    DD->>CHR: search(embedding, top_k=5)
    CHR-->>DD: [{id, score, metadata}]
    DD-->>ORCH: { classification, top_match_similarity, matched_bugs[] }

    note over ORCH,REM: Step 5: Sequential
    ORCH->>REM: analyze(bug_data, triage, log, root_cause, duplicate)
    REM->>EMB: embed_text(fix query)
    EMB-->>REM: [384-dim vector]
    REM->>CHR: search(embedding, top_k=5)
    CHR-->>REM: historical resolutions
    REM-->>ORCH: { suggested_fix, implementation_steps[], fix_source }

    ORCH-->>API: { bug_id, triage, log_analysis, root_cause, duplicate_detection, remediation }
    API-->>U: Complete AnalysisResult JSON
```

---

## 3. RAG Pipeline

```mermaid
flowchart LR
    subgraph Ingestion["Ingestion (seed_data.py)"]
        CSV["historical_defects.csv<br/>12 defects × 3 chunks = 36 docs"]
        CHUNK[Chunker<br/>title / description / resolution]
        EMB1[EmbeddingService<br/>all-MiniLM-L6-v2]
        STORE[ChromaDB add_documents<br/>defect_knowledge_base]
        CSV --> CHUNK --> EMB1 --> STORE
    end

    subgraph Retrieval["Runtime Retrieval (per analysis)"]
        QUERY[Bug signals:<br/>title + description +<br/>exception_type + component]
        EMB2[EmbeddingService<br/>embed_text]
        SEARCH[ChromaDB.search<br/>cosine similarity<br/>top_k=5]
        RESULTS["Results: [{id, document,<br/>metadata, score}]"]
        QUERY --> EMB2 --> SEARCH --> RESULTS
    end

    subgraph Augmentation["Prompt Augmentation"]
        PROMPT["LLM Prompt:<br/>CURRENT BUG signals<br/>+<br/>RETRIEVED HISTORICAL EVIDENCE<br/>(clearly labelled section)"]
        LLM_OUT[LLM Response:<br/>probable_cause, hypotheses,<br/>agent_reasoning, confidence]
        RESULTS --> PROMPT --> LLM_OUT
    end

    STORE -.->|persisted at<br/>chroma_data/chroma.sqlite3| SEARCH
```

---

## 4. Knowledge Base Growth Workflow (M4.2)

```mermaid
flowchart TD
    A([User submits resolved bug]) --> B{Validate required fields}
    B -- Errors found --> C[Return validation errors<br/>valid=false + errors list]
    B -- Valid --> D{Check duplicate<br/>in ChromaDB}
    D --> E[Generate embedding<br/>using same model<br/>all-MiniLM-L6-v2]
    E --> F{Document ID<br/>collision check}
    F -- Collision --> G[Generate new KB-xxxx ID]
    F -- OK --> H[ChromaDB add_documents<br/>id + document + embedding + metadata]
    G --> H
    H --> I[Verify retrieval<br/>similarity search for new doc]
    I --> J[Log to _recently_added]
    J --> K([Return AddResolvedResult<br/>success=true, doc_id, retrievable])
```

---

## 5. Analytics Architecture (M4.1)

```mermaid
flowchart LR
    subgraph Sources["Data Sources"]
        BS[bug_store dict<br/>in-memory]
        CHDB2[ChromaDB<br/>get_all_documents]
    end

    subgraph Compute["Analytics Compute Layer"]
        OV[/overview\]
        SEV[/severity\]
        PRI[/priority\]
        COMP[/components\]
        EXC[/exceptions\]
        RC2[/root-causes\]
        DUP[/duplicates\]
        TRD[/trends\]
        CLU[/clusters\]
    end

    subgraph Filters["Query Filters"]
        F1[component]
        F2[severity]
        F3[priority]
        F4[exception_type]
        F5[date_from / date_to]
        F6[is_duplicate]
    end

    BS --> Compute
    CHDB2 --> Compute
    Filters --> Compute
    Compute --> JSON[Structured JSON response]
```

---

## 6. Frontend Architecture

```mermaid
flowchart TB
    subgraph AppTSX["App.tsx (root)"]
        STATE["State: currentPage, bugs[], selectedBug,<br/>analysisResult, isLoading, notification"]
        ROUTER[Manual string-based router]
    end

    subgraph Pages["Pages"]
        DASH[Dashboard.tsx]
        SUBMIT[BugSubmission.tsx]
        LIST[BugList.tsx]
        ANALYSIS[BugAnalysis.tsx]
        ANALYTICS[Analytics.tsx]
        KB[KnowledgeBase.tsx]
        KBG[KnowledgeGrowth.tsx]
        E2E[E2ETest.tsx]
    end

    subgraph Layout["Layout.tsx"]
        SIDEBAR[Sidebar + Nav<br/>8 items]
        TOPBAR[Top bar + Loading + Notifications]
    end

    subgraph APILayer["services/api.ts"]
        FETCH[apiFetch helper<br/>AbortController 60s timeout]
        CONV[snake_case → camelCase converters]
        E2ERUN[runE2ETests<br/>8 scenarios + 3 error tests]
    end

    AppTSX --> Layout
    Layout --> Pages
    Pages --> APILayer
    APILayer -->|HTTP REST| Backend[(FastAPI Backend)]
```

---

## 7. Deployment Architecture

```mermaid
flowchart TB
    subgraph LocalDev["Local Development"]
        direction LR
        FE_DEV[Vite dev server<br/>:3000] --> BE_DEV[uvicorn --reload<br/>:8000]
        BE_DEV --> PG_LOCAL[(PostgreSQL<br/>:5432)]
        BE_DEV --> CHR_LOCAL[(ChromaDB<br/>./chroma_data)]
    end

    subgraph Docker["Docker Compose"]
        direction LR
        FE_D[frontend container<br/>Nginx :80 → :5173] --> BE_D[backend container<br/>:8000]
        BE_D --> PG_D[(postgres:15-alpine<br/>:5432)]
        BE_D --> VOL[(chroma_data volume)]
    end

    subgraph Render["Render.com (Production)"]
        direction LR
        FE_R[Static Site<br/>defectmind-frontend<br/>.onrender.com] --> BE_R[Web Service<br/>defectmind-ai<br/>.onrender.com:$PORT]
        BE_R --> ENV[Environment Variables<br/>OPENAI_API_KEY<br/>DATABASE_URL<br/>CHROMA_PERSIST_DIR]
    end
```

---

## 8. Service Dependency Graph

```mermaid
graph LR
    BUGS[routers/bugs.py] --> ORCH[orchestrator.py]
    BUGS --> EMB[embedding_service.py]
    BUGS --> CHR[chroma_service.py]
    BUGS --> LLM[llm_service.py]

    ANALYTICS[routers/analytics.py] --> BUGS
    ANALYTICS --> CHR
    ANALYTICS --> EMB

    KNOWLEDGE[routers/knowledge.py] --> CHR
    KNOWLEDGE --> EMB

    ORCH --> T[triage_agent.py]
    ORCH --> L[log_analysis_agent.py]
    ORCH --> RC[root_cause_agent.py]
    ORCH --> DD[duplicate_detection_agent.py]
    ORCH --> REM[remediation_agent.py]

    RC --> CHR
    RC --> EMB
    RC --> LLM
    DD --> CHR
    DD --> EMB
    REM --> CHR
    REM --> EMB
    REM --> LLM

    T --> LLM
    L --> LLM

    CHR --> CHDB[(ChromaDB<br/>defect_knowledge_base)]
    EMB --> ST[sentence-transformers<br/>all-MiniLM-L6-v2]
    LLM --> OAI[OpenAI API<br/>or mock mode]
```

---

## 9. Data Model Overview

```mermaid
erDiagram
    BUG_REPORT {
        string id PK "BUG-{hex12}"
        string title
        text description
        text stack_trace
        text error_logs
        string environment
        json files
        string status "submitted|analyzing|analyzed|error"
        datetime created_at
        datetime updated_at
    }

    ANALYSIS_RESULT {
        string id PK
        string bug_id FK
        json triage
        json log_analysis
        json root_cause
        json duplicate_detection
        json remediation
        datetime created_at
    }

    HISTORICAL_DEFECT {
        string id PK "e.g. MOZ-1001"
        string title
        text description
        string project
        string component
        string severity
        text resolution
        json metadata_json
        datetime created_at
    }

    CHROMA_DOCUMENT {
        string id PK
        text document
        vector embedding "384-dim float[]"
        json metadata "component, severity, resolution, project"
    }

    BUG_REPORT ||--o| ANALYSIS_RESULT : "has analysis"
    HISTORICAL_DEFECT ||--|| CHROMA_DOCUMENT : "embedded as"
```

---

## 10. Parallel Execution Model

```mermaid
gantt
    title Agent Pipeline Execution (asyncio.gather)
    dateFormat  X
    axisFormat  %Ls

    section Wave 1 (parallel)
    Triage Agent        : 0, 80
    Log Analysis Agent  : 0, 80

    section Wave 2 (parallel)
    Root Cause Agent       : 80, 250
    Duplicate Detection    : 80, 200

    section Wave 3 (sequential)
    Remediation Agent   : 250, 380

    section Total
    Complete Pipeline   : 0, 380
```

*Times are approximate and depend on whether mock or real LLM is used.*

---

## 11. Technology Stack Summary

| Layer | Technology | Version | Role |
|---|---|---|---|
| Frontend | React | 18.2 | UI framework |
| Frontend | TypeScript | 5.7 | Type safety |
| Frontend | Vite | 6.3 | Build tool + dev server |
| Frontend | Tailwind CSS | 4.1 | Utility-first styling |
| Frontend | Recharts | 2.10 | Analytics charts |
| Frontend | Lucide React | 0.294 | Icon library |
| Backend | Python | 3.11 | Runtime |
| Backend | FastAPI | 0.104 | HTTP framework |
| Backend | Pydantic | 2.5 | Data validation |
| Backend | Uvicorn | 0.24 | ASGI server |
| Database | PostgreSQL | 15 | Relational DB (ORM defined, in-memory used in demo) |
| Database | SQLAlchemy | 2.0 | Async ORM |
| Vector DB | ChromaDB | 0.4.18 | Vector store + cosine similarity |
| ML | sentence-transformers | 2.2.2 | `all-MiniLM-L6-v2` 384-dim embeddings |
| ML | numpy | 1.26.2 | Vector math |
| LLM | httpx | 0.25.2 | OpenAI API client |
| Container | Docker | - | Container runtime |
| Container | Docker Compose | v3.8 | Multi-service orchestration |
| Deployment | Render.com | - | Cloud platform |
| Web Server | Nginx | alpine | Static file serving + API proxy |
