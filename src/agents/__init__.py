"""
Agent Factory Module

Provides:
- Character sheet loading from YAML files
- DM agent creation
- Player agent creation with automatic provider rotation
- Convenience functions for creating full party
"""

import os
from pathlib import Path
from typing import Dict, List

import yaml

from src.agents.dm_agent import create_dm_agent
from src.agents.player_agent import create_player_agent


def load_character(character_file: str, characters_dir: str = "data/characters") -> Dict:
    """
    Load character sheet from YAML file.

    Args:
        character_file: Character filename (e.g., "character1.yaml")
        characters_dir: Directory containing character files (default: data/characters)

    Returns:
        Character sheet dictionary

    Raises:
        FileNotFoundError: If character file doesn't exist
        yaml.YAMLError: If file is not valid YAML
    """
    file_path = os.path.join(characters_dir, character_file)

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Character file not found: {file_path}")

    with open(file_path, 'r', encoding='utf-8') as f:
        character = yaml.safe_load(f)

    return character


def load_all_characters(characters_dir: str = "data/characters") -> List[Dict]:
    """
    Load all character sheets from directory.

    Args:
        characters_dir: Directory containing character YAML files

    Returns:
        List of character sheet dictionaries

    Note:
        Loads files in alphabetical order (character1.yaml, character2.yaml, character3.yaml)
    """
    characters = []

    # Get all YAML files in directory
    yaml_files = sorted([f for f in os.listdir(characters_dir) if f.endswith('.yaml')])

    for filename in yaml_files:
        try:
            character = load_character(filename, characters_dir)
            characters.append(character)
        except Exception as e:
            print(f"⚠️  Warning: Could not load {filename}: {e}")

    return characters


def create_party(
    character_files: List[str] = None,
    characters_dir: str = "data/characters",
    providers: List[str] = None
) -> List:
    """
    Create a party of player agents from character files.

    Args:
        character_files: List of character filenames (default: all YAML files in directory)
        characters_dir: Directory containing character files
        providers: List of providers for each player (default: ["groq", "gemini", "groq"])

    Returns:
        List of Player Agent instances

    Example:
        >>> party = create_party()
        >>> print([p.name for p in party])
        ['Thorin Ironforge', 'Kira Shadowstep', 'Elara Moonshadow']
    """
    # Default to loading all characters
    if character_files is None:
        characters = load_all_characters(characters_dir)
    else:
        characters = [load_character(f, characters_dir) for f in character_files]

    # Default provider rotation: Groq, Gemini, Groq
    # This distributes load and provides redundancy
    if providers is None:
        providers = ["groq", "gemini", "groq"]

    # Ensure we have enough providers
    if len(providers) < len(characters):
        # Cycle through providers if not enough specified
        providers = (providers * ((len(characters) // len(providers)) + 1))[:len(characters)]

    # Create player agents
    party = []
    for character, provider in zip(characters, providers):
        try:
            player = create_player_agent(character, provider=provider)
            party.append(player)
        except Exception as e:
            print(f"❌ Error creating agent for {character.get('name', 'Unknown')}: {e}")

    return party


def create_game_agents(
    dm_model: str = "gpt-4o-mini",
    player_providers: List[str] = None
) -> tuple:
    """
    Create all agents for a game session (DM + Party).

    Args:
        dm_model: OpenAI model for DM (default: gpt-4o-mini)
        player_providers: List of providers for players (default: ["groq", "gemini", "groq"])

    Returns:
        Tuple of (dm_agent, player_agents_list)

    Example:
        >>> dm, players = create_game_agents()
        >>> print(f"DM: {dm.name}")
        >>> print(f"Players: {[p.name for p in players]}")
    """
    # Create DM with OpenAI
    dm = create_dm_agent(model=dm_model)

    # Create party with mixed providers
    party = create_party(providers=player_providers)

    return dm, party


# Convenience exports
__all__ = [
    'load_character',
    'load_all_characters',
    'create_party',
    'create_game_agents',
    'create_dm_agent',
    'create_player_agent',
]


if __name__ == "__main__":
    """Test agent factory"""
    print("=== Agent Factory Test ===\n")

    # Test character loading
    print("Loading characters...")
    characters = load_all_characters()
    print(f"✅ Loaded {len(characters)} characters:")
    for char in characters:
        print(f"   - {char['name']} ({char['race']} {char['class']})")
    print()

    # Test party creation
    print("Creating party...")
    try:
        party = create_party(providers=["groq", "gemini", "groq"])
        print(f"✅ Party created with {len(party)} players:")
        for i, player in enumerate(party, 1):
            provider = ["Groq", "Gemini", "Groq"][i-1]
            print(f"   {i}. {player.name} (Provider: {provider})")
    except Exception as e:
        print(f"❌ Party creation failed: {e}")
    print()

    # Test full game setup
    print("Creating full game (DM + Party)...")
    try:
        dm, players = create_game_agents()
        print(f"✅ Game agents created:")
        print(f"   DM: {dm.name} (OpenAI gpt-4o-mini)")
        print(f"   Players: {len(players)} agents")
        for player in players:
            print(f"      - {player.name}")
    except Exception as e:
        print(f"❌ Game creation failed: {e}")
