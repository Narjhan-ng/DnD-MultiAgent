# D&D Multi-Agent System

An autonomous AI-powered Dungeons & Dragons 5e game simulation featuring 1 Dungeon Master and 3 Player agents that interact autonomously to create dynamic, emergent storytelling.

**Status**: ✅ **Functionally Complete** (November 2025)

---

## 🎲 Overview

This system simulates complete D&D gaming sessions where:
- **1 DM Agent** narrates the adventure, manages NPCs/monsters, and enforces D&D 5e rules
- **3 Player Agents** control unique characters with distinct personalities (Thorin the Fighter, Elara the Wizard, Finn the Rogue)
- **Intelligent Orchestration** manages dynamic, context-aware turn-taking
- **RAG System** provides on-demand D&D 5e knowledge (rules, monsters, adventure content)
- **Real-time Web UI** allows spectators to watch games unfold via WebSocket

## ✨ Features

- 🤖 **Multi-Agent Gameplay**: Autonomous agents with distinct personalities and playstyles
- 📚 **RAG-Powered Knowledge**: Semantic retrieval from D&D 5e rules, monster stats, and adventure content
- 🎯 **Intelligent Turn Management**: Intent-based orchestration with smart player ordering (relevance + recency + variety)
- 🎲 **Automatic Dice Rolling**: Built-in dice tool supporting D&D notation (`1d20+5`, `2d6`, advantage/disadvantage)
- 🌐 **Real-time Web Interface**: Live game spectating with WebSocket updates
- 💾 **Hybrid Memory System**: Individual agent memories + shared MessageBoard (no bottlenecks)
- 🔄 **Dynamic Narratives**: Emergent storytelling with 8/10 narrative quality rating
- ⚡ **High Performance**: ~7.5s average turn latency

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.9+**
- **API Keys** (minimum: OpenAI for embeddings and agents):
  - **OpenAI** (required) - For agents and embeddings
  - **Groq** (optional) - Fast, free alternative for player agents
  - **Google Gemini** (optional) - Alternative provider to avoid rate limits
  - **Anthropic Claude** (optional) - Production-quality DM agent

### Installation

```bash
# Clone repository
git clone <your-repo-url>
cd DnD

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Or install manually:
pip install datapizza-ai
pip install datapizza-ai-clients-google
pip install datapizza-ai-clients-anthropic
pip install datapizza-ai-parsers-docling
pip install fastapi uvicorn websockets python-dotenv qdrant-client
```

### Configuration

Create a `.env` file in the project root:

```bash
# Required
OPENAI_API_KEY=your_openai_api_key_here

# Optional (for alternative providers)
GROQ_API_KEY=your_groq_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

**Important**: By default, the system uses OpenAI for all agents. OpenAI has a rate limit of 200K tokens/minute, which restricts sessions to ~10 turns. To play longer sessions, consider mixing providers (see Known Limitations below).

### Running the Game

#### Option 1: Web Interface (Recommended)

```bash
# Start the web server
python src/ui/run_server.py

# Open browser to http://localhost:8000
# Click "Start Adventure" and watch the agents play autonomously!
```

#### Option 2: Automated Testing

```bash
# Run automated playthrough test (10-30 turns)
python tests/test_playthrough.py --max-turns 15

