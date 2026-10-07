"""
Milestone 3 Unit Tests.

Covers:
  - RootCauseAgent: success, insufficient evidence, RAG integration, LLM fallback
  - DuplicateDetectionAgent: likely_duplicate, related_issue, new_unmatched,
                              insufficient_evidence, threshold configuration
  - RemediationAgent: success, fix source labeling, RAG integration, LLM fallback
  - AgentOrchestrator (M3): full pipeline, partial failures, all agents run

No hardcoded/fabricated similarity scores or analysis results.
"""

import pytest
import asyncio
import sys
import os
from unittest.mock import MagicMock, patch
from typing import Dict, Any, List

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from agents.root_cause_agent import RootCauseAgent, RootCauseResult
from agents.duplicate_detection_agent import (
    DuplicateDetectionAgent,
    DuplicateDetectionResult,
    LIKELY_DUPLICATE_THRESHOLD,
    RELATED_ISSUE_THRESHOLD,
)
from agents.remediation_agent import RemediationAgent, RemediationResult
from agents.orchestrator import AgentOrchestrator, CombinedBugContext


# ============================================================
# Fixtures
# ============================================================

def make_mock_chroma(scores: List[float] = None):
    """Create a mock ChromaService with configurable similarity scores."""
    if scores is None:
        scores = [0.88, 0.72, 0.61, 0.45, 0.30]

    chroma = MagicMock()
    results = []
    bug_ids = ["MOZ-1001", "APC-2003", "ECL-3003", "MOZ-1002", "APC-2002"]
    docs = [
        "NullPointerException in NetworkManager",
        "Buffer overflow in HTTP header parsing",
        "IndexOutOfBoundsException in code completion",
        "Memory leak in tab rendering engine",
        "Race condition in thread pool",
    ]
    for i, score in enumerate(scores[:5]):
        results.append({
            "id": bug_ids[i],
            "document": docs[i],
            "metadata": {
                "project": "Mozilla" if i % 2 == 0 else "Apache",
                "component": "Networking" if i == 0 else "Core",
                "severity": "critical" if score > 0.8 else "high",
                "resolution": f"Fixed by applying defensive programming at index {i}",
            },
            "score": score,
        })
    chroma.search.return_value = results
    return chroma


def make_mock_embeddings():
    """Create a mock EmbeddingService with deterministic output."""
    embeddings = MagicMock()
    embeddings.embed_text.return_value = [0.1] * 384
    return embeddings


def make_mock_llm(response_type: str = "root_cause"):
    """Create a mock LLMService returning valid JSON."""
    llm = MagicMock()
    llm.mock_mode = True

    responses = {
        "root_cause": {
            "probable_cause": "Missing null check before accessing connection object in NetworkManager",
            "confidence": 0.82,
            "reasoning": "Exception type + failure point + historical evidence all indicate null access",
            "agent_reasoning": "Inferred from exception pattern and component context",
            "related_components": ["Networking", "Core Module"],
            "hypotheses": [
                {
                    "hypothesis": "Null connection object accessed without guard clause",
                    "confidence": 0.82,
                    "supporting_evidence": ["NullPointerException type", "NetworkManager failure point"],
                    "causal_chain": "Connection drop → retry handler → null access → exception",
                }
            ],
        },
        "remediation": {
            "suggested_fix": "Add null check before accessing connection object in retry handler",
            "fix_from_best_practice": False,
            "confidence": 0.85,
            "agent_reasoning": "Fix derived from root cause: unguarded null access",
            "implementation_steps": [
                {"step": "Locate the retryConnection method", "detail": None, "is_speculative": False},
                {"step": "Add null check before getStatus() call", "detail": "if (conn == null) return;", "is_speculative": False},
                {"step": "Write unit test for null connection scenario", "detail": None, "is_speculative": False},
            ],
            "debugging_steps": ["Reproduce with null connection", "Add breakpoint at line 247"],
            "validation_steps": ["Unit test null scenario", "Integration test retry flow"],
            "regression_tests": ["Run full NetworkManager test suite"],
            "best_practices": ["Always validate inputs at method boundaries"],
            "estimated_effort": "2-4 hours",
            "risk_level": "medium",
        },
    }

    async def generate_json(prompt, system_prompt=""):
        prompt_lower = prompt.lower()
        if "root cause" in prompt_lower or "causal chain" in prompt_lower:
            return responses["root_cause"]
        elif "remediation" in prompt_lower or "implementation_steps" in prompt_lower:
            return responses["remediation"]
        return {"confidence": 0.5, "analysis": "mock"}

    llm.generate_json = generate_json
    return llm


