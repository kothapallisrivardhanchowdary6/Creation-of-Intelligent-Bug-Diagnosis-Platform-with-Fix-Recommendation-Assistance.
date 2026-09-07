"""Search API routes."""

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(tags=["search"])


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)


@router.post("/search")
async def search_knowledge_base(request: SearchRequest):
    """Semantic search across the knowledge base."""
    # In production, this uses ChromaDB + embeddings
    # Mock results for demo
    from services.mock_search import mock_search
    results = mock_search(request.query, request.top_k)
    return {"query": request.query, "results": results, "total": len(results)}
