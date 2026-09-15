"""
Milestone 2: Log Analysis Agent with deterministic parsing.

Analyzes stack traces and logs from Java, Python, Node.js, and other languages.
Extracts exception types, error messages, file names, classes, methods, line numbers.
Uses regex parsing for deterministic extraction and LLM reasoning when needed.
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

class ExceptionInfo(BaseModel):
    """Structured exception information."""
    exception_type: str = Field(..., min_length=1)
    error_message: str = Field(default="")
    file_name: Optional[str] = None
    class_name: Optional[str] = None
    method_name: Optional[str] = None
    line_number: Optional[int] = None
    code_path: Optional[str] = None
    confidence: float = Field(default=0.7, ge=0.0, le=1.0)
    
    @validator('line_number')
    def validate_line_number(cls, v):
        if v is not None and v < 0:
            raise ValueError("Line number must be non-negative")
        return v
    
    @validator('confidence')
    def validate_confidence(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError("Confidence must be between 0.0 and 1.0")
        return round(v, 3)


class LogAnalysisResult(BaseModel):
    """Complete log analysis result."""
    exceptions: List[ExceptionInfo] = Field(default_factory=list)
    error_patterns: List[str] = Field(default_factory=list)
    failure_point: Optional[str] = None
    code_path: Optional[str] = None
    stack_trace_summary: Optional[str] = None
    suspicious_logs: List[str] = Field(default_factory=list)
    confidence: float = Field(default=0.7, ge=0.0, le=1.0)
    summary: str = Field(default="")
    
    @validator('confidence')
    def validate_confidence(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError("Confidence must be between 0.0 and 1.0")
        return round(v, 3)


class LogAnalysisAgentOutput(BaseModel):
    """Complete agent output with metadata."""
    agent: str = "Log Analysis Agent"
    result: LogAnalysisResult
    duration: float
    timestamp: str
    status: str = "success"
    error: Optional[str] = None


# ============================================================
# Stack Trace Parsers
# ============================================================

class StackTraceParser:
    """Parses stack traces from multiple languages."""
    
    # Java stack trace patterns
    JAVA_PATTERNS = [
        # Exception with message: java.lang.NullPointerException: message
        re.compile(r'^([\w.]+(?:Exception|Error|Throwable))\s*:\s*(.+)$', re.MULTILINE),
        # Stack frame: at com.package.Class.method(File.java:123)
        re.compile(r'at\s+([\w.$]+)\.([\w$]+)\(([^:]+):(\d+)\)'),
        # Caused by: java.lang.RuntimeException: message
        re.compile(r'Caused by:\s+([\w.]+(?:Exception|Error))\s*:\s*(.+)$', re.MULTILINE),
    ]
    
    # Python stack trace patterns
    PYTHON_PATTERNS = [
        # Traceback header: Traceback (most recent call last):
        re.compile(r'Traceback \(most recent call last\):', re.MULTILINE),
        # File line: File "/path/to/file.py", line 123, in function
        re.compile(r'File "([^"]+)", line (\d+), in (\w+)'),
        # Exception: ExceptionType: message
        re.compile(r'^([\w.]+(?:Error|Exception))\s*:\s*(.+)$', re.MULTILINE),
    ]
    
    # Node.js stack trace patterns
    NODE_PATTERNS = [
        # Error: message
        re.compile(r'^(\w+Error):\s*(.+)$', re.MULTILINE),
        # Stack frame: at FunctionName (/path/to/file.js:123:45)
        re.compile(r'at\s+(.+?)\s+\(([^:]+):(\d+):(\d+)\)'),
        # Stack frame without function: at /path/to/file.js:123:45
        re.compile(r'at\s+([^:]+):(\d+):(\d+)'),
    ]
    
    # Generic error patterns
    GENERIC_PATTERNS = [
        # ERROR level logs
        re.compile(r'(?:ERROR|FATAL|CRITICAL)\s*[:\-]?\s*(.+)', re.IGNORECASE),
        # Exception keywords
        re.compile(r'(exception|error|fail|crash|fatal)', re.IGNORECASE),
    ]
    
    @classmethod
    def detect_language(cls, text: str) -> str:
        """Detect the programming language from stack trace."""
        text_lower = text.lower()
        
        # Java indicators
        if any(ind in text for ind in ['java.lang.', '.java:', 'at com.', 'at org.', 'Caused by:']):
            return 'java'
        
        # Python indicators
        if any(ind in text for ind in ['Traceback (most recent call last)', 'File "', '.py:', 'TypeError:', 'ValueError:']):
            return 'python'
        
        # Node.js indicators
        if any(ind in text for ind in ['node:', '.js:', 'at Object.', 'at Module.', 'npm ERR!']):
            return 'nodejs'
        
        return 'unknown'
    
    @classmethod
    def parse_java(cls, text: str) -> List[ExceptionInfo]:
        """Parse Java stack trace."""
        exceptions = []
        
        # Find exception type and message
        for match in cls.JAVA_PATTERNS[0].finditer(text):
            exc_type = match.group(1)
            message = match.group(2).strip()
            
            # Try to find stack frame details
            file_name = None
            class_name = None
            method_name = None
            line_number = None
            
            # Look for "at" frames after this exception
            remaining_text = text[match.end():]
            frame_match = cls.JAVA_PATTERNS[1].search(remaining_text)
            if frame_match:
                full_class = frame_match.group(1)
                method_name = frame_match.group(2)
                file_name = frame_match.group(3)
                line_number = int(frame_match.group(4))
                
                # Extract class name from full path
                parts = full_class.rsplit('.', 1)
                if len(parts) > 1:
                    class_name = parts[1]
                else:
                    class_name = full_class
            
            exceptions.append(ExceptionInfo(
                exception_type=exc_type,
                error_message=message,
                file_name=file_name,
                class_name=class_name,
                method_name=method_name,
                line_number=line_number,
                code_path=f"{full_class}.{method_name}" if class_name and method_name else None,
                confidence=0.9 if file_name else 0.6
            ))
        
        return exceptions
    
    @classmethod
    def parse_python(cls, text: str) -> List[ExceptionInfo]:
        """Parse Python stack trace."""
        exceptions = []
        
        # Find file/line/function references
        file_refs = cls.PYTHON_PATTERNS[1].findall(text)
        
        # Find exception type and message
        for match in cls.PYTHON_PATTERNS[2].finditer(text):
            exc_type = match.group(1)
            message = match.group(2).strip()
            
            # Use the last file reference as the failure point
            file_name = None
            line_number = None
            method_name = None
            
            if file_refs:
                last_ref = file_refs[-1]
                file_name = last_ref[0]
                line_number = int(last_ref[1])
                method_name = last_ref[2]
            
            exceptions.append(ExceptionInfo(
                exception_type=exc_type,
                error_message=message,
                file_name=file_name,
                method_name=method_name,
                line_number=line_number,
                code_path=f"{file_name}:{line_number} in {method_name}" if file_name and method_name else None,
                confidence=0.85 if file_name else 0.5
            ))
        
        return exceptions
    
    @classmethod
    def parse_nodejs(cls, text: str) -> List[ExceptionInfo]:
        """Parse Node.js stack trace."""
        exceptions = []
        
        # Find error type and message
        for match in cls.NODE_PATTERNS[0].finditer(text):
            exc_type = match.group(1)
            message = match.group(2).strip()
            
            # Try to find stack frame
            file_name = None
            line_number = None
            method_name = None
            
            remaining_text = text[match.end():]
            
            # Try with function name
            frame_match = cls.NODE_PATTERNS[1].search(remaining_text)
            if frame_match:
                method_name = frame_match.group(1)
                file_name = frame_match.group(2)
                line_number = int(frame_match.group(3))
            else:
                # Try without function name
                frame_match = cls.NODE_PATTERNS[2].search(remaining_text)
                if frame_match:
                    file_name = frame_match.group(1)
                    line_number = int(frame_match.group(2))
            
            exceptions.append(ExceptionInfo(
                exception_type=exc_type,
                error_message=message,
                file_name=file_name,
                method_name=method_name,
                line_number=line_number,
                code_path=f"{file_name}:{line_number}" if file_name else None,
                confidence=0.8 if file_name else 0.5
            ))
        
        return exceptions
    
    @classmethod
    def parse_generic(cls, text: str) -> List[ExceptionInfo]:
        """Parse generic error patterns."""
        exceptions = []
        
        # Look for ERROR/FATAL lines
        for match in cls.GENERIC_PATTERNS[0].finditer(text):
            message = match.group(1).strip()
            
            exceptions.append(ExceptionInfo(
                exception_type="Error",
                error_message=message,
                confidence=0.4
            ))
        
        return exceptions
    
    @classmethod
    def parse(cls, text: str) -> List[ExceptionInfo]:
        """Parse stack trace using appropriate language parser."""
        if not text or not text.strip():
            return []
        
        language = cls.detect_language(text)
        
        if language == 'java':
            results = cls.parse_java(text)
        elif language == 'python':
            results = cls.parse_python(text)
        elif language == 'nodejs':
            results = cls.parse_nodejs(text)
        else:
            results = cls.parse_generic(text)
        
        # If no results from specific parser, try generic
        if not results:
            results = cls.parse_generic(text)
        
        return results


# ============================================================
# Log Analysis Agent Implementation
# ============================================================

class LogAnalysisAgent:
    """
    Enhanced Log Analysis Agent for Milestone 2.
    
    Parses stack traces and error logs from multiple languages.
    Extracts structured exception information with file, class, method, line details.
    """

    def __init__(self, llm_service=None):
        self.llm = llm_service
        self.name = "Log Analysis Agent"
        self.version = "2.0.0-M2"
        self.parser = StackTraceParser()

    async def analyze(self, bug_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze logs and stack traces.
        
        Uses deterministic parsing first, then optionally LLM for enrichment.
        Always returns validated Pydantic model output.
        """
        start_time = time.time()
        
        try:
            stack_trace = bug_data.get('stack_trace', '')
            error_logs = bug_data.get('error_logs', '')
            description = bug_data.get('description', '')
            
            # Parse stack traces
            exceptions = []
            if stack_trace:
                exceptions = self.parser.parse(stack_trace)
            
            # Parse error logs if no stack trace exceptions found
            if not exceptions and error_logs:
                exceptions = self.parser.parse(error_logs)
            
            # Extract error patterns
            error_patterns = self._extract_error_patterns(stack_trace, error_logs, description)
            
            # Determine failure point
            failure_point = self._determine_failure_point(exceptions)
            
            # Determine code path
            code_path = self._determine_code_path(exceptions)
            
            # Extract suspicious logs
            suspicious_logs = self._extract_suspicious_logs(error_logs)
            
            # Calculate overall confidence
            confidence = self._calculate_confidence(exceptions, stack_trace, error_logs)
            
            # Generate summary
            summary = self._generate_summary(exceptions, error_patterns, failure_point)
            
            # Build result
            result = LogAnalysisResult(
                exceptions=exceptions,
                error_patterns=error_patterns,
                failure_point=failure_point,
                code_path=code_path,
                stack_trace_summary=self._summarize_stack_trace(stack_trace),
                suspicious_logs=suspicious_logs,
                confidence=confidence,
                summary=summary
            )
            
            # Optionally enrich with LLM
            if self.llm and not getattr(self.llm, 'mock_mode', True) and len(exceptions) == 0:
                try:
                    llm_result = await self._llm_enrich(bug_data, result)
                    if llm_result:
                        result = llm_result
                except Exception as e:
                    logger.warning(f"LLM enrichment failed: {e}")
            
            duration = time.time() - start_time
            logger.info(f"Log Analysis Agent v{self.version} completed in {duration:.2f}s")
            
            output = LogAnalysisAgentOutput(
                result=result,
                duration=duration,
                timestamp=datetime.utcnow().isoformat(),
                status="success"
            )
            
            return output.dict()
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Log Analysis Agent failed: {e}")
            
            # Return fallback result
            fallback = LogAnalysisResult(
                exceptions=[],
                error_patterns=[],
                confidence=0.2,
                summary=f"Analysis failed: {str(e)}. No log data could be parsed."
            )
            
            return LogAnalysisAgentOutput(
                result=fallback,
                duration=duration,
                timestamp=datetime.utcnow().isoformat(),
                status="error",
                error=str(e)
            ).dict()

    def _extract_error_patterns(self, stack_trace: str, error_logs: str, description: str) -> List[str]:
        """Extract common error patterns from all text sources."""
        patterns = []
        all_text = f"{stack_trace} {error_logs} {description}".lower()
        
        pattern_checks = [
            ('Null reference/pointer', ['null', 'nullpointer', 'none', 'undefined', 'nil']),
            ('Resource leak', ['leak', 'not closed', 'not released', 'unclosed']),
            ('Concurrency issue', ['race', 'deadlock', 'concurrent', 'thread', 'sync']),
            ('Timeout', ['timeout', 'timed out', 'deadline']),
            ('Connection failure', ['connection', 'socket', 'network', 'unreachable']),
            ('Permission denied', ['permission', 'denied', 'forbidden', 'unauthorized', 'access']),
            ('Out of memory', ['outofmemory', 'oom', 'heap', 'memory']),
            ('Stack overflow', ['stackoverflow', 'recursion', 'depth']),
            ('Type mismatch', ['typeerror', 'classcast', 'type', 'cast', 'convert']),
            ('Index out of bounds', ['indexoutofbounds', 'arrayindex', 'bounds', 'subscript']),
        ]
        
        for pattern_name, keywords in pattern_checks:
            if any(kw in all_text for kw in keywords):
                patterns.append(pattern_name)
        
        return patterns

    def _determine_failure_point(self, exceptions: List[ExceptionInfo]) -> Optional[str]:
        """Determine the primary failure point from exceptions."""
        if not exceptions:
            return None
        
        # Use the first exception's details
        exc = exceptions[0]
        parts = []
        
        if exc.file_name:
            parts.append(exc.file_name)
        if exc.line_number:
            parts.append(f"line {exc.line_number}")
        if exc.method_name:
            parts.append(f"in {exc.method_name}")
        if exc.class_name:
            parts.append(f"({exc.class_name})")
        
        return ' '.join(parts) if parts else None

    def _determine_code_path(self, exceptions: List[ExceptionInfo]) -> Optional[str]:
        """Determine the code path from exceptions."""
        if not exceptions:
            return None
        
        # Build path from exception details
        exc = exceptions[0]
        if exc.code_path:
            return exc.code_path
        
        # Construct from available parts
        parts = []
        if exc.class_name:
            parts.append(exc.class_name)
        if exc.method_name:
            parts.append(exc.method_name)
        if exc.file_name:
            parts.append(f"({exc.file_name})")
        
        return '.'.join(parts) if parts else None

    def _extract_suspicious_logs(self, error_logs: str) -> List[str]:
        """Extract suspicious log entries."""
        if not error_logs:
            return []
        
        suspicious = []
        lines = error_logs.split('\n')
        
        for line in lines:
            line_lower = line.lower()
            # Check for suspicious keywords
            if any(kw in line_lower for kw in ['error', 'fatal', 'critical', 'exception', 'fail', 'warn']):
                suspicious.append(line.strip())
        
        return suspicious[:10]  # Limit to 10 entries

    def _calculate_confidence(self, exceptions: List[ExceptionInfo], stack_trace: str, error_logs: str) -> float:
        """Calculate overall confidence in the analysis."""
        score = 0.3  # Base
        
        # More exceptions = higher confidence
        if exceptions:
            score += 0.2
            # Average exception confidence
            avg_exc_conf = sum(e.confidence for e in exceptions) / len(exceptions)
            score += avg_exc_conf * 0.2
        
        # Stack trace presence
        if stack_trace and len(stack_trace.strip()) > 50:
            score += 0.15
        
        # Error logs presence
        if error_logs and len(error_logs.strip()) > 50:
            score += 0.1
        
        return min(0.95, score)

    def _summarize_stack_trace(self, stack_trace: str) -> Optional[str]:
        """Generate a summary of the stack trace."""
        if not stack_trace:
            return None
        
        language = self.parser.detect_language(stack_trace)
        lines = [l for l in stack_trace.split('\n') if l.strip()]
        
        summary_parts = [f"Stack trace detected ({language} format)"]
        summary_parts.append(f"Contains {len(lines)} lines")
        
        # Count "at" frames
        if language == 'java':
            at_count = sum(1 for l in lines if l.strip().startswith('at '))
            summary_parts.append(f"{at_count} stack frames")
        elif language == 'python':
            file_count = sum(1 for l in lines if 'File "' in l)
            summary_parts.append(f"{file_count} file references")
        elif language == 'nodejs':
            at_count = sum(1 for l in lines if l.strip().startswith('at '))
            summary_parts.append(f"{at_count} stack frames")
        
        return '. '.join(summary_parts)

    def _generate_summary(self, exceptions: List[ExceptionInfo], patterns: List[str], failure_point: Optional[str]) -> str:
        """Generate human-readable summary."""
        parts = []
        
        if exceptions:
            exc_types = list(set(e.exception_type for e in exceptions))
            parts.append(f"Found {len(exceptions)} exception(s): {', '.join(exc_types[:3])}")
        else:
            parts.append("No structured exceptions detected in logs")
        
        if patterns:
            parts.append(f"Error patterns identified: {', '.join(patterns[:3])}")
        
        if failure_point:
            parts.append(f"Primary failure point: {failure_point}")
        
        return '. '.join(parts) + '.'

    async def _llm_enrich(self, bug_data: Dict, current_result: LogAnalysisResult) -> Optional[LogAnalysisResult]:
        """Use LLM to enrich analysis when parsing fails."""
        prompt = f"""Analyze these logs and stack traces for a software defect.

Stack Trace:
{bug_data.get('stack_trace', 'None provided')}

Error Logs:
{bug_data.get('error_logs', 'None provided')}

Bug Description: {bug_data.get('description', '')}

Current automated analysis found {len(current_result.exceptions)} exceptions.

If you can identify additional exceptions or patterns, provide them.

Respond with JSON:
{{
    "exceptions": [{{"exception_type": "string", "error_message": "string", "file_name": "string", "method_name": "string", "line_number": number, "confidence": 0.0-1.0}}],
    "error_patterns": ["pattern1", "pattern2"],
    "failure_point": "description of where the failure occurs",
    "code_path": "code path to the failure",
    "summary": "overall analysis summary"
}}"""

        try:
            result = await self.llm.generate_json(prompt, "You are a log analysis expert.")
            
            # Merge LLM results with existing
            exceptions = current_result.exceptions.copy()
            for exc_data in result.get('exceptions', []):
                try:
                    exceptions.append(ExceptionInfo(
                        exception_type=exc_data.get('exception_type', 'Unknown'),
                        error_message=exc_data.get('error_message', ''),
                        file_name=exc_data.get('file_name'),
                        method_name=exc_data.get('method_name'),
                        line_number=exc_data.get('line_number'),
                        confidence=float(exc_data.get('confidence', 0.5))
                    ))
                except Exception:
                    pass
            
            return LogAnalysisResult(
                exceptions=exceptions,
                error_patterns=result.get('error_patterns', current_result.error_patterns),
                failure_point=result.get('failure_point', current_result.failure_point),
                code_path=result.get('code_path', current_result.code_path),
                stack_trace_summary=current_result.stack_trace_summary,
                suspicious_logs=current_result.suspicious_logs,
                confidence=max(current_result.confidence, 0.6),
                summary=result.get('summary', current_result.summary)
            )
        except Exception as e:
            logger.warning(f"LLM enrichment failed: {e}")
            return None
