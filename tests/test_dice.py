"""
Test Suite for Dice Rolling Tool

Comprehensive tests for roll_dice tool covering:
- Basic notation (1d20, 2d6, etc.)
- Modifiers (+5, -2)
- Advantage/Disadvantage
- Invalid input handling
- Common D&D scenarios
- Performance

Reference: docs/phases/PHASE_03_DICE.md
"""

import re
import time
from src.tools.dice import roll_dice, set_dice_seed


def test_basic_notation():
    """Test basic dice notation (XdY)"""
    print("=== Test Basic Notation ===")

    # Test single die
    result = roll_dice("1d20")
    assert "1d20" in result
    assert "=" in result
    print(f"✅ Single die: {result}")

    # Test multiple dice
    result = roll_dice("3d6")
    assert "[" in result  # Should show individual rolls
    assert "=" in result
    print(f"✅ Multiple dice: {result}")

    # Test different die sizes
    for die in ["d4", "d6", "d8", "d10", "d12", "d20", "d100"]:
        result = roll_dice(f"1{die}")
        assert f"1{die}" in result
        assert "=" in result
        print(f"✅ {die}: {result}")

    print()


def test_modifiers():
    """Test dice with modifiers (+X, -X)"""
    print("=== Test Modifiers ===")

    # Positive modifier
    result = roll_dice("1d20+5")
    assert "+5" in result
    assert "=" in result
    print(f"✅ Positive modifier: {result}")

    # Negative modifier
    result = roll_dice("2d6-2")
    assert "-2" in result
    assert "=" in result
    print(f"✅ Negative modifier: {result}")

    # No modifier
    result = roll_dice("1d8")
    assert "+" not in result
    assert "-" not in result
    print(f"✅ No modifier: {result}")

    print()


def test_advantage_disadvantage():
    """Test advantage and disadvantage mechanics"""
    print("=== Test Advantage/Disadvantage ===")

    # Advantage
    result = roll_dice("1d20 advantage")
    assert "advantage" in result.lower()
    assert "rolled" in result.lower()  # Should show both rolls
    assert "kept" in result.lower()
    print(f"✅ Advantage: {result}")

    # Disadvantage
    result = roll_dice("1d20 disadvantage")
    assert "disadvantage" in result.lower()
    assert "rolled" in result.lower()
    assert "kept" in result.lower()
    print(f"✅ Disadvantage: {result}")

    # Advantage with modifier
    result = roll_dice("1d20+3 advantage")
    assert "advantage" in result.lower()
    assert "+3" in result
    print(f"✅ Advantage with modifier: {result}")

    print()


def test_invalid_input():
    """Test invalid notation handling"""
    print("=== Test Invalid Input ===")

    # Invalid notation
    result = roll_dice("invalid")
    assert "invalid" in result.lower() or "error" in result.lower()
    print(f"✅ Invalid notation: {result}")

    # Missing number of dice
    result = roll_dice("d20")
    assert "invalid" in result.lower()
    print(f"✅ Missing dice count: {result}")

    # Empty string
    result = roll_dice("")
    assert "invalid" in result.lower()
    print(f"✅ Empty string: {result}")

    print()


def test_dnd_scenarios():
    """Test common D&D scenarios"""
    print("=== Test Common D&D Scenarios ===")

    # Initiative roll
    init_roll = roll_dice("1d20+3")
    print(f"✅ Initiative: {init_roll}")
    assert "1d20+3" in init_roll

    # Attack roll with advantage
    attack_roll = roll_dice("1d20+5 advantage")
    print(f"✅ Attack (advantage): {attack_roll}")
    assert "advantage" in attack_roll.lower()

    # Damage roll
    damage_roll = roll_dice("2d6+3")
    print(f"✅ Damage: {damage_roll}")
    assert "2d6+3" in damage_roll

    # Saving throw
    save_roll = roll_dice("1d20+2")
    print(f"✅ Saving throw: {save_roll}")
    assert "1d20+2" in save_roll

    # Spell damage (Fireball)
    fireball = roll_dice("8d6")
    print(f"✅ Fireball damage: {fireball}")
    assert "8d6" in fireball

    print()


def test_deterministic_rolls():
    """Test deterministic rolls with seed"""
    print("=== Test Deterministic Rolls (Seed) ===")

    # Set seed and roll
    set_dice_seed(42)
    result1 = roll_dice("3d6")

    # Reset seed and roll again
    set_dice_seed(42)
    result2 = roll_dice("3d6")

    # Should be identical
    assert result1 == result2
    print(f"✅ Seeded roll 1: {result1}")
    print(f"✅ Seeded roll 2: {result2}")
    print("✅ Deterministic rolls match!")

    print()


def test_result_format():
    """Test that results are properly formatted"""
    print("=== Test Result Format ===")

    # Basic format: "XdY: [rolls] = total"
    result = roll_dice("2d6")
    pattern = r"2d6: \[\d+, \d+\] = \d+"
    assert re.match(pattern, result), f"Format mismatch: {result}"
    print(f"✅ Basic format: {result}")

    # With modifier: "XdY+Z: [rolls] +Z = total"
    result = roll_dice("2d6+3")
    pattern = r"2d6\+3: \[\d+, \d+\] \+3 = \d+"
    assert re.match(pattern, result), f"Format mismatch: {result}"
    print(f"✅ Modifier format: {result}")

    # Advantage: shows both rolls
    result = roll_dice("1d20 advantage")
    assert "rolled" in result
    assert "kept" in result
    print(f"✅ Advantage format: {result}")

    print()


def test_performance():
    """Test performance of dice rolling"""
    print("=== Test Performance ===")

    start = time.time()
    for _ in range(1000):
        roll_dice("1d20+5")
    elapsed = time.time() - start

    avg_time_ms = (elapsed / 1000) * 1000
    print(f"✅ 1000 rolls in {elapsed:.2f}s ({avg_time_ms:.2f}ms per roll)")

    # Should be < 2ms per roll
    assert avg_time_ms < 2.0, f"Performance too slow: {avg_time_ms:.2f}ms per roll"
    print("✅ Performance acceptable (< 2ms per roll)")

    print()


def test_validation():
    """Test input validation"""
    print("=== Test Validation ===")

    # Too many dice
    result = roll_dice("101d6")
    assert "invalid" in result.lower()
    print(f"✅ Too many dice: {result}")

    # Invalid die size
    result = roll_dice("1d1001")
    assert "invalid" in result.lower()
    print(f"✅ Invalid die size: {result}")

    # Zero dice
    result = roll_dice("0d20")
    assert "invalid" in result.lower()
    print(f"✅ Zero dice: {result}")

    print()


def run_all_tests():
    """Run all test suites"""
    print("\n" + "="*60)
    print("DICE ROLLING TOOL - COMPREHENSIVE TEST SUITE")
    print("="*60 + "\n")

    try:
        test_basic_notation()
        test_modifiers()
        test_advantage_disadvantage()
        test_invalid_input()
        test_dnd_scenarios()
        test_deterministic_rolls()
        test_result_format()
        test_validation()
        test_performance()

        print("="*60)
        print("✅ ALL TESTS PASSED!")
        print("="*60 + "\n")
        return True

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}\n")
        return False
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}\n")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
