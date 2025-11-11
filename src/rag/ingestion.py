"""
Document ingestion pipeline for D&D RAG system.

This module handles:
- Loading D&D documents (rules, monsters, adventures)
- Parsing and chunking documents
- Generating embeddings
- Storing in Qdrant vector collections
"""

import os
from pathlib import Path

from datapizza.core.vectorstore import VectorConfig
from datapizza.embedders import ChunkEmbedder
from datapizza.embedders.openai import OpenAIEmbedder
from datapizza.modules.parsers import TextParser
from datapizza.modules.splitters import NodeSplitter
from datapizza.pipeline import IngestionPipeline
from datapizza.vectorstores.qdrant import QdrantVectorstore

from src.config import (
    COLLECTION_ADVENTURE,
    COLLECTION_MONSTERS,
    COLLECTION_RULES,
    EMBEDDING_MODEL,
    OPENAI_API_KEY,
    QDRANT_LOCATION,
)


def create_vectorstore() -> QdrantVectorstore:
    """
    Create and initialize Qdrant vectorstore.

    Returns:
        QdrantVectorstore: Configured vectorstore instance
    """
    print("📦 Initializing Qdrant vectorstore...")
    vectorstore = QdrantVectorstore(location=QDRANT_LOCATION)

    # Create 3 collections for different document types
    collections = [
        (COLLECTION_RULES, "Rules accessible to all agents"),
        (COLLECTION_MONSTERS, "Monster stats (DM only)"),
        (COLLECTION_ADVENTURE, "Adventure narrative (DM only)"),
    ]

    for collection_name, description in collections:
        try:
            # Check if collection exists, if not create it
            vectorstore.create_collection(
                collection_name,
                vector_config=[VectorConfig(name="embedding", dimensions=1536)]
            )
            print(f"  ✅ Created collection: {collection_name} ({description})")
        except Exception as e:
            # Collection might already exist
            print(f"  ℹ️  Collection {collection_name} already exists or error: {e}")

    return vectorstore


def create_ingestion_pipeline(
    vectorstore: QdrantVectorstore,
    collection_name: str,
    chunk_size: int = 1000
) -> IngestionPipeline:
    """
    Create an ingestion pipeline for processing documents.

    Args:
        vectorstore: Qdrant vectorstore instance
        collection_name: Target collection for ingestion
        chunk_size: Maximum characters per chunk (default: 1000)

    Returns:
        IngestionPipeline: Configured pipeline instance
    """
    # Create embedder
    embedder = ChunkEmbedder(
        client=OpenAIEmbedder(
            api_key=OPENAI_API_KEY,
            model_name=EMBEDDING_MODEL
        ),
        embedding_name="embedding"  # Must match VectorConfig name
    )

    # Create ingestion pipeline
    pipeline = IngestionPipeline(
        modules=[
            TextParser(),                    # Parse text into hierarchical nodes
            NodeSplitter(max_char=chunk_size),  # Split into manageable chunks
            embedder,                         # Generate embeddings
        ],
        vector_store=vectorstore,
        collection_name=collection_name
    )

    return pipeline


def ingest_document(
    file_path: str,
    vectorstore: QdrantVectorstore,
    collection_name: str,
    metadata: dict,
    chunk_size: int = 1000
) -> None:
    """
    Ingest a single document into the vectorstore.

    Args:
        file_path: Path to document file
        vectorstore: Qdrant vectorstore instance
        collection_name: Target collection
        metadata: Document metadata
        chunk_size: Maximum characters per chunk
    """
    # Read file content
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Create pipeline for this collection
    pipeline = create_ingestion_pipeline(vectorstore, collection_name, chunk_size)

    # Ingest document
    print(f"  📄 Ingesting: {Path(file_path).name}")
    print(f"     Collection: {collection_name}")
    print(f"     Size: {len(content)} characters")

    # Run ingestion
    pipeline.run(content, metadata=metadata)

    # Get collection stats
    try:
        info = vectorstore.client.get_collection(collection_name)
        print(f"     ✅ Ingested successfully. Total vectors in collection: {info.vectors_count}")
    except Exception as e:
        print(f"     ⚠️  Could not get collection stats: {e}")


def ingest_documents(
    documents_dir: str = "data/documents",
    chunk_size: int = 1000
) -> QdrantVectorstore:
    """
    Ingest all D&D documents into the RAG system.

    Args:
        documents_dir: Directory containing D&D documents
        chunk_size: Maximum characters per chunk (default: 1000)

    Returns:
        QdrantVectorstore: Populated vectorstore instance
    """
    print("\n" + "="*60)
    print("🎲 D&D RAG SYSTEM - DOCUMENT INGESTION")
    print("="*60 + "\n")

    # Validate API key
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY not found in environment variables")

    # Create vectorstore and collections
    vectorstore = create_vectorstore()

    # Define documents to ingest
    documents = [
        {
            "file": "dnd_basic_rules.md",
            "collection": COLLECTION_RULES,
            "metadata": {
                "source": "D&D 5e Basic Rules",
                "type": "rules",
                "access": "all",
                "description": "Core D&D 5e mechanics and rules"
            }
        },
        {
            "file": "monsters.md",
            "collection": COLLECTION_MONSTERS,
            "metadata": {
                "source": "Monster Stat Blocks",
                "type": "monsters",
                "access": "dm_only",
                "description": "Monster statistics and abilities"
            }
        },
        {
            "file": "starter_adventure.md",
            "collection": COLLECTION_ADVENTURE,
            "metadata": {
                "source": "The Forgotten Crypt",
                "type": "narrative",
                "access": "dm_only",
                "description": "Level 1 adventure for 3-5 players"
            }
        }
    ]

    print(f"📂 Document directory: {documents_dir}\n")

    # Ingest each document
    for doc_info in documents:
        file_path = os.path.join(documents_dir, doc_info["file"])

        if not os.path.exists(file_path):
            print(f"  ⚠️  File not found: {file_path}")
            continue

        try:
            ingest_document(
                file_path=file_path,
                vectorstore=vectorstore,
                collection_name=doc_info["collection"],
                metadata=doc_info["metadata"],
                chunk_size=chunk_size
            )
            print()
        except Exception as e:
            print(f"  ❌ Error ingesting {doc_info['file']}: {e}\n")

    # Print summary
    print("="*60)
    print("📊 INGESTION SUMMARY")
    print("="*60)

    for collection in [COLLECTION_RULES, COLLECTION_MONSTERS, COLLECTION_ADVENTURE]:
        try:
            info = vectorstore.client.get_collection(collection)
            print(f"  {collection}: {info.vectors_count} chunks")
        except Exception as e:
            print(f"  {collection}: Error retrieving stats - {e}")

    print("\n✅ Document ingestion complete!\n")

    return vectorstore


if __name__ == "__main__":
    # Run ingestion when script is executed directly
    vectorstore = ingest_documents()
