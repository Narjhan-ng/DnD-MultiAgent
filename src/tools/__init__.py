"""
Tool Registry for D&D Multi-Agent System

Exports all available tools for easy import by agents.
"""

from src.tools.dice import roll_dice, set_dice_seed

# Export all tools for easy import
__all__ = ['roll_dice', 'set_dice_seed']
