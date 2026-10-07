"""ChromaDB vector database service."""

import os
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class ChromaService:
    """Manages ChromaDB vector database operations."""

    # In-memory store used only when ChromaDB is not installed (mock mode).
    # Keyed by document ID → {id, document, metadata}.
    _mock_store: dict = {}

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
            # Mock mode — persist in the class-level dict so verify/get work
            for i, doc_id in enumerate(ids):
                ChromaService._mock_store[doc_id] = {
                    "id": doc_id,
                    "document": documents[i] if i < len(documents) else "",
                    "metadata": metadatas[i] if i < len(metadatas) else {},
                }
            logger.info(f"[Mock] Stored {len(ids)} documents in mock store")

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

    def get_all_documents(self, limit: int = 500) -> List[Dict[str, Any]]:
        """
        Retrieve all documents from the collection (up to `limit`).
        Used by analytics and cluster endpoints.
        Returns list of {id, document, metadata}.
        """
        if self.collection is not None:
            try:
                result = self.collection.get(
                    limit=limit,
                    include=["documents", "metadatas"],
                )
                docs = []
                ids = result.get("ids") or []
                documents = result.get("documents") or []
                metadatas = result.get("metadatas") or []
                for i, doc_id in enumerate(ids):
                    docs.append({
                        "id": doc_id,
                        "document": documents[i] if i < len(documents) else "",
                        "metadata": metadatas[i] if i < len(metadatas) else {},
                    })
                logger.info(f"Retrieved {len(docs)} documents from ChromaDB")
                return docs
            except Exception as e:
                logger.error(f"get_all_documents failed: {e}", exc_info=True)
                return []
        else:
            # Return mock documents for development
            return [
                {"id": "MOZ-1001", "document": "NullPointerException in NetworkManager when connection drops during file download", "metadata": {"project": "Mozilla Firefox", "component": "Networking", "severity": "critical", "resolution": "Fixed by adding null check before accessing connection object"}},
                {"id": "MOZ-1002", "document": "Memory leak in tab rendering engine when switching tabs rapidly", "metadata": {"project": "Mozilla Firefox", "component": "Layout Engine", "severity": "high", "resolution": "Implemented proper cleanup of render contexts"}},
                {"id": "MOZ-1003", "document": "Segmentation fault in WebGL renderer with unsupported shader operations", "metadata": {"project": "Mozilla Firefox", "component": "Graphics", "severity": "high", "resolution": "Added shader capability validation"}},
                {"id": "APC-2001", "document": "StackOverflowError in recursive XML parser with deeply nested elements", "metadata": {"project": "Apache HTTP Server", "component": "Core", "severity": "critical", "resolution": "Converted recursive parser to iterative approach"}},
                {"id": "APC-2002", "document": "Race condition in thread pool causing deadlock under high concurrency", "metadata": {"project": "Apache Tomcat", "component": "Thread Pool", "severity": "critical", "resolution": "Added proper lock ordering and timeout mechanism"}},
                {"id": "APC-2003", "document": "Buffer overflow in HTTP header parsing with malformed Content-Type", "metadata": {"project": "Apache HTTP Server", "component": "HTTP Parser", "severity": "critical", "resolution": "Implemented bounds checking and input validation"}},
                {"id": "APC-2004", "document": "Connection leak in connection pool when exception occurs during checkout", "metadata": {"project": "Apache Tomcat", "component": "Connection Pool", "severity": "high", "resolution": "Added try-finally block to ensure connection return"}},
                {"id": "ECL-3001", "document": "ClassCastException when refactoring generic types in JDT compiler", "metadata": {"project": "Eclipse JDT", "component": "Compiler", "severity": "medium", "resolution": "Added type erasure handling in generic type resolution"}},
                {"id": "ECL-3002", "document": "UI freeze when opening large workspace with 500+ projects", "metadata": {"project": "Eclipse Platform", "component": "UI Framework", "severity": "high", "resolution": "Moved workspace loading to background thread"}},
                {"id": "ECL-3003", "document": "IndexOutOfBoundsException in code completion with partial token matching", "metadata": {"project": "Eclipse JDT", "component": "Content Assist", "severity": "medium", "resolution": "Added boundary checks in token matching algorithm"}},
                {"id": "ECL-3004", "document": "Deadlock in plugin activation when circular dependencies exist", "metadata": {"project": "Eclipse Platform", "component": "Plugin Framework", "severity": "critical", "resolution": "Implemented dependency graph cycle detection"}},
                {"id": "MOZ-1004", "document": "CSS Grid layout miscalculation with auto-fit and minmax constraints", "metadata": {"project": "Mozilla Firefox", "component": "CSS Engine", "severity": "medium", "resolution": "Fixed constraint solving algorithm for auto-fit tracks"}},
            ]

    def get_document_by_id(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a single document by ID."""
        if self.collection is not None:
            try:
                result = self.collection.get(
                    ids=[doc_id],
                    include=["documents", "metadatas"],
                )
                ids = result.get("ids") or []
                if ids:
                    return {
                        "id": ids[0],
                        "document": (result.get("documents") or [""])[0],
                        "metadata": (result.get("metadatas") or [{}])[0],
                    }
                return None
            except Exception as e:
                logger.error(f"get_document_by_id failed for {doc_id}: {e}")
                return None
        # Mock mode — check the in-memory store first, then static list
        if doc_id in ChromaService._mock_store:
            return ChromaService._mock_store[doc_id]
        return None

    def document_exists(self, doc_id: str) -> bool:
        """Check if a document with the given ID already exists."""
        if self.collection is not None:
            try:
                result = self.collection.get(ids=[doc_id])
                return len(result.get("ids") or []) > 0
            except Exception:
                return False
        # Mock mode
        return doc_id in ChromaService._mock_store

    def delete_collection(self):
        """Delete the collection."""
        if self.client is not None:
            self.client.delete_collection(self.collection_name)
            self.collection = None
