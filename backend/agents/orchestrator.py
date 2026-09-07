"""Agent Orchestrator — coordinates the analysis pipeline."""

import logging
import time
from typing import Dict, Any
from datetime import datetime

from agents.definitions import (
    TriageAgent,
    LogAnalysisAgent,
    RootCauseAgent,
    DuplicateDetectionAgent,
    RemediationAgent
)

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """Orchestrates the multi-agent analysis pipeline."""

    def __init__(self, llm_service, chroma_service, embedding_service):
        self.triage_agent = TriageAgent(llm_service)
        self.log_agent = LogAnalysisAgent(llm_service)
        self.root_cause_agent = RootCauseAgent(llm_service, chroma_service, embedding_service)
        self.duplicate_agent = DuplicateDetectionAgent(chroma_service, embedding_service)
        self.remediation_agent = RemediationAgent(llm_service, chroma_service, embedding_service)

    async def run_pipeline(self, bug_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run the complete analysis pipeline.
        
        Flow:
        1. Triage Agent → severity, priority, category, component
        2. Log Analysis Agent → exceptions, patterns, stack trace analysis
        3. Root Cause Agent → probable cause, evidence, confidence (uses RAG)
        4. Duplicate Detection Agent → similarity, matching bugs (uses vector search)
        5. Remediation Agent → fix suggestions, debugging steps, tests (uses RAG)
        """
        start_time = time.time()
        logger.info(f"Starting analysis pipeline for bug: {bug_data.get('id', 'unknown')}")

        results = {
            "bug_id": bug_data.get("id", "unknown"),
            "timestamp": datetime.utcnow().isoformat(),
            "agents": {}
        }

        # Step 1: Triage
        logger.info("Step 1/5: Running Triage Agent...")
        triage_result = await self.triage_agent.analyze(bug_data)
        results["agents"]["triage"] = triage_result
        results["triage"] = triage_result["result"]

        # Step 2: Log Analysis
        logger.info("Step 2/5: Running Log Analysis Agent...")
        log_result = await self.log_agent.analyze(bug_data)
        results["agents"]["log_analysis"] = log_result
        results["log_analysis"] = log_result["result"]

        # Step 3: Root Cause (depends on triage + log analysis)
        logger.info("Step 3/5: Running Root Cause Agent...")
        root_cause_result = await self.root_cause_agent.analyze(bug_data, triage_result, log_result)
        results["agents"]["root_cause"] = root_cause_result
        results["root_cause"] = root_cause_result["result"]

        # Step 4: Duplicate Detection (independent, uses vector search)
        logger.info("Step 4/5: Running Duplicate Detection Agent...")
        duplicate_result = self.duplicate_agent.analyze(bug_data)
        results["agents"]["duplicate_detection"] = duplicate_result
        results["duplicate_detection"] = duplicate_result["result"]

        # Step 5: Remediation (depends on root cause + triage)
        logger.info("Step 5/5: Running Remediation Agent...")
        remediation_result = await self.remediation_agent.analyze(bug_data, root_cause_result, triage_result)
        results["agents"]["remediation"] = remediation_result
        results["remediation"] = remediation_result["result"]

        # Summary
        total_duration = time.time() - start_time
        results["total_duration"] = total_duration
        results["status"] = "completed"

        logger.info(f"Pipeline completed in {total_duration:.2f}s")
        return results