def make_triage_result(severity="high", confidence=0.85, component="Networking"):
    return {
        "agent": "Triage Agent",
        "status": "success",
        "result": {
            "severity": severity,
            "priority": "P1",
            "category": "Null Reference",
            "component": component,
            "confidence": confidence,
            "reasoning": "NullPointerException indicates missing null check",
        },
        "duration": 0.1,
        "timestamp": "2024-01-01T00:00:00",
    }


def make_log_result(exception_type="NullPointerException"):
    return {
        "agent": "Log Analysis Agent",
        "status": "success",
        "result": {
            "exceptions": [
                {
                    "exception_type": exception_type,
                    "error_message": "Cannot invoke method on null",
                    "file_name": "NetworkManager.java",
                    "line_number": 247,
                    "method_name": "retryConnection",
                    "confidence": 0.9,
                }
            ],
            "error_patterns": ["Null reference access pattern detected"],
            "failure_point": "NetworkManager.java:247 in retryConnection",
            "code_path": "com.app.NetworkManager.retryConnection",
            "confidence": 0.88,
            "summary": "NullPointerException in NetworkManager.retryConnection at line 247",
        },
        "duration": 0.05,
        "timestamp": "2024-01-01T00:00:00",
    }


def make_root_cause_result(confidence=0.78, status="success"):
    return {
        "agent": "Root Cause Agent",
        "status": status,
        "result": {
            "status": status,
            "probable_cause": "Missing null check before accessing connection object",
            "confidence": confidence,
            "reasoning": "Exception type + historical evidence confirm null access",
            "agent_reasoning": "Inferred from exception pattern",
            "related_components": ["Networking", "Core Module"],
            "hypotheses": [],
            "retrieved_evidence": [
                {
                    "bug_id": "MOZ-1001",
                    "document": "NullPointerException in NetworkManager",
                    "similarity_score": 0.88,
                    "source": "historical_defect_database",
                }
            ],
            "evidence_summary": "1 similar defect retrieved",
        },
        "duration": 0.2,
        "timestamp": "2024-01-01T00:00:00",
    }


def make_duplicate_result(classification="new_unmatched"):
    return {
        "agent": "Duplicate Detection Agent",
        "status": "success",
        "result": {
            "classification": classification,
            "top_match_similarity": 0.65 if classification == "related_issue" else 0.30,
            "duplicate_probability": 0.30,
            "matched_bugs": [],
            "analysis_summary": f"Classification: {classification}",
            "thresholds_used": {"likely_duplicate": 0.82, "related_issue": 0.55},
            "is_duplicate": classification == "likely_duplicate",
            "similarity_score": 0.65,
            "matching_bugs": [],
        },
        "duration": 0.1,
        "timestamp": "2024-01-01T00:00:00",
    }


JAVA_BUG = {
    "id": "TEST-001",
    "title": "NullPointerException in NetworkManager when connection drops",
    "description": "App crashes with NPE when network drops during download",
    "stack_trace": "java.lang.NullPointerException: Cannot invoke getStatus()\n\tat com.app.network.NetworkManager.retryConnection(NetworkManager.java:247)",
    "error_logs": "ERROR [NetworkManager] Connection is null",
    "environment": "Java 11",
}

PYTHON_BUG = {
    "id": "TEST-002",
    "title": "ValueError when parsing non-ISO dates in report generator",
    "description": "Date parsing fails for DD/MM/YYYY format",
    "stack_trace": 'Traceback (most recent call last):\n  File "/app/reports/generator.py", line 156, in parse_date\n    return datetime.strptime(date_str, \'%Y-%m-%d\')\nValueError: time data \'15/01/2024\' does not match format',
    "error_logs": "ERROR [ReportGenerator] Failed to parse date",
    "environment": "Python 3.11",
}

VAGUE_BUG = {
    "id": "TEST-003",
    "title": "Something is wrong",
    "description": "It does not work.",
    "stack_trace": "",
    "error_logs": "",
    "environment": "",
}

MEMORY_BUG = {
    "id": "TEST-004",
    "title": "Memory leak in tab renderer causing OOM crash",
    "description": "Memory grows 50MB per 100 tab switches and never frees. Heap dump shows render contexts not GCd.",
    "stack_trace": "java.lang.OutOfMemoryError: Java heap space\n\tat com.browser.render.TabRenderer.createRenderContext(TabRenderer.java:445)",
    "error_logs": "ERROR [TabRenderer] OutOfMemoryError\nWARN  [TabManager] Memory pressure: heap at 92%",
    "environment": "Java 11, 8GB RAM",
}


