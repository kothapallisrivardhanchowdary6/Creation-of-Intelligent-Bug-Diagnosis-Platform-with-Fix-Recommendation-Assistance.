# Project Report

## DefectMind AI — Intelligent Bug Diagnosis Platform Using RAG and Multi-Agent AI

**Version:** 4.0.0-M4
**Live URL:** https://defectmind-frontend.onrender.com/
**Backend API:** https://defectmind-ai.onrender.com/

> **Note on author details:** This document uses placeholders (`[Author Name]`, `[Institution]`, `[Supervisor]`) for personal and institutional information that must be filled in by the project author.

---

## Abstract

DefectMind AI is an intelligent software defect analysis platform that combines Retrieval-Augmented Generation (RAG) with a five-stage multi-agent AI pipeline to automate the diagnosis and remediation of software bugs. The system accepts bug reports containing descriptions, stack traces, and error logs, then routes them through specialised AI agents that perform triage classification, log analysis, root cause identification, duplicate detection, and remediation recommendation. A 384-dimensional ChromaDB vector store backed by the `sentence-transformers/all-MiniLM-L6-v2` embedding model provides semantic context from a curated historical defect knowledge base. The platform operates without requiring a live LLM API key via a deterministic mock mode, and scales to real LLM providers when an OpenAI-compatible key is supplied. A React/TypeScript frontend delivers interactive dashboards, defect analytics, knowledge base growth workflows, and an in-browser end-to-end test runner. The complete system comprises 57 source files, a 104-test suite with 100% pass rate, a Docker Compose deployment configuration, and a live Render.com deployment.

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Problem Statement](#2-problem-statement)
3. [Objectives](#3-objectives)
4. [Literature Review / Existing Systems](#4-literature-review--existing-systems)
5. [Proposed System](#5-proposed-system)
6. [System Requirements](#6-system-requirements)
7. [System Architecture](#7-system-architecture)
8. [Implementation](#8-implementation)
9. [Results and Screenshots](#9-results-and-screenshots)
10. [Testing and Validation](#10-testing-and-validation)
11. [Limitations](#11-limitations)
12. [Conclusion and Future Work](#12-conclusion-and-future-work)
13. [References](#13-references)

---

## 1. Introduction

Software defect management is a fundamental challenge in modern software engineering. Teams spend a disproportionate amount of engineering time on manual bug triage — determining severity, assigning priority, identifying root causes, and looking up similar previously-resolved issues. As codebases and teams scale, this process becomes a bottleneck. Automated tools that can parse stack traces, identify exception patterns, search historical records, and generate actionable fix recommendations can dramatically reduce mean-time-to-resolution (MTTR).

DefectMind AI addresses this challenge by integrating four modern AI capabilities into a single, coherent platform:

1. **Multi-agent orchestration** — specialised agents that each focus on a single analytical task, coordinated by an asynchronous orchestrator.
2. **Retrieval-Augmented Generation (RAG)** — agents ground their reasoning in retrieved historical defects, preventing hallucinated but unsupported conclusions.
3. **Semantic vector search** — ChromaDB with cosine similarity provides sub-second retrieval of contextually similar bugs.
4. **Defect pattern analytics** — a real-time analytics layer computes distributions, trends, and semantic clusters over the accumulated bug corpus.

The project was developed across four milestones, progressively adding capabilities from a basic mock pipeline (M1) through production-grade agents (M2–M3) to a complete analytics and knowledge growth system (M4).

---

## 2. Problem Statement

Software development organisations face several interconnected defect management problems:

**Manual triage is slow and inconsistent.** When a bug is filed, a senior engineer must manually read the report, classify its severity, determine which component it affects, and assign priority. This requires domain expertise and is often subjective, leading to misclassified bugs that block incorrect teams.

**Root cause identification requires deep historical knowledge.** A developer resolving a `NullPointerException` in a caching layer may not know that an identical bug was resolved six months ago in a different module. Tribal knowledge is lost when engineers change teams.

**Duplicate bugs waste triage effort.** Large open-source projects (Mozilla Firefox, Apache, Eclipse) regularly receive hundreds of duplicate bug reports. Manual deduplication consumes significant engineering bandwidth.

**Remediation recommendations are ad hoc.** Without systematic retrieval of similar historical resolutions, engineers cannot leverage institutional knowledge when writing fix descriptions.

**Existing solutions are insufficient.** Static analysis tools (SonarQube, Checkstyle) detect code quality issues but do not diagnose runtime failures. Traditional issue trackers (Jira, Bugzilla) provide workflow but no AI-assisted analysis. LLM chatbots can reason about code but have no access to proprietary historical defect data and may hallucinate solutions.

---

## 3. Objectives

The primary objectives of DefectMind AI are:

1. Implement a **bug submission system** that accepts structured reports including free-text descriptions, stack traces, error logs, and file attachments.
2. Build a **multi-agent AI pipeline** with five specialised agents: Triage, Log Analysis, Root Cause, Duplicate Detection, and Remediation.
3. Implement a **RAG pipeline** using ChromaDB and sentence-transformers to ground agent reasoning in historical defect data.
4. Ensure agents **distinguish evidence from inference** — never presenting unsupported reasoning as confirmed facts.
5. Implement **defect pattern analytics** covering severity distributions, component frequency, exception patterns, duplicate rates, and temporal trends.
6. Build a **knowledge base growth mechanism** that allows confirmed-resolved bugs to be embedded and added to the vector store.
7. Deliver a **comprehensive test suite** with at least five end-to-end test scenarios including duplicate, related, and insufficient-evidence cases.
8. Deploy the complete system to a **public URL** accessible without installation.
9. Support a **mock mode** that provides full functionality without external API keys.

---

## 4. Literature Review / Existing Systems

### 4.1 Existing Approaches

**Automated Bug Triage:**
Early work by Anvik et al. (2006) applied machine learning to assign bug reports to developers using Naive Bayes classifiers. Subsequent approaches used SVM, deep learning, and pre-trained transformers. The key limitation of these approaches is that they require large labelled training datasets and predict a fixed set of classes (developers or components), rather than generating explanatory analysis.

**Duplicate Bug Detection:**
Duplicate detection using textual similarity has been studied extensively (Sun et al., 2010; Nguyen et al., 2012). State-of-the-art approaches use siamese networks and BERT-based encoders. The limitation is that they operate on text similarity alone and do not leverage the resolution content or component metadata.

**LLM-Based Bug Analysis:**
With the advent of large language models (GPT-4, Claude, Gemini), researchers have explored using LLMs to explain code, generate tests, and suggest fixes. The key limitation is that LLMs lack access to project-specific historical data and may hallucinate plausible-sounding but incorrect fixes.

**RAG for Code:**
RAG systems such as GitHub Copilot, Cursor, and Sourcegraph Cody apply retrieval to code context. DefectMind AI applies the same principle specifically to the defect management domain, retrieving resolved defects rather than code files.

### 4.2 Limitations of Existing Systems

| System | Triage | Root Cause | Duplicate Detection | Historical Evidence |
|---|---|---|---|---|
| SonarQube | Partial | No | No | No |
| Jira + ML plugins | Yes (limited) | No | Partial | No |
| GitHub Copilot | No | Partial | No | No |
| BugBot (GitHub) | Partial | No | No | No |
| **DefectMind AI** | **Yes** | **Yes (RAG-grounded)** | **Yes (semantic)** | **Yes** |

---

## 5. Proposed System

DefectMind AI proposes a hybrid deterministic + LLM multi-agent architecture with the following key design decisions:

### 5.1 Evidence-First Design

All agents distinguish between evidence retrieved from the historical knowledge base and reasoning inferred by the agent. The frontend labels these separately using `fix_source`, `agent_reasoning`, and `retrieved_evidence` fields. Speculative steps in remediation are flagged with `is_speculative: true`.

### 5.2 Graceful Degradation

The system is designed to degrade gracefully:
- **No API key:** Mock LLM returns deterministic, category-matched responses.
- **No ChromaDB:** Mock search returns five hardcoded example results.
- **No sentence-transformers:** Mock embeddings use seeded random vectors.
- **No PostgreSQL:** In-memory `bug_store` dictionary serves as the data store.
- **Agent failure:** Wrapped in safe-call handlers; one agent failure does not crash the pipeline.

### 5.3 Milestone Architecture

| Milestone | Key Additions |
|---|---|
| M1 | Bug submission, in-memory store, mock agents, ChromaDB schema, seed data |
| M2 | Pydantic validation, deterministic stack trace parsers (Java/Python/Node.js), parallel agent execution |
| M3 | Real RAG retrieval, LLM integration, root cause confidence thresholds, duplicate detection thresholds |
| M4 | Analytics endpoints (9), KB growth workflow, E2E test runner, 104-test suite |

---

## 6. System Requirements

### 6.1 Functional Requirements

| ID | Requirement |
|---|---|
| FR-01 | The system shall accept bug reports with title, description, stack trace, error logs, and file attachments |
| FR-02 | The system shall classify bugs by severity (critical/high/medium/low) and priority (P0–P3) |
| FR-03 | The system shall parse Java, Python, and Node.js stack traces and extract exception type, file, class, method, and line number |
| FR-04 | The system shall retrieve the top-5 most similar historical defects using cosine similarity |
| FR-05 | The system shall detect duplicate bugs with configurable similarity thresholds (0.82 likely duplicate, 0.55 related) |
| FR-06 | The system shall generate actionable remediation steps distinguishing confirmed fixes from speculative suggestions |
| FR-07 | The system shall return "Insufficient Evidence" rather than a confident result when input signals are sparse |
| FR-08 | The system shall provide analytics on severity distribution, component frequency, exception types, duplicate rates, and trends |
| FR-09 | The system shall allow confirmed-resolved bugs to be embedded and added to the vector knowledge base |
| FR-10 | The system shall expose all functionality via a RESTful JSON API |

### 6.2 Non-Functional Requirements

| ID | Requirement |
|---|---|
| NFR-01 | Bug submission endpoint shall respond in < 2 seconds |
| NFR-02 | Full 5-agent analysis pipeline shall complete in < 120 seconds |
| NFR-03 | Analytics endpoints shall respond in < 5 seconds |
| NFR-04 | The system shall handle agent failures without uncontrolled application crash |
| NFR-05 | All API responses shall be structured JSON |
| NFR-06 | The system shall operate in mock mode without external dependencies |
| NFR-07 | The system shall be deployable via Docker Compose with a single command |

### 6.3 Hardware and Software Requirements

**Development:**
- Python 3.11+
- Node.js 18+
- 4 GB RAM minimum (8 GB recommended for local ML models)
- Docker and Docker Compose

**Production (Render.com):**
- Docker-based deployment
- Environment variables for API keys and database URL
- Persistent volume for ChromaDB data

---

## 7. System Architecture

The complete architecture is documented with Mermaid diagrams in [`SYSTEM_ARCHITECTURE.md`](SYSTEM_ARCHITECTURE.md). A high-level summary follows.

### 7.1 Component Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        User (Browser)                          │
│  Dashboard │ Bug Submit │ Bug List │ Analysis │ Analytics       │
│  Knowledge Base │ KB Growth │ E2E Testing                       │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTP/REST
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                   FastAPI Backend (Python 3.11)                 │
│                                                                 │
│  /api/bugs    /api/analytics    /api/knowledge-base             │
│  /api/search  /api/health                                       │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              Agent Orchestrator                          │   │
│  │  Triage ──► Log Analysis ──► Root Cause ──► Duplicate   │   │
│  │                                    ──► Remediation      │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌────────────────┐  ┌────────────────┐  ┌─────────────────┐   │
│  │ EmbeddingService│  │  ChromaService │  │   LLMService    │   │
│  │ all-MiniLM-L6  │  │  defect_kb     │  │  OpenAI / mock  │   │
│  └────────────────┘  └────────────────┘  └─────────────────┘   │
│                                                                 │
│  ┌────────────────────────────────────────────────────────┐     │
│  │  PostgreSQL (ORM models: BugReport, AnalysisResult,   │     │
│  │  HistoricalDefect) — in-memory dict for demo mode     │     │
│  └────────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────┘
```

### 7.2 Agent Pipeline Execution

Steps 1–2 (Triage + Log Analysis) run in parallel using `asyncio.gather`. Steps 3–4 (Root Cause + Duplicate Detection) run in parallel after step 2 completes. Step 5 (Remediation) runs sequentially after steps 3–4, consuming all prior results.

### 7.3 RAG Pipeline

1. **Ingestion:** `seed_data.py` reads `historical_defects.csv`, chunks each defect into title/description/resolution segments, generates 384-dim embeddings, and stores them in ChromaDB's `defect_knowledge_base` collection.
2. **Query:** Root Cause and Remediation agents construct a query from bug signals, embed it, and call `ChromaService.search()` for top-5 results ranked by cosine similarity.
3. **Augmentation:** Retrieved evidence is injected into the LLM prompt under a clearly-labelled `RETRIEVED HISTORICAL EVIDENCE` section, separated from agent inference.

---

## 8. Implementation

### 8.1 Backend Implementation

**`main.py`** registers four FastAPI routers, initialises services in the lifespan handler, and exposes `GET /api/health`. The application version is `4.0.0-M4`.

**`routers/bugs.py`** implements the core bug lifecycle. An in-memory `bug_store` dictionary acts as the primary data store. Singleton lazy-initialisation patterns are used for LLM, ChromaDB, embedding, and orchestrator services.

**`routers/analytics.py`** (M4.1) implements nine analytics endpoints. All analytics are computed from live `bug_store` data and ChromaDB. No hardcoded values. Filtering via query parameters (component, severity, priority, exception_type, date_from/to, is_duplicate).

**`routers/knowledge.py`** (M4.2) implements the knowledge base growth workflow: validate → duplicate check → embed → store → verify. The `ResolvedBugSubmission` Pydantic model accepts optional fields so that validation errors are returned as structured `{valid, errors, warnings}` responses rather than raw 422 responses.

**`services/chroma_service.py`** wraps ChromaDB with a mock fallback. The `_mock_store` class-level dictionary allows `add_documents`, `get_document_by_id`, and `document_exists` to remain consistent in mock mode.

**`services/embedding_service.py`** wraps `sentence-transformers`. Falls back to seeded `numpy.random` vectors when the model is not installed.

**`services/llm_service.py`** implements an OpenAI-compatible HTTP client via `httpx`. In mock mode, `_mock_generate()` returns deterministic JSON for each agent type (root cause, remediation, triage).

**Agent implementations** (M2–M3) use Pydantic v2 models for structured output validation. `TriageAgent` uses keyword matching across 14 component patterns and 10 category patterns. `LogAnalysisAgent` uses regex parsers for Java, Python, and Node.js stack traces. `RootCauseAgent` and `RemediationAgent` implement the full RAG+LLM pipeline with evidence/reasoning separation. `DuplicateDetectionAgent` uses configurable thresholds (0.82 / 0.55).

### 8.2 Frontend Implementation

**`App.tsx`** implements manual string-based routing (no React Router, despite the dependency being present). Eight pages are supported: `dashboard`, `submit`, `bugs`, `analysis`, `knowledge`, `analytics`, `kb-growth`, `e2e-test`.

**`services/api.ts`** is the complete API client. It handles snake_case → camelCase conversion, implements timeout via `AbortController` (60 seconds), and provides fallback to mock data on network errors. The E2E test runner (`runE2ETests`) is also implemented here — it submits 8 real bugs, runs the analysis pipeline on each, and evaluates assertions.

**`pages/Analytics.tsx`** uses Recharts (pie, bar, line, radar charts) to visualise all analytics data. A filter bar allows filtering by severity, priority, component, exception type, and date range.

**`pages/KnowledgeGrowth.tsx`** implements a multi-step workflow UI with a progress indicator, form with required and advanced fields, status display for each pipeline step, and a sidebar showing KB status.

**`pages/E2ETest.tsx`** renders test scenario cards, runs tests via `runE2ETests`, and displays per-test pipeline stage results, assertions, agent details, and a JSON export of the suite result.

### 8.3 Data Layer

**PostgreSQL ORM models:** `BugReport`, `AnalysisResult`, `HistoricalDefect` (defined but not used in demo mode — in-memory store is used instead).

**ChromaDB collection:** `defect_knowledge_base`, cosine similarity space, 384-dimensional vectors, persisted at `./chroma_data/chroma.sqlite3`.

**Seed data:** 12 historical defects from Mozilla Firefox (4), Apache HTTP Server/Tomcat (4), and Eclipse JDT/Platform (4), each with title, description, component, severity, and resolution.

---

## 9. Results and Screenshots

> **Note:** Live application screenshots would normally be included here. The live application is accessible at https://defectmind-frontend.onrender.com/.

### 9.1 Test Suite Results

The M4 test suite (`test_milestone4.py`) achieves **104/104 tests passing** across 12 test classes:

| Class | Tests | Passing |
|---|---|---|
| TestBugSubmission | 10 | 10 |
| TestTriageAgent | 7 | 7 |
| TestLogAnalysisAgent | 6 | 6 |
| TestRootCauseAgent | 7 | 7 |
| TestDuplicateDetectionAgent | 7 | 7 |
| TestRemediationAgent | 6 | 6 |
| TestRAGPipeline | 7 | 7 |
| TestAnalyticsEndpoints | 14 | 14 |
| TestKnowledgeBaseGrowth | 15 | 15 |
| TestErrorHandling | 12 | 12 |
| TestPerformance | 5 | 5 |
| TestStructuredFindings | 8 | 8 |
| **Total** | **104** | **104** |

### 9.2 Performance Measurements

| Operation | Measured Time |
|---|---|
| Bug submission | < 50ms |
| Full 5-agent pipeline (mock mode) | < 200ms |
| Analytics overview (empty store) | < 30ms |
| KB add-resolved (mock mode) | < 100ms |

*Note: Production times with real LLM will be dominated by LLM API latency (~2–30 seconds depending on model and load).*

### 9.3 Build Output

```
Frontend:  742 KB (gzip: 200 KB) — 1,986 modules transformed
Backend:   Python 3.11, 57 source files, all syntax-valid
Tests:     104/104 passed in 3.2 seconds
```

---

## 10. Testing and Validation

Full test documentation is in [`TESTING_AND_VALIDATION.md`](TESTING_AND_VALIDATION.md).

### 10.1 Test Coverage Summary

- **Submission validation:** Empty, too-short, malformed JSON
- **Pipeline completeness:** All 5 agent results present for all 5 bug scenarios
- **Triage accuracy:** Severity, priority, component populated and in valid ranges
- **Log parsing:** Java NPE, PostgreSQL exception, ConcurrentModificationException, OOM, no-stack-trace
- **Root cause:** Evidence-grounded analysis; sparse/vague bugs capped at ≤ 0.50 confidence
- **Duplicate detection:** Known duplicate (high similarity), related but non-duplicate, unique bugs
- **Remediation:** Fix source labelled, implementation steps list, risk level valid
- **RAG:** Retrieval scores in [0, 1]; evidence retrieved for well-described bugs
- **Analytics:** All 9 endpoints return valid JSON, filters work, empty-store graceful
- **KB growth:** Validate → dup check → embed → store → verify sequence
- **Error handling:** 404 on missing bugs, graceful pipeline failure, no crashes
- **Performance:** Submission < 2s, pipeline < 120s, analytics < 5s

---

## 11. Limitations

### 11.1 Current Limitations

1. **In-memory storage:** Bug reports are stored in a process-level dictionary. Data is lost on server restart. The PostgreSQL ORM models exist but are not connected in the current demo mode.

2. **Mock LLM:** Without an OpenAI API key, all LLM-based analysis uses a single fixed response template per agent type. Real-world accuracy requires a live LLM.

3. **Mock embeddings:** Without `sentence-transformers` installed, mock embeddings are seeded random vectors. Semantic similarity results are not meaningful in this mode.

4. **Knowledge base size:** The seeded knowledge base contains only 12 historical defects. Meaningful duplicate detection and root cause retrieval require a significantly larger corpus.

5. **Single collection:** All defects share one ChromaDB collection. No tenant isolation or project-level partitioning.

6. **No authentication:** The API is fully open. Any caller can submit, delete, or analyze bugs.

7. **Duplicate detection in mock mode:** Mock search always returns the same five results regardless of query. This means duplicate classification is unreliable without real ChromaDB.

8. **English only:** All agents and the embedding model are optimised for English text.

### 11.2 Known Non-Issues

- The "large chunk size" warning in the Vite build is expected and does not affect functionality.
- Pydantic v1 `@validator` deprecation warnings from M2 agent code are cosmetic and do not break functionality.

---

## 12. Conclusion and Future Work

DefectMind AI demonstrates a viable architecture for AI-assisted bug diagnosis that combines deterministic signal extraction, semantic retrieval from historical knowledge, and LLM-based reasoning — while carefully distinguishing evidence from inference.

The project successfully achieved all four milestone objectives:
- M1: Functional submission + mock pipeline
- M2: Production-grade agents with Pydantic validation
- M3: Real RAG pipeline with evidence/reasoning separation
- M4: Analytics, KB growth, 104-test E2E validation

### Future Work

1. **Production database integration:** Connect the existing SQLAlchemy models to real PostgreSQL; migrate from the in-memory store.
2. **Authentication and RBAC:** Implement JWT-based user authentication and role-based access control.
3. **Larger knowledge base:** Seed the ChromaDB collection from public bug trackers (Mozilla Bugzilla, Apache JIRA, Eclipse Bugzilla) for meaningful RAG retrieval.
4. **Streaming analysis:** Use WebSocket or Server-Sent Events to stream agent results progressively as they complete.
5. **Multi-language support:** Extend stack trace parsers to Rust, Go, C++, and Swift.
6. **Agent feedback loop:** Allow users to mark analysis results as correct/incorrect to fine-tune triage thresholds.
7. **Multi-tenancy:** Project-level partitioning of the vector store and bug store.
8. **LLM model selection:** Allow operators to choose between different LLM providers and models per agent.
9. **Export:** Generate PDF/Markdown analysis reports.
10. **IDE integration:** VS Code extension that submits bugs directly from the editor.

---

## 13. References

1. Anvik, J., Hiew, L., & Murphy, G. C. (2006). *Who should fix this bug?* In ICSE 2006. ACM.
2. Sun, C., Lo, D., Wang, X., Jiang, J., & Khoo, S. C. (2010). *A discriminative model approach for accurate duplicate bug report retrieval.* In ICSE 2010. ACM.
3. Lewis, P., Perez, E., Piktus, A., et al. (2020). *Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks.* NeurIPS 2020. arXiv:2005.11401.
4. Reimers, N., & Gurevych, I. (2019). *Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks.* EMNLP 2019. arXiv:1908.10084.
5. FastAPI documentation. (2024). https://fastapi.tiangolo.com/
6. ChromaDB documentation. (2024). https://docs.trychroma.com/
7. Pydantic documentation. (2024). https://docs.pydantic.dev/
8. React documentation. (2024). https://react.dev/
9. Recharts documentation. (2024). https://recharts.org/
10. OpenAI API documentation. (2024). https://platform.openai.com/docs/

---

*Document generated from inspected source code. All API endpoints, agent behaviours, and test results are verified against the actual implementation.*
