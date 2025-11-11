"""
Test Suite for Phase 5: Memory & Orchestration System

Tests:
- MessageBoard
- HybridMemorySystem
- Intent Parsing
- Smart Ordering
- Full Game Loop

Reference: docs/phases/PHASE_05_ORCHESTRATION.md
"""

import asyncio
import time
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from datapizza.agents import Agent
from datapizza.clients.openai import OpenAIClient

from src.memory.message_board import MessageBoard, Message
from src.memory.hybrid_memory import HybridMemorySystem
from src.orchestration.intents import (
    IntentType,
    parse_dm_intent,
    PlayerIntent,
    smart_order_players,
    generate_player_intent
)
from src.orchestration.orchestrator import GameOrchestrator


async def test_message_board():
    """Test MessageBoard posting and retrieval"""
    print("\n=== Testing MessageBoard ===")

    board = MessageBoard()

    # Post messages
    await board.post(Message("DM", "Welcome to the adventure!", metadata={"type": "narration"}))
    await board.post(Message("Player 1", "Hello! I look around.", metadata={"type": "action"}))
    await board.post(Message("Player 2", "I draw my sword.", metadata={"type": "action"}))

    # Retrieve messages
    recent = board.get_recent(10)
    assert len(recent) == 3, f"Expected 3 messages, got {len(recent)}"

    # Context window
    context = board.get_context_window(max_messages=2)
    assert "Player 1" in context and "Player 2" in context
    print(f"Context window:\n{context}")

    # Test subscriber
    received_messages = []

    async def subscriber(msg: Message):
        received_messages.append(msg)

    board.subscribe(subscriber)
    await board.post(Message("System", "Test message", metadata={}))

    assert len(received_messages) == 1
    assert received_messages[0].speaker == "System"

    print("✅ MessageBoard test passed")


async def test_hybrid_memory_system():
    """Test HybridMemorySystem with mock agents"""
    print("\n=== Testing HybridMemorySystem ===")

    # Create test client and agents
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("⚠️  Skipping HybridMemorySystem test: OPENAI_API_KEY not set")
        return

    client = OpenAIClient(
        api_key=api_key,
        model="gpt-4o-mini",
        temperature=0.7
    )

    dm_agent = Agent(
        name="DM",
        client=client,
        system_prompt="You are a D&D dungeon master. Keep responses brief (1-2 sentences)."
    )

    player1_agent = Agent(
        name="Player1",
        client=client,
        system_prompt="You are a brave warrior. Keep responses brief (1 sentence)."
    )

    # Create memory system
    memory_system = HybridMemorySystem(["DM", "Player1"])

    # Test agent response
    await memory_system.agent_respond("DM", dm_agent, "Start a simple adventure")
    await memory_system.agent_respond("Player1", player1_agent, "I look around")

    # Verify board updated
    assert len(memory_system.board.messages) == 2, f"Expected 2 messages, got {len(memory_system.board.messages)}"

    # Verify individual memories
    dm_memory = memory_system.get_agent_memory("DM")
    assert len(dm_memory.memory) > 0, "DM memory should not be empty"

    player1_memory = memory_system.get_agent_memory("Player1")
    assert len(player1_memory.memory) > 0, "Player1 memory should not be empty"

    print(f"Board has {len(memory_system.board.messages)} messages")
    print(f"DM memory has {len(dm_memory.memory)} turns")
    print("✅ HybridMemorySystem test passed")


def test_intent_parsing():
    """Test DM intent parsing"""
    print("\n=== Testing Intent Parsing ===")

    player_names = ["Thorin", "Elara", "Gandalf"]

    # Test DIRECTED
    intent = parse_dm_intent("Thorin, what do you do?", player_names)
    assert intent.type == IntentType.DIRECTED, f"Expected DIRECTED, got {intent.type}"
    assert intent.target == "Thorin", f"Expected target Thorin, got {intent.target}"
    print(f"✓ Directed: {intent}")

    # Test OPEN
    intent = parse_dm_intent("You hear a noise in the distance.", player_names)
    assert intent.type == IntentType.OPEN, f"Expected OPEN, got {intent.type}"
    print(f"✓ Open: {intent}")

    # Test INITIATIVE
    intent = parse_dm_intent("Roll for initiative!", player_names)
    assert intent.type == IntentType.INITIATIVE, f"Expected INITIATIVE, got {intent.type}"
    print(f"✓ Initiative: {intent}")

    # Test case sensitivity
    intent = parse_dm_intent("elara, you see a chest", player_names)
    assert intent.type == IntentType.DIRECTED, f"Expected DIRECTED, got {intent.type}"
    assert intent.target == "Elara", f"Expected target Elara, got {intent.target}"
    print(f"✓ Case insensitive: {intent}")

    print("✅ Intent parsing test passed")


