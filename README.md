# D&D Multi-Agent System

An autonomous AI-powered Dungeons & Dragons 5e game simulation featuring 1 Dungeon Master and 3 Player agents that interact autonomously to create dynamic, emergent storytelling.

## 🎲 Overview

This system simulates complete D&D gaming sessions where:
- **1 DM Agent** narrates the adventure, manages NPCs/monsters, and enforces rules
- **3 Player Agents** control unique characters with distinct personalities
- **Intelligent Orchestration** manages dynamic turn-taking based on context
- **RAG System** provides D&D 5e knowledge (rules, monsters, adventures)
- **Real-time Web UI** allows spectators to watch the game unfold

## ✨ Features

- 🤖 **Multi-Agent Gameplay**: Autonomous agents with unique personalities
- 📚 **RAG-Powered Knowledge**: Semantic retrieval of D&D rules and lore
- 🎯 **Intelligent Turn Management**: Context-aware player ordering
- 🎲 **Automatic Dice Rolling**: Built-in dice tool with advantage/disadvantage
- 🌐 **Real-time Web Interface**: Watch games live via WebSocket
- 💾 **Hybrid Memory System**: Efficient context management
- 🔄 **Dynamic Narratives**: Emergent storytelling from agent interactions

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- API keys for:
  - Groq (free tier - for development)
  - OpenAI (for embeddings)

### Installation

```bash
# Clone repository
cd /path/to/DnD

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install datapizza-ai
pip install datapizza-ai-clients-google
pip install datapizza-ai-clients-anthropic
pip install datapizza-ai-parsers-docling
pip install fastapi uvicorn websockets python-dotenv

# Create .env file
cp .env.example .env
# Edit .env and add your API keys
```

### Configuration

Create a `.env` file in the project root:

```bash
GROQ_API_KEY=your_groq_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here  # Optional, for production
```

### Running the Game

```bash
# Start the web server
python src/ui/run_server.py

# Open browser
open http://localhost:8000

# Click "Start Adventure" and watch!
```

## 📖 Documentation

### Core Documentation

- **[PROJECT.md](PROJECT.md)**: Complete project architecture and technical decisions
- **[CLAUDE.md](CLAUDE.md)**: Datapizza AI framework reference and patterns
- **[User Guide](docs/USER_GUIDE.md)**: How to use the system *(to be created in Phase 7)*
- **[Developer Guide](docs/DEVELOPER_GUIDE.md)**: How to extend and modify *(to be created in Phase 7)*

### Implementation Phases

Development is organized into 8 phases:

1. **[Phase 1: Setup](docs/phases/PHASE_01_SETUP.md)** - Environment setup and dependencies
2. **[Phase 2: RAG System](docs/phases/PHASE_02_RAG.md)** - Document ingestion and retrieval
3. **[Phase 3: Dice System](docs/phases/PHASE_03_DICE.md)** - Dice rolling tool implementation
4. **[Phase 4: Agents](docs/phases/PHASE_04_AGENTS.md)** - DM and Player agents
5. **[Phase 5: Orchestration](docs/phases/PHASE_05_ORCHESTRATION.md)** - Memory and turn management
6. **[Phase 6: UI](docs/phases/PHASE_06_UI.md)** - Web interface with WebSocket
7. **[Phase 7: Integration](docs/phases/PHASE_07_INTEGRATION.md)** - Testing and optimization
8. **[Phase 8: Production](docs/phases/PHASE_08_PRODUCTION.md)** - Deployment (optional)

### Code Examples

Complete implementation examples in [`docs/examples/`](docs/examples/):

- [`dice_tool.py`](docs/examples/dice_tool.py) - Dice rolling with advantage/disadvantage
- [`memory_system.py`](docs/examples/memory_system.py) - Hybrid memory architecture
- [`orchestrator.py`](docs/examples/orchestrator.py) - Game loop and turn management
- [`dm_agent.py`](docs/examples/dm_agent.py) - Dungeon Master agent
- [`player_agent.py`](docs/examples/player_agent.py) - Player agent template
- [`websocket_server.py`](docs/examples/websocket_server.py) - FastAPI server

