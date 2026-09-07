"""ChromaDB vector database service."""

import os
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class ChromaService:
    """Manages ChromaDB vector database operations."""

    def __init__(self):
        self.client = None
        self.collection = None
        self.collection_name = "defect_knowledge_base"
        self._initialize()

    def _initialize(self):
        """Initialize ChromaDB client and collection."""
        try:
            import chromadb
            persist_dir = os.getenv("CHROMA_PERSIST_DIR", "./chroma_data")
            self.client = chromadb.PersistentClient(path=persist_dir)
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            logger.info(f"ChromaDB initialized: {self.collection_name}")
        except ImportError:
            logger.warning("ChromaDB not installed. Using mock vector store.")
            self.client = None
            self.collection = None

    def add_documents(self, ids: List[str], documents: List[str],
                      embeddings: List[List[float]], metadatas: List[Dict[str, Any]]):
        """Add documents to the vector store."""
        if self.collection is not None:
            self.collection.add(
                ids=ids,
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas
            )
            logger.info(f"Added {len(ids)} documents to ChromaDB")
        else:
            logger.info(f"[Mock] Would add {len(ids)} documents")

    def search(self, query_embedding: List[float], top_k: int = 5,
               where: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Search for similar documents."""
        if self.collection is not None:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=where if where else None
            )
            # Format results
            formatted = []
            for i in range(len(results['ids'][0])):
                formatted.append({
                    'id': results['ids'][0][i],
                    'document': results['documents'][0][i] if results.get('documents') else '',
                    'metadata': results['metadatas'][0][i] if results.get('metadatas') else {},
                    'distance': results['distances'][0][i] if results.get('distances') else 0,
                    'score': 1 - (results['distances'][0][i] if results.get('distances') else 0)
                })
            return formatted
        else:
            # Mock search results
            return self._mock_search(top_k)

    def _mock_search(self, top_k: int) -> List[Dict[str, Any]]:
        """Return mock search results for development."""
        mock_results = [
            {"id": "MOZ-1001", "document": "NullPointerException in NetworkManager", "metadata": {"project": "Mozilla", "severity": "critical"}, "score": 0.89},
            {"id": "APC-2003", "document": "Buffer overflow in HTTP header parsing", "metadata": {"project": "Apache", "severity": "critical"}, "score": 0.82},
            {"id": "ECL-3003", "document": "IndexOutOfBoundsException in code completion", "metadata": {"project": "Eclipse", "severity": "medium"}, "score": 0.75},
            {"id": "MOZ-1002", "document": "Memory leak in tab rendering engine", "metadata": {"project": "Mozilla", "severity": "high"}, "score": 0.71},
            {"id": "APC-2002", "document": "Race condition in thread pool", "metadata": {"project": "Apache", "severity": "critical"}, "score": 0.68},
        ]
        return mock_results[:top_k]

    def get_status(self) -> Dict[str, Any]:
        """Get collection status."""
        if self.collection is not None:
            count = self.collection.count()
            return {
                "total_documents": count,
                "collection_name": self.collection_name,
                "status": "ready"
            }
        return {
            "total_documents": 12,
            "collection_name": self.collection_name,
            "status": "mock"
        }

    def delete_collection(self):
        """Delete the collection."""
        if self.client is not None:
            self.client.delete_collection(self.collection_name)
            self.collection = None
