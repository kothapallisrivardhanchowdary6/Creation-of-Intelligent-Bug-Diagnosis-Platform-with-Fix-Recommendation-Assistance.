"""
Milestone 2 Tests — Triage Agent, Log Analysis Agent, and Orchestrator.

Tests cover:
- Different severity levels (critical, high, medium, low)
- Different exception types (Java, Python, Node.js)
- Stack trace parsing for multiple languages
- Missing/messy logs
- Agent failures and fallback
- Orchestration flow
"""

import pytest
import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from agents.triage_agent import TriageAgent, TriageResult
from agents.log_analysis_agent import LogAnalysisAgent, StackTraceParser, LogAnalysisResult
from agents.orchestrator import AgentOrchestrator, CombinedBugContext


# ============================================================
# Triage Agent Tests
# ============================================================

class TestTriageAgentSeverity:
    """Test severity classification for different levels."""

    @pytest.fixture
    def agent(self):
        return TriageAgent()

    @pytest.mark.asyncio
    async def test_critical_severity_crash(self, agent):
        """Critical severity for crash/fatal bugs."""
        bug = {
            "title": "Fatal crash in production database connection",
            "description": "The application crashes with fatal error when database connection is lost. Data corruption possible.",
            "stack_trace": "",
            "error_logs": "",
            "environment": ""
        }
        result = await agent.analyze(bug)
        assert result['result']['severity'] == 'critical'

    @pytest.mark.asyncio
    async def test_critical_severity_security(self, agent):
        """Critical severity for security vulnerabilities."""
        bug = {
            "title": "SQL injection vulnerability in login form",
            "description": "Attackers can exploit SQL injection to bypass authentication. Critical security vulnerability.",
            "stack_trace": "",
            "error_logs": "",
            "environment": ""
        }
        result = await agent.analyze(bug)
        assert result['result']['severity'] == 'critical'

    @pytest.mark.asyncio
    async def test_high_severity_error(self, agent):
        """High severity for error/exception bugs."""
        bug = {
            "title": "NullPointerException in user service",
            "description": "Error occurs when processing null user data. Exception thrown during request handling.",
            "stack_trace": "",
            "error_logs": "",
            "environment": ""
        }
        result = await agent.analyze(bug)
        assert result['result']['severity'] == 'high'

    @pytest.mark.asyncio
    async def test_medium_severity_incorrect(self, agent):
        """Medium severity for incorrect behavior."""
        bug = {
            "title": "Incorrect calculation in report total",
            "description": "The report shows wrong totals. Values are incorrect when summing line items.",
            "stack_trace": "",
            "error_logs": "",
            "environment": ""
        }
        result = await agent.analyze(bug)
        assert result['result']['severity'] == 'medium'

    @pytest.mark.asyncio
    async def test_low_severity_enhancement(self, agent):
        """Low severity for enhancement requests."""
        bug = {
            "title": "Add dark mode toggle to settings",
            "description": "Nice to have enhancement for dark mode support in the settings page.",
            "stack_trace": "",
            "error_logs": "",
            "environment": ""
        }
        result = await agent.analyze(bug)
        assert result['result']['severity'] == 'low'


class TestTriageAgentPriority:
    """Test priority mapping from severity."""

    @pytest.fixture
    def agent(self):
        return TriageAgent()

    @pytest.mark.asyncio
    async def test_p0_for_critical(self, agent):
        """P0 priority for critical severity."""
        bug = {"title": "Fatal crash data loss", "description": "System crash with data loss", "stack_trace": "", "error_logs": "", "environment": ""}
        result = await agent.analyze(bug)
        assert result['result']['priority'] == 'P0'

    @pytest.mark.asyncio
    async def test_p1_for_high(self, agent):
        """P1 priority for high severity."""
        bug = {"title": "Error in processing null", "description": "Exception thrown during processing", "stack_trace": "", "error_logs": "", "environment": ""}
        result = await agent.analyze(bug)
        assert result['result']['priority'] == 'P1'


class TestTriageAgentComponent:
    """Test component classification."""

    @pytest.fixture
    def agent(self):
        return TriageAgent()

    @pytest.mark.asyncio
    async def test_network_component(self, agent):
        """Network component for connection bugs."""
        bug = {"title": "Connection timeout to database", "description": "Network connection fails when accessing database", "stack_trace": "", "error_logs": "", "environment": ""}
        result = await agent.analyze(bug)
        assert 'Networking' in result['result']['component'] or 'Database' in result['result']['component']

    @pytest.mark.asyncio
    async def test_auth_component(self, agent):
        """Authentication component for login bugs."""
        bug = {"title": "Login fails with valid credentials", "description": "Authentication token not accepted after login", "stack_trace": "", "error_logs": "", "environment": ""}
        result = await agent.analyze(bug)
        assert 'Authentication' in result['result']['component']


