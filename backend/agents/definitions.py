"""
AI Agent definitions — backward-compatibility shim.

Milestone 3: The real implementations now live in dedicated modules:
  - agents/triage_agent.py
  - agents/log_analysis_agent.py
  - agents/root_cause_agent.py
  - agents/duplicate_detection_agent.py
  - agents/remediation_agent.py

This file is kept for any legacy code that imports from agents.definitions.
All class names are re-exported from the real modules.
"""

import logging

# Re-export M3 implementations under the original names
from agents.triage_agent import TriageAgent          # noqa: F401
from agents.log_analysis_agent import LogAnalysisAgent  # noqa: F401
from agents.root_cause_agent import RootCauseAgent      # noqa: F401
from agents.duplicate_detection_agent import DuplicateDetectionAgent  # noqa: F401
from agents.remediation_agent import RemediationAgent   # noqa: F401

logger = logging.getLogger(__name__)
logger.debug("agents.definitions: re-exporting M3 agent implementations")

__all__ = [
    "TriageAgent",
    "LogAnalysisAgent",
    "RootCauseAgent",
    "DuplicateDetectionAgent",
    "RemediationAgent",
]
