"""
Milestone 3: Full Agent Orchestrator.

Pipeline:
  Bug Submission
      ↓
  ┌───────────────────────────────┐
  │   Step 1: Triage Agent        │ ←─── parallel ──→
  │   Step 2: Log Analysis Agent  │                   │
  └───────────────────────────────┘                   │
              ↓  Combined Context                      │
  Step 3: Root Cause Agent  (needs triage + log)       │
  Step 4: Duplicate Detection (independent embed search)
              ↓  (all results available)
  Step 5: Remediation Agent  (needs all prior results)
              ↓
  Single structured AnalysisResponse

Preserves full backward-compat with M1/M2 callers.
Handles agent failures, missing logs, and partial results gracefully.
"""

import asyncio
import logging
import time
from typing import Dict, Any, Optional
from datetime import datetime

from agents.triage_agent import TriageAgent, TriageResult
from agents.log_analysis_agent import LogAnalysisAgent, LogAnalysisResult

logger = logging.getLogger(__name__)


class CombinedBugContext:
    """Combined context from Triage and Log Analysis agents."""

    def __init__(self, triage: Optional[Dict] = None, log_analysis: Optional[Dict] = None):
        self.triage = triage
        self.log_analysis = log_analysis
        self.has_triage = triage is not None and triage.get("status") == "success"
        self.has_log_analysis = log_analysis is not None and log_analysis.get("status") == "success"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "triage": self.triage,
            "log_analysis": self.log_analysis,
            "has_triage": self.has_triage,
            "has_log_analysis": self.has_log_analysis,
            "combined_summary": self._generate_summary(),
        }

    def _generate_summary(self) -> str:
        parts = []
        if self.has_triage and self.triage:
            r = self.triage.get("result", {})
            parts.append(
                f"Triage: {r.get('severity', 'unknown')} severity, {r.get('priority', 'unknown')} priority"
            )
        if self.has_log_analysis and self.log_analysis:
            r = self.log_analysis.get("result", {})
            exceptions = r.get("exceptions", [])
            if exceptions:
                exc_types = [e.get("exception_type", "Unknown") for e in exceptions[:3]]
                parts.append(
                    f"Log Analysis: Found {len(exceptions)} exception(s) — {', '.join(exc_types)}"
                )
            else:
                parts.append("Log Analysis: No structured exceptions found")
        return ". ".join(parts) if parts else "No analysis results available."


