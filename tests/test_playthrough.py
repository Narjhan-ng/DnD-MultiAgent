"""
Automated Playthrough Testing Script

Runs a complete adventure playthrough without browser interaction.
Collects metrics: duration, turns, messages, errors, coherence.

Usage:
    python tests/test_playthrough.py [--max-turns 50] [--output logs/playthrough.txt]

Reference: docs/phases/PHASE_07_INTEGRATION.md
"""

import asyncio
import time
import argparse
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv

from src.agents.dm_agent import create_dm_agent
from src.agents.player_agent import create_player_agent
from src.memory.hybrid_memory import HybridMemorySystem
from src.orchestration.orchestrator import GameOrchestrator


# Character sheets for test playthrough
CHARACTER_THORIN = {
    "name": "Thorin",
    "race": "Dwarf",
    "class": "Fighter",
    "level": 3,
    "background": "Soldier",
    "personality": "Brave, loyal, protective. Values honor and courage.",
    "skills": ["Athletics", "Intimidation", "Survival"]
}

CHARACTER_ELARA = {
    "name": "Elara",
    "race": "Elf",
    "class": "Wizard",
    "level": 3,
    "background": "Sage",
    "personality": "Intelligent, curious, strategic. Loves solving mysteries.",
    "skills": ["Arcana", "History", "Investigation"]
}

CHARACTER_FINN = {
    "name": "Finn",
    "race": "Halfling",
    "class": "Rogue",
    "level": 3,
    "background": "Criminal",
    "personality": "Witty, cautious, observant. Quick with jokes.",
    "skills": ["Stealth", "Sleight of Hand", "Perception"]
}


