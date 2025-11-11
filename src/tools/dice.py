"""
Dice Rolling Tool for D&D Multi-Agent System

Complete implementation of roll_dice tool function with support for:
- Basic notation: 1d20, 2d6, 3d8
- Modifiers: 1d20+5, 2d6-2
- Advantage/Disadvantage: 1d20 advantage, 1d20 disadvantage

Reference: docs/phases/PHASE_03_DICE.md
"""

import re
import random
from datapizza.tools import tool


@tool
def roll_dice(notation: str) -> str:
    """
    Roll dice in standard D&D notation.

    Supported formats:
    - Basic: "1d20", "2d6", "3d8"
    - With modifier: "1d20+5", "2d6-2"
    - Advantage/Disadvantage: "1d20 advantage", "1d20 disadvantage"

    Returns formatted string with individual rolls and total.

    Examples:
        >>> roll_dice("1d20")
        "1d20: [15] = 15"

        >>> roll_dice("2d6+3")
        "2d6+3: [4, 5] +3 = 12"

        >>> roll_dice("1d20 advantage")
        "1d20 advantage: rolled [12] and [18], kept [18] = 18"
    """
    # Parse notation with regex
    # Pattern: (num)d(sides)(+/-modifier)? (advantage|disadvantage)?
    pattern = r'(\d+)d(\d+)([+-]\d+)?(\s+(advantage|disadvantage))?'
    match = re.match(pattern, notation.lower().strip())

    if not match:
        return f"Invalid notation: {notation}"

    # Extract components
    num_dice = int(match.group(1))
    num_sides = int(match.group(2))
    modifier = int(match.group(3) or 0)
    adv_type = match.group(5)  # 'advantage' or 'disadvantage' or None

    # Validation
    if num_dice < 1 or num_dice > 100:
        return f"Invalid number of dice: {num_dice} (must be 1-100)"
    if num_sides < 2 or num_sides > 1000:
        return f"Invalid die size: d{num_sides} (must be d2-d1000)"

    # Roll dice
    if adv_type:
        # Roll twice for advantage/disadvantage
        rolls1 = [random.randint(1, num_sides) for _ in range(num_dice)]
        rolls2 = [random.randint(1, num_sides) for _ in range(num_dice)]

        if adv_type == 'advantage':
            rolls = rolls1 if sum(rolls1) > sum(rolls2) else rolls2
            result_text = f"rolled {rolls1} and {rolls2}, kept {rolls}"
        else:  # disadvantage
            rolls = rolls1 if sum(rolls1) < sum(rolls2) else rolls2
            result_text = f"rolled {rolls1} and {rolls2}, kept {rolls}"
    else:
        # Normal roll
        rolls = [random.randint(1, num_sides) for _ in range(num_dice)]
        result_text = str(rolls)

    # Calculate total
    total = sum(rolls) + modifier

    # Format output
    modifier_text = f" {modifier:+d}" if modifier != 0 else ""
    return f"{notation}: {result_text}{modifier_text} = {total}"


def set_dice_seed(seed: int):
    """
    Set random seed for reproducible dice rolls.
    Useful for testing and replay functionality.

    Args:
        seed: Integer seed for random number generator
    """
    random.seed(seed)


# Example usage (not executed when imported as module)
if __name__ == "__main__":
    print("=== Dice Rolling Tool Examples ===\n")

    # Basic rolls
    print("Basic Rolls:")
    print(f"  {roll_dice('1d20')}")
    print(f"  {roll_dice('2d6')}")
    print(f"  {roll_dice('3d8')}")
    print()

    # With modifiers
    print("With Modifiers:")
    print(f"  {roll_dice('1d20+5')}")
    print(f"  {roll_dice('2d6-2')}")
    print(f"  {roll_dice('1d8+3')}")
    print()

    # Advantage/Disadvantage
    print("Advantage/Disadvantage:")
    print(f"  {roll_dice('1d20 advantage')}")
    print(f"  {roll_dice('1d20 disadvantage')}")
    print(f"  {roll_dice('1d20+3 advantage')}")
    print()

    # Common D&D scenarios
    print("Common D&D Scenarios:")
    print(f"  Initiative: {roll_dice('1d20+3')}")
    print(f"  Attack roll: {roll_dice('1d20+5')}")
    print(f"  Damage (longsword): {roll_dice('1d8+3')}")
    print(f"  Fireball damage: {roll_dice('8d6')}")
    print(f"  Saving throw: {roll_dice('1d20+2')}")
    print()

    # Invalid notation
    print("Invalid Notation:")
    print(f"  {roll_dice('invalid')}")
    print(f"  {roll_dice('d20')}")  # Missing number of dice