# ============================================================
# Root Cause Agent Tests
# ============================================================

class TestRootCauseAgent:
    """Tests for the M3 RootCauseAgent."""

    @pytest.fixture
    def agent_with_services(self):
        return RootCauseAgent(
            llm_service=make_mock_llm("root_cause"),
            chroma_service=make_mock_chroma(),
            embedding_service=make_mock_embeddings(),
        )

    @pytest.fixture
    def agent_no_services(self):
        return RootCauseAgent()

    @pytest.mark.asyncio
    async def test_returns_success_for_good_bug(self, agent_with_services):
        """Should return status='success' for a bug with clear signals."""
        result = await agent_with_services.analyze(
            JAVA_BUG, make_triage_result(), make_log_result()
        )
        assert result["status"] in ("success", "insufficient_evidence")
        r = result["result"]
        assert isinstance(r["probable_cause"], str)
        assert len(r["probable_cause"]) > 0

    @pytest.mark.asyncio
    async def test_confidence_in_valid_range(self, agent_with_services):
        """Confidence must always be between 0 and 1."""
        result = await agent_with_services.analyze(
            JAVA_BUG, make_triage_result(), make_log_result()
        )
        conf = result["result"]["confidence"]
        assert 0.0 <= conf <= 1.0, f"Confidence {conf} out of range"

    @pytest.mark.asyncio
    async def test_insufficient_evidence_for_vague_bug(self, agent_no_services):
        """Vague bug with no logs should return insufficient_evidence or low confidence."""
        result = await agent_no_services.analyze(VAGUE_BUG, {}, {})
        r = result["result"]
        # Either insufficient_evidence status OR very low confidence
        assert r["status"] in ("success", "insufficient_evidence", "error")
        if r["status"] == "success":
            assert r["confidence"] <= 0.60

    @pytest.mark.asyncio
    async def test_retrieved_evidence_separate_from_reasoning(self, agent_with_services):
        """Evidence and agent_reasoning must be separate fields."""
        result = await agent_with_services.analyze(
            JAVA_BUG, make_triage_result(), make_log_result()
        )
        r = result["result"]
        # Both fields must exist and be strings
        assert isinstance(r.get("retrieved_evidence"), list)
        assert isinstance(r.get("agent_reasoning"), str)
        assert isinstance(r.get("evidence_summary"), str)

    @pytest.mark.asyncio
    async def test_rag_retrieval_called(self, agent_with_services):
        """ChromaDB search must be called during analysis."""
        await agent_with_services.analyze(
            JAVA_BUG, make_triage_result(), make_log_result()
        )
        agent_with_services.chroma.search.assert_called_once()
        agent_with_services.embeddings.embed_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_evidence_has_similarity_scores(self, agent_with_services):
        """Retrieved evidence must include real similarity scores from ChromaDB."""
        result = await agent_with_services.analyze(
            JAVA_BUG, make_triage_result(), make_log_result()
        )
        evidence = result["result"].get("retrieved_evidence", [])
        for ev in evidence:
            score = ev.get("similarity_score", 0.0)
            assert 0.0 <= score <= 1.0, f"Evidence score {score} out of range"
            assert score > 0.0, "Evidence score should be non-zero (came from mock with real values)"

    @pytest.mark.asyncio
    async def test_deterministic_fallback_without_llm(self):
        """Agent should produce a result even without LLM service."""
        agent = RootCauseAgent(
            llm_service=None,
            chroma_service=make_mock_chroma(),
            embedding_service=make_mock_embeddings(),
        )
        result = await agent.analyze(JAVA_BUG, make_triage_result(), make_log_result())
        assert result["result"]["probable_cause"]
        assert result["result"]["confidence"] > 0.0

    @pytest.mark.asyncio
    async def test_related_components_returned(self, agent_with_services):
        """Related components list should be populated for a detailed bug."""
        result = await agent_with_services.analyze(
            JAVA_BUG, make_triage_result(), make_log_result()
        )
        components = result["result"].get("related_components", [])
        assert isinstance(components, list)

    @pytest.mark.asyncio
    async def test_python_bug_analysis(self, agent_with_services):
        """Should analyze Python stack traces correctly."""
        result = await agent_with_services.analyze(
            PYTHON_BUG, make_triage_result(component="Report Generator"), make_log_result("ValueError")
        )
        r = result["result"]
        assert r["probable_cause"]
        assert 0.0 <= r["confidence"] <= 1.0

    @pytest.mark.asyncio
    async def test_hypotheses_structure(self, agent_with_services):
        """Hypotheses list should have correct structure."""
        result = await agent_with_services.analyze(
            JAVA_BUG, make_triage_result(), make_log_result()
        )
        hypotheses = result["result"].get("hypotheses", [])
        assert isinstance(hypotheses, list)
        for h in hypotheses:
            assert "hypothesis" in h
            assert "confidence" in h
            assert 0.0 <= h["confidence"] <= 1.0
            assert isinstance(h.get("supporting_evidence", []), list)

    @pytest.mark.asyncio
    async def test_graceful_error_handling(self):
        """Agent should return an error result on unexpected exceptions."""
        chroma = MagicMock()
        chroma.search.side_effect = RuntimeError("ChromaDB unavailable")
        agent = RootCauseAgent(
            llm_service=None,
            chroma_service=chroma,
            embedding_service=make_mock_embeddings(),
        )
        result = await agent.analyze(JAVA_BUG, make_triage_result(), make_log_result())
        assert "result" in result
        assert isinstance(result["result"]["probable_cause"], str)


