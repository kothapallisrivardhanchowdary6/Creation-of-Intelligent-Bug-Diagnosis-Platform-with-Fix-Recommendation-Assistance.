# API Documentation

## DefectMind AI — REST API Reference

**Base URL (Production):** `https://defectmind-ai.onrender.com`
**Base URL (Local):** `http://localhost:8000`
**API Prefix:** `/api`
**Interactive Docs:** `/docs` (Swagger UI), `/redoc` (ReDoc)
**App Version:** `4.0.0-M4`

All request and response bodies are JSON. All endpoints return `Content-Type: application/json`.

---

## Table of Contents

1. [Health Check](#1-health-check)
2. [Bug Endpoints](#2-bug-endpoints)
3. [Search Endpoint](#3-search-endpoint)
4. [Knowledge Base Endpoints](#4-knowledge-base-endpoints)
5. [Analytics Endpoints](#5-analytics-endpoints)
6. [Error Codes](#6-error-codes)
7. [Data Schemas](#7-data-schemas)

---

## 1. Health Check

### `GET /api/health`

Returns the current health status of all backend services.

**Request:** No body required.

**Response `200 OK`:**
```json
{
  "status": "healthy",
  "version": "4.0.0-M4",
  "services": {
    "api": "running",
    "database": "connected",
    "chromadb": "ready",
    "embeddings": "loaded",
    "llm": "mock",
    "analytics": "ready",
    "knowledge_growth": "ready"
  },
  "uptime": "N/A"
}
```

**Field notes:**
- `llm`: `"mock"` when `OPENAI_API_KEY` is not set; `"production"` otherwise.
- `uptime`: Not yet implemented — always returns `"N/A"`.

---

## 2. Bug Endpoints

### `POST /api/bugs`

Submit a new bug report. The bug is stored in the in-memory store and returned with a generated ID.

**Request body:**
```json
{
  "title": "NullPointerException in UserProfileService",
  "description": "The service crashes when loading a profile for a deleted user. Steps: 1. Delete user. 2. Access profile page. 3. Observe NPE.",
  "stack_trace": "java.lang.NullPointerException: Cannot invoke User.getProfileData()\n\tat com.app.UserProfileService.loadProfile(UserProfileService.java:142)",
  "error_logs": "[ERROR] UserProfileService - Null user reference in loadProfile()",
  "environment": "Java 17, Spring Boot 3.1, Production"
}
```

**Validation:**
| Field | Rule |
|---|---|
| `title` | Required, min 5 chars, max 500 chars |
| `description` | Required, min 10 chars |
| `stack_trace` | Optional string |
| `error_logs` | Optional string |
| `environment` | Optional string |

**Response `200 OK`:**
```json
{
  "id": "BUG-A3F12B9C04E8",
  "title": "NullPointerException in UserProfileService",
  "description": "The service crashes when loading a profile...",
  "stack_trace": "java.lang.NullPointerException...",
  "error_logs": "[ERROR] UserProfileService...",
  "environment": "Java 17, Spring Boot 3.1, Production",
  "status": "submitted",
  "created_at": "2025-10-14T09:30:00.000000",
  "analysis": null
}
```

**Response `422 Unprocessable Entity`:**
```json
{
  "detail": [
    {
      "loc": ["body", "title"],
      "msg": "String should have at least 5 characters",
      "type": "string_too_short"
    }
  ]
}
```

---

### `GET /api/bugs`

Return all bug reports in the current session (in-memory store).

**Response `200 OK`:**
```json
[
  {
    "id": "BUG-A3F12B9C04E8",
    "title": "NullPointerException in UserProfileService",
    "status": "analyzed",
    "created_at": "2025-10-14T09:30:00.000000",
    "analysis": { "..." }
  }
]
```

---

### `GET /api/bugs/{bug_id}`

Retrieve a single bug report by its ID.

**Path parameter:** `bug_id` — e.g., `BUG-A3F12B9C04E8`

**Response `200 OK`:** Single bug object (same shape as POST response).

**Response `404 Not Found`:**
```json
{ "detail": "Bug not found" }
```

---

### `POST /api/bugs/{bug_id}/analyze`

Run the full five-agent M3 AI analysis pipeline on a submitted bug. This is the primary analysis endpoint.

**Path parameter:** `bug_id`

**Request body:** None.

**Response `200 OK`:**
```json
{
  "bug_id": "BUG-A3F12B9C04E8",
  "timestamp": "2025-10-14T09:30:05.123456",
  "milestone": "M3",
  "status": "completed",
  "total_duration": 0.187,

  "triage": {
    "severity": "high",
    "priority": "P1",
    "category": "Null Reference",
    "component": "Authentication",
    "confidence": 0.85,
    "reasoning": "Classified as high severity Null Reference defect affecting the Authentication component. Stack trace analysis supports this classification."
  },

  "log_analysis": {
    "exceptions": [
      {
        "exception_type": "java.lang.NullPointerException",
        "error_message": "Cannot invoke User.getProfileData() because user is null",
        "file_name": "UserProfileService.java",
        "class_name": "UserProfileService",
        "method_name": "loadProfile",
        "line_number": 142,
        "code_path": "UserProfileService.loadProfile",
        "confidence": 0.9
      }
    ],
    "error_patterns": ["Null reference/pointer"],
    "failure_point": "UserProfileService.java line 142 in loadProfile (UserProfileService)",
    "code_path": "UserProfileService.loadProfile",
    "stack_trace_summary": "Stack trace detected (java format). Contains 3 lines. 1 stack frames",
    "suspicious_logs": ["[ERROR] UserProfileService - Null user reference in loadProfile()"],
    "confidence": 0.75,
    "summary": "Found 1 exception(s): java.lang.NullPointerException. Error patterns identified: Null reference/pointer. Primary failure point: UserProfileService.java line 142 in loadProfile."
  },

  "root_cause": {
    "status": "success",
    "probable_cause": "A null or uninitialized object is being accessed without a prior null check in the Authentication component.",
    "hypotheses": [
      {
        "hypothesis": "A null reference is accessed in the processing pipeline without a prior null-check.",
        "confidence": 0.78,
        "supporting_evidence": ["Exception type confirms null access", "Similar historical defect MOZ-1001 had same root cause"],
        "causal_chain": "Uninitialised input → processing loop → null access → exception"
      }
    ],
    "confidence": 0.5,
    "reasoning": "Category 'Null Reference' in component 'Authentication' detected via triage.",
    "related_components": ["Authentication"],
    "retrieved_evidence": [
      {
        "bug_id": "MOZ-1001",
        "document": "NullPointerException in NetworkManager when connection drops during file download",
        "component": "Networking",
        "severity": "critical",
        "resolution": "Fixed by adding null check before accessing connection object in retry handler.",
        "similarity_score": 0.89,
        "source": "historical_defect_database"
      }
    ],
    "agent_reasoning": "Based on Null Reference pattern in the Authentication component.",
    "evidence_summary": "Retrieved 5 similar historical defect(s). Closest match: MOZ-1001 (89.0% similarity)."
  },

  "duplicate_detection": {
    "classification": "related_issue",
    "top_match_similarity": 0.89,
    "duplicate_probability": 0.6195,
    "matched_bugs": [
      {
        "bug_id": "MOZ-1001",
        "title": "NullPointerException in NetworkManager when connection drops during file download",
        "similarity_score": 0.89,
        "classification": "likely_duplicate",
        "component": "Networking",
        "severity": "critical",
        "exception_type": "",
        "resolution_summary": "Fixed by adding null check before accessing connection object."
      }
    ],
    "analysis_summary": "Related Issue — 5 candidate(s) found. Highest similarity: 89.0%.",
    "thresholds_used": {
      "likely_duplicate": 0.82,
      "related_issue": 0.55
    },
    "is_duplicate": false,
    "similarity_score": 0.89
  },

  "remediation": {
    "status": "success",
    "suggested_fix": "Add a null/bounds check at the entry of the affected method. Use Optional or guard clauses to handle missing values.",
    "fix_source": "historical_evidence",
    "confidence": 0.93,
    "implementation_steps": [
      {
        "step": "Locate the failure point identified in the log analysis.",
        "detail": "Use the code path from the stack trace to navigate to the exact line.",
        "is_speculative": false
      },
      {
        "step": "Add a null check or Optional guard before the property access.",
        "detail": "Example: if (obj == null) { log.warn('...'); return; }",
        "is_speculative": false
      }
    ],
    "debugging_steps": ["Reproduce the issue locally with the same inputs.", "Add a breakpoint at the identified failure point."],
    "validation_steps": ["Write a unit test that reproduces the failure.", "Run the test suite for the affected component."],
    "regression_tests": ["Run full test suite for the affected module."],
    "historical_resolutions": [],
    "best_practices": ["Always validate inputs at method boundaries.", "Use Optional types or null-object pattern for safer APIs."],
    "estimated_effort": "2-4 hours",
    "risk_level": "medium",
    "evidence_summary": "",
    "agent_reasoning": "Fix derived from the identified root cause: unguarded null access."
  },

  "agents": {
    "triage": { "agent": "Triage Agent", "status": "success", "duration": 0.001 },
    "log_analysis": { "agent": "Log Analysis Agent", "status": "success", "duration": 0.002 },
    "root_cause": { "agent": "Root Cause Agent", "status": "success", "duration": 0.05 },
    "duplicate_detection": { "agent": "Duplicate Detection Agent", "status": "success", "duration": 0.03 },
    "remediation": { "agent": "Remediation Agent", "status": "success", "duration": 0.04 }
  }
}
```

**Response `404 Not Found`:**
```json
{ "detail": "Bug not found" }
```

**Response `500 Internal Server Error`:**
```json
{ "detail": "Analysis failed: <error message>" }
```

---

### `GET /api/bugs/{bug_id}/analysis`

Retrieve the stored analysis result for an already-analyzed bug.

**Response `200 OK`:** Same shape as the analyze response above.

**Response `404 Not Found`:**
```json
{ "detail": "No analysis found. Submit and run analysis first." }
```

---

### `DELETE /api/bugs/{bug_id}`

Delete a bug from the store.

**Response `200 OK`:**
```json
{ "status": "deleted", "id": "BUG-A3F12B9C04E8" }
```

---

### `POST /api/bugs/upload`

Upload a file attachment. The file content is returned as text (not stored server-side persistently).

**Request:** `multipart/form-data` with a `file` field.

**Response `200 OK`:**
```json
{
  "name": "error.log",
  "content": "[ERROR] Something failed at 09:30:00\n...",
  "size": 1024
}
```

---

## 3. Search Endpoint

### `POST /api/search`

Perform a semantic search over the knowledge base. Currently uses a mock search service; returns ranked results from the 12 seeded defects.

**Request body:**
```json
{
  "query": "NullPointerException connection retry handler",
  "top_k": 5
}
```

**Validation:**
| Field | Rule |
|---|---|
| `query` | Required, min 1 char |
| `top_k` | Integer, 1–20, default 5 |

**Response `200 OK`:**
```json
{
  "query": "NullPointerException connection retry handler",
  "results": [
    {
      "id": "MOZ-1001",
      "document": "NullPointerException in NetworkManager when connection drops during file download",
      "score": 0.89,
      "metadata": {
        "project": "Mozilla Firefox",
        "component": "Networking",
        "severity": "critical"
      }
    },
    {
      "id": "APC-2003",
      "document": "Buffer overflow in HTTP header parsing with malformed Content-Type",
      "score": 0.82,
      "metadata": {
        "project": "Apache HTTP Server",
        "severity": "critical"
      }
    }
  ],
  "total": 5
}
```

---

## 4. Knowledge Base Endpoints

### `GET /api/knowledge-base/status`

Returns the current status of the ChromaDB knowledge base collection, including document counts and metadata breakdown.

**Response `200 OK`:**
```json
{
  "total_documents": 12,
  "collection_name": "defect_knowledge_base",
  "index_status": "ready",
  "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
  "vector_dimensions": 384,
  "projects": ["Mozilla Firefox", "Apache HTTP Server", "Apache Tomcat", "Eclipse JDT", "Eclipse Platform"],
  "project_breakdown": { "Mozilla Firefox": 4, "Apache HTTP Server": 2, "Apache Tomcat": 2, "Eclipse JDT": 3, "Eclipse Platform": 2 },
  "component_breakdown": { "Networking": 1, "Layout Engine": 1, "Core": 1, "Thread Pool": 1 },
  "severity_breakdown": { "critical": 6, "high": 4, "medium": 3 },
  "user_added_resolved_bugs": 0,
  "last_updated": "2025-10-14T09:30:00.000000"
}
```

---

### `POST /api/knowledge-base/ingest`

Seed the knowledge base with the 12 historical defects from `historical_defects.csv`. Safe to call on an already-seeded KB.

**Request body:** None.

**Response `200 OK` (already seeded):**
```json
{
  "status": "already_indexed",
  "documents_indexed": 12,
  "message": "Knowledge base already contains data. Use /add-resolved to add new entries."
}
```

**Response `200 OK` (newly seeded):**
```json
{
  "status": "completed",
  "documents_indexed": 12,
  "projects": ["Mozilla Firefox", "Apache HTTP Server", "Apache Tomcat", "Eclipse JDT", "Eclipse Platform"]
}
```

---

### `POST /api/knowledge-base/validate`

Validate a resolved bug submission before adding it to the KB. Returns field errors and a duplicate check result without making any changes.

**Request body:**
```json
{
  "title": "NullPointerException fixed in UserProfileService",
  "description": "The UserProfileService crashed when accessing a deleted user profile due to stale cache reference.",
  "root_cause": "The ProfileCache returned a stale reference to a deleted user object without null checking.",
  "resolution": "Added null check before accessing user object in loadProfile(). Also added cache invalidation on user delete.",
  "resolution_confirmed": true,
  "component": "Authentication",
  "severity": "high",
  "priority": "P1",
  "exception_type": "NullPointerException",
  "source": "payment-service-team"
}
```

**All fields:**
| Field | Type | Required | Description |
|---|---|---|---|
| `title` | string | Yes (min 5) | Bug title |
| `description` | string | Yes (min 10) | Bug description |
| `root_cause` | string | Yes (min 5) | Identified root cause |
| `resolution` | string | Yes (min 10) | How it was fixed |
| `resolution_confirmed` | boolean | Yes (must be `true`) | Confirms fix is validated |
| `component` | string | Recommended | Affected component |
| `severity` | string | Recommended | `critical\|high\|medium\|low` |
| `priority` | string | Optional | `P0\|P1\|P2\|P3` |
| `bug_id` | string | Optional | Original bug ID |
| `error_message` | string | Optional | Primary error message |
| `exception_type` | string | Optional | Exception class name |
| `stack_trace` | string | Optional | Stack trace text |
| `confirmed_fix` | string | Optional | Code fix description |
| `source` | string | Optional | Source project / team |
| `category` | string | Optional | Bug category |

**Response `200 OK` (valid):**
```json
{
  "valid": true,
  "errors": [],
  "warnings": [],
  "duplicate_check": {
    "checked": true,
    "potential_duplicates": 0,
    "top_match": {
      "id": "MOZ-1001",
      "document": "NullPointerException in NetworkManager...",
      "similarity": 0.76
    },
    "recommendation": "OK — no close duplicates found"
  }
}
```

**Response `200 OK` (invalid):**
```json
{
  "valid": false,
  "errors": [
    "root_cause is required and must be at least 5 characters",
    "resolution_confirmed must be True — only add confirmed fixes"
  ],
  "warnings": ["component not provided — KB retrieval quality will be lower"],
  "duplicate_check": null
}
```

---

### `POST /api/knowledge-base/add-resolved`

Add a confirmed-resolved bug to the ChromaDB knowledge base. Runs the full validate → embed → store → verify pipeline.

**Request body:** Same schema as `/validate`.

**Response `200 OK` (success):**
```json
{
  "success": true,
  "doc_id": "KB-A3B4C5D6E7F8",
  "validation": {
    "valid": true,
    "errors": [],
    "warnings": []
  },
  "embedding_generated": true,
  "duplicate_check": {
    "checked": true,
    "potential_duplicates": 0,
    "top_match": { "id": "MOZ-1001", "similarity": 0.76, "document": "..." },
    "is_near_duplicate": false
  },
  "indexed": true,
  "retrievable": true,
  "retrieval_score": 0.987,
  "message": "Successfully added to knowledge base as KB-A3B4C5D6E7F8. Immediately retrievable.",
  "timestamp": "2025-10-14T09:35:00.000000"
}
```

**Response `200 OK` (validation failure):**
```json
{
  "success": false,
  "doc_id": "",
  "validation": {
    "valid": false,
    "errors": ["root_cause is required and must be at least 5 characters"],
    "warnings": []
  },
  "embedding_generated": false,
  "duplicate_check": { "checked": false },
  "indexed": false,
  "retrievable": false,
  "message": "Validation failed: root_cause is required...",
  "timestamp": "2025-10-14T09:35:00.000000"
}
```

---

### `GET /api/knowledge-base/recent`

Return recently added KB entries from this session and from ChromaDB metadata.

**Query parameters:**
| Parameter | Type | Default | Description |
|---|---|---|---|
| `limit` | integer | 10 | Maximum entries to return |

**Response `200 OK`:**
```json
{
  "session_added": [
    {
      "doc_id": "KB-A3B4C5D6E7F8",
      "title": "NullPointerException fixed in UserProfileService",
      "component": "Authentication",
      "severity": "high",
      "added_at": "2025-10-14T09:35:00.000000",
      "retrievable": true
    }
  ],
  "all_m4_entries": [],
  "total_session_added": 1,
  "limit": 10
}
```

---

### `POST /api/knowledge-base/search`

Semantic search over the ChromaDB knowledge base using the same embedding model as the RAG pipeline.

**Query parameters:**
| Parameter | Type | Default | Description |
|---|---|---|---|
| `query` | string | required | Search query text |
| `top_k` | integer | 5 | Number of results |

**Response `200 OK`:**
```json
{
  "query": "null pointer connection retry",
  "results": [
    {
      "id": "MOZ-1001",
      "document": "NullPointerException in NetworkManager when connection drops...",
      "score": 0.89,
      "metadata": { "component": "Networking", "severity": "critical" }
    }
  ],
  "total": 5
}
```

---

### `GET /api/knowledge-base/verify/{doc_id}`

Verify that a document with the given ID exists in the KB and can be retrieved by similarity search.

**Path parameter:** `doc_id` — e.g., `KB-A3B4C5D6E7F8`

**Response `200 OK` (found):**
```json
{
  "doc_id": "KB-A3B4C5D6E7F8",
  "exists": true,
  "document_preview": "NullPointerException fixed in UserProfileService...",
  "metadata": { "component": "Authentication", "severity": "high", "added_via": "knowledge_base_growth_m4" },
  "retrievable": true,
  "retrieval_score": 0.987,
  "message": "Document verified — retrievable by similarity search"
}
```

**Response `200 OK` (not found):**
```json
{
  "doc_id": "KB-NONEXISTENT",
  "exists": false,
  "retrievable": false,
  "message": "Document not found in knowledge base"
}
```

---

## 5. Analytics Endpoints

All analytics endpoints support the following optional query parameters unless noted:

| Parameter | Type | Description |
|---|---|---|
| `component` | string | Filter by component name (case-insensitive exact match) |
| `severity` | string | `critical\|high\|medium\|low` |
| `priority` | string | `P0\|P1\|P2\|P3` |
| `exception_type` | string | Filter by exception type (substring match) |
| `date_from` | string | ISO 8601 date string |
| `date_to` | string | ISO 8601 date string |
| `is_duplicate` | boolean | Filter to duplicates only |

All analytics return empty/zero values when no bugs have been submitted and analyzed — no hardcoded values.

---

### `GET /api/analytics/overview`

Top-level analytics summary.

**Response `200 OK`:**
```json
{
  "total_bugs": 5,
  "analyzed_bugs": 5,
  "unanalyzed_bugs": 0,
  "severity_distribution": { "high": 3, "critical": 1, "medium": 1 },
  "priority_distribution": { "P1": 3, "P0": 1, "P2": 1 },
  "top_components": [
    { "component": "Authentication", "count": 2 },
    { "component": "Database", "count": 1 }
  ],
  "top_exceptions": [
    { "exception": "NullPointerException", "count": 2 }
  ],
  "duplicate_stats": { "duplicates": 1, "unique": 4, "duplicate_rate": 0.2 },
  "resolution_distribution": { "has_remediation": 5 },
  "knowledge_base": { "total_documents": 12, "collection_name": "defect_knowledge_base", "status": "mock" },
  "filters_applied": { "component": null, "severity": null, "priority": null, "exception_type": null, "date_from": null, "date_to": null, "is_duplicate": null }
}
```

---

### `GET /api/analytics/severity`

Severity distribution with component breakdown and time series.

**Response `200 OK`:**
```json
{
  "severity_distribution": { "high": 3, "critical": 1 },
  "severity_by_component": { "Authentication": { "high": 2 }, "Database": { "critical": 1 } },
  "severity_over_time": { "2025-W42": { "high": 3 } },
  "total": 4
}
```

---

### `GET /api/analytics/priority`

**Response `200 OK`:**
```json
{
  "priority_distribution": { "P1": 3, "P0": 1 },
  "priority_by_severity": { "critical": { "P0": 1 }, "high": { "P1": 3 } },
  "total": 4
}
```

---

### `GET /api/analytics/components`

Component-wise bug counts with per-severity breakdown.

**Response `200 OK`:**
```json
{
  "components": [
    { "component": "Authentication", "total": 2, "critical": 0, "high": 2, "medium": 0, "low": 0, "unknown": 0 },
    { "component": "Database", "total": 1, "critical": 1, "high": 0, "medium": 0, "low": 0, "unknown": 0 }
  ],
  "total_components": 2,
  "most_affected": "Authentication",
  "total": 3
}
```

---

### `GET /api/analytics/exceptions`

Exception-type frequency and error pattern distribution.

**Response `200 OK`:**
```json
{
  "exception_distribution": [
    { "exception": "NullPointerException", "count": 2 },
    { "exception": "PSQLException", "count": 1 }
  ],
  "exception_by_component": { "Authentication": { "NullPointerException": 2 } },
  "error_patterns": [
    { "pattern": "Null reference/pointer", "count": 3 }
  ],
  "unique_exception_types": 2,
  "total": 3
}
```

---

### `GET /api/analytics/root-causes`

Most common root causes with confidence distribution.

**Response `200 OK`:**
```json
{
  "top_root_causes": [
    { "cause": "A null or uninitialized object is being accessed...", "count": 2 }
  ],
  "root_cause_status": { "success": 4, "insufficient_evidence": 1 },
  "confidence_distribution": { "high_90+": 0, "medium_70_90": 2, "low_50_70": 2, "very_low_50-": 1 },
  "total": 5
}
```

---

### `GET /api/analytics/duplicates`

Duplicate detection statistics.

**Response `200 OK`:**
```json
{
  "total_analyzed": 5,
  "duplicates": 1,
  "unique": 4,
  "related_issues": 2,
  "duplicate_rate": 0.2,
  "classification_distribution": { "likely_duplicate": 1, "related_issue": 2, "new_unmatched": 2 },
  "similarity_distribution": { "very_high_90+": 0, "high_80_90": 3, "medium_55_80": 1, "low_55-": 1 },
  "duplicates_by_component": { "Authentication": 1 }
}
```

---

### `GET /api/analytics/trends`

Defect submission and severity trends over time.

**Additional query parameters:**
| Parameter | Default | Values |
|---|---|---|
| `granularity` | `day` | `day\|week\|month` |

**Response `200 OK`:**
```json
{
  "granularity": "day",
  "trend_series": [
    { "period": "2025-10-14", "total": 5, "high": 3, "critical": 1, "medium": 1, "historical_kb_entries": 0 }
  ],
  "total_bugs": 5,
  "date_range": { "from": "2025-10-14T09:30:00", "to": "2025-10-14T09:35:00" }
}
```

---

### `GET /api/analytics/clusters`

Semantically similar bug clusters from ChromaDB knowledge base.

**Additional query parameters:**
| Parameter | Default | Description |
|---|---|---|
| `top_k` | 5 | Maximum clusters to return |
| `min_similarity` | 0.55 | Minimum similarity threshold |

**Response `200 OK`:**
```json
{
  "kb_clusters": [
    {
      "cluster_id": "cluster_networking",
      "label": "Networking",
      "size": 2,
      "representative_bugs": [
        { "id": "MOZ-1001", "document": "NullPointerException in NetworkManager...", "severity": "critical", "component": "Networking", "project": "Mozilla Firefox" }
      ],
      "severity_breakdown": { "critical": 1, "high": 1 }
    }
  ],
  "submitted_bug_clusters": [
    {
      "submitted_bug_id": "BUG-A3F12B9C04E8",
      "submitted_bug_title": "NullPointerException in UserProfileService",
      "similar_kb_bugs": [
        { "id": "MOZ-1001", "document": "NullPointerException in NetworkManager...", "similarity": 0.89, "component": "Networking" }
      ]
    }
  ],
  "total_documents": 12,
  "min_similarity_threshold": 0.55
}
```

---

### `GET /api/analytics/remediation-patterns`

Common remediation patterns, fix sources, effort, and risk levels.

**Response `200 OK`:**
```json
{
  "fix_source_distribution": { "agent_reasoning": 3, "historical_evidence": 2 },
  "effort_distribution": { "2-4 hours": 4, "Unknown": 1 },
  "risk_distribution": { "medium": 4, "high": 1 },
  "common_steps": [
    { "step": "Locate the failure point identified in the log analysis.", "count": 3 }
  ],
  "total": 5
}
```

---

## 6. Error Codes

| HTTP Status | Meaning | When It Occurs |
|---|---|---|
| `200 OK` | Success | All successful requests |
| `404 Not Found` | Resource not found | Bug ID or doc ID doesn't exist |
| `422 Unprocessable Entity` | Validation error | Required fields missing or invalid format |
| `500 Internal Server Error` | Server error | Analysis pipeline failure, uncaught exception |

Note: The KB endpoints (`/validate`, `/add-resolved`) deliberately return `200` with `{"valid": false, "errors": [...]}` for business-logic validation failures, so the frontend can display structured error messages rather than parsing raw 422 bodies.

---

## 7. Data Schemas

### BugStatus Enum
```
"submitted" | "analyzing" | "analyzed" | "error"
```

### Severity Enum
```
"critical" | "high" | "medium" | "low"
```

### Priority Enum
```
"P0" | "P1" | "P2" | "P3"
```

### DuplicateClassification Enum
```
"likely_duplicate" | "related_issue" | "new_unmatched" | "insufficient_evidence"
```

### FixSource Enum
```
"historical_evidence" | "best_practice" | "agent_reasoning"
```

### RiskLevel Enum
```
"low" | "medium" | "high"
```

### RootCauseStatus Enum
```
"success" | "insufficient_evidence" | "error"
```

---

## CORS

The backend allows all origins (`*`) in the current configuration. In production, this should be restricted to the frontend domain. See `main.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```
