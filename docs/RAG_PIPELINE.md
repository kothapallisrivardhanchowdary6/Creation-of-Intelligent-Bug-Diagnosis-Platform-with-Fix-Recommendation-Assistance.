# RAG Pipeline Documentation

## What is RAG?

Retrieval-Augmented Generation (RAG) combines information retrieval with large language model generation. Instead of relying solely on the model's training data, RAG retrieves relevant documents from a knowledge base and provides them as context for generating responses.

## Pipeline Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    INGESTION PHASE                        │
│                                                          │
│  Raw Data → Cleaning → Normalization → Semantic Chunking │
│           → Metadata Extraction → Embedding Generation   │
│           → ChromaDB Indexing                            │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│                   RETRIEVAL PHASE                        │
│                                                          │
│  Query → Query Embedding → ChromaDB Vector Search       │
│        → Top-K Results → Cosine Similarity Scoring      │
│        → Metadata Filtering → Context Assembly          │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│                  GENERATION PHASE                        │
│                                                          │
│  Retrieved Context + Original Query → LLM Prompt        │
│  → Structured Analysis → JSON Response                  │
└─────────────────────────────────────────────────────────┘
```

## Embeddings

### Model: sentence-transformers/all-MiniLM-L6-v2

- **Dimensions**: 384
- **Type**: Dense vector embedding
- **Training**: Trained on 1 billion+ sentence pairs
- **Performance**: Fast inference, good quality for semantic search
- **Use Case**: Converting bug descriptions to comparable vectors

### How Embeddings Work

1. Text input → Tokenization → Transformer layers → Pooling → 384-dim vector
2. Similar texts produce vectors that are close in vector space
3. Distance/similarity between vectors indicates semantic relatedness

## Cosine Similarity

```
cosine_similarity(A, B) = (A · B) / (||A|| × ||B||)
```

- **Range**: -1 (opposite) to 1 (identical)
- **0**: Orthogonal (unrelated)
- **> 0.7**: High similarity
- **> 0.85**: Very likely related/duplicate

## Semantic Chunking Strategy

Instead of fixed-size chunks, we use semantic chunking:

1. **Title chunk**: Bug title (high signal)
2. **Description chunk**: Full description (context)
3. **Stack trace chunk**: Error traces (technical detail)
4. **Resolution chunk**: How it was fixed (remediation context)

Each chunk gets its own embedding with metadata linking back to the source bug.

## Vector Metadata

Each vector in ChromaDB stores:

```json
{
  "bug_id": "MOZ-1001",
  "project": "Mozilla Firefox",
  "component": "Networking",
  "severity": "critical",
  "section": "description",
  "resolution": "Added null check in retry handler"
}
```

This metadata enables:
- Filtering by project/component/severity
- Context-aware retrieval
- Source attribution

## Top-K Retrieval

1. Query is embedded using the same model
2. ChromaDB performs approximate nearest neighbor search
3. Returns top-K most similar vectors
4. Results are scored by cosine similarity
5. Metadata is used for filtering and context

## Performance Characteristics

| Metric | Value |
|--------|-------|
| Embedding latency | ~10ms per text |
| Search latency | ~5ms for 10K vectors |
| Index build time | ~2s for 1000 documents |
| Memory usage | ~15MB per 1000 vectors |
