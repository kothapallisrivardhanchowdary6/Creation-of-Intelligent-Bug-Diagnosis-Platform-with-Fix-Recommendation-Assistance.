"""
Milestone 3: Root Cause Analysis Agent.

Uses Triage and Log Analysis outputs plus RAG over ChromaDB historical defects
to generate probable root cause hypotheses with confidence, reasoning, and
clearly separated retrieved evidence vs. agent reasoning.

Returns "Insufficient Evidence" when data is too sparse to reason about.
"""

import json
import logging
import time
from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, validator

logger = logging.getLogger(__name__)


# ============================================================
# Pydantic Models
# ============================================================

class HistoricalEvidence(BaseModel):
    """A single piece of historical evidence from RAG retrieval."""
    bug_id: str
    document: str
    component: Optional[str] = None
    severity: Optional[str] = None
    resolution: Optional[str] = None
    similarity_score: float = Field(ge=0.0, le=1.0)
    source: str = "historical_defect_database"


class RootCauseHypothesis(BaseModel):
    """A single root cause hypothesis."""
    hypothesis: str
    confidence: float = Field(ge=0.0, le=1.0)
    supporting_evidence: List[str] = Field(default_factory=list)
    causal_chain: str = ""


class RootCauseResult(BaseModel):
    """Complete root cause analysis result."""
    status: str = "success"  # success | insufficient_evidence | error
    probable_cause: str
    hypotheses: List[RootCauseHypothesis] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str
    related_components: List[str] = Field(default_factory=list)

    # Clearly separated evidence vs reasoning
    retrieved_evidence: List[HistoricalEvidence] = Field(default_factory=list)
    agent_reasoning: str = ""  # What the agent inferred (not from data)
    evidence_summary: str = ""  # Summary of what historical records showed

    insufficient_evidence_reason: Optional[str] = None

    @validator("confidence")
    def round_confidence(cls, v):
        return round(v, 3)


class RootCauseAgentOutput(BaseModel):
    """Complete agent output with metadata."""
    agent: str = "Root Cause Agent"
    version: str = "3.0.0-M3"
    result: RootCauseResult
    duration: float
    timestamp: str
    status: str = "success"
    error: Optional[str] = None


# ============================================================
# Root Cause Agent
# ============================================================

