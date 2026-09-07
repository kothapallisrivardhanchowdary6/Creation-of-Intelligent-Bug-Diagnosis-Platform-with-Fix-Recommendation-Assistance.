"""Mock analysis generator for development without LLM."""

import random
from datetime import datetime
from typing import Dict, Any


def generate_mock_analysis(bug: Dict[str, Any]) -> Dict[str, Any]:
    """Generate mock analysis results for a bug."""
    return {
        "bug_id": bug["id"],
        "timestamp": datetime.utcnow().isoformat(),
        "triage": {
            "severity": _determine_severity(bug),
            "priority": _determine_priority(bug),
            "category": _determine_category(bug),
            "component": _determine_component(bug),
            "confidence": 0.87,
            "reasoning": f"Based on analysis of the bug report, this issue appears to be a {_determine_category(bug).lower()} defect."
        },
        "log_analysis": {
            "exceptions": [
                {"type": "RuntimeException", "message": "Unhandled exception in processing pipeline", "file": "main.py", "line": 45}
            ],
            "stack_trace_analysis": "Stack trace indicates a cascading failure originating from the core processing module.",
            "error_patterns": ["Null reference access", "Unhandled exception in async operation", "Resource cleanup failure"],
            "suspicious_logs": ["ERROR: Connection timeout", "WARN: Retry failed", "FATAL: Unrecoverable state"],
            "summary": "Analysis identified exception patterns consistent with resource management failures."
        },
        "root_cause": {
            "probable_cause": f"Insufficient error handling in the {_determine_component(bug)} module leading to unhandled edge cases.",
            "evidence": [
                "Error pattern matches historical defect patterns",
                "Stack trace points to core module",
                "Similar issues found in related components"
            ],
            "confidence": 0.79,
            "related_components": [_determine_component(bug), "Error Handler", "Resource Manager"],
            "explanation": "The defect originates from insufficient input validation and error handling."
        },
        "duplicate_detection": {
            "is_duplicate": random.random() > 0.6,
            "similarity_score": 0.65 + random.random() * 0.3,
            "duplicate_probability": 0.4 + random.random() * 0.4,
            "matching_bugs": [
                {"bug_id": "MOZ-1001", "title": "NullPointerException in NetworkManager", "similarity": 0.89, "project": "Mozilla Firefox", "component": "Networking", "severity": "critical", "resolution": "Added null check"},
                {"bug_id": "APC-2003", "title": "Buffer overflow in HTTP parser", "similarity": 0.75, "project": "Apache HTTP Server", "component": "Core", "severity": "critical", "resolution": "Added bounds checking"},
                {"bug_id": "ECL-3003", "title": "IndexOutOfBoundsException in completion", "similarity": 0.68, "project": "Eclipse JDT", "component": "Content Assist", "severity": "medium", "resolution": "Added boundary checks"}
            ],
            "analysis": "Semantic analysis found 3 potentially related historical defects."
        },
        "remediation": {
            "suggested_fix": f"Add comprehensive error handling and input validation in {_determine_component(bug)}. Implement defensive programming patterns.",
            "debugging_steps": [
                "Reproduce the issue in a controlled environment",
                "Add detailed logging at the failure point",
                "Verify input validation and null checks",
                "Check resource lifecycle management"
            ],
            "validation_steps": [
                "Create unit test reproducing the failure",
                "Verify fix resolves the original issue",
                "Test edge cases and boundary conditions",
                "Run integration tests"
            ],
            "regression_tests": [
                "Run existing test suite for affected module",
                "Execute end-to-end tests",
                "Verify no performance degradation",
                "Check compatibility with dependent modules"
            ],
            "estimated_effort": "2-4 hours",
            "risk_level": "medium"
        }
    }


def _determine_severity(bug: Dict) -> str:
    text = f"{bug.get('title', '')} {bug.get('description', '')}".lower()
    if any(w in text for w in ['crash', 'fatal', 'data loss', 'security']):
        return 'critical'
    if any(w in text for w in ['error', 'fail', 'broken', 'exception']):
        return 'high'
    if any(w in text for w in ['slow', 'incorrect', 'wrong']):
        return 'medium'
    return 'low'


def _determine_priority(bug: Dict) -> str:
    severity = _determine_severity(bug)
    return {'critical': 'P0', 'high': 'P1', 'medium': 'P2', 'low': 'P3'}[severity]


def _determine_category(bug: Dict) -> str:
    text = f"{bug.get('title', '')} {bug.get('description', '')}".lower()
    if any(w in text for w in ['null', 'undefined', 'reference']):
        return 'Null Reference'
    if any(w in text for w in ['memory', 'leak', 'overflow']):
        return 'Memory Management'
    if any(w in text for w in ['thread', 'race', 'deadlock']):
        return 'Concurrency'
    if any(w in text for w in ['network', 'connection', 'timeout']):
        return 'Network/IO'
    return 'Logic Error'


def _determine_component(bug: Dict) -> str:
    text = f"{bug.get('title', '')} {bug.get('description', '')}".lower()
    if any(w in text for w in ['database', 'query', 'sql']):
        return 'Database Layer'
    if any(w in text for w in ['api', 'endpoint', 'request']):
        return 'API Layer'
    if any(w in text for w in ['ui', 'component', 'page']):
        return 'UI Component'
    return 'Core Module'
