"""
FastAPI WebSocket Server for D&D Multi-Agent Game

Complete implementation with:
- WebSocket connection management
- Real-time message broadcasting
- Game control endpoints (start, pause, stop, reset)
- Integration with GameOrchestrator

Reference: docs/phases/PHASE_06_UI.md
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from typing import List
import asyncio
import json
import os
from pathlib import Path


# ==================== ConnectionManager ====================

class ConnectionManager:
    """
    Manages WebSocket connections and message broadcasting.

    Handles:
    - Client connections/disconnections
    - Broadcasting messages to all clients
    - Error handling for dropped connections
    """

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        """Accept new WebSocket connection"""
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"✅ Client connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        """Remove disconnected WebSocket"""
        self.active_connections.remove(websocket)
        print(f"❌ Client disconnected. Total connections: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        """
        Broadcast message to all connected clients.

        Args:
            message: Dictionary to send as JSON
        """
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                print(f"Error broadcasting to client: {e}")


# ==================== FastAPI Application ====================

app = FastAPI(
    title="D&D Multi-Agent Game",
    description="Real-time spectator interface for AI-powered D&D",
    version="1.0.0"
)

# CORS middleware (allow all origins for development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Connection manager instance
manager = ConnectionManager()

# Game state
orchestrator = None
game_task = None


# ==================== Game Control Functions ====================

async def start_game():
    """
    Initialize and start the game loop.

    Steps:
    1. Create agents (DM + 3 Players)
    2. Initialize orchestrator
    3. Subscribe MessageBoard to broadcast
    4. Start game loop in background
    """
    global orchestrator, game_task

    if orchestrator is None:
        # Import here to avoid circular dependencies
        from src.orchestration.orchestrator import GameOrchestrator
        from src.agents.dm_agent import create_dm_agent
        from src.agents.player_agent import create_player_agent
        from src.memory.hybrid_memory import HybridMemorySystem
        import yaml

        # Verify required API keys are set
        if not os.getenv("OPENAI_API_KEY"):
            await manager.broadcast({
                "type": "system",
                "message": "❌ Error: OPENAI_API_KEY not found in environment"
            })
            return

        # Load character files
        characters_dir = Path("data/characters")
        character_files = sorted(characters_dir.glob("*.yaml"))[:3]

        if len(character_files) < 3:
            await manager.broadcast({
                "type": "system",
                "message": f"❌ Error: Need 3 character files, found {len(character_files)}"
            })
            return

        # Create agents (no API keys needed - read from environment)
        dm = create_dm_agent()
        players = []

        for char_file in character_files:
            with open(char_file, "r") as f:
                character = yaml.safe_load(f)
            # Use OpenAI for players (best tool calling support)
            players.append(create_player_agent(character, provider="openai"))

        # Create memory system
        agent_names = ["DM"] + [p.name for p in players]
        memory_system = HybridMemorySystem(agent_names)

        # Create orchestrator
        orchestrator = GameOrchestrator(dm, players, memory_system)

        # Subscribe MessageBoard to broadcast
        orchestrator.memory.board.subscribe(broadcast_message)

    # Start game loop in background
    game_task = asyncio.create_task(orchestrator.game_loop())

    await manager.broadcast({
        "type": "system",
        "message": "🎲 Game started! The adventure begins..."
    })


async def broadcast_message(message):
    """
    Callback for MessageBoard - broadcasts game messages to all clients.

    Args:
        message: Message from game
    """
    await manager.broadcast({
        "type": "game_message",
        "speaker": message.speaker,
        "text": message.text,
        "timestamp": message.timestamp,
        "metadata": message.metadata if hasattr(message, 'metadata') else {}
    })


def pause_game():
    """Pause the game loop"""
    if orchestrator:
        orchestrator.game_active = False
    asyncio.create_task(manager.broadcast({
        "type": "system",
        "message": "⏸ Game paused"
    }))


def stop_game():
    """Stop and end the game"""
    global game_task

    if orchestrator:
        orchestrator.stop()

    if game_task:
        game_task.cancel()

    asyncio.create_task(manager.broadcast({
        "type": "system",
        "message": "⏹ Game stopped"
    }))


def reset_game():
    """Reset game state for new game"""
    global orchestrator, game_task

    orchestrator = None
    game_task = None

    asyncio.create_task(manager.broadcast({
        "type": "system",
        "message": "🔄 Game reset. Ready to start new adventure!"
    }))


# ==================== WebSocket Endpoint ====================

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time communication.

    Handles:
    - Connection establishment
    - Command reception (start, pause, stop, reset)
    - Disconnection cleanup
    """
    await manager.connect(websocket)

    try:
        while True:
            # Receive commands from client
            data = await websocket.receive_json()
            await handle_command(data)

    except WebSocketDisconnect:
        manager.disconnect(websocket)


async def handle_command(data: dict):
    """
    Handle commands from frontend.

    Commands:
    - start_game: Begin new adventure
    - pause_game: Pause current game
    - stop_game: Stop and end game
    - reset_game: Reset for new game
    """
    command = data.get("type")

    if command == "start_game":
        await start_game()
    elif command == "pause_game":
        pause_game()
    elif command == "stop_game":
        stop_game()
    elif command == "reset_game":
        reset_game()
    else:
        print(f"Unknown command: {command}")


# ==================== HTTP Endpoints ====================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "connections": len(manager.active_connections),
        "game_active": orchestrator.game_active if orchestrator else False
    }


# Mount static files for frontend (must be last)
frontend_path = Path(__file__).parent / "frontend"
if frontend_path.exists():
    app.mount("/", StaticFiles(directory=str(frontend_path), html=True), name="frontend")
