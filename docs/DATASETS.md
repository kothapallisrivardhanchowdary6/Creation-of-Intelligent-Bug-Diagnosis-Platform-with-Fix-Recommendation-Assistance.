# Historical Defect Datasets

## Overview

The system ingests defect data from three major open-source projects: Mozilla, Apache, and Eclipse. These datasets provide realistic historical context for the RAG pipeline.

## Mozilla Firefox (MDVP)

**Source**: Mozilla Bugzilla (https://bugzilla.mozilla.org)

### Characteristics
- **Domain**: Web browser
- **Components**: Networking, Layout Engine, Graphics, CSS Engine, JavaScript
- **Defect Types**: Crashes, memory leaks, rendering issues, security vulnerabilities
- **Scale**: 4 sample defects included

### Sample Defects
| Bug ID | Component | Severity | Description |
|--------|-----------|----------|-------------|
| MOZ-1001 | Networking | Critical | NullPointerException in NetworkManager |
| MOZ-1002 | Layout Engine | High | Memory leak in tab rendering |
| MOZ-1003 | Graphics | High | Segfault in WebGL renderer |
| MOZ-1004 | CSS Engine | Medium | Grid layout miscalculation |

## Apache HTTP Server & Tomcat

**Source**: Apache JIRA (https://issues.apache.org)

### Characteristics
- **Domain**: Web server / Application server
- **Components**: Core, HTTP Parser, Thread Pool, Connection Pool
- **Defect Types**: Security vulnerabilities, concurrency issues, resource leaks
- **Scale**: 4 sample defects included

### Sample Defects
| Bug ID | Component | Severity | Description |
|--------|-----------|----------|-------------|
| APC-2001 | Core | Critical | StackOverflowError in XML parser |
| APC-2002 | Thread Pool | Critical | Race condition causing deadlock |
| APC-2003 | HTTP Parser | Critical | Buffer overflow vulnerability |
| APC-2004 | Connection Pool | High | Connection leak on exception |

## Eclipse JDT & Platform

**Source**: Eclipse Bugzilla (https://bugs.eclipse.org)

### Characteristics
- **Domain**: IDE / Development tools
- **Components**: Compiler, UI Framework, Content Assist, Plugin Framework
- **Defect Types**: Type system issues, UI freezes, deadlocks, crashes
- **Scale**: 4 sample defects included

### Sample Defects
| Bug ID | Component | Severity | Description |
|--------|-----------|----------|-------------|
| ECL-3001 | Compiler | Medium | ClassCastException in generics |
| ECL-3002 | UI Framework | High | UI freeze with large workspace |
| ECL-3003 | Content Assist | Medium | IndexOutOfBounds in completion |
| ECL-3004 | Plugin Framework | Critical | Deadlock in plugin activation |

## Data Schema

### Bug Report Structure
```json
{
  "bug_id": "string (unique identifier)",
  "title": "string (short summary)",
  "description": "string (detailed description)",
  "project": "string (source project)",
  "component": "string (affected component)",
  "severity": "critical|high|medium|low",
  "status": "RESOLVED|OPEN|IN_PROGRESS",
  "resolution": "string (how it was fixed)"
}
```

## Data Ingestion Pipeline

```
CSV/JSON Files
    ↓
Data Cleaning (remove duplicates, normalize text)
    ↓
Normalization (standardize fields, fix encoding)
    ↓
Semantic Chunking (split into title/description/resolution)
    ↓
Metadata Extraction (project, component, severity)
    ↓
Embedding Generation (MiniLM-L6-v2, 384 dims)
    ↓
ChromaDB Indexing (with metadata)
```

## Using External Datasets

To add real datasets:

1. Place CSV/JSON files in `data/` directory
2. Run the ingestion script:
```bash
python scripts/seed_data.py --source data/your_dataset.csv
```
3. Verify indexing:
```bash
curl http://localhost:8000/api/knowledge-base/status
```

## Dataset Statistics

| Metric | Value |
|--------|-------|
| Total sample defects | 12 |
| Projects | 5 (Firefox, HTTP Server, Tomcat, JDT, Platform) |
| Severity distribution | 5 critical, 4 high, 3 medium |
| Average description length | ~350 characters |
| Vector dimensions | 384 |
