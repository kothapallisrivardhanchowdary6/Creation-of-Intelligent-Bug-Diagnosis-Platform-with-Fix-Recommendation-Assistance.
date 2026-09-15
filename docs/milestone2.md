# Milestone 2: Triage & Log Analysis Agents

## Overview

Milestone 2 extends the M1 foundation with production-grade Triage and Log Analysis agents featuring:
- Pydantic-validated structured output
- Deterministic regex-based stack trace parsing (Java, Python, Node.js)
- Parallel agent execution via async orchestrator
- Combined bug context for downstream agents
- Graceful handling of missing/messy data

## Architecture

```
Bug Submission
      ↓
Agent Orchestrator (M2)
   ↙       ↘
Triage    Log Analysis     ← Run concurrently via asyncio.gather()
   ↘       ↙
Combined Bug Context
      ↓
Future M3 Agents (Root Cause, Duplicate, Remediation)
```

### Key Design Decisions

1. **Deterministic First, LLM Optional**: Agents use regex/rules first, then optionally refine with LLM
2. **Pydantic Validation**: All outputs validated against strict schemas
3. **Graceful Degradation**: Missing logs → lower confidence, not failure
4. **Parallel Execution**: Triage and Log Analysis run concurrently

## Triage Agent (`backend/agents/triage_agent.py`)

### Inputs
- Bug title, description, environment, stack trace, error logs

### Output (Pydantic-validated)
```json
{
  "severity": "critical|high|medium|low",
  "priority": "P0|P1|P2|P3",
  "category": "Null Reference|Memory Management|Concurrency|...",
  "component": "Networking|Database|Authentication|...",
  "confidence": 0.0-1.0,
  "reasoning": "Human-readable explanation"
}
```

### Classification Logic

**Severity** — keyword-based with weighted scoring:
- Critical: crash, fatal, data loss, security, vulnerability, CVE, OOM
- High: error, fail, exception, null, timeout, deadlock
- Medium: slow, incorrect, wrong, unexpected, warning
- Low: enhancement, feature request, documentation

**Priority** — direct mapping from severity:
- Critical → P0, High → P1, Medium → P2, Low → P3

**Category** — pattern matching:
- Null Reference, Memory Management, Concurrency, Network/IO, Security, Input Validation, UI/Rendering, Performance, Logic Error, Configuration

**Component** — keyword matching against 14 component categories:
- Networking, Database, Authentication, UI/Frontend, API, File System, Memory Management, Concurrency, Security, Performance, Logging, Configuration, Testing, Build/Deploy

**Confidence** — calculated from available data:
- Base: 0.5
- +0.1 for title, +0.1 for description (>50 chars)
- +0.15 for stack trace, +0.1 for error logs, +0.05 for environment
- +0.1 for >5 keyword matches, +0.05 for >2 matches
- Capped at 0.95

## Log Analysis Agent (`backend/agents/log_analysis_agent.py`)

### Inputs
- Stack trace (any language), error logs, bug description

### Output (Pydantic-validated)
```json
{
  "exceptions": [
    {
      "exception_type": "NullPointerException",
      "error_message": "Cannot invoke method on null",
      "file_name": "UserService.java",
      "class_name": "UserService",
      "method_name": "processEmail",
      "line_number": 45,
      "code_path": "com.app.service.UserService.processEmail",
      "confidence": 0.9
    }
  ],
  "error_patterns": ["Null reference/pointer", "Resource leak"],
  "failure_point": "UserService.java line 45 in processEmail",
  "code_path": "com.app.service.UserService.processEmail",
  "confidence": 0.85,
  "summary": "Found 1 exception: NullPointerException..."
}
```

### Stack Trace Parsing

**Language Detection** — automatic based on patterns:
- Java: `java.lang.`, `.java:`, `at com.`, `Caused by:`
- Python: `Traceback`, `File "`, `.py:`, `TypeError:`
- Node.js: `node:`, `.js:`, `at Object.`, `npm ERR!`

**Java Parser**:
```
java.lang.NullPointerException: message
    at com.package.Class.method(File.java:123)
```
Extracts: exception_type, error_message, class_name, method_name, file_name, line_number

**Python Parser**:
```
Traceback (most recent call last):
  File "/path/to/file.py", line 123, in function
ValueError: message
```
Extracts: exception_type, error_message, file_name, line_number, method_name

**Node.js Parser**:
```
TypeError: message
    at FunctionName (/path/to/file.js:123:45)
```
Extracts: exception_type, error_message, method_name, file_name, line_number

### Error Pattern Detection
Identifies 10 common patterns:
- Null reference/pointer
- Resource leak
- Concurrency issue
- Timeout
- Connection failure
- Permission denied
- Out of memory
- Stack overflow
- Type mismatch
- Index out of bounds

## Orchestrator (`backend/agents/orchestrator.py`)

