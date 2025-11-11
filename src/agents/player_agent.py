"""
Player Agent Implementation

Complete player agent with:
- Character sheet integration
- RAG integration (rules lookup)
- Dice rolling tool
- Personality-driven responses
- Support for Groq and Gemini clients (fast, cost-effective)
"""

from typing import Dict, Literal

from datapizza.agents import Agent
from datapizza.clients.google import GoogleClient
from datapizza.clients.openai import OpenAIClient
from datapizza.clients.openai_like import OpenAILikeClient

from src.config import GROQ_API_KEY, GROQ_MODEL, GOOGLE_API_KEY, OPENAI_API_KEY
from src.rag.retrieval import query_rules_tool
from src.tools.dice import roll_dice


def create_player_system_prompt(character_sheet: Dict) -> str:
    """
    Create system prompt for player agent based on character sheet.

    Args:
        character_sheet: Character data (name, class, race, personality, etc.)

    Returns:
        Formatted system prompt
    """
    return f"""
You are playing {character_sheet['name']}, a level {character_sheet.get('level', 1)} {character_sheet['race']} {character_sheet['class']}.

CHARACTER DETAILS:
Name: {character_sheet['name']}
Class: {character_sheet['class']}
Race: {character_sheet['race']}
Background: {character_sheet.get('background', 'Adventurer')}
Personality: {character_sheet.get('personality', 'Brave and curious')}
Key Skills: {', '.join(character_sheet.get('skills', ['Various']))}

GAMEPLAY INSTRUCTIONS:
- Stay in character - act according to your personality and background
- Declare actions clearly and concisely (1-2 sentences)
- Consider your character's skills and abilities when acting
- Cooperate with other party members
- Ask questions when uncertain about situations
- Use your character's name when referring to yourself in third person
- React naturally to the DM's descriptions and other players' actions

You have access to:
- D&D 5e rules (use query_rules_tool for spell/ability lookups)
- Dice rolling (DM will usually call for rolls, but you can suggest them)

Remember: You are ONE character in a party of adventurers. Work together to overcome challenges and progress the story.
""".strip()


def create_player_agent(
    character_sheet: Dict,
    provider: Literal["groq", "gemini", "openai"] = "openai",
    temperature: float = 0.7
) -> Agent:
    """
    Create player agent with character personality.

    Args:
        character_sheet: Character data dictionary
        provider: LLM provider ("groq", "gemini", "openai") - default: openai
        temperature: Creativity level (0.7 balanced)

    Returns:
        Configured Player Agent

    Example:
        >>> character = load_character("character1.yaml")
        >>> player = create_player_agent(character, provider="openai")
        >>> response = player.run("You see a locked door. What do you do?")

    Note:
        Uses OpenAI (GPT-4o-mini), Groq (Llama 3.1) or Gemini for inference.
        OpenAI recommended for best tool calling support.
    """
    # Create client based on provider
    if provider == "openai":
        client = OpenAIClient(
            api_key=OPENAI_API_KEY,
            model="gpt-4o-mini",  # Fast and cost-effective
            temperature=temperature
        )
    elif provider == "gemini":
        client = GoogleClient(
            api_key=GOOGLE_API_KEY,
            model="gemini-2.5-pro",  # Updated model name
            temperature=temperature
        )
    elif provider == "groq":
        client = OpenAILikeClient(
            api_key=GROQ_API_KEY,
            base_url="https://api.groq.com/openai/v1",
            model=GROQ_MODEL,
            temperature=temperature
        )
    else:
        raise ValueError(f"Invalid provider: {provider}. Must be 'groq', 'gemini', or 'openai'")

    # Create system prompt
    system_prompt = create_player_system_prompt(character_sheet)

    # Create player agent
    player_agent = Agent(
        name=character_sheet['name'],
        client=client,
        system_prompt=system_prompt,
        tools=[roll_dice, query_rules_tool]
    )

    return player_agent


if __name__ == "__main__":
    """Test player agent creation"""
    import yaml

    print("=== Player Agent Test ===\n")

    # Example character (using Fighter from character1.yaml structure)
    test_character = {
        "name": "Thorin Ironforge",
        "class": "Fighter",
        "race": "Dwarf",
        "level": 1,
        "background": "Former soldier with a strong sense of honor",
        "personality": "Brave, loyal, straightforward. Prefers direct action.",
        "skills": ["Athletics", "Intimidation", "Perception"]
    }

    print("Creating player agents with different providers...\n")

    # Test Groq
    try:
        player_groq = create_player_agent(test_character, provider="groq")
        print(f"✅ Player Agent (Groq) created: {player_groq.name}")
        print(f"   Provider: Groq Llama 3.1")
        print(f"   Tools: {[tool.__name__ for tool in player_groq.tools]}")
    except Exception as e:
        print(f"❌ Groq agent failed: {e}")

    print()

    # Test Gemini
    try:
        player_gemini = create_player_agent(test_character, provider="gemini")
        print(f"✅ Player Agent (Gemini) created: {player_gemini.name}")
        print(f"   Provider: Google Gemini Flash")
        print(f"   Tools: {[tool.__name__ for tool in player_gemini.tools]}")
    except Exception as e:
        print(f"❌ Gemini agent failed: {e}")

    print()

    # Test player response
    print("Testing player response...")
    print("Scenario: 'You see a locked treasure chest. What do you do?'")
    print()

    try:
        response = player_groq.run("DM: You see a locked treasure chest in the corner of the room. What do you do?")
        print(f"{player_groq.name}: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
