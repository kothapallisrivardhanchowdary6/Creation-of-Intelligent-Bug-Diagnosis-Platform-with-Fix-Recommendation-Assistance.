"""
Milestone 3: Remediation Agent.

Uses Triage, Log Analysis, Root Cause, and Duplicate Detection results.
Retrieves historical resolutions from the knowledge base via RAG.
Generates specific, actionable fixes with:
  - Confidence score
  - Implementation guidance
  - Supporting evidence (from KB)
  - Validation steps
  - Clear distinction between historical evidence, best practices, and agent reasoning.

Does NOT present speculation as confirmed fixes.
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

class ImplementationStep(BaseModel):
    """A single implementation step with optional code hint."""
    step: str
    detail: Optional[str] = None
    is_speculative: bool = False   # True = not confirmed by historical evidence


class HistoricalResolution(BaseModel):
    """A resolution retrieved from the historical defect knowledge base."""
    bug_id: str
    document: str
    resolution: str
    component: Optional[str] = None
    severity: Optional[str] = None
    similarity_score: float = Field(ge=0.0, le=1.0)
    source: str = "historical_defect_database"


class RemediationResult(BaseModel):
    """Complete remediation result."""
    status: str = "success"  # success | insufficient_evidence | error

    # Primary fix — labeled by source
    suggested_fix: str
    fix_source: str = "agent_reasoning"  # historical_evidence | best_practice | agent_reasoning
    confidence: float = Field(ge=0.0, le=1.0, default=0.5)

    # Actionable guidance
    implementation_steps: List[ImplementationStep] = Field(default_factory=list)
    debugging_steps: List[str] = Field(default_factory=list)
    validation_steps: List[str] = Field(default_factory=list)
    regression_tests: List[str] = Field(default_factory=list)

    # Evidence
    historical_resolutions: List[HistoricalResolution] = Field(default_factory=list)
    best_practices: List[str] = Field(default_factory=list)

    # Meta
    estimated_effort: str = "Unknown"
    risk_level: str = "medium"   # low | medium | high
    evidence_summary: str = ""
    agent_reasoning: str = ""

    @validator("confidence")
    def round_confidence(cls, v):
        return round(v, 3)

    @validator("risk_level")
    def validate_risk(cls, v):
        if v not in ("low", "medium", "high"):
            return "medium"
        return v


class RemediationAgentOutput(BaseModel):
    """Complete agent output with metadata."""
    agent: str = "Remediation Agent"
    version: str = "3.0.0-M3"
    result: RemediationResult
    duration: float
    timestamp: str
    status: str = "success"
    error: Optional[str] = None


# ============================================================
# Remediation Agent
# ============================================================

class RemediationAgent:
    """
    Milestone 3 Remediation Agent.

    Pipeline:
    1. Extract signals from all upstream agent results.
    2. Build a rich RAG query using bug + root cause + component info.
    3. Retrieve and label historical resolutions.
    4. Call LLM with clearly separated evidence vs. speculation instructions.
    5. Return structured, actionable remediation with source labels.
    """

    INSUFFICIENT_CONFIDENCE_THRESHOLD = 0.20

    def __init__(self, llm_service=None, chroma_service=None, embedding_service=None):
        self.llm = llm_service
        self.chroma = chroma_service
        self.embeddings = embedding_service
        self.name = "Remediation Agent"
        self.version = "3.0.0-M3"

    async def analyze(
        self,
        bug_data: Dict[str, Any],
        triage_result: Dict[str, Any],
        log_result: Dict[str, Any],
        root_cause_result: Dict[str, Any],
        duplicate_result: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Generate remediation suggestions.

        Args:
            bug_data:           Original bug report.
            triage_result:      TriageAgent output.
            log_result:         LogAnalysisAgent output.
            root_cause_result:  RootCauseAgent output.
            duplicate_result:   DuplicateDetectionAgent output.

        Returns:
            RemediationAgentOutput as dict.
        """
        start_time = time.time()

        try:
            # ── 1. Extract signals ────────────────────────────────────────
            signals = self._extract_signals(
                bug_data, triage_result, log_result, root_cause_result, duplicate_result
            )

            # ── 2. RAG for historical resolutions ─────────────────────────
            historical_resolutions = []
            if self.chroma and self.embeddings:
                historical_resolutions = self._retrieve_resolutions(signals)

            # ── 3. LLM for actionable guidance ───────────────────────────
            llm_result = await self._run_llm(signals, historical_resolutions)

            # ── 4. Compute confidence ─────────────────────────────────────
            base_conf = llm_result.get("confidence", 0.5)
            hist_boost = min(0.15, len(historical_resolutions) * 0.04)
            final_conf = round(min(0.95, base_conf + hist_boost), 3)

            # ── 5. Build result ───────────────────────────────────────────
            impl_steps = self._build_implementation_steps(
                llm_result, historical_resolutions
            )

            fix_source = "agent_reasoning"
            if historical_resolutions and historical_resolutions[0].similarity_score >= 0.70:
                fix_source = "historical_evidence"
            elif llm_result.get("fix_from_best_practice"):
                fix_source = "best_practice"

            result = RemediationResult(
                status="success",
                suggested_fix=llm_result.get(
                    "suggested_fix",
                    f"Review and correct the error handling in the {signals.get('component', 'affected')} component.",
                ),
                fix_source=fix_source,
                confidence=final_conf,
                implementation_steps=impl_steps,
                debugging_steps=llm_result.get("debugging_steps", []),
                validation_steps=llm_result.get("validation_steps", []),
                regression_tests=llm_result.get("regression_tests", []),
                historical_resolutions=historical_resolutions,
                best_practices=llm_result.get("best_practices", []),
                estimated_effort=llm_result.get("estimated_effort", "2–4 hours"),
                risk_level=llm_result.get("risk_level", "medium"),
                evidence_summary=self._summarize_resolutions(historical_resolutions),
                agent_reasoning=llm_result.get("agent_reasoning", ""),
            )

            duration = time.time() - start_time
            logger.info(
                f"Remediation Agent completed in {duration:.2f}s — "
                f"confidence={final_conf:.2f}, fix_source={fix_source}"
            )

            output = RemediationAgentOutput(
                result=result,
                duration=duration,
                timestamp=datetime.utcnow().isoformat(),
                status="success",
            )
            return output.dict()

        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Remediation Agent failed: {e}", exc_info=True)
            return RemediationAgentOutput(
                result=RemediationResult(
                    status="error",
                    suggested_fix="Remediation analysis failed due to an internal error.",
                    confidence=0.0,
                    agent_reasoning=f"Error: {str(e)}",
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
        triage_result: Dict,
        log_result: Dict,
        root_cause_result: Dict,
        duplicate_result: Dict,
    ) -> Dict[str, Any]:
        """Flatten all upstream results into a signals dict."""
        triage = triage_result.get("result", {}) if triage_result else {}
        log = log_result.get("result", {}) if log_result else {}
        rc = root_cause_result.get("result", {}) if root_cause_result else {}
        dup = duplicate_result.get("result", {}) if duplicate_result else {}

        exceptions = log.get("exceptions", [])
        primary_exc = exceptions[0] if exceptions else {}

        return {
            "title": bug_data.get("title", ""),
            "description": bug_data.get("description", ""),
            "environment": bug_data.get("environment", ""),
            "severity": triage.get("severity", "medium"),
            "priority": triage.get("priority", "P2"),
            "category": triage.get("category", "Logic Error"),
            "component": triage.get("component", "Unknown"),
            "triage_reasoning": triage.get("reasoning", ""),
            "exception_type": primary_exc.get("exception_type", ""),
            "error_message": primary_exc.get("error_message", ""),
            "failure_point": log.get("failure_point", ""),
            "error_patterns": log.get("error_patterns", []),
            "probable_cause": rc.get("probable_cause", ""),
            "root_cause_reasoning": rc.get("reasoning", ""),
            "root_cause_confidence": rc.get("confidence", 0.0),
            "related_components": rc.get("related_components", []),
            "duplicate_classification": dup.get("classification", ""),
            "top_duplicate_id": (
                dup.get("matched_bugs", [{}])[0].get("bug_id", "")
                if dup.get("matched_bugs") else ""
            ),
        }

    def _retrieve_resolutions(self, signals: Dict[str, Any]) -> List[HistoricalResolution]:
        """RAG: find historical bugs with similar characteristics and resolutions."""
        query_parts = [
            signals.get("title", ""),
            signals.get("probable_cause", ""),
            signals.get("category", ""),
            signals.get("component", ""),
            signals.get("exception_type", ""),
        ]
        query_text = " ".join(p for p in query_parts if p).strip()
        if not query_text:
            return []

        try:
            query_embedding = self.embeddings.embed_text(query_text)
            raw = self.chroma.search(query_embedding, top_k=4)

            resolutions = []
            for r in raw:
                score = float(r.get("score", 0.0))
                meta = r.get("metadata", {})
                resolution_text = meta.get("resolution", "")
                # Only include if there's an actual resolution
                if not resolution_text:
                    resolution_text = "No resolution recorded in the knowledge base."

                resolutions.append(
                    HistoricalResolution(
                        bug_id=r.get("id", "UNKNOWN"),
                        document=r.get("document", ""),
                        resolution=resolution_text,
                        component=meta.get("component", meta.get("project", "")),
                        severity=meta.get("severity", ""),
                        similarity_score=round(float(score), 4),
                    )
                )
            return resolutions
        except Exception as e:
            logger.warning(f"Remediation RAG retrieval failed: {e}")
            return []

    def _summarize_resolutions(self, resolutions: List[HistoricalResolution]) -> str:
        """One-sentence summary of retrieved resolutions."""
        if not resolutions:
            return "No historical resolutions retrieved from the knowledge base."
        top = resolutions[0]
        return (
            f"Retrieved {len(resolutions)} historical resolution(s). "
            f"Closest match: {top.bug_id} ({top.similarity_score:.1%}) — {top.resolution[:80]}."
        )

    async def _run_llm(
        self,
        signals: Dict[str, Any],
        resolutions: List[HistoricalResolution],
    ) -> Dict[str, Any]:
        """Call LLM for actionable remediation or fall back to deterministic."""
        if not self.llm:
            return self._deterministic_remediation(signals, resolutions)

        res_text = self._format_resolutions_for_prompt(resolutions)

        prompt = f"""You are an expert software engineer specializing in bug remediation.

=== CURRENT BUG ===
Title: {signals['title']}
Description: {signals['description']}
Severity: {signals['severity']} | Priority: {signals['priority']}
Category: {signals['category']} | Component: {signals['component']}
Exception: {signals['exception_type']} — {signals['error_message']}
Failure Point: {signals['failure_point']}
Environment: {signals['environment']}

=== ROOT CAUSE ANALYSIS ===
Probable Cause: {signals['probable_cause']}
Reasoning: {signals['root_cause_reasoning']}
Root Cause Confidence: {signals['root_cause_confidence']:.0%}
Related Components: {', '.join(signals['related_components']) if signals['related_components'] else 'None identified'}

=== DUPLICATE DETECTION ===
Classification: {signals['duplicate_classification']}
Closest Historical Bug: {signals['top_duplicate_id'] or 'None'}

{res_text}

=== INSTRUCTIONS ===
1. Generate SPECIFIC, ACTIONABLE remediation steps — not generic advice.
2. Clearly label each fix as:
   - "historical_evidence" if directly supported by the resolutions above
   - "best_practice" if it follows industry-standard patterns
   - "agent_reasoning" if it is your inference (mark as speculative)
3. Do NOT present speculative fixes as confirmed solutions.
4. Return ONLY a valid JSON object — no markdown fences.

Required JSON schema:
{{
  "suggested_fix": "Precise description of the primary fix",
  "fix_from_best_practice": true/false,
  "confidence": 0.0-1.0,
  "agent_reasoning": "What you inferred (not from evidence)",
  "implementation_steps": [
    {{"step": "string", "detail": "optional code hint or explanation", "is_speculative": false}}
  ],
  "debugging_steps": ["step 1", ...],
  "validation_steps": ["step 1", ...],
  "regression_tests": ["test 1", ...],
  "best_practices": ["practice 1", ...],
  "estimated_effort": "e.g. 2-4 hours",
  "risk_level": "low|medium|high"
}}"""

        try:
            raw = await self.llm.generate_json(
                prompt,
                "You are a software engineering expert specializing in defect remediation.",
            )
            if "raw_response" in raw:
                return self._deterministic_remediation(signals, resolutions)
            return raw
        except Exception as e:
            logger.warning(f"LLM call failed in RemediationAgent: {e}")
            return self._deterministic_remediation(signals, resolutions)

    def _format_resolutions_for_prompt(self, resolutions: List[HistoricalResolution]) -> str:
        if not resolutions:
            return "=== HISTORICAL RESOLUTIONS ===\nNo similar historical resolutions found."
        lines = ["=== HISTORICAL RESOLUTIONS (from defect knowledge base) ==="]
        for i, r in enumerate(resolutions, 1):
            lines.append(
                f"[Resolution {i}] Bug: {r.bug_id} | Similarity: {r.similarity_score:.2%}"
                f" | Component: {r.component or 'N/A'}"
            )
            lines.append(f"  Description: {r.document}")
            lines.append(f"  Resolution:  {r.resolution}")
        return "\n".join(lines)

    def _build_implementation_steps(
        self,
        llm_result: Dict,
        resolutions: List[HistoricalResolution],
    ) -> List[ImplementationStep]:
        """Parse and validate implementation steps from LLM output."""
        raw_steps = llm_result.get("implementation_steps", [])
        result = []
        for s in raw_steps[:8]:  # cap at 8 steps
            if isinstance(s, str):
                result.append(ImplementationStep(step=s))
            elif isinstance(s, dict):
                try:
                    result.append(
                        ImplementationStep(
                            step=s.get("step", ""),
                            detail=s.get("detail"),
                            is_speculative=bool(s.get("is_speculative", False)),
                        )
                    )
                except Exception:
                    pass
        # If LLM returned nothing, build from deterministic
        if not result:
            result = self._default_implementation_steps(
                llm_result.get("suggested_fix", ""), resolutions
            )
        return result

    def _default_implementation_steps(
        self, suggested_fix: str, resolutions: List[HistoricalResolution]
    ) -> List[ImplementationStep]:
        """Fallback implementation steps."""
        steps = [
            ImplementationStep(
                step="Reproduce the defect in a local or staging environment.",
                is_speculative=False,
            ),
            ImplementationStep(
                step="Add detailed logging around the identified failure point.",
                is_speculative=False,
            ),
            ImplementationStep(
                step="Apply the suggested fix with proper null/bounds checking.",
                detail=suggested_fix[:120] if suggested_fix else None,
                is_speculative=False,
            ),
        ]
        if resolutions:
            top = resolutions[0]
            steps.append(
                ImplementationStep(
                    step=f"Apply resolution pattern from historical bug {top.bug_id}.",
                    detail=top.resolution[:120],
                    is_speculative=False,
                )
            )
        steps.append(
            ImplementationStep(
                step="Write a unit test covering the exact failure scenario.",
                is_speculative=False,
            )
        )
        return steps

    def _deterministic_remediation(
        self, signals: Dict, resolutions: List[HistoricalResolution]
    ) -> Dict[str, Any]:
        """
        Deterministic remediation when LLM is unavailable.
        Uses category/component patterns and historical resolutions.
        """
        category = signals.get("category", "Logic Error")
        component = signals.get("component", "Unknown Component")
        exception_type = signals.get("exception_type", "")
        probable_cause = signals.get("probable_cause", "")
        severity = signals.get("severity", "medium")

        # Build suggested fix from patterns
        fix_map = {
            "Null Reference": (
                f"Add null/None checks before accessing objects in {component}. "
                "Use Optional types or guard clauses to handle missing values safely. "
                "Consider adding assertion checks at method entry points."
            ),
            "Memory Management": (
                f"Ensure all resources in {component} are released using try-finally or "
                "context managers (try-with-resources in Java). "
                "Profile memory usage to identify the specific leak point."
            ),
            "Concurrency": (
                f"Review synchronization in {component}: add proper locks, use thread-safe "
                "data structures, and implement lock ordering to prevent deadlock. "
                "Consider using higher-level concurrency primitives (Executors, CompletableFuture)."
            ),
            "Network/IO": (
                f"Add timeout configuration, retry logic with exponential backoff, and "
                "circuit breaker pattern in {component}. Handle partial failures explicitly."
            ),
            "Security": (
                f"Implement input validation and output encoding in {component}. "
                "Use parameterized queries, whitelist validation, and review OWASP guidelines."
            ),
            "Input Validation": (
                f"Add comprehensive input validation in {component} before processing. "
                "Validate type, range, and format. Return clear error messages for invalid input."
            ),
            "Performance": (
                f"Profile {component} to identify bottlenecks. "
                "Implement caching, batch operations, and asynchronous processing where applicable."
            ),
        }

        suggested_fix = fix_map.get(
            category,
            f"Review error handling in {component}. Add defensive programming patterns "
            "and comprehensive unit tests covering the failure scenario.",
        )
        if exception_type:
            suggested_fix += f" Specifically address the {exception_type}."

        # Incorporate historical resolutions
        fix_from_best_practice = False
        if resolutions and resolutions[0].similarity_score >= 0.60:
            top_res = resolutions[0]
            if top_res.resolution and top_res.resolution != "No resolution recorded in the knowledge base.":
                suggested_fix = (
                    f"Based on historical fix for {top_res.bug_id} ({top_res.similarity_score:.0%} similar): "
                    f"{top_res.resolution}. "
                    f"Apply the same pattern to {component}: {suggested_fix}"
                )
                fix_from_best_practice = True

        debugging_steps = [
            f"Reproduce the issue with the exact inputs that triggered the failure.",
            f"Add detailed logging at the failure point in {component}.",
            "Verify the fix resolves the issue in a controlled environment.",
            "Check related code paths that might have the same defect.",
        ]
        if exception_type:
            debugging_steps.insert(
                1,
                f"Set a breakpoint at the {exception_type} throw site to inspect state.",
            )

        validation_steps = [
            "Create a unit test that reproduces the exact failure scenario.",
            "Verify the fix does not regress existing functionality.",
            "Run integration tests for the affected component.",
            "Test boundary conditions and edge cases.",
            "Verify the fix under the original environment conditions.",
        ]

        regression_tests = [
            f"Run the full test suite for {component}.",
            "Execute end-to-end tests covering the user-facing workflow.",
            "Performance test to ensure no regression under load.",
            "Cross-component integration test for related components.",
        ]

        best_practices = [
            "Follow defensive programming principles (validate inputs, check nulls).",
            "Add observability (logging, metrics) around critical paths.",
            "Document the root cause and fix in the commit message and ticket.",
        ]

        effort_map = {"critical": "4–8 hours", "high": "2–4 hours", "medium": "1–2 hours", "low": "< 1 hour"}
        risk_map = {"critical": "high", "high": "medium", "medium": "medium", "low": "low"}

        confidence = self._calculate_confidence(signals, resolutions)

        agent_reasoning = (
            f"Remediation derived from {category} pattern in {component}. "
            + (f"Exception type '{exception_type}' informed the specific fix approach. " if exception_type else "")
            + (f"Root cause '{probable_cause[:60]}...' provided direction. " if probable_cause else "")
            + (f"{len(resolutions)} historical resolution(s) incorporated." if resolutions else "No historical resolutions found.")
        )

        return {
            "suggested_fix": suggested_fix,
            "fix_from_best_practice": fix_from_best_practice,
            "confidence": confidence,
            "agent_reasoning": agent_reasoning,
            "implementation_steps": [],  # Will be built by _build_implementation_steps
            "debugging_steps": debugging_steps,
            "validation_steps": validation_steps,
            "regression_tests": regression_tests,
            "best_practices": best_practices,
            "estimated_effort": effort_map.get(severity, "2–4 hours"),
            "risk_level": risk_map.get(severity, "medium"),
        }

    def _calculate_confidence(
        self, signals: Dict, resolutions: List[HistoricalResolution]
    ) -> float:
        """Calculate confidence score."""
        score = 0.35  # base

        if signals.get("probable_cause"):
            score += 0.15
        if signals.get("root_cause_confidence"):
            score += min(0.10, float(signals["root_cause_confidence"]) * 0.15)
        if signals.get("exception_type"):
            score += 0.08
        if signals.get("failure_point"):
            score += 0.07
        if signals.get("error_patterns"):
            score += min(0.05, len(signals["error_patterns"]) * 0.02)
        for r in resolutions[:3]:
            score += min(0.06, r.similarity_score * 0.07)

        return round(min(0.90, score), 3)