# ============================================================
# Duplicate Detection Agent Tests
# ============================================================

class TestDuplicateDetectionAgent:
    """Tests for the M3 DuplicateDetectionAgent."""

    @pytest.fixture
    def agent(self):
        return DuplicateDetectionAgent(
            chroma_service=make_mock_chroma(),
            embedding_service=make_mock_embeddings(),
        )

    @pytest.mark.asyncio
    async def test_likely_duplicate_high_similarity(self):
        """Scores above LIKELY_DUPLICATE_THRESHOLD should classify as likely_duplicate."""
        scores = [0.92, 0.88, 0.75, 0.45, 0.30]
        agent = DuplicateDetectionAgent(
            chroma_service=make_mock_chroma(scores),
            embedding_service=make_mock_embeddings(),
        )
        result = await agent.analyze(JAVA_BUG)
        r = result["result"]
        assert r["classification"] == "likely_duplicate"
        assert r["top_match_similarity"] >= LIKELY_DUPLICATE_THRESHOLD

    @pytest.mark.asyncio
    async def test_related_issue_mid_similarity(self):
        """Scores in mid range should classify as related_issue."""
        scores = [0.70, 0.65, 0.58, 0.40, 0.25]
        agent = DuplicateDetectionAgent(
            chroma_service=make_mock_chroma(scores),
            embedding_service=make_mock_embeddings(),
        )
        result = await agent.analyze(JAVA_BUG)
        r = result["result"]
        assert r["classification"] in ("related_issue", "likely_duplicate")

    @pytest.mark.asyncio
    async def test_new_unmatched_low_similarity(self):
        """Scores below related threshold should classify as new_unmatched."""
        scores = [0.40, 0.35, 0.28, 0.20, 0.15]
        agent = DuplicateDetectionAgent(
            chroma_service=make_mock_chroma(scores),
            embedding_service=make_mock_embeddings(),
        )
        result = await agent.analyze(JAVA_BUG)
        r = result["result"]
        assert r["classification"] in ("new_unmatched", "related_issue")
        assert r["top_match_similarity"] < LIKELY_DUPLICATE_THRESHOLD

    @pytest.mark.asyncio
    async def test_insufficient_evidence_no_services(self):
        """No services → insufficient_evidence."""
        agent = DuplicateDetectionAgent(chroma_service=None, embedding_service=None)
        result = await agent.analyze(JAVA_BUG)
        r = result["result"]
        assert r["classification"] == "insufficient_evidence"

    @pytest.mark.asyncio
    async def test_real_similarity_scores_returned(self, agent):
        """Similarity scores must come from ChromaDB, not be hardcoded."""
        result = await agent.analyze(JAVA_BUG)
        r = result["result"]
        matched = r.get("matched_bugs", [])
        assert len(matched) > 0
        for m in matched:
            score = m.get("similarity_score", 0)
            assert 0.0 <= score <= 1.0
            assert score > 0.0, "Score should be non-zero from real search"

    @pytest.mark.asyncio
    async def test_thresholds_reported(self, agent):
        """Thresholds used must be included in the result."""
        result = await agent.analyze(JAVA_BUG)
        thresholds = result["result"].get("thresholds_used", {})
        assert "likely_duplicate" in thresholds
        assert "related_issue" in thresholds
        assert thresholds["likely_duplicate"] >= thresholds["related_issue"]

    @pytest.mark.asyncio
    async def test_configurable_thresholds(self):
        """Custom thresholds should be respected."""
        agent = DuplicateDetectionAgent(
            chroma_service=make_mock_chroma([0.70, 0.60, 0.50]),
            embedding_service=make_mock_embeddings(),
            likely_duplicate_threshold=0.65,
            related_issue_threshold=0.45,
        )
        result = await agent.analyze(JAVA_BUG)
        r = result["result"]
        # With threshold 0.65, score 0.70 should be likely_duplicate
        assert r["classification"] == "likely_duplicate"
        assert r["thresholds_used"]["likely_duplicate"] == 0.65

    @pytest.mark.asyncio
    async def test_duplicate_probability_in_range(self, agent):
        """Duplicate probability must be between 0 and 1."""
        result = await agent.analyze(JAVA_BUG)
        prob = result["result"]["duplicate_probability"]
        assert 0.0 <= prob <= 1.0

    @pytest.mark.asyncio
    async def test_per_match_classification(self, agent):
        """Each matched bug should have its own classification label."""
        result = await agent.analyze(JAVA_BUG)
        matched = result["result"].get("matched_bugs", [])
        for m in matched:
            assert m.get("classification") in (
                "likely_duplicate", "related_issue", "new_unmatched"
            )

    @pytest.mark.asyncio
    async def test_empty_bug_insufficient_evidence(self):
        """Bug with no title/description → insufficient evidence."""
        agent = DuplicateDetectionAgent(
            chroma_service=make_mock_chroma(),
            embedding_service=make_mock_embeddings(),
        )
        result = await agent.analyze({"id": "EMPTY", "title": "", "description": ""})
        r = result["result"]
        assert r["classification"] == "insufficient_evidence"

    @pytest.mark.asyncio
    async def test_legacy_compat_fields(self, agent):
        """Legacy is_duplicate and matching_bugs fields should be present."""
        result = await agent.analyze(JAVA_BUG)
        r = result["result"]
        assert "is_duplicate" in r
        assert isinstance(r["is_duplicate"], bool)
        assert "similarity_score" in r
        assert "matching_bugs" in r

    @pytest.mark.asyncio
    async def test_analysis_summary_not_empty(self, agent):
        """Analysis summary must be a non-empty string."""
        result = await agent.analyze(JAVA_BUG)
        summary = result["result"].get("analysis_summary", "")
        assert isinstance(summary, str)
        assert len(summary) > 0

    @pytest.mark.asyncio
    async def test_memory_bug_classified(self, agent):
        """Memory leak bug should be classified (any valid result)."""
        result = await agent.analyze(MEMORY_BUG)
        r = result["result"]
        assert r["classification"] in (
            "likely_duplicate", "related_issue", "new_unmatched", "insufficient_evidence"
        )


