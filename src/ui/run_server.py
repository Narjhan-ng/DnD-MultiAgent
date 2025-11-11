"""
Server startup script for D&D Multi-Agent Game

Usage:
    python src/ui/run_server.py

Server will start on:
    http://localhost:8000 (Web interface)
    ws://localhost:8000/ws (WebSocket endpoint)
"""

import uvicorn
from dotenv import load_dotenv
import sys
from pathlib import Path

if __name__ == "__main__":
    # Add project root to Python path
    project_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(project_root))

    # Load environment variables
    load_dotenv()

    print("=" * 50)
    print("D&D Multi-Agent Game Server")
    print("=" * 50)
    print("Starting server on http://localhost:8000")
    print("WebSocket endpoint: ws://localhost:8000/ws")
    print("Press Ctrl+C to stop")
    print("=" * 50)

    uvicorn.run(
        "src.ui.server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Auto-reload during development
        log_level="info"
    )
