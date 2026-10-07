"""LLM service with OpenAI-compatible API and mock mode."""

import os
import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class LLMService:
    """LLM service supporting OpenAI-compatible APIs with mock fallback."""

    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY", "")
        self.api_base = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
        self.model = os.getenv("LLM_MODEL", "gpt-4o-mini")
        self.mock_mode = not bool(self.api_key)

        if self.mock_mode:
            logger.info("LLM running in MOCK mode (no API key configured)")
        else:
            logger.info(f"LLM configured: {self.model} at {self.api_base}")

    async def generate(self, prompt: str, system_prompt: str = "",
                       temperature: float = 0.3, max_tokens: int = 2000) -> str:
        """Generate text from the LLM."""
        if self.mock_mode:
            return self._mock_generate(prompt, system_prompt)

        try:
            import httpx
            async with httpx.AsyncClient(timeout=60.0) as client:
                messages = []
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt})
                messages.append({"role": "user", "content": prompt})

                response = await client.post(
                    f"{self.api_base}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": messages,
                        "temperature": temperature,
                        "max_tokens": max_tokens
                    }
                )
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"LLM API error: {e}")
            return self._mock_generate(prompt, system_prompt)

    async def generate_json(self, prompt: str, system_prompt: str = "") -> Dict[str, Any]:
        """Generate structured JSON response."""
        response = await self.generate(prompt, system_prompt)
        try:
            # Try to extract JSON from response
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                response = response.split("```")[1].split("```")[0]
            return json.loads(response.strip())
        except json.JSONDecodeError:
            logger.warning("Failed to parse LLM JSON response, returning raw")
            return {"raw_response": response}

    def _mock_generate(self, prompt: str, system_prompt: str) -> str:
        """Generate mock response for development — covers all M3 agent prompts."""
        prompt_lower = prompt.lower()

        # Root Cause Agent (M3)
        if "root cause" in prompt_lower or "causal chain" in prompt_lower:
            return json.dumps({
                "probable_cause": "Missing null/bounds check before accessing an object property in the affected component's processing pipeline.",
                "confidence": 0.78,
                "reasoning": (
                    "1. The exception type indicates a null or out-of-bounds access. "
                    "2. The failure point is in the component's core processing loop. "
                    "3. Historical defects with similar patterns were resolved by adding guard clauses."
                ),
                "agent_reasoning": (
                    "Inferred that the unguarded access occurs under a specific conditional branch "
                    "that is only reached when input arrives in a partially-initialised state."
                ),
                "related_components": ["Core Module", "Error Handler", "Input Validator"],
                "hypotheses": [
                    {
                        "hypothesis": "A null reference is accessed in the processing pipeline without a prior null-check.",
                        "confidence": 0.78,
                        "supporting_evidence": [
                            "Exception type confirms null access",
                            "Failure point in core processing loop",
                            "Similar historical defect MOZ-1001 had same root cause"
                        ],
                        "causal_chain": "Uninitialised input → processing loop → null access → exception"
                    }
                ]
            })

        # Remediation Agent (M3)
        elif "remediation" in prompt_lower or "implementation_steps" in prompt_lower:
            return json.dumps({
                "suggested_fix": (
                    "Add a null/bounds check at the entry of the affected method. "
                    "Use Optional or guard clauses to handle missing values. "
                    "Implement defensive programming with early returns for invalid inputs."
                ),
                "fix_from_best_practice": False,
                "confidence": 0.82,
                "agent_reasoning": (
                    "Fix derived from the identified root cause: unguarded null access. "
                    "Pattern matches resolution of similar historical defects."
                ),
                "implementation_steps": [
                    {
                        "step": "Locate the failure point identified in the log analysis.",
                        "detail": "Use the code path from the stack trace to navigate to the exact line.",
                        "is_speculative": False
                    },
                    {
                        "step": "Add a null check or Optional guard before the property access.",
                        "detail": "Example: if (obj == null) { log.warn('...'); return; }",
                        "is_speculative": False
                    },
                    {
                        "step": "Add a unit test covering the null/missing-input scenario.",
                        "detail": "Test should assert the method handles null gracefully.",
                        "is_speculative": False
                    },
                    {
                        "step": "Review adjacent code for the same pattern.",
                        "detail": "Search for similar unchecked accesses in the same component.",
                        "is_speculative": True
                    }
                ],
                "debugging_steps": [
                    "Reproduce the issue locally with the same inputs.",
                    "Add a breakpoint at the identified failure point.",
                    "Inspect the object state just before the exception.",
                    "Verify which code path leads to the null state."
                ],
                "validation_steps": [
                    "Write a unit test that reproduces the failure.",
                    "Run the test suite for the affected component.",
                    "Verify fix resolves the original bug without regressions.",
                    "Test boundary conditions and edge cases."
                ],
                "regression_tests": [
                    "Run full test suite for the affected module.",
                    "Execute integration tests for the user-facing workflow.",
                    "Performance test to verify no regression under load."
                ],
                "best_practices": [
                    "Always validate inputs at method boundaries.",
                    "Use Optional types or null-object pattern for safer APIs.",
                    "Add observability (logging, metrics) around critical paths."
                ],
                "estimated_effort": "2-4 hours",
                "risk_level": "medium"
            })

        # Triage Agent (legacy + M3 compat)
        elif "triage" in prompt_lower:
            return json.dumps({
                "severity": "high",
                "priority": "P1",
                "category": "Null Reference",
                "component": "Core Module",
                "confidence": 0.85,
                "reasoning": (
                    "Based on the error pattern, this appears to be a null reference issue "
                    "requiring immediate attention."
                )
            })

        else:
            return json.dumps({
                "analysis": "Mock analysis result for development purposes.",
                "confidence": 0.75
            })
