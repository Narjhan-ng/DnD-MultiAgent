"""
Dungeon Master Agent Implementation

Complete DM agent with:
- RAG integration (rules, monsters, adventure)
- Dice rolling tool
- Narrative-focused system prompt
- OpenAI client for high-quality narration
"""

from datapizza.agents import Agent
from datapizza.clients.openai import OpenAIClient

from src.config import OPENAI_API_KEY
from src.rag.retrieval import query_rules_tool, query_monsters_tool, query_adventure_tool
from src.tools.dice import roll_dice


# DM System Prompt
DM_SYSTEM_PROMPT = """
You are an expert Dungeon Master for Dungeons & Dragons 5th Edition.

Your responsibilities:
- Narrate the adventure with vivid, engaging descriptions
- Manage NPCs and monsters with distinct personalities
- Enforce D&D 5e rules fairly and consistently
- Call for dice rolls when needed (use roll_dice tool)
- Respond to player actions with consequences
- Keep the story moving forward

You have access to:
- D&D 5e rules knowledge (use query_rules_tool)
- Monster stats (use query_monsters_tool)
- Adventure narrative (use query_adventure_tool)
- Dice rolling (use roll_dice tool)

Style guidelines:
- Keep responses concise (2-4 sentences unless describing new scene)
- Address players by character name
- Use present tense for immersion ("You see..." not "You saw...")
- Ask for rolls BEFORE describing outcomes
- Be descriptive but not overly verbose
- Let players make meaningful choices

Game flow:
1. Describe scene/situation
2. Wait for player responses
3. Call for dice rolls if needed
4. Describe outcomes and consequences
5. Introduce next challenge/scene

Remember: You are facilitating a fun, collaborative story. Be fair, creative, and responsive to player actions.
""".strip()


def create_dm_agent(
    model: str = "gpt-4o-mini",
    temperature: float = 0.8
) -> Agent:
    """
    Create DM agent with OpenAI for high-quality narration.

    Args:
        model: OpenAI model name (default: gpt-4o-mini for best cost/quality)
        temperature: Creativity level (0.8 recommended for DM)

    Returns:
        Configured DM Agent with OpenAI client

    Example:
        >>> dm = create_dm_agent()
        >>> response = dm.run("Start the adventure")
        >>> print(response.text)

    Note:
        Uses OpenAI for superior narrative quality and context understanding.
        GPT-4o-mini provides excellent balance of quality and cost.
    """
    # Create OpenAI client for DM (high quality narration)
    client = OpenAIClient(
        api_key=OPENAI_API_KEY,
        model=model,
        temperature=temperature
    )

    # Create DM agent with all tools
    dm_agent = Agent(
        name="DM",
        client=client,
        system_prompt=DM_SYSTEM_PROMPT,
        tools=[
            roll_dice,
            query_rules_tool,
            query_monsters_tool,
            query_adventure_tool
        ]
    )

    return dm_agent


if __name__ == "__main__":
    """Test DM agent creation"""
    print("=== DM Agent Test ===\n")

    # Create DM
    dm = create_dm_agent()

    print("✅ DM Agent created successfully!")
    print(f"  Name: {dm.name}")
    print(f"  Model: OpenAI gpt-4o-mini")
    print(f"  Tools: {[tool.__name__ for tool in dm.tools]}")
    print(f"  System Prompt Length: {len(dm.system_prompt)} chars")
    print()

    # Test DM response
    print("Testing DM response...")
    print("Prompt: 'Start the adventure. Describe the opening scene.'")
    print()

    try:
        response = dm.run("Start the adventure. Describe the opening scene.")
        print(f"DM: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
