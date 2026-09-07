"""
AI-Based Software Defect Analysis System — Backend
FastAPI application with agent orchestration, RAG pipeline, and vector search.
"""

import os
import uuid
import logging
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import modules
from database.connection import init_db, get_session
from database.models import BugReport, AnalysisResult
from services.embedding_service import EmbeddingService
from services.chroma_service import ChromaService
from services.llm_service import LLMService
from agents.orchestrator import AgentOrchestrator
from routers.bugs import router as bugs_router
from routers.search import router as search_router
from routers.knowledge import router as knowledge_router

# ============================================================
# Pydantic Models
# ============================================================

class BugSubmission(BaseModel):
    title: str = Field(..., min_length=5, max_length=500)
    description: str = Field(..., min_length=10)
    stack_trace: Optional[str] = None
    error_logs: Optional[str] = None
    environment: Optional[str] = None
    files: Optional[List[Dict[str, Any]]] = None

class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)

class HealthResponse(BaseModel):
    status: str
    version: str
    services: Dict[str, str]
    uptime: str

# ============================================================
# Application
# ============================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management."""
    logger.info("Starting AI Defect Analysis System...")
    await init_db()
    logger.info("Database initialized")
    
    # Initialize services
    embedding_service = EmbeddingService()
    chroma_service = ChromaService()
    llm_service = LLMService()
    
    logger.info("Services initialized")
    yield
    logger.info("Shutting down...")

app = FastAPI(
    title="AI Defect Analysis System",
    description="Milestone 1: Foundation & Bug Understanding",
    version="1.0.0-M1",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(bugs_router, prefix="/api")
app.include_router(search_router, prefix="/api")
app.include_router(knowledge_router, prefix="/api")

@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        version="1.0.0-M1",
        services={
            "api": "running",
            "database": "connected",
            "chromadb": "ready",
            "embeddings": "loaded",
            "llm": os.getenv("LLM_MODE", "mock")
        },
        uptime="N/A"
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
