# D&D Multi-Agent System - Project Documentation

## Project Overview

Sistema multi-agente per simulare partite di Dungeons & Dragons 5e con 4 agenti (1 Dungeon Master + 3 giocatori) che interagiscono autonomamente. Gli spettatori possono avviare e osservare la partita attraverso un'interfaccia testuale.

---

## Architecture

### Agents

#### 1. Dungeon Master (DM)
- **Role**: Narratore, arbitro delle regole, gestore dei PNG e mostri
- **Knowledge Base (RAG)**:
  - Manuale del regolamento D&D 5e
  - Manuale dei mostri
  - Avventura specifica da giocare
- **Responsibilities**:
  - Descrivere scenari e ambientazioni
  - Gestire PNG e mostri
  - Arbitrare le regole
  - Gestire il flusso della narrazione
  - Chiamare i tiri di dado quando necessario

#### 2-4. Player Agents (3 giocatori)
- **Role**: Giocatori che controllano personaggi
- **Knowledge Base (RAG)**:
  - Manuale del regolamento D&D 5e (regole comuni)
- **Responsibilities**:
  - Prendere decisioni per il proprio personaggio
  - Dichiarare azioni in base al contesto
  - Rispettare le regole del gioco
  - Interagire con il DM e altri giocatori

**Character Details** (da definire):
- Player 1: [Classe, razza, background, personality]
- Player 2: [Classe, razza, background, personality]
- Player 3: [Classe, razza, background, personality]

---

## Technical Components

### 1. RAG System

#### Ingestion Phase

**Development Strategy**: Singola avventura piccola per velocità e focus