def test_smart_ordering():
    """Test smart ordering algorithm"""
    print("\n=== Testing Smart Ordering ===")

    intents = [
        PlayerIntent(player_name="P1", wants_to_respond=True, relevance_score=8, reason="Expert lockpicker"),
        PlayerIntent(player_name="P2", wants_to_respond=True, relevance_score=4, reason="Can help"),
        PlayerIntent(player_name="P3", wants_to_respond=False, relevance_score=0, reason="Not relevant"),
    ]

    # Test with empty last_speakers
    ordered = smart_order_players(intents, last_speakers=[])
    assert "P3" not in ordered, "P3 should not be in order (wants_to_respond=False)"
    assert "P1" in ordered and "P2" in ordered, "P1 and P2 should be in order"
    print(f"Order (no recency): {ordered}")

    # Test with recency penalty
    ordered = smart_order_players(intents, last_speakers=["P1"])
    print(f"Order (P1 spoke last): {ordered}")
    # P1 should be penalized, but exact order depends on variety randomness

    # Test all want to respond = False
    intents_none = [
        PlayerIntent(player_name="P1", wants_to_respond=False, relevance_score=0, reason=""),
        PlayerIntent(player_name="P2", wants_to_respond=False, relevance_score=0, reason=""),
    ]
    ordered = smart_order_players(intents_none, last_speakers=[])
    assert len(ordered) == 0, "Should return empty list if no one wants to respond"

    print("✅ Smart ordering test passed")


async def test_game_loop():
    """Test full game loop with real agents (limited turns)"""
    print("\n=== Testing Full Game Loop ===")

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("⚠️  Skipping Game Loop test: OPENAI_API_KEY not set")
        return

    # Create client
    client = OpenAIClient(
        api_key=api_key,
        model="gpt-4o-mini",
        temperature=0.7
    )

    # Create DM agent
    dm_agent = Agent(
        name="DM",
        client=client,
        system_prompt="You are a D&D dungeon master. Keep narration brief (1-2 sentences). Create simple scenarios."
    )

    # Create player agents
    player1 = Agent(
        name="Thorin",
        client=client,
        system_prompt="You are Thorin, a dwarf warrior. Keep responses very brief (1 sentence)."
    )

    player2 = Agent(
        name="Elara",
        client=client,
        system_prompt="You are Elara, an elf ranger. Keep responses very brief (1 sentence)."
    )

    # Create memory system
    memory_system = HybridMemorySystem(["DM", "Thorin", "Elara"])

    # Create orchestrator
    orchestrator = GameOrchestrator(
        dm_agent=dm_agent,
        player_agents=[player1, player2],
        memory_system=memory_system
    )

    # Run limited game loop (3 turns)
    print("\nStarting 3-turn game loop...")
    await orchestrator.game_loop(max_turns=3, initial_prompt="Start a simple adventure in a tavern. Keep it brief.")

    # Verify messages on board
    assert len(orchestrator.memory.board.messages) >= 3, "Should have at least 3 messages"
    print(f"\n✓ Game loop completed with {len(orchestrator.memory.board.messages)} messages")

    # Print transcript
    print("\n=== Game Transcript ===")
    for msg in orchestrator.memory.board.messages:
        print(f"[{msg.speaker}]: {msg.text}\n")

    print("✅ Game loop test passed")


async def main():
    """Run all tests"""
    print("=" * 60)
    print("PHASE 5 ORCHESTRATION TESTS")
    print("=" * 60)

    try:
        # Unit tests (no API required)
        await test_message_board()
        test_intent_parsing()
        test_smart_ordering()

        # Integration tests (require API key)
        await test_hybrid_memory_system()
        await test_game_loop()

        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED")
        print("=" * 60)

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        raise
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
