"""Tests for AI agents."""

import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock


class TestTriageAgent:
    """Test the Triage Agent."""

    def test_severity_classification_critical(self):
        """Critical bugs should be classified correctly."""
        from agents.mock_analysis import _determine_severity
        bug = {"title": "Fatal crash in production", "description": "System crashes with data loss"}
        assert _determine_severity(bug) == "critical"

    def test_severity_classification_high(self):
        """High severity bugs should be classified correctly."""
        from agents.mock_analysis import _determine_severity
        bug = {"title": "Error in processing", "description": "Exception thrown during request handling"}
        assert _determine_severity(bug) == "high"

    def test_severity_classification_medium(self):
        """Medium severity bugs should be classified correctly."""
        from agents.mock_analysis import _determine_severity
        bug = {"title": "Incorrect output", "description": "Wrong calculation in report"}
        assert _determine_severity(bug) == "medium"

    def test_priority_mapping(self):
        """Priority should map correctly from severity."""
        from agents.mock_analysis import _determine_priority
        assert _determine_priority({"title": "Fatal crash", "description": "data loss"}) == "P0"
        assert _determine_priority({"title": "Error handling", "description": "exception fail"}) == "P1"

    def test_category_detection_null(self):
        """Null reference bugs should be categorized correctly."""
        from agents.mock_analysis import _determine_category
        bug = {"title": "NullPointerException in service", "description": "null reference error"}
        assert _determine_category(bug) == "Null Reference"

    def test_category_detection_memory(self):
        """Memory bugs should be categorized correctly."""
        from agents.mock_analysis import _determine_category
        bug = {"title": "Memory leak in handler", "description": "memory grows over time"}
        assert _determine_category(bug) == "Memory Management"

    def test_category_detection_concurrency(self):
        """Concurrency bugs should be categorized correctly."""
        from agents.mock_analysis import _determine_category
        bug = {"title": "Race condition in pool", "description": "deadlock between threads"}
        assert _determine_category(bug) == "Concurrency"


class TestMockAnalysis:
    """Test the mock analysis generator."""

    def test_generate_mock_analysis_structure(self):
        """Mock analysis should have all required fields."""
        from agents.mock_analysis import generate_mock_analysis
        bug = {
            "id": "TEST-001",
            "title": "Test bug with error handling",
            "description": "An exception occurs during processing"
        }
        result = generate_mock_analysis(bug)

        assert "bug_id" in result
        assert "timestamp" in result
        assert "triage" in result
        assert "log_analysis" in result
        assert "root_cause" in result
        assert "duplicate_detection" in result
        assert "remediation" in result

    def test_triage_fields(self):
        """Triage result should have all required fields."""
        from agents.mock_analysis import generate_mock_analysis
        bug = {"id": "TEST-001", "title": "Error in module", "description": "Exception during processing"}
        result = generate_mock_analysis(bug)
        triage = result["triage"]

        assert triage["severity"] in ["critical", "high", "medium", "low"]
        assert triage["priority"] in ["P0", "P1", "P2", "P3"]
        assert isinstance(triage["category"], str)
        assert isinstance(triage["component"], str)
        assert 0 <= triage["confidence"] <= 1

    def test_duplicate_detection_fields(self):
        """Duplicate detection should have required fields."""
        from agents.mock_analysis import generate_mock_analysis
        bug = {"id": "TEST-001", "title": "Error in module", "description": "Exception during processing"}
        result = generate_mock_analysis(bug)
        dup = result["duplicate_detection"]

        assert isinstance(dup["is_duplicate"], bool)
        assert 0 <= dup["similarity_score"] <= 1
        assert 0 <= dup["duplicate_probability"] <= 1
        assert isinstance(dup["matching_bugs"], list)
        assert len(dup["matching_bugs"]) > 0

    def test_remediation_fields(self):
        """Remediation should have required fields."""
        from agents.mock_analysis import generate_mock_analysis
        bug = {"id": "TEST-001", "title": "Error in module", "description": "Exception during processing"}
        result = generate_mock_analysis(bug)
        rem = result["remediation"]

        assert isinstance(rem["suggested_fix"], str)
        assert isinstance(rem["debugging_steps"], list)
        assert isinstance(rem["validation_steps"], list)
        assert isinstance(rem["regression_tests"], list)
        assert rem["risk_level"] in ["low", "medium", "high"]


class TestMockSearch:
    """Test the mock search service."""

    def test_search_returns_results(self):
        """Search should return results."""
        from services.mock_search import mock_search
        results = mock_search("null pointer exception")
        assert len(results) > 0
        assert len(results) <= 5

    def test_search_respects_top_k(self):
        """Search should respect top_k parameter."""
        from services.mock_search import mock_search
        results = mock_search("error", top_k=3)
        assert len(results) <= 3

    def test_search_results_have_scores(self):
        """Search results should have similarity scores."""
        from services.mock_search import mock_search
        results = mock_search("memory leak")
        for r in results:
            assert "score" in r
            assert 0 <= r["score"] <= 1

    def test_search_results_sorted_by_score(self):
        """Results should be sorted by score descending."""
        from services.mock_search import mock_search
        results = mock_search("crash error exception")
        scores = [r["score"] for r in results]
        assert scores == sorted(scores, reverse=True)
