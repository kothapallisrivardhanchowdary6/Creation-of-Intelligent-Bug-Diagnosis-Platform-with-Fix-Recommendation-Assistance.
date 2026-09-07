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
        """Generate mock response for development."""
        if "triage" in prompt.lower():
            return json.dumps({
                "severity": "high",
                "priority": "P1",
                "category": "Null Reference",
                "component": "Core Module",
                "confidence": 0.85,
                "reasoning": "Based on the error pattern, this appears to be a null reference issue requiring immediate attention."
            })
        elif "root cause" in prompt.lower():
            return json.dumps({
                "probable_cause": "Missing null check before accessing object property in the processing pipeline",
                "evidence": ["Error pattern matches null reference defects", "Stack trace points to uninitialized object"],
                "confidence": 0.78,
                "related_components": ["Core Module", "Error Handler"]
            })
        elif "remediation" in prompt.lower():
            return json.dumps({
                "suggested_fix": "Add null safety checks and optional chaining. Implement defensive programming with early returns.",
                "debugging_steps": ["Reproduce in controlled environment", "Add logging at failure point", "Verify null checks"],
                "validation_steps": ["Unit test for failure scenario", "Edge case testing", "Integration tests"],
                "regression_tests": ["Run existing test suite", "End-to-end tests", "Performance verification"],
                "estimated_effort": "2-4 hours",
                "risk_level": "medium"
            })
        else:
            return json.dumps({
                "analysis": "Mock analysis result for development purposes.",
                "confidence": 0.75
            })
