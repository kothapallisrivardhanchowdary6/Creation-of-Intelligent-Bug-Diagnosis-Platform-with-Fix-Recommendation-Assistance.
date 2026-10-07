"""
Bug report API routes — Milestone 3 integration.

POST /api/bugs/{id}/analyze now runs the full M3 pipeline:
  Triage → Log Analysis → Root Cause → Duplicate Detection → Remediation

All services (LLM, ChromaDB, Embeddings) are injected into the orchestrator
so M3 agents can do real RAG-based analysis.
"""

import uuid
import logging
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel, Field

from agents.orchestrator import AgentOrchestrator
from services.llm_service import LLMService
from services.chroma_service import ChromaService
from services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["bugs"])


class BugSubmission(BaseModel):
    title: str = Field(..., min_length=5, max_length=500)
    description: str = Field(..., min_length=10)
    stack_trace: Optional[str] = None
    error_logs: Optional[str] = None
    environment: Optional[str] = None
    files: Optional[list] = None


# ── Singleton services (shared across requests) ────────────────────────────────
_llm_service: Optional[LLMService] = None
_chroma_service: Optional[ChromaService] = None
_embedding_service: Optional[EmbeddingService] = None
_orchestrator: Optional[AgentOrchestrator] = None


def get_llm_service() -> LLMService:
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service


def get_chroma_service() -> ChromaService:
    global _chroma_service
    if _chroma_service is None:
        _chroma_service = ChromaService()
    return _chroma_service


def get_embedding_service() -> EmbeddingService:
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service


def get_orchestrator() -> AgentOrchestrator:
    """
    Return the singleton orchestrator, fully wired with all M3 services.
    Services are initialized lazily and shared across requests.
    """
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = AgentOrchestrator(
            llm_service=get_llm_service(),
            chroma_service=get_chroma_service(),
            embedding_service=get_embedding_service(),
        )
        logger.info("AgentOrchestrator (M3) initialized with LLM + ChromaDB + Embeddings")
    return _orchestrator


# ── In-memory bug store (demo; production should use PostgreSQL) ───────────────
bug_store: dict = {}


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
        "analysis": None,
    }
    bug_store[bug_id] = bug
    logger.info(f"Bug submitted: {bug_id}")
    return bug


@router.post("/bugs/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload a file attachment."""
    content = await file.read()
    return {
        "name": file.filename,
        "content": content.decode("utf-8", errors="replace"),
        "size": len(content),
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
    Run the full M3 AI analysis pipeline on a submitted bug.

    Pipeline steps (M3):
      1. Triage Agent         — severity, priority, component, category
      2. Log Analysis Agent   — exception parsing, failure point, code path
      3. Root Cause Agent     — RAG + LLM hypothesis generation
      4. Duplicate Detection  — real embedding similarity search
      5. Remediation Agent    — RAG-grounded actionable fix suggestions

    All results are returned in a single structured response.
    Results are specific to the bug being analyzed — no hardcoded values.
    """
    if bug_id not in bug_store:
        raise HTTPException(status_code=404, detail="Bug not found")

    bug = bug_store[bug_id]
    bug["status"] = "analyzing"
    logger.info(f"Starting M3 analysis for bug: {bug_id}")

    try:
        orchestrator = get_orchestrator()
        analysis = await orchestrator.run_m3_pipeline(bug)

        bug["status"] = "analyzed"
        bug["analysis"] = analysis
        logger.info(f"M3 analysis completed for bug: {bug_id}")
        return analysis

    except Exception as e:
        logger.error(f"M3 analysis failed for bug {bug_id}: {e}", exc_info=True)
        bug["status"] = "error"
        bug["error"] = str(e)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.get("/bugs/{bug_id}/analysis")
async def get_analysis(bug_id: str):
    """Get analysis results for a bug."""
    if bug_id not in bug_store:
        raise HTTPException(status_code=404, detail="Bug not found")
    bug = bug_store[bug_id]
    if not bug.get("analysis"):
        raise HTTPException(
            status_code=404,
            detail="No analysis found. Submit and run analysis first.",
        )
    return bug["analysis"]


@router.delete("/bugs/{bug_id}")
async def delete_bug(bug_id: str):
    """Delete a bug report."""
    if bug_id not in bug_store:
        raise HTTPException(status_code=404, detail="Bug not found")
    del bug_store[bug_id]
    return {"status": "deleted", "id": bug_id}
