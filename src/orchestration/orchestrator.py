"""
GameOrchestrator - Main game loop coordinator

Responsibilities:
- Run game loop
- Parse DM intent
- Gather player intents
- Order player responses
- Manage turn flow

Reference: docs/phases/PHASE_05_ORCHESTRATION.md
Architecture: PROJECT.md Section 4.5
"""

import asyncio
from typing import List, Optional
from datapizza.agents import Agent

from src.memory.hybrid_memory import HybridMemorySystem
from src.memory.message_board import Message
from src.orchestration.intents import (
    IntentType,
    DMIntent,
    parse_dm_intent,
    generate_player_intent,
    smart_order_players
)


class GameOrchestrator:
    """
    Main game orchestrator coordinating all agents.

    Responsibilities:
    - Run game loop
    - Parse DM intent
    - Gather player intents
    - Order player responses
    - Manage turn flow
    """

    def __init__(
        self,
        dm_agent: Agent,
        player_agents: List[Agent],
        memory_system: HybridMemorySystem
    ):
        """
        Initialize game orchestrator.

        Args:
            dm_agent: Dungeon Master agent
            player_agents: List of player agents
            memory_system: HybridMemorySystem instance
        """
        self.dm = dm_agent
        self.players = player_agents
        self.player_names = [p.name for p in player_agents]
        self.memory = memory_system
        self.last_speakers = []
        self.game_active = False
        self.initiative_order = None
        self.turn_count = 0

    async def game_loop(self, max_turns: int = 50, initial_prompt: Optional[str] = None):
        """
        Main game loop - orchestrates multi-agent interaction.

        Flow:
        1. DM narrates/prompts
        2. Parse DM intent
        3. Determine who responds (directed/open/initiative)
        4. Players respond in calculated order
        5. Repeat

        Args:
            max_turns: Maximum number of turns before stopping
            initial_prompt: Optional custom initial prompt for DM
        """
        self.game_active = True
        self.turn_count = 0

        # Post system message
        await self.memory.board.post(
            Message("System", "Game started!", metadata={"type": "system"})
        )

        while self.game_active and self.turn_count < max_turns:
            self.turn_count += 1

            # 1. DM narrates/prompts
            if self.turn_count == 1 and initial_prompt:
                dm_prompt = initial_prompt
            elif self.turn_count == 1:
                dm_prompt = "Start the adventure. Describe the opening scene."
            else:
                dm_prompt = "Continue the adventure based on recent events."

            dm_response = await self.memory.agent_respond(
                "DM",
                self.dm,
                dm_prompt
            )

            # 2. Parse DM intent
            intent = parse_dm_intent(dm_response.text, self.player_names)
            print(f"[Turn {self.turn_count}] {intent}")

            # 3. Determine who responds
            responders = await self._determine_responders(intent, dm_response.text)

            # 4. Players respond
            for player in responders:
                try:
                    player_response = await self.memory.agent_respond(
                        player.name,
                        player,
                        f"Respond to DM's message: {dm_response.text}",
                        timeout=60.0
                    )
                    self.last_speakers.append(player.name)
                except asyncio.TimeoutError:
                    # Log timeout and continue with next player
                    error_msg = f"⚠️ {player.name} failed to respond within timeout (60s)"
                    print(error_msg)
                    await self.memory.board.post(
                        Message("System", error_msg, metadata={"type": "error"})
                    )
                except Exception as e:
                    # Log other errors and continue
                    error_msg = f"⚠️ Error from {player.name}: {str(e)}"
                    print(error_msg)
                    await self.memory.board.post(
                        Message("System", error_msg, metadata={"type": "error"})
                    )

                # Optional: DM can react immediately to critical actions
                # (implement if needed)

            # Optional: Update game state snapshot
            # self.memory.update_context_snapshot({...})

        # Game ended
        await self.memory.board.post(
            Message(
                "System",
                f"Game ended after {self.turn_count} turns.",
                metadata={"type": "system"}
            )
        )

    async def _determine_responders(
        self,
        intent: DMIntent,
        dm_message: str
    ) -> List[Agent]:
        """
        Determine which players should respond based on intent.

        Args:
            intent: Parsed DM intent
            dm_message: DM's message text

        Returns:
            List of agents that should respond
        """
        if intent.type == IntentType.DIRECTED:
            # Single player responds
            player = self.get_player(intent.target)
            return [player] if player else []

        elif intent.type == IntentType.OPEN:
            # Gather intents in parallel
            intent_tasks = [
                generate_player_intent(
                    player,
                    dm_message,
                    self.memory.board.get_context_window(max_messages=10)
                )
                for player in self.players
            ]
            player_intents = await asyncio.gather(*intent_tasks)

            # Smart ordering
            ordered_names = smart_order_players(player_intents, self.last_speakers)
            responders = [self.get_player(name) for name in ordered_names]
            return [r for r in responders if r is not None]

        elif intent.type == IntentType.INITIATIVE:
            # Initiative order (simplified - all players respond)
            # TODO: Implement actual initiative rolls if needed
            return self.players

        return []

    def get_player(self, name: str) -> Optional[Agent]:
        """
        Get player agent by name.

        Args:
            name: Player name to search for

        Returns:
            Agent if found, None otherwise
        """
        for player in self.players:
            if player.name == name:
                return player
        return None

    def stop(self):
        """Stop the game loop"""
        self.game_active = False

    def pause(self):
        """Pause the game loop"""
        self.game_active = False

    def resume(self):
        """Resume the game loop"""
        self.game_active = True

    def get_transcript(self) -> List[Message]:
        """
        Get full game transcript.

        Returns:
            List of all messages from the board
        """
        return self.memory.board.messages

    def get_recent_transcript(self, n: int = 10) -> List[Message]:
        """
        Get recent game transcript.

        Args:
            n: Number of recent messages to retrieve

        Returns:
            List of recent messages
        """
        return self.memory.board.get_recent(n)
