"""
Retrieval pipeline for D&D RAG system.

This module handles:
- Query rewriting for better retrieval
- Vector similarity search
- Context-aware response generation
"""

from typing import Optional

from datapizza.clients.openai_like import OpenAILikeClient
from datapizza.embedders.openai import OpenAIEmbedder
from datapizza.modules.prompt import ChatPromptTemplate
from datapizza.modules.rewriters import ToolRewriter
from datapizza.pipeline import DagPipeline
from datapizza.tools import tool
from datapizza.vectorstores.qdrant import QdrantVectorstore

from src.config import (
    COLLECTION_ADVENTURE,
    COLLECTION_MONSTERS,
    COLLECTION_RULES,
    EMBEDDING_MODEL,
    GROQ_API_KEY,
    GROQ_MODEL,
    OPENAI_API_KEY,
    QDRANT_LOCATION,
)


# Global pipeline instance (initialized on first use)
_retrieval_pipeline: Optional[DagPipeline] = None
_vectorstore: Optional[QdrantVectorstore] = None


def initialize_retrieval_pipeline(vectorstore: Optional[QdrantVectorstore] = None) -> tuple[DagPipeline, QdrantVectorstore]:
    """
    Initialize the RAG retrieval pipeline with query rewriting.

    Args:
        vectorstore: Optional existing vectorstore to reuse (for in-memory mode)

    Returns:
        tuple: (DagPipeline, QdrantVectorstore) instances
    """
    print("🔧 Initializing RAG retrieval pipeline...")

    # Create Groq client for fast inference (using OpenAI-like API)
    groq_client = OpenAILikeClient(
        api_key=GROQ_API_KEY,
        model=GROQ_MODEL,
        base_url="https://api.groq.com/openai/v1",
        temperature=0.7
    )

    # Create OpenAI embedder
    embedder = OpenAIEmbedder(
        api_key=OPENAI_API_KEY,
        model_name=EMBEDDING_MODEL
    )

    # Use provided vectorstore or create new one
    if vectorstore is None:
        vectorstore = QdrantVectorstore(location=QDRANT_LOCATION)

    # Create DAG pipeline
    dag_pipeline = DagPipeline()

    # Module 1: Query Rewriter (improves retrieval quality)
    # NOTE: ToolRewriter disabled due to Groq trying to call non-existent tools
    # Instead, we'll use direct embedding of the original query
    # dag_pipeline.add_module(
    #     "rewriter",
    #     ToolRewriter(
    #         client=groq_client,
    #         system_prompt=(
    #             "You are a D&D 5e expert. Rewrite user queries to improve retrieval of D&D rules, "
    #             "monsters, and adventure content. Expand abbreviations, add relevant keywords, "
    #             "and clarify ambiguous terms. Keep queries concise but comprehensive."
    #         )
    #     )
    # )

    # Module 2: Embedder (convert query to vector)
    dag_pipeline.add_module("embedder", embedder)

    # Module 3: Retriever (search vectorstore)
    dag_pipeline.add_module("retriever", vectorstore)

    # Module 4: Prompt Builder (format context for LLM)
    dag_pipeline.add_module(
        "prompt",
        ChatPromptTemplate(
            user_prompt_template="Question: {{user_prompt}}",
            retrieval_prompt_template=(
                "Context from D&D documents:\n"
                "{% for chunk in chunks %}"
                "---\n"
                "{{ chunk.text }}\n"
                "{% endfor %}"
                "---\n\n"
                "Answer the question using ONLY the information provided in the context above. "
                "If the context doesn't contain enough information, say so. "
                "Be concise and accurate. Cite specific rules or stat blocks when relevant."
            )
        )
    )

    # Module 5: Generator (produce final answer)
    dag_pipeline.add_module("generator", groq_client)

    # Connect modules in the pipeline
    # dag_pipeline.connect("rewriter", "embedder", target_key="text")  # Rewriter disabled
    dag_pipeline.connect("embedder", "retriever", target_key="query_vector")
    dag_pipeline.connect("retriever", "prompt", target_key="chunks")
    dag_pipeline.connect("prompt", "generator", target_key="memory")

    print("  ✅ Pipeline initialized successfully\n")

    return dag_pipeline, vectorstore


def get_retrieval_pipeline(vectorstore: Optional[QdrantVectorstore] = None) -> tuple[DagPipeline, QdrantVectorstore]:
    """
    Get or create the retrieval pipeline (singleton pattern).

    Args:
        vectorstore: Optional existing vectorstore to reuse

    Returns:
        tuple: (DagPipeline, QdrantVectorstore) instances
    """
    global _retrieval_pipeline, _vectorstore

    # If vectorstore is provided, reinitialize with that vectorstore
    if vectorstore is not None:
        _retrieval_pipeline, _vectorstore = initialize_retrieval_pipeline(vectorstore)
    elif _retrieval_pipeline is None or _vectorstore is None:
        _retrieval_pipeline, _vectorstore = initialize_retrieval_pipeline()

    return _retrieval_pipeline, _vectorstore


