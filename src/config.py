import os
from dotenv import load_dotenv

load_dotenv()

# API Keys
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# Model configuration
# Updated models as of Nov 2025 - check https://console.groq.com/docs/models
GROQ_MODEL = "llama-3.3-70b-versatile"  # Alternative: "mixtral-8x7b-32768", "llama-3.1-8b-instant"
EMBEDDING_MODEL = "text-embedding-3-small"

# Vectorstore configuration
QDRANT_LOCATION = ":memory:"  # Change to host/port for external Qdrant

# Collections
COLLECTION_RULES = "dnd_rules"
COLLECTION_MONSTERS = "dnd_monsters"
COLLECTION_ADVENTURE = "dnd_adventure"
