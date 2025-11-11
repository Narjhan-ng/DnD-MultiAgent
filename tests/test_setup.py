"""
Test Datapizza AI installation and basic imports
"""

def test_datapizza_imports():
    """Test that all Datapizza AI imports work correctly"""
    try:
        # Core imports
        from datapizza.agents import Agent
        from datapizza.memory import Memory
        from datapizza.tools import tool
        from datapizza.type import ROLE, TextBlock

        # Client imports
        from datapizza.clients.openai import OpenAIClient
        from datapizza.clients.google import GoogleClient
        from datapizza.clients.anthropic import AnthropicClient
        from datapizza.clients.openai_like import OpenAILikeClient

        # Embedders & Vectorstores
        from datapizza.embedders import ChunkEmbedder
        from datapizza.embedders.openai import OpenAIEmbedder
        from datapizza.vectorstores.qdrant import QdrantVectorstore
        from datapizza.core.vectorstore import VectorConfig

        # Pipelines
        from datapizza.pipeline import IngestionPipeline, DagPipeline

        # Tracing
        from datapizza.tracing import ContextTracing

        print("✅ All Datapizza AI imports successful!")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False


def test_web_framework_imports():
    """Test that web framework imports work correctly"""
    try:
        import fastapi
        import uvicorn
        import websockets

        print("✅ Web framework imports successful!")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False


def test_pydantic_imports():
    """Test Pydantic for structured outputs"""
    try:
        from pydantic import BaseModel, Field

        class TestModel(BaseModel):
            name: str
            value: int

        test = TestModel(name="test", value=42)
        assert test.name == "test"
        assert test.value == 42

        print("✅ Pydantic imports and functionality successful!")
        return True
    except Exception as e:
        print(f"❌ Pydantic error: {e}")
        return False


if __name__ == "__main__":
    print("Testing Datapizza AI Setup")
    print("=" * 50)

    results = []
    results.append(test_datapizza_imports())
    results.append(test_web_framework_imports())
    results.append(test_pydantic_imports())

    print("=" * 50)
    if all(results):
        print("🎉 All tests passed! Setup is complete.")
    else:
        print("⚠️  Some tests failed. Check the errors above.")
