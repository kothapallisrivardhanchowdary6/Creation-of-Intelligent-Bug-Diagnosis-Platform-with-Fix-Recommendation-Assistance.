"""AI Agent definitions for defect analysis."""

import json
import logging
import time
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class TriageAgent:
    """Classifies bug severity, priority, category, and component."""

    def __init__(self, llm_service):
        self.llm = llm_service
        self.name = "Triage Agent"

    async def analyze(self, bug_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze bug for triage classification."""
        start_time = time.time()

        prompt = f"""Analyze this software bug report and provide triage classification.

Bug Title: {bug_data.get('title', '')}
Description: {bug_data.get('description', '')}
Stack Trace: {bug_data.get('stack_trace', 'None provided')}
Error Logs: {bug_data.get('error_logs', 'None provided')}
Environment: {bug_data.get('environment', 'Not specified')}

Respond with JSON:
{{
    "severity": "critical|high|medium|low",
    "priority": "P0|P1|P2|P3",
    "category": "string describing the defect category",
    "component": "string identifying the affected component",
    "confidence": 0.0-1.0,
    "reasoning": "brief explanation of classification"
}}"""

        result = await self.llm.generate_json(prompt, "You are a software defect triage expert.")
        duration = time.time() - start_time
        logger.info(f"Triage Agent completed in {duration:.2f}s")

        return {
            "agent": self.name,
            "result": result,
            "duration": duration,
            "timestamp": datetime.utcnow().isoformat()
        }


class LogAnalysisAgent:
    """Analyzes error logs, stack traces, and exception patterns."""

    def __init__(self, llm_service):
        self.llm = llm_service
        self.name = "Log Analysis Agent"

    async def analyze(self, bug_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze logs and stack traces."""
        start_time = time.time()

        prompt = f"""Analyze these error logs and stack traces for a software defect.

Stack Trace:
{bug_data.get('stack_trace', 'None provided')}

Error Logs:
{bug_data.get('error_logs', 'None provided')}

Bug Description: {bug_data.get('description', '')}

Respond with JSON:
{{
    "exceptions": [{{"type": "string", "message": "string", "file": "string", "line": number}}],
    "stack_trace_analysis": "string describing the failure chain",
    "error_patterns": ["list of identified error patterns"],
    "suspicious_logs": ["list of suspicious log entries"],
    "summary": "overall analysis summary"
}}"""

        result = await self.llm.generate_json(prompt, "You are a log analysis expert specializing in error pattern detection.")
        duration = time.time() - start_time
        logger.info(f"Log Analysis Agent completed in {duration:.2f}s")

        return {
            "agent": self.name,
            "result": result,
            "duration": duration,
            "timestamp": datetime.utcnow().isoformat()
        }


class RootCauseAgent:
    """Identifies probable root cause with evidence and confidence."""

    def __init__(self, llm_service, chroma_service, embedding_service):
        self.llm = llm_service
        self.chroma = chroma_service
        self.embeddings = embedding_service
        self.name = "Root Cause Agent"

    async def analyze(self, bug_data: Dict[str, Any], triage_result: Dict, log_result: Dict) -> Dict[str, Any]:
        """Determine root cause using RAG."""
        start_time = time.time()

        # Retrieve similar historical bugs for context
        query_text = f"{bug_data.get('title', '')} {bug_data.get('description', '')}"
        query_embedding = self.embeddings.embed_text(query_text)
        similar_bugs = self.chroma.search(query_embedding, top_k=3)

        context = "\n".join([
            f"- {b.get('document', '')} (Similarity: {b.get('score', 0):.2f})"
            for b in similar_bugs
        ])

        prompt = f"""Based on the following information, identify the probable root cause of this defect.

Bug: {bug_data.get('title', '')}
Description: {bug_data.get('description', '')}
Triage: {json.dumps(triage_result.get('result', {}))}
Log Analysis: {json.dumps(log_result.get('result', {}))}

Similar Historical Bugs:
{context}

Respond with JSON:
{{
    "probable_cause": "detailed description of the root cause",
    "evidence": ["list of supporting evidence"],
    "confidence": 0.0-1.0,
    "related_components": ["list of related components"],
    "explanation": "detailed explanation of the causal chain"
}}"""

        result = await self.llm.generate_json(prompt, "You are a root cause analysis expert with deep knowledge of software defects.")
        duration = time.time() - start_time
        logger.info(f"Root Cause Agent completed in {duration:.2f}s")

        return {
            "agent": self.name,
            "result": result,
            "duration": duration,
            "timestamp": datetime.utcnow().isoformat()
        }


class DuplicateDetectionAgent:
    """Detects potential duplicate bugs using semantic similarity."""

    def __init__(self, chroma_service, embedding_service):
        self.chroma = chroma_service
        self.embeddings = embedding_service
        self.name = "Duplicate Detection Agent"

    def analyze(self, bug_data: Dict[str, Any]) -> Dict[str, Any]:
        """Detect duplicates using vector similarity."""
        start_time = time.time()

        query_text = f"{bug_data.get('title', '')} {bug_data.get('description', '')}"
        query_embedding = self.embeddings.embed_text(query_text)
        results = self.chroma.search(query_embedding, top_k=5)

        # Calculate duplicate probability
        max_similarity = max([r.get('score', 0) for r in results]) if results else 0
        is_duplicate = max_similarity > 0.85
        duplicate_probability = min(1.0, max_similarity * 1.1)

        matching_bugs = [
            {
                "bug_id": r.get('id', ''),
                "title": r.get('document', ''),
                "similarity": r.get('score', 0),
                "project": r.get('metadata', {}).get('project', 'Unknown'),
                "component": r.get('metadata', {}).get('component', 'Unknown'),
                "severity": r.get('metadata', {}).get('severity', 'Unknown'),
                "resolution": r.get('metadata', {}).get('resolution', 'Unknown')
            }
            for r in results
        ]

        duration = time.time() - start_time
        logger.info(f"Duplicate Detection Agent completed in {duration:.2f}s")

        return {
            "agent": self.name,
            "result": {
                "is_duplicate": is_duplicate,
                "similarity_score": max_similarity,
                "duplicate_probability": duplicate_probability,
                "matching_bugs": matching_bugs,
                "analysis": f"Found {len(matching_bugs)} similar historical defects. Highest similarity: {max_similarity:.2%}."
            },
            "duration": duration,
            "timestamp": datetime.utcnow().isoformat()
        }


class RemediationAgent:
    """Suggests fixes, debugging steps, and testing strategies."""

    def __init__(self, llm_service, chroma_service, embedding_service):
        self.llm = llm_service
        self.chroma = chroma_service
        self.embeddings = embedding_service
        self.name = "Remediation Agent"

    async def analyze(self, bug_data: Dict[str, Any], root_cause_result: Dict,
                      triage_result: Dict) -> Dict[str, Any]:
        """Generate remediation suggestions."""
        start_time = time.time()

        # Get historical resolutions
        query_text = f"{bug_data.get('title', '')} {root_cause_result.get('result', {}).get('probable_cause', '')}"
        query_embedding = self.embeddings.embed_text(query_text)
        similar_bugs = self.chroma.search(query_embedding, top_k=3)

        resolutions = "\n".join([
            f"- {b.get('metadata', {}).get('resolution', 'N/A')}"
            for b in similar_bugs
        ])

        prompt = f"""Based on the root cause analysis, suggest remediation steps.

Bug: {bug_data.get('title', '')}
Root Cause: {json.dumps(root_cause_result.get('result', {}))}
Category: {triage_result.get('result', {}).get('category', 'Unknown')}
Component: {triage_result.get('result', {}).get('component', 'Unknown')}

Historical Resolutions:
{resolutions}

Respond with JSON:
{{
    "suggested_fix": "detailed fix description",
    "debugging_steps": ["step 1", "step 2", ...],
    "validation_steps": ["step 1", "step 2", ...],
    "regression_tests": ["test 1", "test 2", ...],
    "estimated_effort": "time estimate",
    "risk_level": "low|medium|high"
}}"""

        result = await self.llm.generate_json(prompt, "You are a software engineering expert specializing in bug remediation.")
        duration = time.time() - start_time
        logger.info(f"Remediation Agent completed in {duration:.2f}s")

        return {
            "agent": self.name,
            "result": result,
            "duration": duration,
            "timestamp": datetime.utcnow().isoformat()
        }
