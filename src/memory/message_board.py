"""
MessageBoard - Shared event log for all game messages

Provides:
- Thread-safe message posting and retrieval
- Subscriber pattern for WebSocket integration
- Context window generation for LLM prompts

Reference: docs/phases/PHASE_05_ORCHESTRATION.md
"""

import asyncio
import time
from dataclasses import dataclass, field
from typing import List, Callable, Dict, Optional


@dataclass
class Message:
    """Single message in the game log"""
    speaker: str          # "DM", "Player 1", "System"
    text: str            # Message content
    timestamp: float = field(default_factory=time.time)
    metadata: Dict = field(default_factory=dict)  # type, dice_roll, turn_number, etc.

    def to_dict(self) -> dict:
        """Serialize for UI/storage"""
        return {
            "speaker": self.speaker,
            "text": self.text,
            "timestamp": self.timestamp,
            "metadata": self.metadata
        }


class MessageBoard:
    """
    Thread-safe event log for all game messages.
    Used for UI display, tracing, and context building.
    """

    def __init__(self):
        self.messages: List[Message] = []
        self.lock = asyncio.Lock()
        self.subscribers: List[Callable] = []

    async def post(self, message: Message):
        """Post message to board and notify subscribers"""
        async with self.lock:
            self.messages.append(message)
            await self._notify_subscribers(message)

    async def _notify_subscribers(self, message: Message):
        """Notify all subscribers (e.g., WebSocket clients)"""
        for callback in self.subscribers:
            try:
                await callback(message)
            except Exception as e:
                print(f"Error notifying subscriber: {e}")

    def get_recent(self, n: int = 50) -> List[Message]:
        """Get last N messages for UI"""
        return self.messages[-n:]

    def get_context_window(self, max_messages: int = 20) -> str:
        """Get recent messages formatted for LLM context"""
        recent = self.messages[-max_messages:]
        return "\n".join([f"[{m.speaker}]: {m.text}" for m in recent])

    def subscribe(self, callback: Callable):
        """Subscribe to new messages (for WebSocket)"""
        self.subscribers.append(callback)

    def unsubscribe(self, callback: Callable):
        """Unsubscribe from new messages"""
        if callback in self.subscribers:
            self.subscribers.remove(callback)

    def clear(self):
        """Clear all messages (useful for testing)"""
        self.messages.clear()

    def __len__(self) -> int:
        """Return number of messages"""
        return len(self.messages)