# Save transcript to file
python tests/test_playthrough.py --max-turns 15 --output logs/game_session.txt
```

#### Option 3: Component Testing

```bash
# Test individual components
python tests/test_rag.py              # RAG retrieval system
python tests/test_agents.py           # Agent creation and responses
python tests/test_orchestration.py    # Full orchestration stack
python tests/test_dice.py             # Dice rolling tool
```

---

## 📖 Documentation

### Core Documentation

- **[PROJECT.md](PROJECT.md)** - Complete project architecture, technical decisions, and design rationale
- **Implementation code** - See `src/` directory for full implementation (agents, memory, orchestration, RAG, tools, UI)
- **Character sheets** - See `data/characters/*.yaml` for character definitions

**Note**: Phase documentation (`docs/phases/`) and internal development docs (`CLAUDE.md`, `docs/examples/`, `docs/BUGS.md`) are excluded from version control but available locally for development reference.

### What Was Built

Development was completed across 7 phases (Nov 7-11, 2025):

1. **Phase 1: Setup** ✅ - Environment configuration, dependencies, API setup
2. **Phase 2: RAG System** ✅ - Document ingestion pipeline + retrieval system (Qdrant + OpenAI embeddings)
3. **Phase 3: Dice System** ✅ - Dice rolling tool with D&D 5e notation support
4. **Phase 4: Agents** ✅ - DM and Player agent implementations with distinct personalities
5. **Phase 5: Orchestration** ✅ - HybridMemorySystem, MessageBoard, GameOrchestrator, intent system
6. **Phase 6: UI** ✅ - FastAPI WebSocket server + HTML/CSS/JS frontend
7. **Phase 7: Integration** ✅ - End-to-end testing, validation, bug documentation

**Phase 8 (Production)** is optional and not yet implemented (deployment, monitoring, scaling).

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────┐
│           Web Browser (Spectator)           │
│  ┌───────────────────────────────────────┐  │
│  │  Control Panel  │  Message Board      │  │
│  │  [Start/Pause]  │  [Auto-scroll]      │  │
│  │  Status Panel   │  Live Updates       │  │
│  └───────────────────────────────────────┘  │
└─────────────┬───────────────────────────────┘
              │ WebSocket (Real-time)
              ▼
┌─────────────────────────────────────────────┐
│      FastAPI Server + GameOrchestrator      │
│  ┌─────────────────────────────────────┐   │
│  │  DM Agent (OpenAI gpt-4o-mini)      │   │
│  │  - RAG tools (rules, monsters, adv) │   │
│  │  - Dice rolling tool                │   │
│  │  - Narrative generation             │   │
│  └─────────────────────────────────────┘   │
│  ┌─────────────────────────────────────┐   │
│  │  Player Agents (3 Characters)       │   │
│  │  - Thorin (Fighter, cautious)       │   │
│  │  - Elara (Wizard, curious)          │   │
│  │  - Finn (Rogue, witty)              │   │
│  │  - Intent-based participation       │   │
│  └─────────────────────────────────────┘   │
│  ┌─────────────────────────────────────┐   │
│  │  HybridMemorySystem                 │   │
│  │  - Individual agent memories        │   │
│  │  - Shared MessageBoard              │   │
│  │  - Context window (last 20 msgs)    │   │
│  └─────────────────────────────────────┘   │
└─────────────┬───────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────┐
│  RAG System (Qdrant + OpenAI Embeddings)   │
│  - dnd_rules collection (basic rules)       │
│  - dnd_monsters collection (monster stats)  │
│  - dnd_adventure collection (story content) │
└─────────────────────────────────────────────┘
```

### Key Design Decisions

- **Hybrid Memory**: Individual agent memories prevent context pollution, shared board enables coordination
- **Intent System**: Players generate "intents" (want to respond? relevance score 0-10) → smart ordering by relevance + recency + variety
- **RAG Tools**: Knowledge retrieval wrapped as `@tool` functions → agents call naturally ("What are grappling rules?")
- **Dice as Tool**: Python function (~1ms) instead of LLM sub-agent (~500ms) → 500x faster, deterministic
- **Multi-Provider**: Supports OpenAI, Groq, Gemini, Anthropic via factory pattern

---

## 🛠️ Tech Stack

- **Framework**: [Datapizza AI](https://datapizza.ai) - Multi-agent orchestration framework
- **LLM Providers**: OpenAI (default), Groq, Google Gemini, Anthropic Claude
- **Vector Store**: Qdrant (in-memory mode for development)
- **Embeddings**: OpenAI text-embedding-3-small (1536 dimensions)
- **Web Server**: FastAPI + WebSocket (real-time communication)
- **Frontend**: Vanilla HTML/CSS/JavaScript (MVP)
- **Testing**: pytest + custom playthrough automation

---

## 📊 Project Status

### Completion Status

| Phase | Status | Completion Date |
|-------|--------|-----------------|
| Phase 1: Setup | ✅ Complete | Nov 7, 2025 |
| Phase 2: RAG System | ✅ Complete | Nov 9, 2025 |
| Phase 3: Dice Tools | ✅ Complete | Nov 9, 2025 |
| Phase 4: Agents | ✅ Complete | Nov 10, 2025 |
| Phase 5: Orchestration | ✅ Complete | Nov 10, 2025 |
| Phase 6: Web UI | ✅ Complete | Nov 10, 2025 |
| Phase 7: Integration & Testing | ✅ Complete | Nov 11, 2025 |
| Phase 8: Production Deployment | ⏳ Optional | Not started |

**Current Status**: ✅ **System is functionally complete and operational**

### Validated Features

**Core Functionality** (All Working):
- ✅ Autonomous multi-agent gameplay (no manual intervention required)
- ✅ 1 DM + 3 player agents with distinct personalities
- ✅ RAG-powered knowledge retrieval (rules, monsters, adventure)
- ✅ Automatic dice rolling with D&D 5e notation
- ✅ Intelligent turn management (intent-based orchestration)
- ✅ Real-time WebSocket UI with live updates
- ✅ Hybrid memory system (individual + shared)

**Validated Through Testing**:
- ✅ 10-turn automated playthrough completed successfully
- ✅ Multi-agent coordination: All 3 players participate naturally
- ✅ Narrative quality: **8/10 rating** (excellent coherence and creativity)
- ✅ Average turn latency: **~7.5 seconds**
- ✅ System stability: No crashes or deadlocks
- ✅ Character differentiation: Thorin (cautious), Elara (curious), Finn (witty) personalities emerge clearly

### Known Limitations

⚠️ **OpenAI Rate Limit** (Critical):
- OpenAI has a 200K tokens/minute limit
- System hits limit at ~10 turns with all OpenAI agents
- **Workaround**: Mix providers (e.g., DM: OpenAI, Players: Groq/Gemini)
- See local `docs/BUGS.md` (Bug #5) for detailed solution

⚠️ **Other Limitations**:
- Extended sessions (50+ turns) not fully tested due to rate limit
- RAG tools partially tested (insufficient turns before rate limit)
- Logging uses `print()` instead of Python logging module
- Production deployment not implemented (Phase 8)

---

## 🎯 Testing & Performance

### Test Suite

```bash
# Run all tests
python -m pytest tests/ -v

# Individual test files
python tests/test_setup.py            # Environment validation
python tests/test_rag.py              # RAG pipeline (ingestion + retrieval)
python tests/test_dice.py             # Dice tool unit tests
python tests/test_agents.py           # Agent creation and responses
python tests/test_orchestration.py    # Memory, intents, orchestration
python tests/test_playthrough.py      # End-to-end automated gameplay
```

### Performance Metrics (10-turn test)

| Metric | Value | Status |
|--------|-------|--------|
| **Average turn latency** | ~7.5 seconds | ✅ Excellent |
| **DM response time** | 2-5 seconds | ✅ Good |
| **Player intent generation** (parallel) | 3-6 seconds | ✅ Good |
| **Player response time** | 2-8 seconds | ✅ Good |
| **RAG retrieval latency** | ~500ms | ✅ Fast |
| **Messages per turn** | 5-10 messages | ✅ Natural |
| **Token usage** | ~2,350 tokens/turn | ✅ Efficient |
| **Total messages generated** | 60+ messages | ✅ Rich |
| **System stability** | 100% (no crashes) | ✅ Stable |
| **Narrative quality** | 8/10 | ✅ High-quality |

### Test Results Summary

**What Works**:
- ✅ System runs autonomously without manual intervention
- ✅ All 3 players participate with distinct personalities
- ✅ Turn management (OPEN/DIRECTED intents) works correctly
- ✅ Dice tool called successfully multiple times
- ✅ Narrative coherence maintained across turns
- ✅ Character differentiation clear (Thorin cautious, Elara curious, Finn witty)

**Partially Tested**:
- ⚠️ RAG tools (only 10 turns completed before rate limit)
- ⚠️ Long-session stability (50+ turns not tested)

---

## 📦 Project Structure

```
DnD/
├── src/
│   ├── agents/              # DM and Player agent implementations
│   │   ├── dm_agent.py      # Dungeon Master with RAG tools
│   │   └── player_agent.py  # Player agent factory (multi-provider)
│   ├── memory/              # Memory management
│   │   ├── hybrid_memory.py # HybridMemorySystem (individual + shared)
│   │   └── message_board.py # MessageBoard (event log + pub/sub)
│   ├── orchestration/       # Game loop and coordination
│   │   ├── orchestrator.py  # GameOrchestrator (main game loop)
│   │   └── intents.py       # Intent parsing and smart ordering
│   ├── rag/                 # RAG system
│   │   ├── ingestion.py     # Document ingestion pipeline
│   │   └── retrieval.py     # Retrieval pipeline + tool wrappers
│   ├── tools/               # Custom tools
│   │   └── dice.py          # Dice rolling with D&D notation
│   ├── ui/                  # Web interface
│   │   ├── server.py        # FastAPI WebSocket server
│   │   └── run_server.py    # Server entry point
│   └── config.py            # Configuration management
│
├── tests/                   # Comprehensive test suite (9 files)
│   ├── test_setup.py        # Environment validation
│   ├── test_rag.py          # RAG pipeline tests
│   ├── test_dice.py         # Dice tool unit tests
│   ├── test_agents.py       # Agent tests
│   ├── test_orchestration.py # Orchestration tests
│   └── test_playthrough.py  # End-to-end automated gameplay
│
├── data/
│   ├── characters/          # Character sheets (YAML)
│   │   ├── thorin.yaml      # Thorin the Fighter
│   │   ├── elara.yaml       # Elara the Wizard
│   │   └── finn.yaml        # Finn the Rogue
│   ├── documents/           # D&D knowledge base (3 files)
│   │   ├── basic_rules.txt  # D&D 5e rules
│   │   ├── monsters.txt     # Monster stats
│   │   └── adventure.txt    # Adventure content
│   └── vectorstore/         # Qdrant database (excluded from git)
│
├── frontend/                # Web UI
│   ├── index.html           # Main page
│   ├── style.css            # Styling
│   └── app.js               # WebSocket client
│
├── logs/                    # Game logs (excluded from git)
├── PROJECT.md               # Complete architecture documentation
├── README.md                # This file
├── requirements.txt         # Python dependencies
├── .env.example             # Environment configuration template
└── .gitignore               # Git exclusions
```

---

## 🚀 Future Enhancements (Optional)

### Phase 8: Production Deployment (Not Implemented)

If deploying to production, consider:

**High Priority**:
- [ ] Mix LLM providers (DM: OpenAI, Players: Groq/Gemini) to avoid rate limits
- [ ] Structured logging (replace `print()` with Python `logging` module)
- [ ] Rate limiting middleware with exponential backoff
- [ ] Configuration management (move hard-coded values to YAML/TOML)

**Medium Priority**:
- [ ] Observability (Datapizza ContextTracing for token tracking)
- [ ] Docker containerization
- [ ] CI/CD pipeline
- [ ] Session persistence (save/load game state)

**Low Priority**:
- [ ] Authentication/authorization
- [ ] Multi-user support (multiple concurrent games)
- [ ] Prometheus metrics

### Advanced Features (Future Vision)

- [ ] **Multi-adventure support**: Dynamic adventure loading from library
- [ ] **Character progression**: XP tracking, leveling, equipment management
- [ ] **Persistent game state**: Save/load campaigns across sessions
- [ ] **Voice synthesis**: TTS for character dialogue with distinct voices
- [ ] **3D dice animations**: Visual dice roll effects
- [ ] **Character portraits**: AI-generated character images
- [ ] **Battle maps**: Visual grid-based combat
- [ ] **Mobile UI**: Responsive design for tablets/phones
- [ ] **Streaming responses**: Real-time token-by-token generation
- [ ] **RAG caching**: Cache frequent queries (rules lookups)

---

## 🐛 Known Issues & Workarounds

### Critical Issues

**Issue #1: OpenAI Rate Limit Blocks Extended Sessions**
- **Problem**: 200K tokens/minute limit reached at ~10 turns with all OpenAI agents
- **Impact**: Cannot run long sessions (30+ turns)
- **Workaround**: Mix providers in `src/agents/player_agent.py`:
  ```python
  player1 = create_player_agent(char1, provider="groq")     # Groq
  player2 = create_player_agent(char2, provider="gemini")   # Gemini
  player3 = create_player_agent(char3, provider="openai")   # OpenAI
  ```
- **Permanent Fix**: Implement rate limiting middleware with request queuing

### Minor Issues

- **Logging**: Uses `print()` instead of logging module (not production-ready)
- **Hard-coded values**: Some configuration values in code instead of config file
- **RAG testing**: Tools not extensively tested due to rate limit

See local `docs/BUGS.md` for complete bug documentation (excluded from git).

---

## 🤝 Contributing

This is a personal research project, but feedback and contributions are welcome!

**How to contribute**:
- Report bugs via GitHub issues
- Suggest features or improvements
- Share your own multi-agent D&D experiments
- Fork and extend with your own adventures or character types

**Areas for contribution**:
- Additional LLM provider integrations
- New adventure modules
- UI/UX improvements
- Performance optimizations
- Documentation improvements

---

## 🙏 Acknowledgments

- **[Datapizza AI](https://datapizza.ai)** - Excellent multi-agent orchestration framework
- **Wizards of the Coast** - D&D 5e System Reference Document (SRD)
- **OpenAI** - GPT-4o-mini for high-quality agent responses
- **Groq** - Fast, free LLM API for development
- **D&D Community** - Inspiration from human players worldwide

---

## 📄 License

This project is for educational and research purposes. D&D content is used under the Open Gaming License (OGL).

---

**Built with [Datapizza AI](https://datapizza.ai)** - A modern framework for multi-agent orchestration
