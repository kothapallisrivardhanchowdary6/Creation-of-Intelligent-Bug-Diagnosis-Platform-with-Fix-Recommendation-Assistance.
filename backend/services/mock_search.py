"""Mock search service for development."""

from typing import List, Dict


HISTORICAL_BUGS = [
    {"bug_id": "MOZ-1001", "title": "NullPointerException in NetworkManager when connection drops", "description": "Fixed by adding null check", "project": "Mozilla Firefox", "component": "Networking", "severity": "critical", "score_base": 0.85},
    {"bug_id": "MOZ-1002", "title": "Memory leak in tab rendering engine", "description": "Implemented proper cleanup", "project": "Mozilla Firefox", "component": "Layout Engine", "severity": "high", "score_base": 0.72},
    {"bug_id": "APC-2001", "title": "StackOverflowError in recursive XML parser", "description": "Converted to iterative approach", "project": "Apache HTTP Server", "component": "Core", "severity": "critical", "score_base": 0.78},
    {"bug_id": "APC-2002", "title": "Race condition in thread pool causing deadlock", "description": "Added lock ordering and timeout", "project": "Apache Tomcat", "component": "Thread Pool", "severity": "critical", "score_base": 0.69},
    {"bug_id": "APC-2003", "title": "Buffer overflow in HTTP header parsing", "description": "Implemented bounds checking", "project": "Apache HTTP Server", "component": "HTTP Parser", "severity": "critical", "score_base": 0.82},
    {"bug_id": "ECL-3001", "title": "ClassCastException in JDT compiler", "description": "Added type erasure handling", "project": "Eclipse JDT", "component": "Compiler", "severity": "medium", "score_base": 0.61},
    {"bug_id": "ECL-3002", "title": "UI freeze with large workspace", "description": "Moved to background thread", "project": "Eclipse Platform", "component": "UI Framework", "severity": "high", "score_base": 0.55},
    {"bug_id": "ECL-3003", "title": "IndexOutOfBoundsException in code completion", "description": "Added boundary checks", "project": "Eclipse JDT", "component": "Content Assist", "severity": "medium", "score_base": 0.74},
    {"bug_id": "MOZ-1003", "title": "Segmentation fault in WebGL renderer", "description": "Added shader validation", "project": "Mozilla Firefox", "component": "Graphics", "severity": "high", "score_base": 0.67},
    {"bug_id": "APC-2004", "title": "Connection leak in connection pool", "description": "Added try-finally for connection return", "project": "Apache Tomcat", "component": "Connection Pool", "severity": "high", "score_base": 0.80},
    {"bug_id": "ECL-3004", "title": "Deadlock in plugin activation", "description": "Implemented cycle detection", "project": "Eclipse Platform", "component": "Plugin Framework", "severity": "critical", "score_base": 0.63},
    {"bug_id": "MOZ-1004", "title": "CSS Grid layout miscalculation", "description": "Fixed constraint solving", "project": "Mozilla Firefox", "component": "CSS Engine", "severity": "medium", "score_base": 0.52},
]


def mock_search(query: str, top_k: int = 5) -> List[Dict]:
    """Mock semantic search based on keyword matching."""
    query_lower = query.lower()
    query_words = set(query_lower.split())

    results = []
    for bug in HISTORICAL_BUGS:
        text = f"{bug['title']} {bug['description']} {bug['component']} {bug['project']}".lower()
        text_words = set(text.split())
        overlap = len(query_words & text_words)
        relevance = overlap / max(len(query_words), 1)
        score = bug['score_base'] * 0.5 + relevance * 0.5

        results.append({
            "bug_id": bug["bug_id"],
            "title": bug["title"],
            "description": bug["description"],
            "score": min(1.0, score),
            "project": bug["project"],
            "metadata": {
                "component": bug["component"],
                "severity": bug["severity"],
                "resolution": bug["description"]
            }
        })

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_k]