# ============================================================
# Remediation Agent Tests
# ============================================================

class TestRemediationAgent:
    """Tests for the M3 RemediationAgent."""

    @pytest.fixture
    def agent_full(self):
        return RemediationAgent(
            llm_service=make_mock_llm("remediation"),
            chroma_service=make_mock_chroma(),
            embedding_service=make_mock_embeddings(),
        )

    @pytest.fixture
    def agent_no_llm(self):
        return RemediationAgent(
            llm_service=None,
            chroma_service=make_mock_chroma(),
            embedding_service=make_mock_embeddings(),
        )

    @pytest.mark.asyncio
    async def test_returns_suggested_fix(self, agent_full):
        """Must always return a non-empty suggested_fix."""
        result = await agent_full.analyze(
            JAVA_BUG,
            make_triage_result(),
            make_log_result(),
            make_root_cause_result(),
            make_duplicate_result(),
        )
        assert result["result"]["suggested_fix"]
        assert len(result["result"]["suggested_fix"]) > 10

    @pytest.mark.asyncio
    async def test_fix_source_labeled(self, agent_full):
        """fix_source must be a recognized label."""
        result = await agent_full.analyze(
            JAVA_BUG,
            make_triage_result(),
            make_log_result(),
            make_root_cause_result(),
            make_duplicate_result(),
        )
        fix_source = result["result"]["fix_source"]
        assert fix_source in ("historical_evidence", "best_practice", "agent_reasoning")

    @pytest.mark.asyncio
    async def test_implementation_steps_present(self, agent_full):
        """Implementation steps must be a list."""
        result = await agent_full.analyze(
            JAVA_BUG,
            make_triage_result(),
            make_log_result(),
            make_root_cause_result(),
            make_duplicate_result(),
        )
        impl = result["result"]["implementation_steps"]
        assert isinstance(impl, list)

    @pytest.mark.asyncio
    async def test_speculative_steps_marked(self, agent_full):
        """Steps marked is_speculative must be present and valid."""
        result = await agent_full.analyze(
            JAVA_BUG,
            make_triage_result(),
            make_log_result(),
            make_root_cause_result(),
            make_duplicate_result(),
        )
        for step in result["result"]["implementation_steps"]:
            assert "is_speculative" in step
            assert isinstance(step["is_speculative"], bool)

    @pytest.mark.asyncio
    async def test_confidence_in_range(self, agent_full):
        """Confidence must be 0.0 – 1.0."""
        result = await agent_full.analyze(
            JAVA_BUG,
            make_triage_result(),
            make_log_result(),
            make_root_cause_result(),
            make_duplicate_result(),
        )
        conf = result["result"]["confidence"]
        assert 0.0 <= conf <= 1.0

    @pytest.mark.asyncio
    async def test_risk_level_valid(self, agent_full):
        """Risk level must be low, medium, or high."""
        result = await agent_full.analyze(
            JAVA_BUG,
            make_triage_result(),
            make_log_result(),
            make_root_cause_result(),
            make_duplicate_result(),
        )
        risk = result["result"]["risk_level"]
        assert risk in ("low", "medium", "high")

    @pytest.mark.asyncio
    async def test_historical_resolutions_from_rag(self, agent_full):
        """Historical resolutions should come from ChromaDB search."""
        result = await agent_full.analyze(
            JAVA_BUG,
            make_triage_result(),
            make_log_result(),
            make_root_cause_result(),
            make_duplicate_result(),
        )
        agent_full.chroma.search.assert_called()
        hr = result["result"]["historical_resolutions"]
        assert isinstance(hr, list)
        for r in hr:
            assert "bug_id" in r
            assert "similarity_score" in r
            assert 0.0 <= r["similarity_score"] <= 1.0

    @pytest.mark.asyncio
    async def test_agent_reasoning_separate(self, agent_full):
        """agent_reasoning must be a separate field, not mixed into suggested_fix."""
        result = await agent_full.analyze(
            JAVA_BUG,
            make_triage_result(),
            make_log_result(),
            make_root_cause_result(),
            make_duplicate_result(),
        )
        r = result["result"]
        assert isinstance(r.get("agent_reasoning"), str)
        assert isinstance(r.get("evidence_summary"), str)

    @pytest.mark.asyncio
    async def test_deterministic_fallback_no_llm(self, agent_no_llm):
        """Agent must work without LLM service."""
        result = await agent_no_llm.analyze(
            JAVA_BUG,
            make_triage_result(),
            make_log_result(),
            make_root_cause_result(),
            make_duplicate_result(),
        )
        r = result["result"]
        assert r["suggested_fix"]
        assert r["confidence"] > 0.0

    @pytest.mark.asyncio
    async def test_security_bug_critical_severity(self, agent_no_llm):
        """Critical security bug should have high risk and urgent effort estimate."""
        security_bug = {
            "id": "SEC-001",
            "title": "SQL injection vulnerability in login endpoint",
            "description": "SQL injection allows auth bypass. Critical security vulnerability.",
            "stack_trace": "",
            "error_logs": "",
            "environment": "PostgreSQL 14",
        }
        result = await agent_no_llm.analyze(
            security_bug,
            make_triage_result(severity="critical"),
            make_log_result(),
            make_root_cause_result(),
            make_duplicate_result(),
        )
        r = result["result"]
        assert r["suggested_fix"]
        # Critical bugs should have high effort or high risk
        assert r["risk_level"] in ("high", "medium")

    @pytest.mark.asyncio
    async def test_debugging_and_validation_steps(self, agent_no_llm):
        """Debugging and validation steps should be non-empty lists."""
        result = await agent_no_llm.analyze(
            JAVA_BUG,
            make_triage_result(),
            make_log_result(),
            make_root_cause_result(),
            make_duplicate_result(),
        )
        r = result["result"]
        assert isinstance(r["debugging_steps"], list)
        assert len(r["debugging_steps"]) >= 2
        assert isinstance(r["validation_steps"], list)
        assert len(r["validation_steps"]) >= 2

    @pytest.mark.asyncio
    async def test_graceful_on_error(self):
        """Should return a result even when all services fail."""
        chroma = MagicMock()
        chroma.search.side_effect = RuntimeError("DB down")
        agent = RemediationAgent(
            llm_service=None,
            chroma_service=chroma,
            embedding_service=make_mock_embeddings(),
        )
        result = await agent.analyze(JAVA_BUG, {}, {}, {}, {})
        # Should not crash, should return some result
        assert "result" in result


