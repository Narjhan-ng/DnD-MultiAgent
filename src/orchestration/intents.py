"""
Intent Parsing & Generation System

Provides:
- IntentType enum (DIRECTED, OPEN, INITIATIVE)
- DMIntent parsing from DM messages
- PlayerIntent generation with relevance scoring
- Smart ordering algorithm for player responses

Reference: docs/phases/PHASE_05_ORCHESTRATION.md
"""

import re
import random
import os
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field
from datapizza.agents import Agent
from datapizza.clients.openai import OpenAIClient

# Create dedicated intent client (fast model for structured outputs)
_intent_client = None

def get_intent_client():
    """Get or create OpenAI client for intent generation"""
    global _intent_client
    if _intent_client is None:
        _intent_client = OpenAIClient(
            api_key=os.getenv("OPENAI_API_KEY"),
            model="gpt-4o-mini",  # Fast and supports structured outputs
            temperature=0.3
        )
    return _intent_client


class IntentType(Enum):
    """Types of DM prompts"""
    DIRECTED = "directed"      # Specific player addressed
    OPEN = "open"             # All players can respond
    INITIATIVE = "initiative"  # Combat started (initiative order)


class DMIntent:
    """Parsed DM intent from message"""

    def __init__(
        self,
        intent_type: IntentType,
        target: Optional[str] = None,
        context: str = "exploration"
    ):
        self.type = intent_type
        self.target = target  # Player name if DIRECTED
        self.context = context  # "exploration", "combat", "dialogue"

    def __repr__(self):
        if self.type == IntentType.DIRECTED:
            return f"DMIntent(DIRECTED → {self.target})"
        else:
            return f"DMIntent({self.type.value.upper()})"


def parse_dm_intent(dm_message: str, player_names: List[str]) -> DMIntent:
    """
    Parse DM message to determine intent type.

    Logic:
    1. Check for initiative/combat keywords → INITIATIVE
    2. Check for specific player name → DIRECTED
    3. Default → OPEN

    Args:
        dm_message: DM's message text
        player_names: List of player character names

    Returns:
        DMIntent with type and optional target
    """
    text_lower = dm_message.lower()

    # Check for initiative/combat
    initiative_keywords = [
        "initiative",
        "roll for initiative",
        "combat begins",
        "attacks",
        "roll initiative"
    ]
    if any(keyword in text_lower for keyword in initiative_keywords):
        return DMIntent(IntentType.INITIATIVE, context="combat")

    # Check for directed prompt (player name mentioned)
    for name in player_names:
        # Match whole word (avoid false positives)
        pattern = rf'\b{re.escape(name.lower())}\b'
        if re.search(pattern, text_lower):
            return DMIntent(IntentType.DIRECTED, target=name, context="exploration")

    # Check context clues
    context = "exploration"
    if any(word in text_lower for word in ["says", "asks you", "speaks to"]):
        context = "dialogue"

    # Default: open prompt
    return DMIntent(IntentType.OPEN, context=context)


class PlayerIntent(BaseModel):
    """Player agent's intent to respond"""
    player_name: str = ""
    wants_to_respond: bool
    relevance_score: int = Field(ge=0, le=10)  # 0-10
    reason: str


async def generate_player_intent(
    player_agent: Agent,
    dm_message: str,
    game_context: str
) -> PlayerIntent:
    """
    Generate intent for a player agent.

    Uses dedicated OpenAI client for structured outputs (Groq doesn't support json_schema).

    Args:
        player_agent: Player agent to query
        dm_message: DM's latest message
        game_context: Recent game context (from MessageBoard)

    Returns:
        PlayerIntent with relevance score and reasoning
    """
    # Get character info from agent's system prompt
    character_name = player_agent.name

    intent_prompt = f"""
You are analyzing whether {character_name} should respond to this D&D game situation.

DM Message: {dm_message}
Recent Game Context: {game_context}

Evaluate if {character_name} wants to respond to this situation.
Rate relevance (0-10): How appropriate is it for {character_name} to act now?
Provide a brief reason (one sentence).
"""

    try:
        # Use dedicated OpenAI client (supports structured outputs)
        client = get_intent_client()
        response = await client.a_structured_response(
            input=intent_prompt,
            output_cls=PlayerIntent
        )

        intent = response.structured_data[0]
        intent.player_name = character_name
        return intent

    except Exception as e:
        # Fallback: default intent
        print(f"Error generating intent for {character_name}: {e}")
        return PlayerIntent(
            player_name=character_name,
            wants_to_respond=True,
            relevance_score=5,
            reason="Default response due to error"
        )


def smart_order_players(
    player_intents: List[PlayerIntent],
    last_speakers: List[str]
) -> List[str]:
    """
    Order players by relevance, recency, and variety.

    Scoring algorithm:
    - Relevance: 50% weight (character expertise match)
    - Recency: 30% weight (bonus if haven't spoken recently)
    - Variety: 20% weight (random factor for unpredictability)

    Args:
        player_intents: List of player intents
        last_speakers: Recent speaker history (most recent last)

    Returns:
        Ordered list of player names
    """
    # Filter only players who want to respond
    active_intents = [p for p in player_intents if p.wants_to_respond]

    if not active_intents:
        # Fallback: no one wants to respond
        return []

    scored_players = []
    for intent in active_intents:
        # Relevance score (0-10, normalize to 0-1)
        relevance = intent.relevance_score / 10.0

        # Recency bonus (penalty for recent speakers)
        recency = 1.0
        if last_speakers:
            if intent.player_name in last_speakers[-3:]:
                recency = 0.5  # Spoke in last 3 turns
            if intent.player_name == last_speakers[-1]:
                recency = 0.0  # Spoke last turn

        # Variety bonus (random factor 0-0.3)
        variety = random.random() * 0.3

        # Composite priority score
        priority = (relevance * 0.5) + (recency * 0.3) + (variety * 0.2)

        scored_players.append((intent.player_name, priority, intent.reason))

    # Sort by priority (descending)
    scored_players.sort(key=lambda x: x[1], reverse=True)

    return [name for name, _, _ in scored_players]