- **Documents to ingest**:
  - `players_handbook.pdf` (Player's Handbook 5e) - Solo sezioni essenziali (basic rules, combat, spells)
  - `monster_manual.pdf` (Monster Manual) - Solo mostri usati nell'avventura
  - `starter_adventure.pdf` - **Una singola avventura breve** (vedi raccomandazioni sotto)

- **Vector Collections**:
  - `dnd_rules` - Regole base (tutti gli agenti)
  - `dnd_monsters` - Mostri dell'avventura (solo DM)
  - `dnd_adventure` - L'avventura singola (solo DM)

- **Recommended Starter Adventures** (pick one):
  1. **"A Most Potent Brew"** - ~10 pagine, 1-shot, livello 1, perfetto per test
  2. **"The Delian Tomb"** - ~5 pagine, ultra-semplice, creato da Matthew Colville
  3. **"Wild Sheep Chase"** - ~15 pagine, divertente, auto-contenuta
  4. **Custom Micro-Adventure** - Crea una mini-avventura 5-10 pagine per massimo controllo

**Implementation**: IngestionPipeline con DoclingParser

**Note**: Multi-adventure support verrà implementato in fase futura (vedi Technical Enhancements)

#### Retrieval Phase
- **Implementation**: DagPipeline con query rewriting
- **Retrieval Strategy**: Semantic search con top-k chunks
- Ogni agente accede alle collection pertinenti durante le decisioni

### 2. Dice Rolling System

**Decision**: ✅ **Option A - Tool Function** (più performante)

**Rationale**:
- **Performance**: ~1ms (Python nativo) vs ~500ms (LLM sub-agent call)
- **Cost**: $0 vs $0.001 per roll
- **Reliability**: Deterministic, no hallucinations
- **Simplicity**: Implementazione diretta, meno moving parts

**Implementation**:
```python
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
    """
    # Parse notation
    pattern = r'(\d+)d(\d+)([+-]\d+)?(\s+(advantage|disadvantage))?'
    match = re.match(pattern, notation.lower().strip())

    if not match:
        return f"Invalid notation: {notation}"

    num_dice = int(match.group(1))
    num_sides = int(match.group(2))
    modifier = int(match.group(3) or 0)
    adv_type = match.group(5)  # 'advantage' or 'disadvantage' or None

    # Roll dice
    if adv_type:
        # Roll twice for advantage/disadvantage
        rolls1 = [random.randint(1, num_sides) for _ in range(num_dice)]
        rolls2 = [random.randint(1, num_sides) for _ in range(num_dice)]
        if adv_type == 'advantage':
            rolls = rolls1 if sum(rolls1) > sum(rolls2) else rolls2
            result_text = f"advantage (rolled {rolls1} and {rolls2}, kept {rolls}"
        else:
            rolls = rolls1 if sum(rolls1) < sum(rolls2) else rolls2
            result_text = f"disadvantage (rolled {rolls1} and {rolls2}, kept {rolls}"
    else:
        rolls = [random.randint(1, num_sides) for _ in range(num_dice)]
        result_text = str(rolls)

    total = sum(rolls) + modifier
    modifier_text = f" {modifier:+d}" if modifier != 0 else ""

    return f"{notation}: {result_text}{modifier_text} = {total}"

# Example outputs:
# roll_dice("1d20+3") → "1d20+3: [15] +3 = 18"
# roll_dice("2d6") → "2d6: [3, 5] = 8"
# roll_dice("1d20 advantage") → "1d20 advantage: (rolled [12] and [18], kept [18]) = 18"
```

**Requirements**:
- ✅ Supportare notazione standard: `1d20`, `2d6+3`, `1d20+5 advantage`, etc.
- ✅ Logging dei risultati sulla board
- ✅ Deterministic seed per replay (optional: set `random.seed()`)
- ✅ Advantage/disadvantage per D&D 5e

### 3. Shared Memory System

**Decision**: ✅ **Option C - Hybrid** (performance + flessibilità)

**Rationale**:
- **Performance**: Memory individuale = no contention, no bottleneck
- **Scalability**: Pronto per distribuzione multi-container futura
- **Traceability**: MessageBoard fornisce trace completo per UI e debugging
- **Flexibility**: Context snapshot per sincronizzazione efficiente

**Architecture**:
```python
class MessageBoard:
    """
    Event log completo di tutti i messaggi del gioco.
    Usato per UI display e trace.
    """
    def __init__(self):
        self.messages = []  # List of Message objects
        self.lock = asyncio.Lock()

    async def post(self, message: Message):
        async with self.lock:
            self.messages.append(message)
            await self.notify_subscribers(message)  # WebSocket push

    def get_recent(self, n: int = 50):
        """Get last N messages for UI"""
        return self.messages[-n:]

    def get_context_window(self, max_messages: int = 20):
        """Get recent messages formatted for LLM context"""
        recent = self.messages[-max_messages:]
        return "\n".join([f"[{m.speaker}]: {m.text}" for m in recent])


class Message:
    def __init__(self, speaker: str, text: str, metadata: dict = None):
        self.speaker = speaker  # "DM", "Player 1", "System", etc.
        self.text = text
        self.timestamp = time.time()
        self.metadata = metadata or {}  # type, dice_roll, etc.


class HybridMemorySystem:
    """
    Ogni agente ha propria Memory (Datapizza Memory object).
    Shared MessageBoard per coordinazione e UI.
    Context snapshot per efficienza.
    """
    def __init__(self):
        # Individual memories
        self.agent_memories = {
            "dm": Memory(),
            "player1": Memory(),
            "player2": Memory(),
            "player3": Memory()
        }

        # Shared components
        self.board = MessageBoard()
        self.context_snapshot = {
            "game_state": {},
            "last_sync": time.time()
        }

    async def agent_respond(self, agent_name: str, agent: Agent):
        """
        Agent generates response using:
        1. Own memory (conversation history)
        2. Recent board context (what others said)
        3. Context snapshot (game state)
        """
        # Build context from board
        board_context = self.board.get_context_window(max_messages=20)

        # Agent uses own memory + board context
        response = await agent.a_run(
            board_context,
            memory=self.agent_memories[agent_name]
        )

        # Update agent's memory
        self.agent_memories[agent_name].add_turn(
            TextBlock(content=response.text),
            role=ROLE.ASSISTANT
        )

        # Post to shared board
        message = Message(
            speaker=agent_name,
            text=response.text,
            metadata={"type": "agent_response"}
        )
        await self.board.post(message)

        return response

    def update_context_snapshot(self, game_state: dict):
        """
        Update shared context (HP, location, active effects, etc.)
        Lightweight sync without full memory replication.
        """
        self.context_snapshot["game_state"] = game_state
        self.context_snapshot["last_sync"] = time.time()
```

**Benefits**:
- ✅ **No Bottleneck**: Ogni agente ha propria Memory, no contention
- ✅ **Full Trace**: MessageBoard mantiene log completo per UI
- ✅ **Efficient Sync**: Context snapshot invece di full memory sharing
- ✅ **Scalable**: Pronto per Docker multi-container (Redis pub/sub per board)
- ✅ **Token Efficient**: Context window limitato (ultimi 20 messaggi) invece di full history

**Performance Considerations**:
- Context window: Ultimi 20 messaggi (~2000-3000 tokens) invece di full history
- Memory individuale: Illimitata (per agent internal reasoning)
- Board: Append-only log, ottimizzato per letture recenti
- Snapshot: Update ogni N turni, non ogni messaggio

### 4. Turn Management & Orchestration

**System**: Intelligent Orchestration (Dynamic, Context-Aware)

Per evitare un flusso rigido e ripetitivo (DM → P1 → P2 → P3 → DM → ...), il sistema usa un **orchestratore intelligente** che determina dinamicamente chi risponde in base al contesto.

#### Core Principles

1. **DM Maintains Control**: Il DM può dirigere la conversazione
2. **Dynamic Response**: I player rispondono quando è rilevante, non in ordine fisso
3. **Anti-Repetition**: Il sistema varia l'ordine per naturalezza
4. **Context-Aware**: L'ordine dipende dal tipo di situazione (esplorazione, combattimento, dialogo)

#### Orchestration Flow

```
[Spectator] --start--> [GameOrchestrator]
                             |
                             v
                        [DM Agent]
                             |
                             v
                    Parse DM Intent & Context
                             |
            +----------------+----------------+
            |                |                |
         DIRECTED          OPEN          INITIATIVE
            |                |                |
    [Specific Player]   [All Players]   [Initiative Order]
                             |
                    Gather Player Intents
                             |
                    Smart Ordering Algorithm
                             |
                +------------+------------+
                |            |            |
           [Player 2]   [Player 1]   [Player 3]
                |            |            |
                v            v            v
                    [Message Board]
                             |
                             v
                        [DM Response]
                             |
                        (cycle repeats)
```

#### DM Prompt Types

Il DM può generare 3 tipi di prompt che guidano l'orchestrazione:

**Type 1: Directed Prompt** (Player specifico)
```python
{
    "text": "Thorin, what do you do?",
    "type": "directed",
    "target": "Player 1",
    "context": "exploration"
}
```
→ Solo Player 1 risponde

**Type 2: Open Prompt** (Tutti possono rispondere)
```python
{
    "text": "You hear a noise behind the door. What do you do?",
    "type": "open",
    "target": None,
    "context": "exploration"
}
```
→ Tutti i player valutano se rispondere, sistema ordina intelligentemente

**Type 3: Initiative Prompt** (Ordine fisso)
```python
{
    "text": "Roll for initiative!",
    "type": "initiative",
    "target": None,
    "context": "combat"
}
```
→ Sistema usa initiative order (basato su roll iniziale)

#### Player Intent Generation

Quando il DM fa un **open prompt**, ogni player genera rapidamente un "intent":

```python
class PlayerAgent:
    async def generate_intent(self, dm_message, game_context):
        """
        Lightweight check: voglio rispondere a questo messaggio?
        """
        prompt = f"""
        DM: {dm_message}
        Game Context: {game_context}
        Your Character: {self.character_sheet}

        Do you want to respond to this situation?
        Rate your relevance (0-10): How appropriate is it for YOUR character to act now?
        Brief reason (one sentence).
        """

        response = await self.quick_invoke(prompt)  # Fast, low-token call

        return {
            "wants_to_respond": response.wants,      # bool
            "relevance_score": response.relevance,   # 0-10
            "reason": response.reason                # string
        }
```

**Example Intent Responses**:
```python
# DM: "You see a locked chest"

Player 1 (Fighter):
{
    "wants_to_respond": False,
    "relevance_score": 3,
    "reason": "I'm not skilled with locks, I'll let the rogue handle this"
}

Player 2 (Rogue):
{
    "wants_to_respond": True,
    "relevance_score": 9,
    "reason": "Perfect opportunity to use my lockpicking expertise"
}

Player 3 (Wizard):
{
    "wants_to_respond": True,
    "relevance_score": 6,
    "reason": "I could detect magic on it to check for traps"
}
```

#### Smart Ordering Algorithm

L'orchestratore ordina i player che vogliono rispondere usando:

```python
class GameOrchestrator:
    def smart_order(self, player_intents, context):
        """
        Ordina i player considerando:
        1. Relevance score (più rilevante = priorità)
        2. Recency (chi ha parlato meno recentemente)
        3. Variety (evita sempre lo stesso ordine)
        4. Character specialization (rogue per lockpicking, etc.)
        """

        active_players = [p for p in player_intents if p.wants_to_respond]

        if not active_players:
            # Fallback: random player
            return [random.choice(self.all_players)]

        # Score composito
        for player in active_players:
            player.priority = (
                player.relevance_score * 0.5 +          # Rilevanza al contesto
                self.recency_bonus(player) * 0.3 +      # Bonus se non ha parlato da un po'
                self.variety_bonus(player) * 0.2        # Bonus per variare ordine
            )

        # Ordina per priority (decrescente)
        ordered = sorted(active_players, key=lambda p: p.priority, reverse=True)

        return ordered
```

#### Flow Examples

**Example 1: Exploration (Open Prompt)**
```
[DM]: You enter a dark chamber with three exits. What do you do?
[System]: Type=OPEN, gathering player intents...

  Player 1 (Fighter): wants=True, relevance=5 "I'll guard the rear"
  Player 2 (Rogue): wants=True, relevance=8 "I'll check for traps"
  Player 3 (Wizard): wants=False, relevance=2 "Not my expertise"

[System]: Order: Player 2 (8), Player 1 (5)

[Player 2 - Kira]: I carefully examine the floor for pressure plates
[DM]: Roll Investigation
[Player 2]: *rolls 1d20+5* = 19
[DM]: You spot a hidden tripwire near the left exit
[Player 1 - Thrain]: I'll take the lead through the safe path
[DM]: The party moves cautiously forward...
```

**Example 2: Directed Prompt**
```
[DM]: Elara, the merchant is speaking to you. How do you respond?
[System]: Type=DIRECTED, target=Player 3

[Player 3 - Elara]: I greet him warmly and ask about his wares
[DM]: He shows you a selection of potions...
```

**Example 3: Combat (Initiative)**
```
[DM]: Three goblins leap from the shadows! Roll initiative!
[System]: Type=INITIATIVE, rolling...

  Player 2: 18
  Goblin 1: 15
  Player 1: 12
  Player 3: 9
  Goblin 2-3: 7

[System]: Initiative order locked: P2 → Goblin1 → P1 → P3 → Goblins

[Player 2 - Kira]: I attack with my shortbow at Goblin 1
[DM]: Roll to hit
[Player 2]: *rolls 1d20+5* = 17
[DM]: That hits! Roll damage
[Player 2]: *rolls 1d6+3* = 7
[DM]: Your arrow strikes true! The goblin snarls. His turn...
[DM]: Goblin 1 attacks Kira... *rolls* ... misses!
[Player 1 - Thrain]: I charge the nearest goblin with my greatsword
...
```

**Example 4: Mixed (Multiple Responses)**
```
[DM]: You find a strange magical artifact glowing on the pedestal. What do you do?
[System]: Type=OPEN

  Player 1: wants=True, relevance=4 "I'm cautious about magic"
  Player 2: wants=False, relevance=2 "Not interested"
  Player 3: wants=True, relevance=10 "MAGIC! My specialty!"

[System]: Order: Player 3 (10), Player 1 (4)

[Player 3 - Elara]: I cast Detect Magic to identify it
[DM]: Roll Arcana
[Player 3]: *rolls* = 22
[DM]: It's a powerful abjuration artifact, seems safe to touch
[Player 1 - Thrain]: I'll stand ready in case something goes wrong
[Player 3 - Elara]: I carefully pick it up
[DM]: The artifact pulses with energy and bonds to you...
```

#### Implementation Pseudo-Code

```python
class GameOrchestrator:
    def __init__(self):
        self.dm_agent = DMAgent()
        self.players = [Player1Agent(), Player2Agent(), Player3Agent()]
        self.board = MessageBoard()
        self.initiative_order = None
        self.last_speakers = []  # Track recent speakers

    async def game_loop(self):
        while self.game_active:
            # 1. DM narrates/prompts
            dm_response = await self.dm_agent.respond(self.board.context)
            self.board.post(dm_response)

            # 2. Parse DM intent
            intent = self.parse_dm_intent(dm_response)

            # 3. Determine who responds
            if intent.type == "directed":
                responders = [self.get_player(intent.target)]

            elif intent.type == "open":
                # Gather intents in parallel
                intents = await asyncio.gather(*[
                    player.generate_intent(dm_response, self.board.context)
                    for player in self.players
                ])
                responders = self.smart_order(intents)

            elif intent.type == "initiative":
                if not self.initiative_order:
                    self.initiative_order = await self.roll_initiative()
                responders = self.initiative_order

            # 4. Players respond in order
            for player in responders:
                player_response = await player.respond(self.board.context)
                self.board.post(player_response)
                self.last_speakers.append(player.name)

                # DM può reagire dopo ogni azione
                if self.dm_should_respond(player_response):
                    dm_reaction = await self.dm_agent.respond(self.board.context)
                    self.board.post(dm_reaction)

            # 5. Update game state
            self.update_context()

    def parse_dm_intent(self, dm_message):
        # Parse metadata o analizza il testo per determinare tipo
        if any(name in dm_message.text for name in self.player_names):
            return Intent(type="directed", target=self.extract_target(dm_message))
        elif "initiative" in dm_message.text.lower():
            return Intent(type="initiative")
        else:
            return Intent(type="open")

    def smart_order(self, player_intents):
        # Implementazione algoritmo di ordinamento
        # (vedi sezione precedente)
        pass
```

#### Performance Considerations

**Token Usage**:
- Intent generation: ~50-100 tokens per player
- Total per open prompt: ~150-300 tokens
- Accettabile per fluidità del gameplay

**Latency**:
- Intent generation: parallel → ~1-2 secondi totali
- Ordinamento: <100ms
- Totale overhead: ~2 secondi per decisione

**Optimization**:
- Cache intents simili (stesso contesto)
- Use faster models per intent generation (gpt-4o-mini, gemini-flash)
- Fallback a round-robin se timeout

#### Benefits

✅ **Naturalezza**: Players reagiscono quando ha senso, non meccanicamente
✅ **Varietà**: Ordine sempre diverso, evita monotonia
✅ **Specializzazione**: Characters con skill rilevanti parlano per primi
✅ **Controllo DM**: DM può dirigere quando necessario
✅ **Scalabilità**: Funziona con 3+ players
✅ **Immersione**: Simula tavolo reale dove i giocatori si "parlano sopra"

---

## LLM Models

### Development/Testing Phase
**Provider**: Groq (free API)
- **Model**: `llama-3.1-70b-versatile` o `mixtral-8x7b-32768`
- **Reason**: Free tier, buone performance, velocità
- **Implementation**: `OpenAILikeClient` o client Groq specifico

### Production Phase
**Multi-Model Strategy**:

| Agent | Model | Reason |
|-------|-------|--------|
| **DM** | Claude 3.5 Sonnet / GPT-4 | Migliore creatività narrativa, gestione complessità |
| **Player 1** | GPT-4o-mini | Bilanciamento costo/qualità |
| **Player 2** | Gemini 1.5 Flash | Velocità, context window ampio |
| **Player 3** | Mixtral 8x7B | Open source, performance solide |

**Justification**:
- DM richiede il modello migliore (narratore principale)
- Players possono usare modelli più economici
- Diversità di modelli → comportamenti più variegati

---

## User Interface

### Text-Based Interface

**Components**:
1. **Control Panel**:
   - Button: `[Start Adventure]`
   - Button: `[Pause]`
   - Button: `[Resume]`
   - Button: `[Stop]`
   - Settings: Model selection, turn speed, etc.

2. **Message Board** (main display):
   ```
   [DM]: You find yourselves at the entrance of a dark cave...
   [Player 1 - Thorin]: I light a torch and peer into the darkness
   [DM]: Roll a Perception check
   [System]: Thorin rolls 1d20+3 = [15] + 3 = 18
   [DM]: You notice ancient runes carved into the stone...
   [Player 2 - Elara]: I examine the runes using Arcana
   ...
   ```

3. **Status Panel** (sidebar):
   - Current turn indicator
   - Agent status (thinking, writing, waiting)
   - Token usage
   - Performance metrics

**Decision**: ✅ **Web UI** (FastAPI + React + WebSocket)

**Rationale**:
- **Accessibility**: Browser-based, no installation required
- **Real-time**: WebSocket per live updates dal game loop
- **Modern UX**: Responsive design, animazioni, rich formatting
- **Cross-platform**: Funziona su desktop, tablet, mobile
- **Deployment**: Facile deploy su cloud (Vercel, Railway, AWS)

**Tech Stack**:

**Backend**:
```python
# FastAPI + WebSocket + CORS
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import asyncio

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"])

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            await connection.send_json(message)

manager = ConnectionManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Receive commands from UI
            data = await websocket.receive_json()
            if data["type"] == "start_game":
                await game_orchestrator.start()
            elif data["type"] == "pause_game":
                await game_orchestrator.pause()
    except WebSocketDisconnect:
        manager.active_connections.remove(websocket)

@app.post("/api/start")
async def start_game():
    asyncio.create_task(run_game_loop())
    return {"status": "started"}
```

**Frontend** (Option 1 - React):
```jsx
// React + TypeScript + Tailwind CSS
import { useEffect, useState } from 'react'

function GameBoard() {
  const [messages, setMessages] = useState([])
  const [ws, setWs] = useState(null)

  useEffect(() => {
    const socket = new WebSocket('ws://localhost:8000/ws')

    socket.onmessage = (event) => {
      const message = JSON.parse(event.data)
      setMessages(prev => [...prev, message])
    }

    setWs(socket)
    return () => socket.close()
  }, [])

  return (
    <div className="game-container">
      <ControlPanel ws={ws} />
      <MessageBoard messages={messages} />
      <StatusPanel />
    </div>
  )
}
```

**Frontend** (Option 2 - Vanilla JS - più semplice per MVP):
```html
<!-- Simple HTML + Vanilla JS + Socket -->
<!DOCTYPE html>
<html>
<head>
    <title>D&D Multi-Agent Game</title>
    <style>
        .message-board { height: 500px; overflow-y: auto; }
        .message { padding: 10px; border-bottom: 1px solid #ddd; }
        .dm-message { background: #f0f8ff; }
        .player-message { background: #fff5f5; }
        .system-message { background: #f5f5f5; font-style: italic; }
    </style>
</head>
<body>
    <div id="control-panel">
        <button onclick="startGame()">Start Adventure</button>
        <button onclick="pauseGame()">Pause</button>
        <button onclick="stopGame()">Stop</button>
    </div>

    <div id="message-board" class="message-board"></div>

    <div id="status-panel">
        <div id="dm-status">DM: Ready</div>
        <div id="player1-status">Player 1: Ready</div>
        <div id="player2-status">Player 2: Ready</div>
        <div id="player3-status">Player 3: Ready</div>
    </div>

    <script>
        const ws = new WebSocket('ws://localhost:8000/ws')
        const board = document.getElementById('message-board')

        ws.onmessage = (event) => {
            const msg = JSON.parse(event.data)
            addMessage(msg)
        }

        function addMessage(msg) {
            const div = document.createElement('div')
            div.className = `message ${msg.type}-message`
            div.innerHTML = `<strong>[${msg.speaker}]</strong>: ${msg.text}`
            board.appendChild(div)
            board.scrollTop = board.scrollHeight
        }

        function startGame() {
            ws.send(JSON.stringify({type: 'start_game'}))
        }
    </script>
</body>
</html>
```

**Architecture Diagram**:
```
┌──────────────────────────────────────────┐
│          Browser (Frontend)              │
│  ┌────────────────────────────────────┐  │
│  │  Control Panel                     │  │
│  │  [Start] [Pause] [Stop] [Reset]   │  │
│  └────────────────────────────────────┘  │
│  ┌────────────────────────────────────┐  │
│  │  Message Board                     │  │
│  │  ┌──────────────────────────────┐ │  │
│  │  │ [DM]: Welcome adventurers... │ │  │
│  │  │ [Kira]: I look around...     │ │  │
│  │  │ [System]: Roll 1d20+3 = 18   │ │  │
│  │  │ [DM]: You notice...          │ │  │
│  │  └──────────────────────────────┘ │  │
│  │  [Auto-scroll, syntax highlight]  │  │
│  └────────────────────────────────────┘  │
│  ┌────────────────────────────────────┐  │
│  │  Status Panel                      │  │
│  │  🎭 DM: ⏳ Thinking...            │  │
│  │  ⚔️  Kira (P1): 💬 Ready          │  │
│  │  🏹 Thrain (P2): ⏸️  Waiting      │  │
│  │  🔮 Elara (P3): ✅ Done           │  │
│  │  📊 Tokens: 1.2K | Time: 45s     │  │
│  └────────────────────────────────────┘  │
└──────────────┬───────────────────────────┘
               │ WebSocket
               ▼
┌──────────────────────────────────────────┐
│   Backend (Python FastAPI)               │
│  ┌────────────────────────────────────┐  │
│  │  WebSocket Manager                 │  │
│  │  - broadcast(message)              │  │
│  │  - handle_commands()               │  │
│  └─────────────┬──────────────────────┘  │
│                │                          │
│  ┌─────────────▼──────────────────────┐  │
│  │  GameOrchestrator                  │  │
│  │  - DM Agent                        │  │
│  │  - Player Agents (3)               │  │
│  │  - HybridMemorySystem              │  │
│  │  - MessageBoard                    │  │
│  └────────────────────────────────────┘  │
└──────────────────────────────────────────┘
```

**Recommended Stack for MVP**:
- **Backend**: FastAPI + WebSocket (async native, semplice)
- **Frontend**: Vanilla HTML/JS (veloce da implementare)
- **Styling**: Tailwind CDN o CSS puro
- **Deploy**: Railway/Render (backend), Vercel (frontend statico)

**Future Enhancements**:
- React/Vue refactor per UI più ricca
- Message animations e typing indicators
- Dice roll animations (3D dice rolling)
- Character avatars e portraits
- Sound effects e background music
- Mobile-responsive layout

---

## Implementation Phases

### Phase 1: Core Setup ✓ (Planned)
- [x] Project structure
- [ ] Install Datapizza AI
- [ ] Setup Groq API
- [ ] Basic client connection test
- [ ] Document structure setup

### Phase 2: RAG System
- [ ] Select and acquire starter adventure (recommend: "A Most Potent Brew" or "The Delian Tomb")
- [ ] Acquire D&D 5e Basic Rules PDF (free SRD or essential sections from PHB)
- [ ] Extract relevant monsters from Monster Manual (only those in adventure)
- [ ] Implement ingestion pipeline for all 3 documents
- [ ] Create vector collections (dnd_rules, dnd_monsters, dnd_adventure)
- [ ] Test retrieval quality with sample queries
- [ ] Optimize chunk size and retrieval strategy

### Phase 3: Dice System
- [x] ✅ Decided: Tool Function approach (più performante)
- [ ] Implement `roll_dice` tool function con regex parsing
- [ ] Test notation parsing (1d20, 2d6+3, advantage/disadvantage)
- [ ] Add to DM and Player agents tool list
- [ ] Test integration con game flow

### Phase 4: Agent Implementation
- [ ] Implement base DM agent
- [ ] Implement Player agent template
- [ ] Define character sheets (3 players)
- [ ] Test individual agent responses
- [ ] Integrate RAG with agents

### Phase 5: Memory & Communication
- [x] ✅ Decided: Hybrid Memory System (Option C)
- [ ] Implement MessageBoard class (append-only event log)
- [ ] Implement Message class con metadata
- [ ] Implement HybridMemorySystem (individual memories + shared board)
- [ ] Implement GameOrchestrator with intelligent turn management
- [ ] Implement DM intent parsing (directed/open/initiative)
- [ ] Implement player intent generation system
- [ ] Implement smart ordering algorithm (relevance + recency + variety)
- [ ] Test multi-agent communication with dynamic turns
- [ ] Optimize performance (context window limiting, caching)

### Phase 6: User Interface
- [x] ✅ Decided: Web UI (FastAPI + WebSocket + Vanilla JS/React)
- [ ] Setup FastAPI backend with WebSocket support
- [ ] Implement ConnectionManager for WebSocket broadcasting
- [ ] Create frontend HTML structure (control panel, board, status)
- [ ] Implement WebSocket client connection
- [ ] Implement real-time message display (auto-scroll)
- [ ] Add control buttons (Start, Pause, Stop)
- [ ] Implement status panel with agent states
- [ ] Style UI (Tailwind CDN or custom CSS)
- [ ] Test end-to-end real-time updates
- [ ] Polish UX (animations, transitions, responsive)

### Phase 7: Integration & Testing
- [ ] End-to-end integration
- [ ] Run test adventure scenarios
- [ ] Performance optimization
- [ ] Bug fixes
- [ ] Documentation

### Phase 8: Production Ready (Optional)
- [ ] Switch to production models
- [ ] Deploy infrastructure
- [ ] Monitoring & logging
- [ ] Cost optimization

---

## Technical Decisions To Make

### High Priority
1. ~~**Memory Architecture**~~ ✅ **DECIDED**: Hybrid System (Option C - individual memories + shared board)
2. ~~**Dice System**~~ ✅ **DECIDED**: Tool Function (più performante, ~1ms latency)
3. ~~**UI Framework**~~ ✅ **DECIDED**: Web UI (FastAPI + WebSocket + Vanilla JS/React)
4. ~~**Turn Management**~~ ✅ **DECIDED**: Intelligent Orchestration (dynamic, context-aware)

### Medium Priority
5. Character definitions for 3 players (aligned with starter adventure level)
6. ~~Adventure module selection~~ ✅ **DECIDED**: Single small adventure for development
7. Retrieval strategy tuning (top-k, reranking)
8. Error handling & recovery strategies

### Low Priority
9. Observability & tracing integration
10. Save/load game state
11. Replay functionality
12. Multi-adventure support

---

## Resources & References

### Documents Needed

**For Development Phase**:
- [ ] **D&D 5e Basic Rules** (FREE): https://dnd.wizards.com/resources/systems-reference-document
  - Alternative: Extract essential chapters from Player's Handbook
- [ ] **Starter Adventure** (pick one):
  - "A Most Potent Brew" by Winghorn Press (pay-what-you-want on DMs Guild)
  - "The Delian Tomb" by Matthew Colville (free, Google search)
  - "Wild Sheep Chase" by Winghorn Press (pay-what-you-want)
- [ ] **Monster Stats** (extract from SRD or Monster Manual):
  - Only monsters used in selected adventure (typically 3-5 creature types)

**Optional/Future**:
- Full Player's Handbook PDF (more complete rules)
- Full Monster Manual PDF (for multi-adventure support)
- Additional adventures (Lost Mine of Phandelver, Curse of Strahd, etc.)

### APIs
- **Groq**: https://console.groq.com/ (free tier)
- **OpenAI**: https://platform.openai.com/ (production)
- **Anthropic**: https://console.anthropic.com/ (production DM)
- **Google AI**: https://ai.google.dev/ (production players)

### Framework Reference
- Datapizza AI: `/Users/nicolagnasso/projects/DnD/datapizza-ai-main/`
- Quick reference: `CLAUDE.md`
- Documentation: https://docs.datapizza.ai

---

## Notes & Ideas

### Gameplay Enhancements (Future)
- Character progression (XP, leveling)
- Inventory management
- Combat tracker with initiative
- Maps & visual descriptions
- Sound effects / ambient music
- Voice synthesis for character dialogue

### Technical Enhancements (Future)
- **Multi-Adventure Support**:
  - Adventure selection UI per utente
  - Hybrid cache system (on-demand ingestion + caching)
  - Qdrant snapshot/restore per fast loading
  - Pre-cache avventure popolari
  - Reference: Analisi completa Hybrid approach (A Priori vs On-Demand vs Hybrid)
- Distributed agents (multiple machines con Docker)
- Web-based spectator mode (streaming live)
- Save/load game state (serializzazione partita)
- AI DM training on custom adventures
- Player personality fine-tuning per comportamenti più distintivi
- Dynamic difficulty adjustment basato su performance party

---

## Changelog

### 2025-10-28
- Initial project documentation created
- Defined core architecture with 4 agents
- Outlined RAG system approach
- Listed implementation phases
- Identified key technical decisions
- **Added Intelligent Orchestration system**: Detailed turn management con dynamic ordering
  - DM intent types (directed/open/initiative)
  - Player intent generation mechanism
  - Smart ordering algorithm con relevance, recency, variety
  - Flow examples per diversi scenari
  - Performance considerations e pseudo-code implementativo
- Decided on dynamic turn management approach (avoids rigid round-robin)
- **Simplified development strategy**: Single small adventure per initial development
  - Recommended starter adventures: "A Most Potent Brew", "The Delian Tomb", "Wild Sheep Chase"
  - Use D&D 5e Basic Rules (SRD - free) instead of full PHB
  - Extract only necessary monsters for the adventure
  - Multi-adventure support moved to future enhancements
  - Added detailed multi-adventure roadmap (Hybrid cache approach) for Phase 8+
- **Finalized ALL high-priority technical decisions**:
  1. ✅ **Memory System**: Hybrid (individual agent memories + shared MessageBoard)
     - Performance: No bottleneck, token-efficient context windows
     - Implementation: MessageBoard class + HybridMemorySystem
     - Full pseudo-code provided
  2. ✅ **Dice Rolling**: Tool Function approach
     - Performance: ~1ms vs ~500ms for sub-agent
     - Cost: $0 vs $0.001 per roll
     - Full implementation with regex parsing, advantage/disadvantage support
  3. ✅ **UI Framework**: Web UI (FastAPI + WebSocket)
     - Backend: FastAPI with async WebSocket
     - Frontend: Vanilla JS for MVP, React for future
     - Real-time updates via WebSocket broadcasting
     - Full code examples and architecture diagrams provided
  4. ✅ **Turn Management**: Intelligent Orchestration (already decided earlier)
- Updated all implementation phases with specific tasks based on decisions
- All core architecture decisions now complete - ready for development!

---

## Project Status

**Current Status**: ✅ **Functionally Complete** (as of 2025-11-11)

### Completed Phases

- ✅ **Phase 1**: Setup & Environment (2025-11-07)
- ✅ **Phase 2**: RAG System (2025-11-09)
- ✅ **Phase 3**: Dice Tools (2025-11-09)
- ✅ **Phase 4**: Agent Implementation (2025-11-10)
- ✅ **Phase 5**: Orchestration & Memory (2025-11-10)
- ✅ **Phase 6**: Web UI (2025-11-10)
- ✅ **Phase 7**: Integration & Testing (2025-11-11)

### System Capabilities

The D&D Multi-Agent System is now fully operational with the following features:

**Core Functionality**:
- ✅ 1 Dungeon Master + 3 Player agents with distinct personalities
- ✅ RAG-powered knowledge retrieval (rules, monsters, adventure)
- ✅ Automatic dice rolling with D&D 5e notation
- ✅ Intelligent turn management and orchestration
- ✅ Real-time web interface with WebSocket updates
- ✅ Autonomous gameplay without manual intervention

**Validated Through Testing**:
- ✅ Automated playthrough test infrastructure (`tests/test_playthrough.py`)
- ✅ 10-turn playthrough completed successfully
- ✅ Multi-agent coordination verified
- ✅ Narrative quality: 8/10 rating
- ✅ Average turn latency: ~7.5 seconds
- ✅ System stability: No crashes or deadlocks

**Known Limitations**:
- ⚠️ OpenAI rate limit (200K TPM) restricts extended sessions to ~10 turns
  - **Workaround**: Use Gemini for player agents (documented in `docs/BUGS.md`)
- ⚠️ Long session stability (50+ turns) not fully tested due to rate limit
- ⚠️ User documentation incomplete (technical docs complete)

### How to Use

1. **Start the server**:
   ```bash
   python src/ui/run_server.py
   ```

2. **Open browser**: Navigate to `http://localhost:8000`

3. **Start adventure**: Click "Start Adventure" button

4. **Watch the game**: Agents play autonomously, real-time updates via WebSocket

5. **Run automated test** (optional):
   ```bash
   python tests/test_playthrough.py --max-turns 15
   ```

### Documentation

- **Phase Documentation**: `docs/phases/PHASE_*.md` (all phases)
- **Bug Tracking**: `docs/BUGS.md`
- **Completion Report**: `docs/phases/PHASE_07_COMPLETION.md`
- **Code Examples**: `docs/examples/*.py`

### Future Enhancements (Optional - Phase 8)

If continuing development, consider:
- Provider distribution (Gemini for players) to overcome rate limits
- User authentication and persistent game state
- Token tracking and cost management
- Extended documentation (user guides)
- Performance optimizations (context window reduction)

---

## Next Steps

**Project is complete for local use.** No further phases required.

Optional: Phase 8 (Production Ready) - See `docs/phases/PHASE_08_PRODUCTION.md` for deployment considerations.