## 🏗️ Architecture

```
┌─────────────────────────────────────────────┐
│           Web Browser (Spectator)           │
│  ┌───────────────────────────────────────┐  │
│  │  Control Panel  │  Message Board      │  │
│  │  Status Panel   │  Auto-scroll        │  │
│  └───────────────────────────────────────┘  │
└─────────────┬───────────────────────────────┘
              │ WebSocket (Real-time)
              ▼
┌─────────────────────────────────────────────┐
│      FastAPI Server + GameOrchestrator      │
│  ┌─────────────────────────────────────┐   │
│  │  DM Agent (RAG + Dice + Narrative)  │   │
│  └─────────────────────────────────────┘   │
│  ┌─────────────────────────────────────┐   │
│  │  Player Agents (3 Characters)       │   │
│  │  - Intelligent turn ordering        │   │
│  │  - Context-aware responses          │   │
│  └─────────────────────────────────────┘   │
│  ┌─────────────────────────────────────┐   │
│  │  Hybrid Memory System               │   │
│  │  - Individual memories              │   │
│  │  - Shared MessageBoard              │   │
│  └─────────────────────────────────────┘   │
└─────────────┬───────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────┐
│  RAG System (Qdrant + OpenAI Embeddings)   │
│  - D&D 5e Rules                             │
│  - Monster Stats                            │
│  - Adventure Narrative                      │
└─────────────────────────────────────────────┘
```

## 🛠️ Tech Stack

- **Framework**: [Datapizza AI](https://docs.datapizza.ai) - Multi-agent orchestration
- **LLM Providers**: Groq (dev), OpenAI, Anthropic, Google Gemini (prod)
- **Vector Store**: Qdrant (in-memory or external)
- **Embeddings**: OpenAI text-embedding-3-small
- **Web Server**: FastAPI + WebSocket
- **Frontend**: Vanilla HTML/CSS/JS (MVP), React (future)

## 📊 Project Status

| Phase | Status | Completion |
|-------|--------|------------|
| Phase 1: Setup | ⏳ Pending | 0% |
| Phase 2: RAG | ⏳ Pending | 0% |
| Phase 3: Dice | ⏳ Pending | 0% |
| Phase 4: Agents | ⏳ Pending | 0% |
| Phase 5: Orchestration | ⏳ Pending | 0% |
| Phase 6: UI | ⏳ Pending | 0% |
| Phase 7: Integration | ⏳ Pending | 0% |
| Phase 8: Production | ⏳ Optional | 0% |

**Current Stage**: Planning complete, ready for Phase 1 implementation

## 🎯 Roadmap

### MVP (Phases 1-6)
- [x] Architecture design and technical decisions
- [x] Documentation structure
- [ ] Core implementation (Phases 1-6)
- [ ] End-to-end testing
- [ ] Demo video

### Future Enhancements
- [ ] Multi-adventure support
- [ ] Character progression (XP, leveling)
- [ ] Save/load game states
- [ ] Voice synthesis for character dialogue
- [ ] 3D dice roll animations
- [ ] Character portraits and maps
- [ ] Mobile-responsive UI

## 🤝 Contributing

This is a personal project, but feedback and suggestions are welcome! Feel free to:
- Report bugs via issues
- Suggest features or improvements
- Share your own multi-agent D&D experiments

## 🙏 Acknowledgments

- **Datapizza AI** - Multi-agent framework
- **D&D 5e SRD** - Rules and content (Wizards of the Coast)
- **Groq** - Fast, free LLM API for development
- Inspired by the creativity of human D&D players worldwide

---

*"In the realm of imagination, even artificial minds can weave tales of wonder."*