class PlaythroughMetrics:
    """Collects and tracks playthrough metrics"""

    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.total_turns = 0
        self.total_messages = 0
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.dm_messages = 0
        self.player_messages = 0
        self.system_messages = 0
        self.timeouts = 0
        self.exceptions = 0

    def start(self):
        """Start timing"""
        self.start_time = time.time()

    def stop(self):
        """Stop timing"""
        self.end_time = time.time()

    @property
    def duration_seconds(self) -> float:
        """Total duration in seconds"""
        if not self.start_time or not self.end_time:
            return 0.0
        return self.end_time - self.start_time

    @property
    def duration_minutes(self) -> float:
        """Total duration in minutes"""
        return self.duration_seconds / 60.0

    @property
    def avg_time_per_turn(self) -> float:
        """Average time per turn in seconds"""
        if self.total_turns == 0:
            return 0.0
        return self.duration_seconds / self.total_turns

    def add_error(self, error: str):
        """Record an error"""
        self.errors.append(error)
        if "timeout" in error.lower():
            self.timeouts += 1
        else:
            self.exceptions += 1

    def add_warning(self, warning: str):
        """Record a warning"""
        self.warnings.append(warning)

    def analyze_messages(self, board):
        """Analyze messages from message board"""
        self.total_messages = len(board.messages)

        for msg in board.messages:
            if msg.speaker == "DM":
                self.dm_messages += 1
            elif msg.speaker == "System":
                self.system_messages += 1
                # Check for errors in system messages
                if msg.metadata and msg.metadata.get("type") == "error":
                    self.add_error(msg.content)
            else:
                self.player_messages += 1

    def generate_report(self) -> str:
        """Generate human-readable report"""
        report = []
        report.append("=" * 60)
        report.append("PLAYTHROUGH METRICS REPORT")
        report.append("=" * 60)
        report.append(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")

        report.append("⏱️  TIMING")
        report.append(f"  Duration: {self.duration_minutes:.1f} minutes ({self.duration_seconds:.1f}s)")
        report.append(f"  Total Turns: {self.total_turns}")
        report.append(f"  Avg Time/Turn: {self.avg_time_per_turn:.2f}s")
        report.append("")

        report.append("💬 MESSAGES")
        report.append(f"  Total Messages: {self.total_messages}")
        report.append(f"  DM Messages: {self.dm_messages}")
        report.append(f"  Player Messages: {self.player_messages}")
        report.append(f"  System Messages: {self.system_messages}")
        report.append("")

        report.append("⚠️  ERRORS & WARNINGS")
        report.append(f"  Total Errors: {len(self.errors)}")
        report.append(f"  Timeouts: {self.timeouts}")
        report.append(f"  Exceptions: {self.exceptions}")
        report.append(f"  Warnings: {len(self.warnings)}")

        if self.errors:
            report.append("")
            report.append("  Error Details:")
            for i, error in enumerate(self.errors[:10], 1):  # Show first 10
                report.append(f"    {i}. {error}")
            if len(self.errors) > 10:
                report.append(f"    ... and {len(self.errors) - 10} more errors")

        if self.warnings:
            report.append("")
            report.append("  Warning Details:")
            for i, warning in enumerate(self.warnings[:5], 1):  # Show first 5
                report.append(f"    {i}. {warning}")
            if len(self.warnings) > 5:
                report.append(f"    ... and {len(self.warnings) - 5} more warnings")

        report.append("")
        report.append("✅ VALIDATION CHECKLIST")
        report.append(f"  [ ] Average turn latency < 5s: {'✅' if self.avg_time_per_turn < 5.0 else '❌'} ({self.avg_time_per_turn:.2f}s)")
        report.append(f"  [ ] No critical errors: {'✅' if len(self.errors) == 0 else '❌'} ({len(self.errors)} errors)")
        report.append(f"  [ ] Completed full adventure: {'✅' if self.total_turns >= 20 else '⚠️'} ({self.total_turns} turns)")
        report.append("")

        report.append("=" * 60)

        return "\n".join(report)


async def setup_game_system(verbose: bool = True):
    """
    Initialize all game components (agents, memory, orchestrator).

    Returns:
        GameOrchestrator instance ready to run
    """
    if verbose:
        print("🎲 Setting up game system...")

    # Load environment variables
    load_dotenv()

    # 1. Create agents using factory functions
    if verbose:
        print("  🎭 Creating agents...")

    # DM Agent
    dm_agent = create_dm_agent(model="gpt-4o-mini", temperature=0.8)

    # Player Agents (using existing character sheets)
    player_agents = [
        create_player_agent(CHARACTER_THORIN, provider="openai", temperature=0.9),
        create_player_agent(CHARACTER_ELARA, provider="openai", temperature=0.9),
        create_player_agent(CHARACTER_FINN, provider="openai", temperature=0.9)
    ]

    # 2. Create memory system
    if verbose:
        print("  🧠 Initializing memory system...")

    agent_names = ["DM"] + [agent.name for agent in player_agents]
    memory_system = HybridMemorySystem(agent_names=agent_names)

    # 3. Create orchestrator
    if verbose:
        print("  🎼 Creating orchestrator...")
    orchestrator = GameOrchestrator(
        dm_agent=dm_agent,
        player_agents=player_agents,
        memory_system=memory_system
    )

    if verbose:
        print("✅ Game system ready!\n")

    return orchestrator


async def run_playthrough(max_turns: int = 50, output_file: str = None, verbose: bool = True):
    """
    Run a complete playthrough and collect metrics.

    Args:
        max_turns: Maximum number of turns
        output_file: Optional file path to save transcript
        verbose: Print progress to console

    Returns:
        PlaythroughMetrics instance with results
    """
    metrics = PlaythroughMetrics()

    try:
        # Setup
        orchestrator = await setup_game_system(verbose=verbose)

        # Run game loop
        if verbose:
            print(f"🎮 Starting adventure (max {max_turns} turns)...\n")
            print("=" * 60)

        metrics.start()

        await orchestrator.game_loop(
            max_turns=max_turns,
            initial_prompt="Begin a short D&D adventure for a party of three adventurers exploring a mysterious abandoned tower."
        )

        metrics.stop()
        metrics.total_turns = orchestrator.turn_count

        # Analyze messages
        metrics.analyze_messages(orchestrator.memory.board)

        if verbose:
            print("=" * 60)
            print("\n✅ Playthrough complete!\n")

        # Save transcript if requested
        if output_file:
            await save_transcript(orchestrator.memory.board, output_file, metrics)
            if verbose:
                print(f"💾 Transcript saved to: {output_file}\n")

    except Exception as e:
        metrics.add_error(f"Fatal error: {str(e)}")
        if verbose:
            print(f"\n❌ Playthrough failed: {e}\n")
        raise

    return metrics


async def save_transcript(board, output_file: str, metrics: PlaythroughMetrics):
    """Save complete game transcript to file"""
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        # Header
        f.write("=" * 80 + "\n")
        f.write("D&D MULTI-AGENT PLAYTHROUGH TRANSCRIPT\n")
        f.write("=" * 80 + "\n")
        f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Duration: {metrics.duration_minutes:.1f} minutes\n")
        f.write(f"Total Turns: {metrics.total_turns}\n")
        f.write(f"Total Messages: {metrics.total_messages}\n")
        f.write("\n" + "=" * 80 + "\n\n")

        # Messages
        for i, msg in enumerate(board.messages, 1):
            timestamp = msg.metadata.get('timestamp', 'N/A') if msg.metadata else 'N/A'
            f.write(f"[{i}] {msg.speaker} ({timestamp})\n")
            f.write("-" * 80 + "\n")
            f.write(f"{msg.content}\n\n")

        # Footer
        f.write("\n" + "=" * 80 + "\n")
        f.write("END OF TRANSCRIPT\n")
        f.write("=" * 80 + "\n")


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Run automated D&D playthrough test")
    parser.add_argument(
        "--max-turns",
        type=int,
        default=30,
        help="Maximum number of turns (default: 30)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="logs/playthrough_01.txt",
        help="Output file for transcript (default: logs/playthrough_01.txt)"
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress progress output"
    )

    args = parser.parse_args()

    # Run playthrough
    metrics = await run_playthrough(
        max_turns=args.max_turns,
        output_file=args.output,
        verbose=not args.quiet
    )

    # Print report
    print(metrics.generate_report())

    # Save metrics to separate file
    metrics_file = args.output.replace(".txt", "_metrics.txt")
    with open(metrics_file, 'w') as f:
        f.write(metrics.generate_report())

    print(f"\n📊 Metrics saved to: {metrics_file}")

    # Exit with error code if there were errors
    if metrics.errors:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
