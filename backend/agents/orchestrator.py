"""
Milestone 2: Enhanced Agent Orchestrator.

Flow:
Bug Submission → Agent Orchestrator
                    ↙       ↘
              Triage    Log Analysis  (parallel)
                    ↘       ↙
              Combined Bug Context
                    ↓
           Future M3 Agents (Root Cause, Duplicate, Remediation)

Handles missing logs, invalid input, agent failure, and partial results.
"""

import asyncio
import logging
import time
from typing import Dict, Any, Optional, List
from datetime import datetime

from agents.triage_agent import TriageAgent, TriageResult
from agents.log_analysis_agent import LogAnalysisAgent, LogAnalysisResult

logger = logging.getLogger(__name__)


class CombinedBugContext:
    """Combined context from Triage and Log Analysis agents."""
    
    def __init__(self, triage: Optional[Dict] = None, log_analysis: Optional[Dict] = None):
        self.triage = triage
        self.log_analysis = log_analysis
        self.has_triage = triage is not None and triage.get('status') == 'success'
        self.has_log_analysis = log_analysis is not None and log_analysis.get('status') == 'success'
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for downstream agents."""
        return {
            'triage': self.triage,
            'log_analysis': self.log_analysis,
            'has_triage': self.has_triage,
            'has_log_analysis': self.has_log_analysis,
            'combined_summary': self._generate_summary()
        }
    
    def _generate_summary(self) -> str:
        """Generate combined summary."""
        parts = []
        
        if self.has_triage and self.triage:
            result = self.triage.get('result', {})
            parts.append(f"Triage: {result.get('severity', 'unknown')} severity, {result.get('priority', 'unknown')} priority")
        
        if self.has_log_analysis and self.log_analysis:
            result = self.log_analysis.get('result', {})
            exceptions = result.get('exceptions', [])
            if exceptions:
                exc_types = [e.get('exception_type', 'Unknown') for e in exceptions[:3]]
                parts.append(f"Log Analysis: Found {len(exceptions)} exception(s) - {', '.join(exc_types)}")
            else:
                parts.append("Log Analysis: No structured exceptions found")
        
        return '. '.join(parts) if parts else "No analysis results available."


class AgentOrchestrator:
    """
    Milestone 2 Orchestrator.
    
    Runs Triage and Log Analysis agents (potentially in parallel),
    combines their results, and provides context for future M3 agents.
    """

    def __init__(self, llm_service=None, chroma_service=None, embedding_service=None):
        self.llm_service = llm_service
        self.chroma_service = chroma_service
        self.embedding_service = embedding_service
        
        # M2 Agents
        self.triage_agent = TriageAgent(llm_service)
        self.log_agent = LogAnalysisAgent(llm_service)
    
    async def run_m2_pipeline(self, bug_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run Milestone 2 pipeline: Triage + Log Analysis → Combined Context.
        
        This is the primary M2 entry point.
        """
        start_time = time.time()
        bug_id = bug_data.get('id', 'unknown')
        logger.info(f"Starting M2 pipeline for bug: {bug_id}")
        
        results = {
            "bug_id": bug_id,
            "timestamp": datetime.utcnow().isoformat(),
            "milestone": "M2",
            "agents": {},
            "status": "pending"
        }
        
        # Run Triage and Log Analysis (potentially in parallel)
        try:
            # Run both agents concurrently
            triage_task = self._safe_run_agent(self.triage_agent, bug_data, "triage")
            log_task = self._safe_run_agent(self.log_agent, bug_data, "log_analysis")
            
            triage_result, log_result = await asyncio.gather(triage_task, log_task)
            
            results["agents"]["triage"] = triage_result
            results["agents"]["log_analysis"] = log_result
            
            # Create combined context
            combined = CombinedBugContext(triage_result, log_result)
            results["combined_context"] = combined.to_dict()
            
            # Extract key results for convenience
            if triage_result and triage_result.get('status') == 'success':
                results["triage"] = triage_result.get('result', {})
            
            if log_result and log_result.get('status') == 'success':
                results["log_analysis"] = log_result.get('result', {})
            
            results["status"] = "completed"
            
        except Exception as e:
            logger.error(f"M2 pipeline failed: {e}")
            results["status"] = "error"
            results["error"] = str(e)
        
        total_duration = time.time() - start_time
        results["total_duration"] = total_duration
        
        logger.info(f"M2 pipeline completed in {total_duration:.2f}s — Status: {results['status']}")
        return results
    
    async def run_full_pipeline(self, bug_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run the full M1+M2 pipeline (backward compatible).
        
        M2 agents first, then M1 agents (Root Cause, Duplicate, Remediation).
        """
        start_time = time.time()
        bug_id = bug_data.get('id', 'unknown')
        logger.info(f"Starting full pipeline for bug: {bug_id}")
        
        # Run M2 pipeline first
        m2_results = await self.run_m2_pipeline(bug_data)
        
        # Now run M1 agents if available
        results = m2_results.copy()
        results["milestone"] = "M1+M2"
        
        try:
            # Import M1 agents lazily to avoid circular imports
            from agents.definitions import RootCauseAgent, DuplicateDetectionAgent, RemediationAgent
            
            if self.chroma_service and self.embedding_service:
                # Step 3: Root Cause
                logger.info("Step 3: Running Root Cause Agent...")
                root_cause_agent = RootCauseAgent(self.llm_service, self.chroma_service, self.embedding_service)
                triage_agent_result = results["agents"].get("triage", {})
                log_agent_result = results["agents"].get("log_analysis", {})
                root_cause_result = await self._safe_run_agent_with_context(
                    root_cause_agent, bug_data, triage_agent_result, log_agent_result, "root_cause"
                )
                results["agents"]["root_cause"] = root_cause_result
                if root_cause_result:
                    results["root_cause"] = root_cause_result.get("result", {})
                
                # Step 4: Duplicate Detection
                logger.info("Step 4: Running Duplicate Detection Agent...")
                duplicate_agent = DuplicateDetectionAgent(self.chroma_service, self.embedding_service)
                duplicate_result = self._safe_run_agent_sync(duplicate_agent, bug_data, "duplicate_detection")
                results["agents"]["duplicate_detection"] = duplicate_result
                if duplicate_result:
                    results["duplicate_detection"] = duplicate_result.get("result", {})
                
                # Step 5: Remediation
                logger.info("Step 5: Running Remediation Agent...")
                remediation_agent = RemediationAgent(self.llm_service, self.chroma_service, self.embedding_service)
                remediation_result = await self._safe_run_agent_with_context(
                    remediation_agent, bug_data, 
                    results["agents"].get("root_cause", {}),
                    results["agents"].get("triage", {}),
                    "remediation"
                )
                results["agents"]["remediation"] = remediation_result
                if remediation_result:
                    results["remediation"] = remediation_result.get("result", {})
            
        except ImportError:
            logger.warning("M1 agents not available, returning M2 results only")
        except Exception as e:
            logger.error(f"M1 agents failed: {e}")
            results["m1_error"] = str(e)
        
        total_duration = time.time() - start_time
        results["total_duration"] = total_duration
        
        logger.info(f"Full pipeline completed in {total_duration:.2f}s")
        return results
    
    async def _safe_run_agent(self, agent, bug_data: Dict, agent_name: str) -> Optional[Dict]:
        """Safely run an agent with error handling."""
        try:
            result = await agent.analyze(bug_data)
            logger.info(f"{agent_name} completed successfully")
            return result
        except Exception as e:
            logger.error(f"{agent_name} failed: {e}")
            return {
                "agent": agent_name,
                "status": "error",
                "error": str(e),
                "result": {},
                "duration": 0,
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def _safe_run_agent_with_context(self, agent, bug_data: Dict, 
                                            context1: Dict, context2: Dict, 
                                            agent_name: str) -> Optional[Dict]:
        """Safely run an agent that takes additional context."""
        try:
            result = await agent.analyze(bug_data, context1, context2)
            logger.info(f"{agent_name} completed successfully")
            return result
        except Exception as e:
            logger.error(f"{agent_name} failed: {e}")
            return {
                "agent": agent_name,
                "status": "error",
                "error": str(e),
                "result": {},
                "duration": 0,
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def _safe_run_agent_sync(self, agent, bug_data: Dict, agent_name: str) -> Optional[Dict]:
        """Safely run a synchronous agent."""
        try:
            result = agent.analyze(bug_data)
            logger.info(f"{agent_name} completed successfully")
            return result
        except Exception as e:
            logger.error(f"{agent_name} failed: {e}")
            return {
                "agent": agent_name,
                "status": "error",
                "error": str(e),
                "result": {},
                "duration": 0,
                "timestamp": datetime.utcnow().isoformat()
            }
