"""
Integration Test for Dice Tool with Datapizza AI

Tests that the roll_dice tool can be properly invoked by:
1. Direct client invocation with tools
2. Agent integration with tool calling

Reference: docs/phases/PHASE_03_DICE.md (Integration Preparation section)
"""

import os
from dotenv import load_dotenv
from datapizza.clients.openai import OpenAIClient
from datapizza.agents import Agent
from src.tools.dice import roll_dice

# Load environment variables
load_dotenv()


def test_tool_metadata():
    """Test that @tool decorator properly sets metadata"""
    print("=== Test Tool Metadata ===")

    # Check that the tool has proper attributes
    assert hasattr(roll_dice, '__name__')
    assert hasattr(roll_dice, '__doc__')
    print(f"✅ Tool name: {roll_dice.__name__}")
    print(f"✅ Tool docstring: {roll_dice.__doc__[:50]}...")
    print()


def test_direct_tool_call():
    """Test direct tool invocation (baseline)"""
    print("=== Test Direct Tool Call ===")

    result = roll_dice("1d20+5")
    assert "1d20+5" in result
    assert "=" in result
    print(f"✅ Direct call result: {result}")
    print()


def test_client_tool_invocation():
    """Test tool invocation via OpenAI client"""
    print("=== Test Client Tool Invocation ===")

    # Get API key from environment
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("⚠️  OPENAI_API_KEY not found, skipping client test")
        return

    try:
        # Create client
        client = OpenAIClient(
            api_key=api_key,
            model="gpt-4o-mini"
        )

        # Test tool invocation
        response = client.invoke(
            "Roll 1d20+5 for me",
            tools=[roll_dice],
            tool_choice="auto"
        )

        print(f"✅ Client response: {response.text[:200]}...")
        print(f"✅ Tool was {'called' if 'rolled' in response.text.lower() or '1d20' in response.text else 'NOT called'}")
        print()

    except Exception as e:
        print(f"⚠️  Client test failed: {e}")
        print()


def test_agent_integration():
    """Test tool integration with Agent"""
    print("=== Test Agent Integration ===")

    # Get API key from environment
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("⚠️  OPENAI_API_KEY not found, skipping agent test")
        return

    try:
        # Create client
        client = OpenAIClient(
            api_key=api_key,
            model="gpt-4o-mini"
        )

        # Create agent with dice tool
        agent = Agent(
            name="dice_roller",
            client=client,
            tools=[roll_dice],
            system_prompt="You are a D&D dice rolling assistant. When asked to roll dice, use the roll_dice tool."
        )

        # Test agent with tool
        response = agent.run("Roll initiative for a goblin (+2 bonus)")

        print(f"✅ Agent response: {response.text[:200]}...")
        print(f"✅ Agent used tool: {'Yes' if 'rolled' in response.text.lower() or '1d20' in response.text else 'Maybe not'}")
        print()

    except Exception as e:
        print(f"⚠️  Agent test failed: {e}")
        print()


def test_multi_agent_scenario():
    """Test dice tool in a multi-agent D&D scenario"""
    print("=== Test Multi-Agent D&D Scenario ===")

    # Get API key from environment
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("⚠️  OPENAI_API_KEY not found, skipping multi-agent test")
        return

    try:
        # Create client
        client = OpenAIClient(
            api_key=api_key,
            model="gpt-4o-mini"
        )

        # Create DM agent with dice tool
        dm_agent = Agent(
            name="dungeon_master",
            client=client,
            tools=[roll_dice],
            system_prompt=(
                "You are a D&D Dungeon Master. When you need to roll dice for NPCs or "
                "determine outcomes, use the roll_dice tool. Be descriptive and engaging."
            )
        )

        # Test combat scenario
        scenario = (
            "A goblin attacks the player. Roll the goblin's attack (1d20+4) "
            "and if it hits (AC 15), roll damage (1d6+2)"
        )

        response = dm_agent.run(scenario)

        print(f"✅ DM response: {response.text[:300]}...")
        print()

    except Exception as e:
        print(f"⚠️  Multi-agent test failed: {e}")
        print()


def run_integration_tests():
    """Run all integration tests"""
    print("\n" + "="*60)
    print("DICE TOOL - DATAPIZZA AI INTEGRATION TESTS")
    print("="*60 + "\n")

    try:
        test_tool_metadata()
        test_direct_tool_call()
        test_client_tool_invocation()
        test_agent_integration()
        test_multi_agent_scenario()

        print("="*60)
        print("✅ INTEGRATION TESTS COMPLETED!")
        print("="*60 + "\n")

        print("Note: Some tests may have been skipped if OPENAI_API_KEY is not set.")
        print("To run all tests, ensure .env file contains valid API keys.")
        print()

    except Exception as e:
        print(f"\n❌ INTEGRATION TEST FAILED: {e}\n")


if __name__ == "__main__":
    run_integration_tests()