class RootCauseAgent:
    """
    Milestone 3 Root Cause Analysis Agent.

    Pipeline:
    1. Extract key signals from Triage and Log Analysis results.
    2. Build a rich RAG query and retrieve top-k similar historical defects.
    3. Clearly label what came from the database (evidence) vs. what was inferred.
    4. Call LLM with the combined context to generate hypotheses.
    5. Return "Insufficient Evidence" if confidence is too low.
    """

    # If overall confidence drops below this threshold, mark as insufficient
    INSUFFICIENT_EVIDENCE_THRESHOLD = 0.25
    # Minimum number of signals needed before attempting root cause
    MIN_SIGNALS_REQUIRED = 1

    def __init__(self, llm_service=None, chroma_service=None, embedding_service=None):
        self.llm = llm_service
        self.chroma = chroma_service
        self.embeddings = embedding_service
        self.name = "Root Cause Agent"
        self.version = "3.0.0-M3"

    async def analyze(
        self,
        bug_data: Dict[str, Any],
        triage_result: Dict[str, Any],
        log_result: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Run root cause analysis.

        Args:
            bug_data: Original bug report dict.
            triage_result: Output from TriageAgent (agent wrapper dict).
            log_result:    Output from LogAnalysisAgent (agent wrapper dict).

        Returns:
            RootCauseAgentOutput as dict.
        """
        start_time = time.time()

        try:
            # ── 1. Extract signals ────────────────────────────────────────
            triage = triage_result.get("result", {}) if triage_result else {}
            log = log_result.get("result", {}) if log_result else {}

            signals = self._extract_signals(bug_data, triage, log)
            signal_count = sum(1 for v in signals.values() if v)

            if signal_count < self.MIN_SIGNALS_REQUIRED:
                return self._insufficient_evidence(
                    "No meaningful signals extracted from bug report, triage, or log analysis.",
                    time.time() - start_time,
                )

            # ── 2. RAG retrieval ──────────────────────────────────────────
            retrieved_evidence = []
            if self.chroma and self.embeddings:
                retrieved_evidence = self._retrieve_evidence(signals)

            # ── 3. Build context for LLM ──────────────────────────────────
            evidence_text = self._format_evidence_for_prompt(retrieved_evidence)
            evidence_summary = self._summarize_evidence(retrieved_evidence)

            # ── 4. LLM reasoning ──────────────────────────────────────────
            llm_result = await self._run_llm_analysis(
                bug_data, signals, retrieved_evidence, evidence_text
            )

            # ── 5. Compute final confidence ───────────────────────────────
            base_confidence = llm_result.get("confidence", 0.5)
            evidence_boost = min(0.15, len(retrieved_evidence) * 0.04)
            final_confidence = min(0.95, base_confidence + evidence_boost)

            # Cap confidence for sparse/vague bug reports so that mock evidence
            # boosts and LLM over-confidence don't produce misleading results.
            # A bug is considered sparse when it has NO actual log data (no stack
            # trace, no error_logs) AND a short description — regardless of what
            # downstream agents may have inferred from the sparse text.
            has_stack_trace  = bool((bug_data.get("stack_trace") or "").strip())
            has_error_logs   = bool((bug_data.get("error_logs") or "").strip())
            description_len  = len((bug_data.get("description") or "").strip())
            sparse_report = (not has_stack_trace
                             and not has_error_logs
                             and description_len < 80)
            if sparse_report:
                final_confidence = min(final_confidence, 0.50)

            if final_confidence < self.INSUFFICIENT_EVIDENCE_THRESHOLD:
                return self._insufficient_evidence(
                    "Confidence too low to produce a reliable root cause analysis.",
                    time.time() - start_time,
                )

            # ── 6. Build hypotheses ────────────────────────────────────────
            hypotheses = self._build_hypotheses(llm_result, retrieved_evidence)

            result = RootCauseResult(
                status="success",
                probable_cause=llm_result.get(
                    "probable_cause",
                    "Unable to determine specific root cause from available data.",
                ),
                hypotheses=hypotheses,
                confidence=final_confidence,
                reasoning=llm_result.get("reasoning", ""),
                related_components=llm_result.get("related_components", []),
                retrieved_evidence=retrieved_evidence,
                agent_reasoning=llm_result.get("agent_reasoning", ""),
                evidence_summary=evidence_summary,
            )

            duration = time.time() - start_time
            logger.info(f"Root Cause Agent completed in {duration:.2f}s — confidence={final_confidence:.2f}")

            output = RootCauseAgentOutput(
                result=result,
                duration=duration,
                timestamp=datetime.utcnow().isoformat(),
                status="success",
            )
            return output.dict()

        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Root Cause Agent failed: {e}", exc_info=True)
            return RootCauseAgentOutput(
                result=RootCauseResult(
                    status="error",
                    probable_cause="Analysis failed due to an internal error.",
                    confidence=0.0,
                    reasoning=f"Agent encountered an error: {str(e)}",
                    agent_reasoning="",
                    evidence_summary="",
                ),
                duration=duration,
                timestamp=datetime.utcnow().isoformat(),
                status="error",
                error=str(e),
            ).dict()

    # ──────────────────────────────────────────────────────────────────────
    # Private helpers
    # ──────────────────────────────────────────────────────────────────────

    def _extract_signals(
        self,
        bug_data: Dict,
        triage: Dict,
        log: Dict,
    ) -> Dict[str, Any]:
        """Extract key signals from all available data sources."""
        exceptions = log.get("exceptions", [])
        primary_exception = exceptions[0] if exceptions else {}

        return {
            "title": bug_data.get("title", ""),
            "description": bug_data.get("description", ""),
            "severity": triage.get("severity", ""),
            "category": triage.get("category", ""),
            "component": triage.get("component", ""),
            "triage_reasoning": triage.get("reasoning", ""),
            "exception_type": primary_exception.get("exception_type", ""),
            "error_message": primary_exception.get("error_message", ""),
            "failure_point": log.get("failure_point", ""),
            "code_path": log.get("code_path", ""),
            "error_patterns": log.get("error_patterns", []),
            "stack_trace": bug_data.get("stack_trace", ""),
            "environment": bug_data.get("environment", ""),
        }

    def _retrieve_evidence(self, signals: Dict[str, Any]) -> List[HistoricalEvidence]:
        """RAG: embed a rich query and retrieve top-k historical defects."""
        query_parts = [
            signals.get("title", ""),
            signals.get("description", ""),
            signals.get("exception_type", ""),
            signals.get("error_message", ""),
            signals.get("category", ""),
            signals.get("component", ""),
        ]
        query_text = " ".join(p for p in query_parts if p).strip()
        if not query_text:
            return []

        try:
            query_embedding = self.embeddings.embed_text(query_text)
            raw_results = self.chroma.search(query_embedding, top_k=5)

            evidence = []
            for r in raw_results:
                score = r.get("score", 0.0)
                meta = r.get("metadata", {})
                evidence.append(
                    HistoricalEvidence(
                        bug_id=r.get("id", "UNKNOWN"),
                        document=r.get("document", ""),
                        component=meta.get("component", meta.get("project", "")),
                        severity=meta.get("severity", ""),
                        resolution=meta.get("resolution", ""),
                        similarity_score=round(float(score), 4),
                    )
                )
            return evidence
        except Exception as e:
            logger.warning(f"RAG retrieval failed: {e}")
            return []

    def _format_evidence_for_prompt(self, evidence: List[HistoricalEvidence]) -> str:
        """Format retrieved evidence for inclusion in the LLM prompt."""
        if not evidence:
            return "No similar historical defects found in the knowledge base."

        lines = ["=== RETRIEVED HISTORICAL EVIDENCE (from defect database) ==="]
        for i, ev in enumerate(evidence, 1):
            lines.append(
                f"[Evidence {i}] Bug ID: {ev.bug_id} | Similarity: {ev.similarity_score:.2%}"
            )
            lines.append(f"  Description: {ev.document}")
            if ev.component:
                lines.append(f"  Component:   {ev.component}")
            if ev.severity:
                lines.append(f"  Severity:    {ev.severity}")
            if ev.resolution:
                lines.append(f"  Resolution:  {ev.resolution}")
        return "\n".join(lines)

    def _summarize_evidence(self, evidence: List[HistoricalEvidence]) -> str:
        """One-sentence summary of retrieved evidence for display."""
        if not evidence:
            return "No historical defects retrieved from the knowledge base."
        top = evidence[0]
        return (
            f"Retrieved {len(evidence)} similar historical defect(s). "
            f"Closest match: {top.bug_id} ({top.similarity_score:.1%} similarity) — {top.document[:80]}."
        )

    async def _run_llm_analysis(
        self,
        bug_data: Dict,
        signals: Dict,
        evidence: List[HistoricalEvidence],
        evidence_text: str,
    ) -> Dict[str, Any]:
        """Call LLM for root cause reasoning."""
        if not self.llm:
            return self._deterministic_analysis(signals, evidence)

        prompt = f"""You are a root cause analysis expert for software defects.

=== CURRENT BUG ===
Title: {signals['title']}
Description: {signals['description']}
Severity: {signals['severity']}   Category: {signals['category']}   Component: {signals['component']}
Exception: {signals['exception_type']} — {signals['error_message']}
Failure Point: {signals['failure_point']}
Code Path: {signals['code_path']}
Error Patterns: {', '.join(signals['error_patterns'])}
Environment: {signals['environment']}

=== TRIAGE AGENT REASONING ===
{signals['triage_reasoning']}

{evidence_text}

=== INSTRUCTIONS ===
1. Clearly distinguish what you KNOW from the evidence above vs. what you are INFERRING.
2. Use the historical evidence only as supporting context, not as a direct answer.
3. If there is insufficient data to form a confident hypothesis, say so explicitly.
4. Return ONLY a valid JSON object — no markdown fences.

Required JSON schema:
{{
  "probable_cause": "A precise, specific root cause description (not vague)",
  "confidence": 0.0-1.0,
  "reasoning": "Step-by-step causal chain reasoning (what leads to what)",
  "agent_reasoning": "What you inferred that is NOT directly from the evidence",
  "related_components": ["list of components implicated"],
  "hypotheses": [
    {{
      "hypothesis": "specific hypothesis text",
      "confidence": 0.0-1.0,
      "supporting_evidence": ["evidence item 1", "evidence item 2"],
      "causal_chain": "brief causal chain"
    }}
  ]
}}"""

        try:
            raw = await self.llm.generate_json(
                prompt,
                "You are a root cause analysis expert specializing in software defect forensics.",
            )
            if "raw_response" in raw:
                # LLM returned unparseable text — fall back to deterministic
                return self._deterministic_analysis(signals, evidence)
            return raw
        except Exception as e:
            logger.warning(f"LLM call failed in RootCauseAgent: {e}")
            return self._deterministic_analysis(signals, evidence)

    def _deterministic_analysis(
        self, signals: Dict, evidence: List[HistoricalEvidence]
    ) -> Dict[str, Any]:
        """
        Fallback deterministic root cause analysis when LLM is unavailable.
        Based on signals and retrieved evidence patterns.
        """
        category = signals.get("category", "Logic Error")
        component = signals.get("component", "Unknown Component")
        exception_type = signals.get("exception_type", "")
        error_message = signals.get("error_message", "")
        failure_point = signals.get("failure_point", "")
        error_patterns = signals.get("error_patterns", [])

        # Infer probable cause from signals
        cause_map = {
            "Null Reference": (
                f"A null or uninitialized object is being accessed without a prior null check "
                f"in the {component} component."
            ),
            "Memory Management": (
                f"A resource in {component} is not being released properly, leading to "
                f"memory pressure or a resource leak."
            ),
            "Concurrency": (
                f"A race condition or inadequate synchronization in {component} allows concurrent "
                f"threads to corrupt shared state."
            ),
            "Network/IO": (
                f"An I/O operation in {component} lacks proper timeout handling or retry logic, "
                f"causing failure on transient network errors."
            ),
            "Security": (
                f"Input in {component} is not properly validated or sanitized, creating a "
                f"potential security vulnerability."
            ),
            "Input Validation": (
                f"Malformed or unexpected input reaches {component} without validation, "
                f"triggering an unhandled exception."
            ),
            "Performance": (
                f"An inefficient algorithm or missing cache in {component} causes excessive "
                f"resource consumption under load."
            ),
        }

        probable_cause = cause_map.get(
            category,
            f"An unhandled condition in the {component} component causes the reported failure.",
        )

        if exception_type:
            probable_cause = f"{probable_cause} The immediate trigger is a {exception_type}."
        if failure_point:
            probable_cause += f" Failure detected at: {failure_point}."

        # Build evidence items
        supporting_evidence = []
        if exception_type:
            supporting_evidence.append(f"Exception type identified: {exception_type}")
        if error_message:
            supporting_evidence.append(f"Error message: {error_message[:100]}")
        if failure_point:
            supporting_evidence.append(f"Failure point: {failure_point}")
        for p in error_patterns[:3]:
            supporting_evidence.append(f"Error pattern detected: {p}")
        for ev in evidence[:2]:
            supporting_evidence.append(
                f"Historical defect {ev.bug_id} ({ev.similarity_score:.1%} similarity): {ev.document[:60]}"
            )

        confidence = self._calculate_deterministic_confidence(signals, evidence)

        hypotheses = [
            {
                "hypothesis": probable_cause,
                "confidence": confidence,
                "supporting_evidence": supporting_evidence[:4],
                "causal_chain": (
                    f"Bug input → {component} processing → {exception_type or 'failure'} "
                    f"→ observed error"
                ),
            }
        ]

        related_components = [component]
        if evidence:
            for ev in evidence[:3]:
                if ev.component and ev.component not in related_components:
                    related_components.append(ev.component)

        agent_reasoning = (
            f"Based on {category} pattern in the {component} component "
            + (f"with a {exception_type} exception " if exception_type else "")
            + f"and {len(error_patterns)} error pattern(s) detected. "
            + (
                f"Supported by {len(evidence)} historical defect(s) with similar characteristics."
                if evidence
                else "No historical evidence retrieved."
            )
        )

        return {
            "probable_cause": probable_cause,
            "confidence": confidence,
            "reasoning": (
                f"Category '{category}' in component '{component}' detected via triage. "
                + (f"Exception '{exception_type}' points to a specific code path. " if exception_type else "")
                + (f"Failure at '{failure_point}' confirms the location. " if failure_point else "")
                + f"{len(evidence)} similar historical defect(s) retrieved for context."
            ),
            "agent_reasoning": agent_reasoning,
            "related_components": related_components,
            "hypotheses": hypotheses,
        }

    def _calculate_deterministic_confidence(
        self, signals: Dict, evidence: List[HistoricalEvidence]
    ) -> float:
        """Calculate confidence without LLM.

        Caps at 0.50 when the bug has very few meaningful signals (vague report),
        so that mock evidence boosts cannot produce overconfident results.
        """
        score = 0.30  # base

        if signals.get("exception_type"):
            score += 0.15
        if signals.get("failure_point"):
            score += 0.12
        if signals.get("error_patterns"):
            score += min(0.10, len(signals["error_patterns"]) * 0.03)
        if signals.get("stack_trace"):
            score += 0.08
        if signals.get("category") and signals["category"] != "Logic Error":
            score += 0.05

        # Determine whether the bug report is sparse using RAW input signals
        # (not inferred fields like error_patterns which may come from description text)
        has_stack_trace = bool((signals.get("stack_trace") or "").strip())
        has_exception   = bool((signals.get("exception_type") or "").strip())
        # Only count failure_point (from real stack trace parsing), not error_patterns
        # which the log agent may infer from the description alone
        has_failure_pt  = bool((signals.get("failure_point") or "").strip())
        description_len = len((signals.get("description") or "").strip())

        sparse_report = (not has_stack_trace
                         and not has_exception
                         and not has_failure_pt
                         and description_len < 80)

        if sparse_report:
            # Never exceed 0.50 for vague reports — evidence from mock search
            # does not constitute real supporting data
            return round(min(0.50, score), 3)

        # Evidence from RAG (genuine boost only for non-sparse bugs)
        for ev in evidence:
            score += min(0.05, ev.similarity_score * 0.06)

        return round(min(0.85, score), 3)

    def _build_hypotheses(
        self, llm_result: Dict, evidence: List[HistoricalEvidence]
    ) -> List[RootCauseHypothesis]:
        """Convert raw LLM hypotheses list to Pydantic models."""
        raw_hyps = llm_result.get("hypotheses", [])
        result = []
        for h in raw_hyps[:3]:  # cap at 3 hypotheses
            try:
                result.append(
                    RootCauseHypothesis(
                        hypothesis=h.get("hypothesis", ""),
                        confidence=min(1.0, float(h.get("confidence", 0.5))),
                        supporting_evidence=h.get("supporting_evidence", []),
                        causal_chain=h.get("causal_chain", ""),
                    )
                )
            except Exception:
                pass
        return result

    def _insufficient_evidence(self, reason: str, duration: float) -> Dict[str, Any]:
        """Return a structured Insufficient Evidence result."""
        logger.info(f"Root Cause Agent: Insufficient Evidence — {reason}")
        return RootCauseAgentOutput(
            result=RootCauseResult(
                status="insufficient_evidence",
                probable_cause="Insufficient Evidence",
                confidence=0.0,
                reasoning=reason,
                agent_reasoning="",
                evidence_summary="",
                insufficient_evidence_reason=reason,
            ),
            duration=duration,
            timestamp=datetime.utcnow().isoformat(),
            status="insufficient_evidence",
        ).dict()
