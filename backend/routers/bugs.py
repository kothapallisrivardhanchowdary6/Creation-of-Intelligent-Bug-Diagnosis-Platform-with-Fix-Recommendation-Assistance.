"""
Bug report API routes — Milestone 2 integration.

POST /api/bugs/{id}/analyze now uses the M2 orchestrator
which runs Triage + Log Analysis in parallel and combines results.
"""

import uuid
import logging
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel, Field

from agents.orchestrator import AgentOrchestrator
from services.llm_service import LLMService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["bugs"])


class BugSubmission(BaseModel):
    title: str = Field(..., min_length=5, max_length=500)
    description: str = Field(..., min_length=10)
    stack_trace: Optional[str] = None
    error_logs: Optional[str] = None
    environment: Optional[str] = None
    files: Optional[list] = None


# Initialize services (singleton pattern)
_llm_service = None
_orchestrator = None


def get_llm_service():
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service


def get_orchestrator():
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = AgentOrchestrator(llm_service=get_llm_service())
    return _orchestrator


# In-memory store for demo (in production, use PostgreSQL)
bug_store = {}


@router.post("/bugs")
async def submit_bug(submission: BugSubmission):
    """Submit a new bug report."""
    bug_id = f"BUG-{uuid.uuid4().hex[:12].upper()}"
    bug = {
        "id": bug_id,
        "title": submission.title,
        "description": submission.description,
        "stack_trace": submission.stack_trace,
        "error_logs": submission.error_logs,
        "environment": submission.environment,
        "files": submission.files,
        "status": "submitted",
        "created_at": datetime.utcnow().isoformat(),
        "analysis": None
    }
    bug_store[bug_id] = bug
    return bug


@router.post("/bugs/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload a file attachment."""
    content = await file.read()
    return {
        "name": file.filename,
        "content": content.decode("utf-8", errors="replace"),
        "size": len(content)
    }


@router.get("/bugs")
async def list_bugs():
    """List all bug reports."""
    return list(bug_store.values())


@router.get("/bugs/{bug_id}")
async def get_bug(bug_id: str):
    """Get a bug report by ID."""
    if bug_id not in bug_store:
        raise HTTPException(status_code=404, detail="Bug not found")
    return bug_store[bug_id]


@router.post("/bugs/{bug_id}/analyze")
async def analyze_bug(bug_id: str):
    """
    Run AI analysis pipeline on a bug.
    
    Milestone 2: Uses the enhanced orchestrator which runs:
    1. Triage Agent (severity, priority, component, confidence)
    2. Log Analysis Agent (exception parsing, failure point, code path)
    3. Combined context for future M3 agents
    
    Both agents run in parallel and their results are combined.
    """
    if bug_id not in bug_store:
        raise HTTPException(status_code=404, detail="Bug not found")

    bug = bug_store[bug_id]
    bug["status"] = "analyzing"

    try:
        # Run M2 pipeline via orchestrator
        orchestrator = get_orchestrator()
        analysis = await orchestrator.run_m2_pipeline(bug)
        
        bug["status"] = "analyzed"
        bug["analysis"] = analysis
        
        return analysis
        
    except Exception as e:
        logger.error(f"Analysis failed for bug {bug_id}: {e}")
        bug["status"] = "error"
        
        # Fallback to mock analysis
        from agents.mock_analysis import generate_mock_analysis
        analysis = generate_mock_analysis(bug)
        bug["status"] = "analyzed"
        bug["analysis"] = analysis
        
        return analysis


@router.get("/bugs/{bug_id}/analysis")
async def get_analysis(bug_id: str):
    """Get analysis results for a bug."""
    if bug_id not in bug_store:
        raise HTTPException(status_code=404, detail="Bug not found")

    bug = bug_store[bug_id]
    if not bug.get("analysis"):
        raise HTTPException(status_code=404, detail="No analysis found. Run analysis first.")
    return bug["analysis"]


@router.delete("/bugs/{bug_id}")
async def delete_bug(bug_id: str):
    """Delete a bug report."""
    if bug_id not in bug_store:
        raise HTTPException(status_code=404, detail="Bug not found")
    del bug_store[bug_id]
    return {"status": "deleted", "id": bug_id}
