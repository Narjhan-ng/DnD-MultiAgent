"""
RAG (Retrieval-Augmented Generation) module for D&D AI system.

This module provides document ingestion and retrieval capabilities
for D&D rules, monsters, and adventure content.
"""

from .ingestion import ingest_documents
from .retrieval import query_rag, initialize_retrieval_pipeline

__all__ = ["ingest_documents", "query_rag", "initialize_retrieval_pipeline"]
