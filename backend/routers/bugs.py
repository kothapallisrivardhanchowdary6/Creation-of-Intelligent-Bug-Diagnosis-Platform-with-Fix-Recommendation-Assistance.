"""Bug report API routes."""

import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel, Field

router = APIRouter(tags=["bugs"])


class BugSubmission(BaseModel):
    title: str = Field(..., min_length=5, max_length=500)
    description: str = Field(..., min_length=10)
    stack_trace: Optional[str] = None
    error_logs: Optional[str] = None
    environment: Optional[str] = None
    files: Optional[list] = None


class BugResponse(BaseModel):
    id: str
    title: str
    description: str
    stack_trace: Optional[str]
    error_logs: Optional[str]
    environment: Optional[str]
    status: str
    created_at: str
    analysis: Optional[dict] = None


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
    """Run AI analysis pipeline on a bug."""
    if bug_id not in bug_store:
        raise HTTPException(status_code=404, detail="Bug not found")

    bug = bug_store[bug_id]
    bug["status"] = "analyzing"

    # In production, this calls the AgentOrchestrator
    # For now, return mock analysis
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