### M2 Pipeline Flow

```python
async def run_m2_pipeline(bug_data):
    # Run both agents concurrently
    triage_task = safe_run_agent(triage_agent, bug_data)
    log_task = safe_run_agent(log_agent, bug_data)
    
    triage_result, log_result = await asyncio.gather(triage_task, log_task)
    
    # Create combined context
    combined = CombinedBugContext(triage_result, log_result)
    
    return {
        "triage": triage_result,
        "log_analysis": log_result,
        "combined_context": combined.to_dict()
    }
```

### Error Handling
- Each agent wrapped in `_safe_run_agent()` with try/except
- Failed agents return fallback results with `status: "error"`
- Pipeline continues even if one agent fails
- Combined context tracks which agents succeeded

### CombinedBugContext
Merges outputs from both agents:
- `has_triage` / `has_log_analysis` — success flags
- `combined_summary` — human-readable merge
- Ready for downstream M3 agents

## API Integration

### POST /api/bugs/{id}/analyze

Updated to use M2 orchestrator:

```python
@router.post("/bugs/{bug_id}/analyze")
async def analyze_bug(bug_id: str):
    orchestrator = get_orchestrator()
    analysis = await orchestrator.run_m2_pipeline(bug)
    return analysis
```

Response includes:
```json
{
  "bug_id": "BUG-XXX",
  "milestone": "M2",
  "status": "completed",
  "triage": { "severity": "high", "priority": "P1", ... },
  "log_analysis": { "exceptions": [...], "failure_point": "...", ... },
  "combined_context": { "has_triage": true, "has_log_analysis": true, ... },
  "total_duration": 0.05
}
```

## Frontend Updates

The BugAnalysis page now displays:

### Triage Section
- Severity badge with color coding
- Priority level
- Component assignment
- Confidence bar
- Detailed reasoning

### Log Analysis Section (M2 additions)
- **Failure Point**: File, line, method where failure occurs
- **Code Path**: Full code path to the failure
- **Enhanced Exceptions**: Shows class, method, file, line for each
- **Confidence Bar**: Visual confidence indicator
- **Error Patterns**: Tagged pattern list

## Test Cases

### Test Suite (`backend/tests/test_milestone2.py`)

25+ tests covering:
- Severity classification (critical, high, medium, low)
- Priority mapping
- Component detection
- Java stack trace parsing
- Python traceback parsing
- Node.js stack trace parsing
- Missing/messy log handling
- Orchestrator flow
- Combined context creation
- Pydantic validation

### Evaluation Data (`data/milestone2_test_cases.json`)

10 realistic test cases:
- TC-001: Java NullPointerException
- TC-002: Python ValueError
- TC-003: Node.js TypeError
- TC-004: Critical security vulnerability (no stack trace)
- TC-005: Java OutOfMemoryError
- TC-006: Missing logs (description only)
- TC-007: Race condition (ConcurrentModificationException)
- TC-008: Low severity enhancement
- TC-009: Connection timeout (SocketTimeoutException)
- TC-010: ArrayIndexOutOfBoundsException

### Evaluation Script (`scripts/evaluate_milestone2.py`)

Runs actual agent code against test cases and measures:
- Severity accuracy
- Priority accuracy
- Component accuracy
- Exception type accuracy
- File name accuracy
- Line number accuracy
- Method name accuracy

## Running Tests

```bash
# Unit tests
cd backend
pytest tests/test_milestone2.py -v

# Evaluation (runs actual agents)
python scripts/evaluate_milestone2.py
```

## Files Created/Modified

### New Files
- `backend/agents/triage_agent.py` — Enhanced Triage Agent with Pydantic
- `backend/agents/log_analysis_agent.py` — Log Analysis with regex parsing
- `backend/tests/test_milestone2.py` — M2 test suite
- `data/milestone2_test_cases.json` — Test case data
- `scripts/evaluate_milestone2.py` — Evaluation runner
- `docs/milestone2.md` — This document

### Modified Files
- `backend/agents/orchestrator.py` — M2 parallel execution flow
- `backend/routers/bugs.py` — Integrated M2 orchestrator
- `src/types/index.ts` — Added M2 fields to types
- `src/services/mockData.ts` — M2 mock data generation
- `src/pages/BugAnalysis.tsx` — Display M2 results

## Known Limitations

1. **No real LLM**: Mock mode uses deterministic rules only
2. **Single-language detection**: Mixed-language traces may not parse correctly
3. **No fuzzy matching**: File names must match exactly in tests
4. **Confidence heuristic**: Not calibrated against real-world data
5. **No streaming**: Results returned after full pipeline completion

## Next Steps (Milestone 3)

- Root Cause Agent using combined context
- Duplicate Detection with real ChromaDB
- Remediation Agent with RAG-powered suggestions
- Real LLM integration for refinement
- Streaming results via WebSocket
