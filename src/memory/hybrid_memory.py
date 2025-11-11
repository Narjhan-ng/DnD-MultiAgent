"""
HybridMemorySystem - Individual agent memories + shared MessageBoard

Provides:
- Individual Memory per agent (conversation history)
- Shared MessageBoard access (game events)
- Context snapshot management (game state)

Reference: docs/phases/PHASE_05_ORCHESTRATION.md
Architecture: PROJECT.md Section 4.5
"""

import time
import asyncio
from typing import Dict, List
from datapizza.memory import Memory
from datapizza.type import ROLE, TextBlock
from datapizza.agents import Agent

from src.memory.message_board import MessageBoard, Message


class HybridMemorySystem:
    """
    Individual agent memories + shared MessageBoard.
    Efficient, scalable, no bottleneck.
    """

    def __init__(self, agent_names: List[str]):
        """
        Initialize hybrid memory system.

        Args:
            agent_names: List of agent names (including "DM")
        """
        # Individual memories for each agent
        self.agent_memories: Dict[str, Memory] = {
            name: Memory() for name in agent_names
        }

        # Shared components
        self.board = MessageBoard()
        self.context_snapshot = {
            "game_state": {},
            "last_sync": time.time()
        }

    async def agent_respond(
        self,
        agent_name: str,
        agent: Agent,
        prompt: str,
        include_board_context: bool = True,
        timeout: float = 60.0
    ) -> any:
        """
        Agent generates response using:
        1. Own memory (conversation history)
        2. Recent board context (what others said)
        3. Context snapshot (game state)

        Args:
            agent_name: Name of the agent responding
            agent: Agent object
            prompt: User prompt for the agent
            include_board_context: Whether to include board context (default True)
            timeout: Maximum seconds to wait for agent response (default 60.0)

        Returns:
            Agent response object

        Raises:
            asyncio.TimeoutError: If agent doesn't respond within timeout
        """
        # Build context from board
        board_context = ""
        if include_board_context and len(self.board.messages) > 0:
            board_context = self.board.get_context_window(max_messages=20)
            board_context = f"Recent game context:\n{board_context}\n\n"

        # Full prompt with context
        full_prompt = f"{board_context}{prompt}"

        # Set agent's memory to the correct one for this agent
        # Store original memory to restore later if agent is shared
        original_memory = agent._memory
        agent._memory = self.agent_memories[agent_name]

        try:
            # Agent uses own memory (now set in agent._memory)
            # Add timeout to prevent infinite hangs
            response = await asyncio.wait_for(
                agent.a_run(full_prompt),
                timeout=timeout
            )

            # Update agent's memory (it's already been updated by agent.a_run if stateless=False)
            # But we keep it updated here for consistency with stateless agents
            if agent._stateless:
                self.agent_memories[agent_name].add_turn(
                    TextBlock(content=full_prompt),
                    role=ROLE.USER
                )
                self.agent_memories[agent_name].add_turn(
                    response.content,
                    role=ROLE.ASSISTANT
                )
        finally:
            # Restore original memory if needed
            agent._memory = original_memory

        # Post to shared board
        message = Message(
            speaker=agent_name,
            text=response.text,
            timestamp=time.time(),
            metadata={"type": "agent_response"}
        )
        await self.board.post(message)

        return response

    def update_context_snapshot(self, game_state: dict):
        """
        Update shared context (HP, location, active effects).

        Args:
            game_state: Dictionary containing current game state
        """
        self.context_snapshot["game_state"] = game_state
        self.context_snapshot["last_sync"] = time.time()

    def get_game_state(self) -> dict:
        """Get current game state snapshot"""
        return self.context_snapshot["game_state"]

    def get_agent_memory(self, agent_name: str) -> Memory:
        """Get individual agent's memory"""
        return self.agent_memories.get(agent_name)

    def clear_all_memories(self):
        """Clear all agent memories and board (useful for testing)"""
        for memory in self.agent_memories.values():
            memory.clear()
        self.board.clear()
        self.context_snapshot = {
            "game_state": {},
            "last_sync": time.time()
        }