# ============================================================
# Log Analysis Agent Tests
# ============================================================

class TestStackTraceParserJava:
    """Test Java stack trace parsing."""

    def test_parse_java_null_pointer(self):
        """Parse Java NullPointerException."""
        trace = """java.lang.NullPointerException: Cannot invoke method on null
\tat com.app.service.UserService.processEmail(UserService.java:45)
\tat com.app.controller.UserController.handleRequest(UserController.java:23)"""
        
        exceptions = StackTraceParser.parse(trace)
        assert len(exceptions) >= 1
        assert 'NullPointerException' in exceptions[0].exception_type
        assert exceptions[0].file_name == 'UserService.java'
        assert exceptions[0].line_number == 45
        assert exceptions[0].method_name == 'processEmail'

    def test_parse_java_out_of_memory(self):
        """Parse Java OutOfMemoryError."""
        trace = """java.lang.OutOfMemoryError: Java heap space
\tat java.util.Arrays.copyOf(Arrays.java:3537)
\tat com.app.service.ImageProcessor.resize(ImageProcessor.java:234)"""
        
        exceptions = StackTraceParser.parse(trace)
        assert len(exceptions) >= 1
        assert 'OutOfMemoryError' in exceptions[0].exception_type

    def test_detect_java_language(self):
        """Detect Java language from stack trace."""
        trace = "java.lang.NullPointerException\n\tat com.app.Service.method(File.java:10)"
        assert StackTraceParser.detect_language(trace) == 'java'


class TestStackTraceParserPython:
    """Test Python stack trace parsing."""

    def test_parse_python_value_error(self):
        """Parse Python ValueError."""
        trace = """Traceback (most recent call last):
  File "/app/reports/generator.py", line 156, in parse_date
    return datetime.strptime(date_str, '%Y-%m-%d')
ValueError: time data '15/01/2024' does not match format"""
        
        exceptions = StackTraceParser.parse(trace)
        assert len(exceptions) >= 1
        assert 'ValueError' in exceptions[0].exception_type
        assert exceptions[0].file_name == '/app/reports/generator.py'
        assert exceptions[0].line_number == 156
        assert exceptions[0].method_name == 'parse_date'

    def test_detect_python_language(self):
        """Detect Python language from stack trace."""
        trace = 'Traceback (most recent call last):\n  File "test.py", line 10'
        assert StackTraceParser.detect_language(trace) == 'python'


class TestStackTraceParserNode:
    """Test Node.js stack trace parsing."""

    def test_parse_node_type_error(self):
        """Parse Node.js TypeError."""
        trace = """TypeError: Cannot read property 'id' of undefined
    at UserProfileHandler.getUser (/app/api/users.js:89:24)
    at Layer.handle (/app/node_modules/express/lib/router/layer.js:95:5)"""
        
        exceptions = StackTraceParser.parse(trace)
        assert len(exceptions) >= 1
        assert 'TypeError' in exceptions[0].exception_type
        assert exceptions[0].file_name == '/app/api/users.js'
        assert exceptions[0].line_number == 89

    def test_detect_node_language(self):
        """Detect Node.js language from stack trace."""
        trace = "TypeError: message\n    at Function (/app/test.js:10:5)"
        assert StackTraceParser.detect_language(trace) == 'nodejs'


class TestLogAnalysisMissingLogs:
    """Test handling of missing/messy logs."""

    @pytest.fixture
    def agent(self):
        return LogAnalysisAgent()

    @pytest.mark.asyncio
    async def test_empty_stack_trace(self, agent):
        """Handle empty stack trace gracefully."""
        bug = {"stack_trace": "", "error_logs": "", "description": "Something went wrong"}
        result = await agent.analyze(bug)
        assert result['status'] == 'success'
        assert result['result']['confidence'] < 0.5

    @pytest.mark.asyncio
    async def test_messy_logs(self, agent):
        """Handle messy/unstructured logs."""
        bug = {
            "stack_trace": "some random text\nnot a real stack trace",
            "error_logs": "ERROR something broke\nWARN might be bad",
            "description": "The thing is broken"
        }
        result = await agent.analyze(bug)
        assert result['status'] == 'success'
        assert len(result['result']['suspicious_logs']) > 0

    @pytest.mark.asyncio
    async def test_none_values(self, agent):
        """Handle None values in bug data."""
        bug = {"stack_trace": None, "error_logs": None, "description": "Bug with no logs"}
        result = await agent.analyze(bug)
        assert result['status'] == 'success'