class AgentOrchestrator:
    """
    Milestone 3 Orchestrator.

    Runs the full 5-agent pipeline:
      Triage + Log Analysis (parallel) →
      Root Cause + Duplicate Detection (parallel, both need M2 context) →
      Remediation (needs all prior)

    All agents wrapped in safe-call helpers — pipeline never crashes.
    """

    def __init__(self, llm_service=None, chroma_service=None, embedding_service=None):
        self.llm_service = llm_service
        self.chroma_service = chroma_service
        self.embedding_service = embedding_service

        # M2 Agents (always available)
        self.triage_agent = TriageAgent(llm_service)
        self.log_agent = LogAnalysisAgent(llm_service)

        # M3 Agents (lazy import to avoid circular deps)
        self._root_cause_agent = None
        self._duplicate_agent = None
        self._remediation_agent = None

    # ──────────────────────────────────────────────────────────────────────
    # Public entry points
    # ──────────────────────────────────────────────────────────────────────

    async def run_m3_pipeline(self, bug_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Full Milestone 3 pipeline.
        Returns one structured response containing all 5 agent results.
        """
        start_time = time.time()
        bug_id = bug_data.get("id", "unknown")
        logger.info(f"[M3] Starting full pipeline for bug: {bug_id}")

        results: Dict[str, Any] = {
            "bug_id": bug_id,
            "timestamp": datetime.utcnow().isoformat(),
            "milestone": "M3",
            "agents": {},
            "status": "pending",
        }

        # ── Step 1 + 2: Triage & Log Analysis in parallel ─────────────────
        triage_task = self._safe_run(self.triage_agent, bug_data, "triage")
        log_task = self._safe_run(self.log_agent, bug_data, "log_analysis")
        triage_result, log_result = await asyncio.gather(triage_task, log_task)

        results["agents"]["triage"] = triage_result
        results["agents"]["log_analysis"] = log_result

        combined = CombinedBugContext(triage_result, log_result)
        results["combined_context"] = combined.to_dict()

        if triage_result and triage_result.get("status") == "success":
            results["triage"] = triage_result.get("result", {})
        if log_result and log_result.get("status") == "success":
            results["log_analysis"] = log_result.get("result", {})

        # ── Step 3 + 4: Root Cause & Duplicate Detection in parallel ──────
        rc_agent = self._get_root_cause_agent()
        dup_agent = self._get_duplicate_agent()

        rc_task = self._safe_run_with_context(
            rc_agent, bug_data, triage_result, log_result, "root_cause"
        )
        dup_task = self._safe_run(dup_agent, bug_data, "duplicate_detection")

        root_cause_result, duplicate_result = await asyncio.gather(rc_task, dup_task)

        results["agents"]["root_cause"] = root_cause_result
        results["agents"]["duplicate_detection"] = duplicate_result

        if root_cause_result and root_cause_result.get("status") in ("success", "insufficient_evidence"):
            results["root_cause"] = root_cause_result.get("result", {})
        if duplicate_result and duplicate_result.get("status") in ("success", "insufficient_evidence"):
            results["duplicate_detection"] = duplicate_result.get("result", {})

        # ── Step 5: Remediation (needs all prior results) ─────────────────
        rem_agent = self._get_remediation_agent()
        remediation_result = await self._safe_run_remediation(
            rem_agent,
            bug_data,
            triage_result,
            log_result,
            root_cause_result,
            duplicate_result,
        )

        results["agents"]["remediation"] = remediation_result
        if remediation_result and remediation_result.get("status") in ("success",):
            results["remediation"] = remediation_result.get("result", {})

        results["status"] = "completed"
        results["total_duration"] = round(time.time() - start_time, 3)

        logger.info(
            f"[M3] Pipeline completed in {results['total_duration']:.2f}s for bug {bug_id}"
        )
        return results

    async def run_m2_pipeline(self, bug_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Milestone 2 pipeline — Triage + Log Analysis only.
        Preserved for backward compatibility.
        """
        start_time = time.time()
        bug_id = bug_data.get("id", "unknown")
        logger.info(f"[M2] Starting pipeline for bug: {bug_id}")

        results: Dict[str, Any] = {
            "bug_id": bug_id,
            "timestamp": datetime.utcnow().isoformat(),
            "milestone": "M2",
            "agents": {},
            "status": "pending",
        }

        try:
            triage_task = self._safe_run(self.triage_agent, bug_data, "triage")
            log_task = self._safe_run(self.log_agent, bug_data, "log_analysis")
            triage_result, log_result = await asyncio.gather(triage_task, log_task)

            results["agents"]["triage"] = triage_result
            results["agents"]["log_analysis"] = log_result

            combined = CombinedBugContext(triage_result, log_result)
            results["combined_context"] = combined.to_dict()

            if triage_result and triage_result.get("status") == "success":
                results["triage"] = triage_result.get("result", {})
            if log_result and log_result.get("status") == "success":
                results["log_analysis"] = log_result.get("result", {})

            results["status"] = "completed"

        except Exception as e:
            logger.error(f"M2 pipeline failed: {e}")
            results["status"] = "error"
            results["error"] = str(e)

        results["total_duration"] = round(time.time() - start_time, 3)
        logger.info(f"[M2] Pipeline completed in {results['total_duration']:.2f}s")
        return results

    async def run_full_pipeline(self, bug_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Alias for run_m3_pipeline — full M3 pipeline entry point.
        Kept for backward compat with code that calls run_full_pipeline.
        """
        return await self.run_m3_pipeline(bug_data)

    # ──────────────────────────────────────────────────────────────────────
    # Agent factory helpers (lazy init)
    # ──────────────────────────────────────────────────────────────────────

    def _get_root_cause_agent(self):
        if self._root_cause_agent is None:
            from agents.root_cause_agent import RootCauseAgent
            self._root_cause_agent = RootCauseAgent(
                self.llm_service, self.chroma_service, self.embedding_service
            )
        return self._root_cause_agent

    def _get_duplicate_agent(self):
        if self._duplicate_agent is None:
            from agents.duplicate_detection_agent import DuplicateDetectionAgent
            self._duplicate_agent = DuplicateDetectionAgent(
                self.chroma_service, self.embedding_service
            )
        return self._duplicate_agent

    def _get_remediation_agent(self):
        if self._remediation_agent is None:
            from agents.remediation_agent import RemediationAgent
            self._remediation_agent = RemediationAgent(
                self.llm_service, self.chroma_service, self.embedding_service
            )
        return self._remediation_agent

    # ──────────────────────────────────────────────────────────────────────
    # Safe call wrappers
    # ──────────────────────────────────────────────────────────────────────

    async def _safe_run(
        self, agent, bug_data: Dict, agent_name: str
    ) -> Optional[Dict]:
        """Safely run an agent that takes only bug_data."""
        try:
            result = await agent.analyze(bug_data)
            logger.info(f"Agent '{agent_name}' completed — status={result.get('status','?')}")
            return result
        except Exception as e:
            logger.error(f"Agent '{agent_name}' failed: {e}", exc_info=True)
            return self._error_result(agent_name, str(e))

    async def _safe_run_with_context(
        self,
        agent,
        bug_data: Dict,
        context1: Optional[Dict],
        context2: Optional[Dict],
        agent_name: str,
    ) -> Optional[Dict]:
        """Safely run an agent that takes bug_data + two context dicts."""
        try:
            result = await agent.analyze(bug_data, context1 or {}, context2 or {})
            logger.info(f"Agent '{agent_name}' completed — status={result.get('status','?')}")
            return result
        except Exception as e:
            logger.error(f"Agent '{agent_name}' failed: {e}", exc_info=True)
            return self._error_result(agent_name, str(e))

    async def _safe_run_remediation(
        self,
        agent,
        bug_data: Dict,
        triage: Optional[Dict],
        log: Optional[Dict],
        root_cause: Optional[Dict],
        duplicate: Optional[Dict],
    ) -> Optional[Dict]:
        """Safely run the Remediation agent (5 inputs)."""
        try:
            result = await agent.analyze(
                bug_data,
                triage or {},
                log or {},
                root_cause or {},
                duplicate or {},
            )
            logger.info(f"Agent 'remediation' completed — status={result.get('status','?')}")
            return result
        except Exception as e:
            logger.error(f"Agent 'remediation' failed: {e}", exc_info=True)
            return self._error_result("remediation", str(e))

    @staticmethod
    def _error_result(agent_name: str, error: str) -> Dict[str, Any]:
        return {
            "agent": agent_name,
            "status": "error",
            "error": error,
            "result": {},
            "duration": 0,
            "timestamp": datetime.utcnow().isoformat(),
        }
