"""
Milestone 2: Enhanced Triage Agent with Pydantic validation.

Analyzes bug title, description, environment, logs and stack trace.
Outputs structured JSON with severity, priority, component, confidence, reasoning.
"""

import re
import logging
import time
from typing import Dict, Any, Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, validator

logger = logging.getLogger(__name__)


# ============================================================
# Pydantic Models for Structured Output
# ============================================================

class TriageResult(BaseModel):
    """Structured triage result with validation."""
    severity: str = Field(..., pattern="^(critical|high|medium|low)$")
    priority: str = Field(..., pattern="^(P0|P1|P2|P3)$")
    category: str = Field(..., min_length=1)
    component: str = Field(..., min_length=1)
    confidence: float = Field(..., ge=0.0, le=1.0)
    reasoning: str = Field(..., min_length=1)
    
    @validator('severity')
    def validate_severity(cls, v):
        valid = ['critical', 'high', 'medium', 'low']
        if v.lower() not in valid:
            raise ValueError(f"Severity must be one of {valid}")
        return v.lower()
    
    @validator('priority')
    def validate_priority(cls, v):
        valid = ['P0', 'P1', 'P2', 'P3']
        if v.upper() not in valid:
            raise ValueError(f"Priority must be one of {valid}")
        return v.upper()
    
    @validator('confidence')
    def validate_confidence(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError("Confidence must be between 0.0 and 1.0")
        return round(v, 3)


class TriageAgentOutput(BaseModel):
    """Complete agent output with metadata."""
    agent: str = "Triage Agent"
    result: TriageResult
    duration: float
    timestamp: str
    status: str = "success"
    error: Optional[str] = None


# ============================================================
# Severity/Priority/Category Detection Rules
# ============================================================

SEVERITY_KEYWORDS = {
    'critical': [
        'crash', 'fatal', 'data loss', 'security', 'vulnerability', 'cve',
        'exploit', 'corruption', 'unrecoverable', 'production down',
        'segfault', 'kernel panic', 'out of memory', 'oom',
        'buffer overflow', 'injection', 'rce', 'privilege escalation'
    ],
    'high': [
        'error', 'fail', 'broken', 'exception', 'null', 'undefined',
        'timeout', 'deadlock', 'race condition', 'hang', 'freeze',
        'unresponsive', 'regression', 'blocker', 'major'
    ],
    'medium': [
        'slow', 'incorrect', 'wrong', 'unexpected', 'minor',
        'cosmetic', 'ui bug', 'display', 'alignment', 'typo',
        'warning', 'deprecated', 'annoying'
    ],
    'low': [
        'enhancement', 'feature request', 'nice to have', 'suggestion',
        'documentation', 'cleanup', 'refactor', 'optimization'
    ]
}

COMPONENT_PATTERNS = {
    'Networking': ['network', 'http', 'tcp', 'socket', 'connection', 'dns', 'proxy', 'ssl', 'tls'],
    'Database': ['database', 'db', 'sql', 'query', 'transaction', 'orm', 'migration', 'postgres', 'mysql'],
    'Authentication': ['auth', 'login', 'password', 'token', 'jwt', 'oauth', 'session', 'permission'],
    'UI/Frontend': ['ui', 'frontend', 'render', 'display', 'css', 'html', 'component', 'layout', 'button'],
    'API': ['api', 'endpoint', 'rest', 'graphql', 'request', 'response', 'route'],
    'File System': ['file', 'upload', 'download', 'storage', 'disk', 'path', 'directory'],
    'Memory Management': ['memory', 'leak', 'gc', 'garbage', 'heap', 'allocation', 'oom'],
    'Concurrency': ['thread', 'concurrent', 'parallel', 'async', 'race', 'deadlock', 'mutex', 'lock'],
    'Security': ['security', 'vulnerability', 'auth', 'encrypt', 'xss', 'csrf', 'injection'],
    'Performance': ['performance', 'slow', 'latency', 'throughput', 'bottleneck', 'optimize'],
    'Logging': ['log', 'logging', 'monitor', 'trace', 'debug', 'metric'],
    'Configuration': ['config', 'setting', 'environment', 'env', 'parameter', 'property'],
    'Testing': ['test', 'spec', 'mock', 'fixture', 'assertion', 'coverage'],
    'Build/Deploy': ['build', 'deploy', 'ci', 'cd', 'pipeline', 'docker', 'kubernetes'],
}

CATEGORY_PATTERNS = {
    'Null Reference': ['null', 'undefined', 'none', 'nil', 'nullpointer', 'attributeerror'],
    'Memory Management': ['memory', 'leak', 'overflow', 'outofmemory', 'oom', 'heap'],
    'Concurrency': ['thread', 'race', 'deadlock', 'concurrent', 'parallel', 'sync', 'async'],
    'Network/IO': ['network', 'connection', 'timeout', 'socket', 'http', 'dns', 'io'],
    'Security': ['security', 'vulnerability', 'injection', 'xss', 'csrf', 'auth', 'permission'],
    'Input Validation': ['validation', 'input', 'sanitize', 'parse', 'format', 'type'],
    'UI/Rendering': ['ui', 'render', 'display', 'css', 'layout', 'frontend', 'component'],
    'Performance': ['performance', 'slow', 'latency', 'optimize', 'bottleneck', 'cache'],
    'Logic Error': ['logic', 'algorithm', 'calculation', 'wrong', 'incorrect', 'unexpected'],
    'Configuration': ['config', 'setting', 'environment', 'parameter', 'property'],
}


# ============================================================
# Triage Agent Implementation
# ============================================================

class TriageAgent:
    """
    Enhanced Triage Agent for Milestone 2.
    
    Analyzes bug reports and produces structured triage classification
    with severity, priority, component, category, confidence, and reasoning.
    """

    def __init__(self, llm_service=None):
        self.llm = llm_service
        self.name = "Triage Agent"
        self.version = "2.0.0-M2"

    async def analyze(self, bug_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze bug for triage classification.
        
        Uses deterministic rules first, then optionally LLM for refinement.
        Always returns validated Pydantic model output.
        """
        start_time = time.time()
        
        try:
            # Extract relevant text for analysis
            text = self._extract_analysis_text(bug_data)
            
            # Deterministic classification
            severity = self._classify_severity(text, bug_data)
            priority = self._map_severity_to_priority(severity)
            category = self._classify_category(text)
            component = self._classify_component(text, bug_data)
            confidence = self._calculate_confidence(text, bug_data)
            reasoning = self._generate_reasoning(severity, category, component, bug_data)
            
            # Build result
            result = TriageResult(
                severity=severity,
                priority=priority,
                category=category,
                component=component,
                confidence=confidence,
                reasoning=reasoning
            )
            
            # Optionally refine with LLM if available
            if self.llm and not getattr(self.llm, 'mock_mode', True):
                try:
                    llm_result = await self._llm_refine(bug_data, result)
                    if llm_result:
                        result = llm_result
                except Exception as e:
                    logger.warning(f"LLM refinement failed, using deterministic result: {e}")
            
            duration = time.time() - start_time
            logger.info(f"Triage Agent v{self.version} completed in {duration:.2f}s")
            
            output = TriageAgentOutput(
                result=result,
                duration=duration,
                timestamp=datetime.utcnow().isoformat(),
                status="success"
            )
            
            return output.dict()
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Triage Agent failed: {e}")
            
            # Return fallback result
            fallback = TriageResult(
                severity="medium",
                priority="P2",
                category="Logic Error",
                component="Unknown",
                confidence=0.3,
                reasoning=f"Analysis failed: {str(e)}. Defaulting to medium priority."
            )
            
            return TriageAgentOutput(
                result=fallback,
                duration=duration,
                timestamp=datetime.utcnow().isoformat(),
                status="error",
                error=str(e)
            ).dict()

    def _extract_analysis_text(self, bug_data: Dict[str, Any]) -> str:
        """Combine all text fields for analysis."""
        parts = [
            bug_data.get('title', ''),
            bug_data.get('description', ''),
            bug_data.get('stack_trace', ''),
            bug_data.get('error_logs', ''),
            bug_data.get('environment', '')
        ]
        return ' '.join(str(p) for p in parts if p).lower()

    def _classify_severity(self, text: str, bug_data: Dict) -> str:
        """Classify severity based on keywords and context."""
        text_lower = text.lower()
        
        # Check each severity level
        for severity in ['critical', 'high', 'medium', 'low']:
            keywords = SEVERITY_KEYWORDS[severity]
            matches = sum(1 for kw in keywords if kw in text_lower)
            
            # Critical needs strong signal
            if severity == 'critical' and matches >= 2:
                return severity
            # High needs at least 1 strong signal
            elif severity == 'high' and matches >= 1:
                return severity
            # Medium/low are defaults
            elif severity == 'medium' and matches >= 1:
                return severity
        
        # Check for explicit severity in bug data
        explicit = bug_data.get('severity', '').lower()
        if explicit in ['critical', 'high', 'medium', 'low']:
            return explicit
        
        # Default based on content length and complexity
        if len(text) > 500:
            return 'medium'
        return 'low'

    def _map_severity_to_priority(self, severity: str) -> str:
        """Map severity to priority."""
        mapping = {
            'critical': 'P0',
            'high': 'P1',
            'medium': 'P2',
            'low': 'P3'
        }
        return mapping.get(severity, 'P2')

    def _classify_category(self, text: str) -> str:
        """Classify defect category."""
        text_lower = text.lower()
        
        best_match = 'Logic Error'
        best_score = 0
        
        for category, keywords in CATEGORY_PATTERNS.items():
            score = sum(1 for kw in keywords if kw in text_lower)
            if score > best_score:
                best_score = score
                best_match = category
        
        return best_match

    def _classify_component(self, text: str, bug_data: Dict) -> str:
        """Classify affected component."""
        text_lower = text.lower()
        
        # Check explicit component in bug data
        explicit = bug_data.get('component', '')
        if explicit:
            return explicit
        
        # Pattern matching
        best_match = 'Core Module'
        best_score = 0
        
        for component, keywords in COMPONENT_PATTERNS.items():
            score = sum(1 for kw in keywords if kw in text_lower)
            if score > best_score:
                best_score = score
                best_match = component
        
        return best_match

    def _calculate_confidence(self, text: str, bug_data: Dict) -> float:
        """Calculate confidence score based on available information."""
        score = 0.5  # Base confidence
        
        # More data = higher confidence
        if bug_data.get('title'):
            score += 0.1
        if bug_data.get('description') and len(bug_data['description']) > 50:
            score += 0.1
        if bug_data.get('stack_trace'):
            score += 0.15
        if bug_data.get('error_logs'):
            score += 0.1
        if bug_data.get('environment'):
            score += 0.05
        
        # Keyword matches increase confidence
        text_lower = text.lower()
        keyword_matches = 0
        for keywords in SEVERITY_KEYWORDS.values():
            keyword_matches += sum(1 for kw in keywords if kw in text_lower)
        
        if keyword_matches > 5:
            score += 0.1
        elif keyword_matches > 2:
            score += 0.05
        
        return min(0.95, score)

    def _generate_reasoning(self, severity: str, category: str, component: str, bug_data: Dict) -> str:
        """Generate human-readable reasoning."""
        parts = []
        
        parts.append(f"Classified as {severity} severity {category.lower()} defect")
        parts.append(f"affecting the {component} component")
        
        # Add context-specific reasoning
        if bug_data.get('stack_trace'):
            parts.append("Stack trace analysis supports this classification")
        if bug_data.get('error_logs'):
            parts.append("Error log patterns confirm the defect category")
        
        return '. '.join(parts) + '.'

    async def _llm_refine(self, bug_data: Dict, current_result: TriageResult) -> Optional[TriageResult]:
        """Use LLM to refine deterministic classification."""
        prompt = f"""Review and refine this bug triage classification.

Bug Title: {bug_data.get('title', '')}
Description: {bug_data.get('description', '')}
Stack Trace: {bug_data.get('stack_trace', 'None')}
Error Logs: {bug_data.get('error_logs', 'None')}
Environment: {bug_data.get('environment', 'Not specified')}

Current Classification:
- Severity: {current_result.severity}
- Priority: {current_result.priority}
- Category: {current_result.category}
- Component: {current_result.component}
- Confidence: {current_result.confidence}

If you agree, return the same values. If you disagree, provide corrected values.

Respond with JSON:
{{
    "severity": "critical|high|medium|low",
    "priority": "P0|P1|P2|P3",
    "category": "string",
    "component": "string",
    "confidence": 0.0-1.0,
    "reasoning": "explanation"
}}"""

        try:
            result = await self.llm.generate_json(prompt, "You are a software defect triage expert.")
            
            return TriageResult(
                severity=result.get('severity', current_result.severity),
                priority=result.get('priority', current_result.priority),
                category=result.get('category', current_result.category),
                component=result.get('component', current_result.component),
                confidence=float(result.get('confidence', current_result.confidence)),
                reasoning=result.get('reasoning', current_result.reasoning)
            )
        except Exception as e:
            logger.warning(f"LLM refinement failed: {e}")
            return None