def query_rag(
    query: str,
    collection_name: str = COLLECTION_RULES,
    k: int = 3,
    use_rewriter: bool = True,
    verbose: bool = False,
    vectorstore: Optional[QdrantVectorstore] = None
) -> str:
    """
    Query the RAG system for D&D information.

    Args:
        query: User question or search query
        collection_name: Which collection to search (rules/monsters/adventure)
        k: Number of chunks to retrieve (default: 3)
        use_rewriter: Whether to use query rewriting (default: True)
        verbose: Print debug information (default: False)
        vectorstore: Optional existing vectorstore to reuse

    Returns:
        str: Generated answer based on retrieved context

    Example:
        >>> answer = query_rag("What are the rules for grappling?")
        >>> print(answer)
    """
    pipeline, vectorstore = get_retrieval_pipeline(vectorstore)

    if verbose:
        print(f"📝 Query: {query}")
        print(f"📚 Collection: {collection_name}")
        print(f"🔍 Retrieving top-{k} chunks\n")

    # Run the pipeline
    try:
        result = pipeline.run({
            # "rewriter": {"user_prompt": query} if use_rewriter else None,  # Rewriter disabled
            "embedder": {"text": query},  # Always use direct embedding
            "prompt": {"user_prompt": query},
            "retriever": {"collection_name": collection_name, "k": k},
            "generator": {"input": query}
        })

        answer = result['generator'].text

        if verbose:
            print(f"✅ Answer generated ({len(answer)} characters)\n")

        return answer

    except Exception as e:
        error_msg = f"Error querying RAG system: {e}"
        print(f"❌ {error_msg}")
        return error_msg


def query_rules(query: str, k: int = 3, verbose: bool = False, vectorstore: Optional[QdrantVectorstore] = None) -> str:
    """
    Query D&D rules collection.

    Args:
        query: Question about D&D rules
        k: Number of chunks to retrieve
        verbose: Print debug info
        vectorstore: Optional existing vectorstore

    Returns:
        str: Answer based on D&D rules
    """
    return query_rag(query, COLLECTION_RULES, k, verbose=verbose, vectorstore=vectorstore)


def query_monsters(query: str, k: int = 1, verbose: bool = False, vectorstore: Optional[QdrantVectorstore] = None) -> str:
    """
    Query monster stats collection (DM only).

    Args:
        query: Question about monsters
        k: Number of chunks to retrieve (default: 1 for specific lookups)
        verbose: Print debug info
        vectorstore: Optional existing vectorstore

    Returns:
        str: Monster information
    """
    return query_rag(query, COLLECTION_MONSTERS, k, verbose=verbose, vectorstore=vectorstore)


def query_adventure(query: str, k: int = 5, verbose: bool = False, vectorstore: Optional[QdrantVectorstore] = None) -> str:
    """
    Query adventure narrative collection (DM only).

    Args:
        query: Question about the adventure
        k: Number of chunks to retrieve (default: 5 for more context)
        verbose: Print debug info
        vectorstore: Optional existing vectorstore

    Returns:
        str: Adventure narrative information
    """
    return query_rag(query, COLLECTION_ADVENTURE, k, verbose=verbose, vectorstore=vectorstore)


# ============================================================================
# Tool Wrappers for Agent Integration
# ============================================================================

@tool
def query_rules_tool(query: str) -> str:
    """Query D&D 5e rules knowledge base. Use this to look up game mechanics, spell descriptions, ability checks, combat rules, and other rulebook information."""
    try:
        result = query_rules(query, k=3, verbose=False)
        # Ensure result is never None or empty
        if not result or result.strip() == "":
            return "No relevant information found in the rules database."
        return result
    except Exception as e:
        return f"Error querying rules: {str(e)}"


@tool
def query_monsters_tool(query: str) -> str:
    """Query monster stats and abilities knowledge base. Use this to look up monster stats, abilities, weaknesses, and combat tactics. DM use only."""
    try:
        result = query_monsters(query, k=1, verbose=False)
        # Ensure result is never None or empty
        if not result or result.strip() == "":
            return "No relevant monster information found."
        return result
    except Exception as e:
        return f"Error querying monsters: {str(e)}"


@tool
def query_adventure_tool(query: str) -> str:
    """Query adventure narrative and story knowledge base. Use this to retrieve plot points, NPC information, location descriptions, and quest details. DM use only."""
    try:
        result = query_adventure(query, k=5, verbose=False)
        # Ensure result is never None or empty
        if not result or result.strip() == "":
            return "No relevant adventure information found."
        return result
    except Exception as e:
        return f"Error querying adventure: {str(e)}"


if __name__ == "__main__":
    # Example usage
    print("\n" + "="*60)
    print("🎲 D&D RAG SYSTEM - RETRIEVAL TEST")
    print("="*60 + "\n")

    # Test queries
    test_queries = [
        ("What are the rules for grappling?", COLLECTION_RULES, 3),
        ("What are goblin stats?", COLLECTION_MONSTERS, 1),
        ("What is the opening scene?", COLLECTION_ADVENTURE, 3),
    ]

    for query, collection, k in test_queries:
        print(f"\n{'='*60}")
        print(f"Query: {query}")
        print(f"Collection: {collection}")
        print(f"{'='*60}\n")

        answer = query_rag(query, collection, k, verbose=True)
        print(f"Answer:\n{answer}\n")