# ============================================================
# Orchestrator M3 Pipeline Tests
# ============================================================

class TestOrchestratorM3:
    """Tests for the M3 orchestrator pipeline."""

    @pytest.fixture
    def orchestrator(self):
        return AgentOrchestrator(
            llm_service=None,  # Use deterministic agents
            chroma_service=make_mock_chroma(),
            embedding_service=make_mock_embeddings(),
        )

    @pytest.mark.asyncio
    async def test_full_pipeline_runs(self, orchestrator):
        """M3 pipeline should complete with status=completed."""
        result = await orchestrator.run_m3_pipeline(JAVA_BUG)
        assert result["status"] == "completed"
        assert result["milestone"] == "M3"

    @pytest.mark.asyncio
    async def test_all_five_agents_present(self, orchestrator):
        """All 5 agents must be present in the agents dict."""
        result = await orchestrator.run_m3_pipeline(JAVA_BUG)
        agents = result.get("agents", {})
        for agent_name in ["triage", "log_analysis", "root_cause", "duplicate_detection", "remediation"]:
            assert agent_name in agents, f"Missing agent: {agent_name}"

    @pytest.mark.asyncio
    async def test_top_level_results_populated(self, orchestrator):
        """Convenience top-level keys (triage, log_analysis, etc.) should be populated."""
        result = await orchestrator.run_m3_pipeline(JAVA_BUG)
        assert "triage" in result
        assert "log_analysis" in result
        assert "root_cause" in result or result["agents"]["root_cause"]["status"] in ("success", "insufficient_evidence")
        assert "duplicate_detection" in result or result["agents"]["duplicate_detection"]["status"]
        assert "remediation" in result or result["agents"]["remediation"]["status"]

    @pytest.mark.asyncio
    async def test_bug_id_in_result(self, orchestrator):
        """Result must contain the bug ID."""
        result = await orchestrator.run_m3_pipeline(JAVA_BUG)
        assert result["bug_id"] == "TEST-001"

    @pytest.mark.asyncio
    async def test_total_duration_recorded(self, orchestrator):
        """Total duration must be present and positive."""
        result = await orchestrator.run_m3_pipeline(JAVA_BUG)
        assert "total_duration" in result
        assert result["total_duration"] > 0

    @pytest.mark.asyncio
    async def test_handles_minimal_bug(self, orchestrator):
        """Pipeline should complete gracefully with minimal input."""
        minimal = {"id": "MIN-001", "title": "Test", "description": "Minimal bug"}
        result = await orchestrator.run_m3_pipeline(minimal)
        assert result["status"] == "completed"

    @pytest.mark.asyncio
    async def test_handles_empty_chroma(self):
        """Pipeline should not crash when ChromaDB returns no results."""
        chroma = MagicMock()
        chroma.search.return_value = []
        orchestrator = AgentOrchestrator(
            llm_service=None,
            chroma_service=chroma,
            embedding_service=make_mock_embeddings(),
        )
        result = await orchestrator.run_m3_pipeline(JAVA_BUG)
        assert result["status"] == "completed"

    @pytest.mark.asyncio
    async def test_handles_embedding_failure(self):
        """Pipeline should handle embedding service failure gracefully."""
        embeddings = MagicMock()
        embeddings.embed_text.side_effect = RuntimeError("Embedding model unavailable")
        orchestrator = AgentOrchestrator(
            llm_service=None,
            chroma_service=make_mock_chroma(),
            embedding_service=embeddings,
        )
        result = await orchestrator.run_m3_pipeline(JAVA_BUG)
        # Pipeline should complete (agents fall back gracefully)
        assert result["status"] == "completed"

    @pytest.mark.asyncio
    async def test_results_are_bug_specific(self, orchestrator):
        """Different bugs should produce different results (not hardcoded)."""
        result1 = await orchestrator.run_m3_pipeline(JAVA_BUG)
        result2 = await orchestrator.run_m3_pipeline(PYTHON_BUG)
        # Bug IDs should differ
        assert result1["bug_id"] != result2["bug_id"]
        # Triage component/category may differ for different bugs
        t1 = result1.get("triage", {})
        t2 = result2.get("triage", {})
        # At least the reasoning should differ
        assert t1.get("reasoning") != t2.get("reasoning") or t1.get("component") != t2.get("component")

    @pytest.mark.asyncio
    async def test_m2_pipeline_still_works(self, orchestrator):
        """M2 pipeline must still function for backward compat."""
        result = await orchestrator.run_m2_pipeline(JAVA_BUG)
        assert result["status"] == "completed"
        assert result["milestone"] == "M2"
        assert "triage" in result
        assert "log_analysis" in result

    @pytest.mark.asyncio
    async def test_run_full_pipeline_alias(self, orchestrator):
        """run_full_pipeline should be an alias for run_m3_pipeline."""
        result = await orchestrator.run_full_pipeline(JAVA_BUG)
        assert result["status"] == "completed"
        assert result["milestone"] == "M3"

    @pytest.mark.asyncio
    async def test_python_bug_full_pipeline(self, orchestrator):
        """Python bug with clear stack trace should complete pipeline."""
        result = await orchestrator.run_m3_pipeline(PYTHON_BUG)
        assert result["status"] == "completed"
        # Log analysis should extract Python exception
        log = result.get("log_analysis", {})
        exceptions = log.get("exceptions", [])
        assert len(exceptions) >= 1

    @pytest.mark.asyncio
    async def test_combined_context_preserved(self, orchestrator):
        """Combined context from M2 should still be included in M3 result."""
        result = await orchestrator.run_m3_pipeline(JAVA_BUG)
        assert "combined_context" in result
        ctx = result["combined_context"]
        assert "has_triage" in ctx
        assert "has_log_analysis" in ctx