# ============================================================
# Orchestrator Tests
# ============================================================

class TestOrchestrator:
    """Test the M2 orchestrator."""

    @pytest.fixture
    def orchestrator(self):
        return AgentOrchestrator()

    @pytest.mark.asyncio
    async def test_m2_pipeline_runs(self, orchestrator):
        """M2 pipeline should complete successfully."""
        bug = {
            "id": "TEST-001",
            "title": "Test bug",
            "description": "A test bug for evaluation",
            "stack_trace": "java.lang.NullPointerException\n\tat com.test.Service.method(File.java:10)",
            "error_logs": "ERROR: test error",
            "environment": "Test"
        }
        result = await orchestrator.run_m2_pipeline(bug)
        assert result['status'] == 'completed'
        assert 'triage' in result
        assert 'log_analysis' in result
        assert 'combined_context' in result

    @pytest.mark.asyncio
    async def test_combined_context_created(self, orchestrator):
        """Combined context should merge triage and log analysis."""
        bug = {
            "id": "TEST-002",
            "title": "Error in processing",
            "description": "Exception during data processing",
            "stack_trace": "",
            "error_logs": "",
            "environment": ""
        }
        result = await orchestrator.run_m2_pipeline(bug)
        context = result['combined_context']
        assert context['has_triage'] == True
        assert context['has_log_analysis'] == True

    @pytest.mark.asyncio
    async def test_handles_empty_bug(self, orchestrator):
        """Orchestrator should handle empty/minimal bug data."""
        bug = {"id": "TEST-003", "title": "Minimal", "description": "Minimal bug data"}
        result = await orchestrator.run_m2_pipeline(bug)
        assert result['status'] == 'completed'

    @pytest.mark.asyncio
    async def test_agent_failure_handling(self, orchestrator):
        """Orchestrator should handle agent failures gracefully."""
        # Even with missing data, agents should return fallback results
        bug = {"id": "TEST-004"}
        result = await orchestrator.run_m2_pipeline(bug)
        assert result['status'] == 'completed'


class TestCombinedBugContext:
    """Test the CombinedBugContext class."""

    def test_context_with_both_results(self):
        """Context should work with both triage and log analysis."""
        triage = {"status": "success", "result": {"severity": "high"}}
        log = {"status": "success", "result": {"exceptions": []}}
        ctx = CombinedBugContext(triage, log)
        assert ctx.has_triage
        assert ctx.has_log_analysis

    def test_context_with_missing_triage(self):
        """Context should handle missing triage."""
        triage = {"status": "error", "result": {}}
        log = {"status": "success", "result": {"exceptions": []}}
        ctx = CombinedBugContext(triage, log)
        assert not ctx.has_triage
        assert ctx.has_log_analysis

    def test_context_to_dict(self):
        """Context should serialize to dict."""
        triage = {"status": "success", "result": {"severity": "high"}}
        log = {"status": "success", "result": {"exceptions": []}}
        ctx = CombinedBugContext(triage, log)
        d = ctx.to_dict()
        assert 'triage' in d
        assert 'log_analysis' in d
        assert 'combined_summary' in d


# ============================================================
# Pydantic Validation Tests
# ============================================================

class TestPydanticValidation:
    """Test Pydantic model validation."""

    def test_triage_result_valid(self):
        """Valid triage result should pass validation."""
        result = TriageResult(
            severity="high",
            priority="P1",
            category="Null Reference",
            component="Core Module",
            confidence=0.85,
            reasoning="Test reasoning"
        )
        assert result.severity == "high"
        assert result.confidence == 0.85

    def test_triage_result_invalid_severity(self):
        """Invalid severity should fail validation."""
        with pytest.raises(Exception):
            TriageResult(
                severity="invalid",
                priority="P1",
                category="Test",
                component="Test",
                confidence=0.5,
                reasoning="Test"
            )

    def test_triage_result_invalid_confidence(self):
        """Confidence outside 0-1 should fail."""
        with pytest.raises(Exception):
            TriageResult(
                severity="high",
                priority="P1",
                category="Test",
                component="Test",
                confidence=1.5,
                reasoning="Test"
            )

    def test_log_analysis_result_valid(self):
        """Valid log analysis result should pass."""
        result = LogAnalysisResult(
            exceptions=[],
            error_patterns=["test"],
            confidence=0.7,
            summary="Test summary"
        )
        assert result.confidence == 0.7
