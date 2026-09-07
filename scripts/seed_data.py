"""
Seed script for loading historical defect data into ChromaDB.
"""

import os
import sys
import csv
import json
import logging

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_csv(filepath: str) -> list:
    """Load defects from CSV file."""
    defects = []
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            defects.append(row)
    logger.info(f"Loaded {len(defects)} defects from {filepath}")
    return defects


def chunk_defect(defect: dict) -> list:
    """Split a defect into semantic chunks."""
    chunks = []
    bug_id = defect.get('bug_id', 'unknown')
    project = defect.get('project', 'Unknown')
    component = defect.get('component', 'Unknown')
    severity = defect.get('severity', 'unknown')

    # Title chunk
    chunks.append({
        'id': f"{bug_id}-title",
        'text': defect.get('title', ''),
        'metadata': {
            'bug_id': bug_id,
            'project': project,
            'component': component,
            'severity': severity,
            'section': 'title'
        }
    })

    # Description chunk
    chunks.append({
        'id': f"{bug_id}-description",
        'text': defect.get('description', ''),
        'metadata': {
            'bug_id': bug_id,
            'project': project,
            'component': component,
            'severity': severity,
            'section': 'description'
        }
    })

    # Resolution chunk
    if defect.get('resolution'):
        chunks.append({
            'id': f"{bug_id}-resolution",
            'text': defect.get('resolution', ''),
            'metadata': {
                'bug_id': bug_id,
                'project': project,
                'component': component,
                'severity': severity,
                'section': 'resolution',
                'resolution': defect.get('resolution', '')
            }
        })

    return chunks


def seed_data(data_path: str = None):
    """Seed the knowledge base with historical defect data."""
    if data_path is None:
        data_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'historical_defects.csv')

    logger.info(f"Seeding data from: {data_path}")

    # Load data
    defects = load_csv(data_path)

    # Chunk defects
    all_chunks = []
    for defect in defects:
        chunks = chunk_defect(defect)
        all_chunks.extend(chunks)

    logger.info(f"Created {len(all_chunks)} chunks from {len(defects)} defects")

    # Try to use real services, fall back to mock
    try:
        from services.embedding_service import EmbeddingService
        from services.chroma_service import ChromaService

        embedding_service = EmbeddingService()
        chroma_service = ChromaService()

        # Generate embeddings
        texts = [c['text'] for c in all_chunks]
        embeddings = embedding_service.embed_batch(texts)

        # Index in ChromaDB
        ids = [c['id'] for c in all_chunks]
        documents = [c['text'] for c in all_chunks]
        metadatas = [c['metadata'] for c in all_chunks]

        chroma_service.add_documents(ids, documents, embeddings, metadatas)
        logger.info("Successfully indexed all chunks in ChromaDB")

    except ImportError:
        logger.warning("Services not available. Data would be indexed as:")
        for chunk in all_chunks[:3]:
            logger.info(f"  {chunk['id']}: {chunk['text'][:50]}...")
        logger.info(f"  ... and {len(all_chunks) - 3} more chunks")

    return len(all_chunks)


if __name__ == "__main__":
    count = seed_data()
    print(f"\nSeeding complete! {count} chunks indexed.")
