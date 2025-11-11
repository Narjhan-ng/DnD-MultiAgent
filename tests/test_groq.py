"""
Test Groq API connection using OpenAI-like client

Note: This test requires a valid GROQ_API_KEY in your .env file
"""
import sys
import os

# Add src to path so we can import config
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.config import GROQ_API_KEY, GROQ_MODEL


def test_groq_connection():
    """Test connection to Groq API"""
    if not GROQ_API_KEY or GROQ_API_KEY == "your_groq_api_key_here":
        print("⚠️  GROQ_API_KEY not configured in .env file")
        print("   Please add your Groq API key to continue")
        print("   Visit: https://console.groq.com/ to get your key")
        return False

    try:
        from datapizza.clients.openai_like import OpenAILikeClient

        print(f"Testing Groq API with model: {GROQ_MODEL}")

        client = OpenAILikeClient(
            api_key=GROQ_API_KEY,
            base_url="https://api.groq.com/openai/v1",
            model=GROQ_MODEL
        )

        response = client.invoke("Say 'Hello D&D!' and nothing else")
        print(f"✅ Groq API connection successful!")
        print(f"   Response: {response.text}")
        return True

    except Exception as e:
        print(f"❌ Groq API connection failed: {e}")
        return False


if __name__ == "__main__":
    print("Testing Groq API Connection")
    print("=" * 50)

    success = test_groq_connection()

    print("=" * 50)
    if success:
        print("🎉 Groq API test passed!")
    else:
        print("⚠️  Groq API test failed. Check your API key and connection.")