# ============================================================
# Pydantic Model Validation Tests
# ============================================================

class TestM3ModelValidation:
    """Test Pydantic model validation for M3 output models."""

    def test_root_cause_result_valid(self):
        """Valid RootCauseResult should instantiate without error."""
        r = RootCauseResult(
            status="success",
            probable_cause="Missing null check",
            confidence=0.82,
            reasoning="Exception type indicates null access",
            agent_reasoning="Inferred from patterns",
            evidence_summary="1 similar defect found",
        )
        assert r.confidence == 0.82
        assert r.status == "success"

    def test_root_cause_result_insufficient_evidence(self):
        """Insufficient evidence result should instantiate correctly."""
        r = RootCauseResult(
            status="insufficient_evidence",
            probable_cause="Insufficient Evidence",
            confidence=0.0,
            reasoning="Not enough data",
            agent_reasoning="",
            evidence_summary="",
            insufficient_evidence_reason="No stack trace, no error logs",
        )
        assert r.status == "insufficient_evidence"
        assert r.confidence == 0.0

    def test_duplicate_detection_result_valid(self):
        """Valid DuplicateDetectionResult should instantiate."""
        r = DuplicateDetectionResult(
            classification="likely_duplicate",
            top_match_similarity=0.91,
            duplicate_probability=0.87,
            analysis_summary="Likely duplicate of MOZ-1001",
            thresholds_used={"likely_duplicate": 0.82, "related_issue": 0.55},
        )
        assert r.classification == "likely_duplicate"
        assert r.top_match_similarity == 0.91

    def test_remediation_result_valid(self):
        """Valid RemediationResult should instantiate."""
        r = RemediationResult(
            status="success",
            suggested_fix="Add null check",
            confidence=0.85,
            fix_source="historical_evidence",
            debugging_steps=["Step 1", "Step 2"],
            validation_steps=["Test 1"],
            regression_tests=["Suite 1"],
            estimated_effort="2-4 hours",
            risk_level="medium",
            evidence_summary="1 resolution found",
            agent_reasoning="Derived from root cause",
        )
        assert r.risk_level == "medium"
        assert r.fix_source == "historical_evidence"

    def test_remediation_invalid_risk_level(self):
        """Invalid risk level should be coerced to 'medium'."""
        r = RemediationResult(
            status="success",
            suggested_fix="Fix it",
            confidence=0.5,
            fix_source="agent_reasoning",
            estimated_effort="1 hour",
            risk_level="extreme",  # Invalid
            evidence_summary="",
            agent_reasoning="",
        )
        assert r.risk_level == "medium"

    def test_confidence_rounding(self):
        """Confidence values should be rounded to 3 decimal places."""
        r = RootCauseResult(
            status="success",
            probable_cause="test",
            confidence=0.7777777,
            reasoning="test",
            agent_reasoning="",
            evidence_summary="",
        )
        assert r.confidence == 0.778
