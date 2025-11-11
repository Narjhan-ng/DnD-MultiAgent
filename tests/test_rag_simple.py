"""
Simple RAG test that runs ingestion and retrieval in the same session.
This is necessary because Qdrant :memory: mode doesn't persist between runs.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config import COLLECTION_ADVENTURE, COLLECTION_MONSTERS, COLLECTION_RULES
from src.rag.ingestion import ingest_documents
from src.rag.retrieval import query_adventure, query_monsters, query_rules


def main():
    """Run ingestion then test retrieval in the same session."""
    print("\n" + "="*70)
    print("🎲 D&D RAG SYSTEM - SIMPLE TEST (INGESTION + RETRIEVAL)")
    print("="*70 + "\n")

    # Step 1: Ingest documents
    print("STEP 1: Ingesting documents...")
    print("-"*70)
    vectorstore = ingest_documents()

    # Step 2: Test retrieval
    print("\n" + "="*70)
    print("STEP 2: Testing retrieval...")
    print("="*70 + "\n")

    test_queries = [
        {
            "name": "Rules - Grappling",
            "query": "What are the rules for grappling?",
            "function": query_rules,
            "k": 3
        },
        {
            "name": "Rules - Fireball",
            "query": "How does the Fireball spell work?",
            "function": query_rules,
            "k": 3
        },
        {
            "name": "Monster - Goblin",
            "query": "What are goblin stats?",
            "function": query_monsters,
            "k": 1
        },
        {
            "name": "Adventure - Opening",
            "query": "What is the opening scene of the adventure?",
            "function": query_adventure,
            "k": 5
        },
    ]

    results = []
    for test in test_queries:
        print(f"\n{'='*70}")
        print(f"TEST: {test['name']}")
        print(f"Query: {test['query']}")
        print(f"{'='*70}\n")

        try:
            answer = test['function'](test['query'], k=test['k'], verbose=False, vectorstore=vectorstore)
            print(f"✅ SUCCESS\n")
            print(f"Answer ({len(answer)} chars):")
            print("-"*70)
            print(answer)
            print("-"*70)
            results.append({"test": test['name'], "success": True})

        except Exception as e:
            print(f"❌ FAILED: {e}\n")
            results.append({"test": test['name'], "success": False, "error": str(e)})

    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)

    passed = sum(1 for r in results if r.get("success"))
    total = len(results)

    for r in results:
        status = "✅" if r.get("success") else "❌"
        print(f"  {status} {r['test']}")

    print(f"\n{'='*70}")
    print(f"TOTAL: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 ALL TESTS PASSED - Phase 2 RAG System Working!")
    else:
        print("⚠️  Some tests failed - Review output above")

    print(f"{'='*70}\n")


if __name__ == "__main__":
    main()
