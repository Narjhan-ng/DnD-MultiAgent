# Phase 01 - Human Player Integration

**Data Inizio**: 2025-11-11
**Durata Stimata**: 1-2 giorni
**Status**: 🔵 Pianificata

---

## Recap Fase Precedente

**Phase 7 - Integration & Testing** (Completata il 2025-11-11)

Il sistema D&D Multi-Agent è stato completato con successo nelle prime 7 fasi di sviluppo:
- ✅ 1 DM + 3 Player agents AI completamente autonomi
- ✅ RAG system con Player's Handbook, Monster Manual, Adventure
- ✅ Intelligent orchestration (dynamic turn management)
- ✅ Web UI con WebSocket real-time updates
- ✅ Automated testing (10-turn playthrough validated)
- ✅ System stability verificata

Il sistema attuale è **funzionalmente completo** per partite autonome con solo agenti AI. Non è presente alcuna possibilità di interazione umana diretta.

---

## Obiettivi Phase 01

Questa fase introduce la possibilità di **giocatori umani** nel sistema, permettendo una **configurazione flessibile** della partita:

- 0 giocatori umani → partita AI autonoma (modalità attuale)
- 1 giocatore umano + 2 AI → partita collaborativa
- 2 giocatori umani + 1 AI → partita prevalentemente umana
- 3 giocatori umani + 0 AI → partita completamente umana

Ogni giocatore umano può scegliere un personaggio dalla galleria (default o custom) e interagirà tramite un'interfaccia dedicata durante il proprio turno.

---

## Componenti da Implementare

### 1.1 HumanPlayerAgent Wrapper

**File**: `src/agents/human_agent.py` (NUOVO)

#### Descrizione
Classe che incapsula un giocatore umano e lo rende compatibile con l'interfaccia degli Agent AI esistenti. Gestisce l'async wait per l'input dell'utente tramite WebSocket.

#### Responsabilità
- Implementare interfaccia Agent-like (`a_run()` method)
- Gestire `asyncio.Future` per aspettare input utente
- Timeout 60 secondi → fallback a risposta AI-generata
- Notificare UI quando è il turno del giocatore
- Supportare metadata per dice rolls e tool calls

#### Struttura Chiave
```python
class HumanPlayerAgent:
    def __init__(self, character_sheet: dict):
        self.name = character_sheet['name']
        self.character_sheet = character_sheet
        self.pending_prompt = None
        self.response_future: Optional[asyncio.Future] = None
        self.timeout_seconds = 60

    async def a_run(self, prompt: str) -> Response:
        """
        Metodo principale compatibile con Agent AI.
        Restituisce response quando human submits via WebSocket.
        """
        # Implementazione con Future + timeout

    def submit_response(self, text: str):
        """Chiamato dal WebSocket handler quando l'utente invia risposta"""
```

#### Test di Validazione
- [ ] `test_human_agent_basic_response()` - risposta normale entro timeout
- [ ] `test_human_agent_timeout()` - timeout 60s → fallback AI
- [ ] `test_human_agent_character_sheet()` - accesso corretto a character data

---

### 1.2 Lobby System (Setup Partita)

**File**: `src/ui/frontend/lobby.html` (NUOVO)

#### Descrizione
Interfaccia per configurare la partita prima dell'avvio. L'utente seleziona quanti giocatori umani parteciperanno (0-3) e assegna personaggi a ciascun slot.

#### UI Layout
```
┌────────────────────────────────────────────┐
│ D&D Multi-Agent System - Game Setup       │
├────────────────────────────────────────────┤
│ Number of Human Players:                   │
│   [All AI] [1 Human] [2 Humans] [3 Humans]│
├────────────────────────────────────────────┤
│ Player Slot 1: [Human/AI Toggle]           │
│   Character: [Thorin Ironforge ▼]          │
│   [Preview] [Create New Character]         │
│                                             │
│ Player Slot 2: [Human/AI Toggle]           │
│   Character: [Elara Moonshadow ▼]          │
│   [Preview] [Create New Character]         │
│                                             │
│ Player Slot 3: [Human/AI Toggle]           │
│   Character: [Finn Quickfoot ▼]            │
│   [Preview] [Create New Character]         │
├────────────────────────────────────────────┤
│         [Start Adventure]                  │
└────────────────────────────────────────────┘
```

#### Funzionalità
- Selezione numero giocatori umani (0-3)
- Dropdown per assegnare personaggi da galleria
- Preview character (modal con full stats)
- Button "Create New Character" → character creator (Phase 03)
- Validazione: almeno 1 player (umano o AI)

#### API Endpoint Richiesti
- `GET /api/characters` - lista personaggi disponibili
- `GET /api/characters/{name}` - dettagli personaggio per preview
- `POST /api/configure_game` - salva configurazione partita

---

### 1.3 Backend - Game Configuration

**File**: `src/ui/server.py` (MODIFICA)

#### Endpoint da Aggiungere

##### `POST /api/configure_game`
Riceve configurazione dalla lobby e la salva per `start_game()`.

```python
class GameConfig(BaseModel):
    players: List[PlayerConfig]

class PlayerConfig(BaseModel):
    slot: int  # 1, 2, 3
    type: str  # "human" or "ai"
    character_file: str  # path to YAML

@app.post("/api/configure_game")
async def configure_game(config: GameConfig):
    global game_config
    game_config = config
    return {"status": "configured"}
```

##### `POST /api/start_game` (MODIFICA)
Modifica per leggere `game_config` e istanziare mix di HumanPlayerAgent e Agent AI.

```python
async def start_game():
    players = []
    for player_cfg in game_config.players:
        if player_cfg.type == "human":
            # Create HumanPlayerAgent
            char_sheet = load_character(player_cfg.character_file)
            agent = HumanPlayerAgent(char_sheet)
        else:
            # Create AI Agent
            agent = create_player_agent(player_cfg.character_file)
        players.append(agent)

    # ... rest of initialization
```

---

### 1.4 Turn Management per Human Players

**File**: `src/orchestration/orchestrator.py` (MODIFICA)

#### Modifiche Necessarie

##### Riconoscimento Human vs AI
```python
async def _player_response(self, player):
    if isinstance(player, HumanPlayerAgent):
        # Human player: wait for input via WebSocket
        response = await player.a_run(prompt)
    else:
        # AI player: normal agent call
        response = await memory.agent_respond(player.name, player, prompt)
    return response
```

##### Notifica UI per Turno Umano
```python
async def _notify_human_turn(self, player_name: str, prompt: str):
    """Invia messaggio WebSocket per mostrare input form"""
    await self.board.post(Message(
        speaker="System",
        text=f"{player_name}'s turn",
        metadata={
            "type": "human_turn",
            "player_name": player_name,
            "prompt": prompt
        }
    ))
```

##### Timeout Handling
Se il giocatore umano non risponde entro 60s:
- Log warning
- Genera fallback response con AI (quick mini-agent)
- Continua partita senza bloccare gli altri

---

### 1.5 Frontend - Human Input Interface

**File**: `src/ui/frontend/index.html` (MODIFICA)

#### Aggiunte HTML

```html
<!-- Human Player Input Section (nascosto di default) -->
<div id="player-input-section" class="hidden">
    <div class="turn-indicator">
        <h3>Your turn, <span id="current-player-name"></span>!</h3>
        <p id="dm-prompt"></p>
    </div>

    <div class="input-area">
        <textarea
            id="player-action-text"
            placeholder="Describe your action..."
            rows="4"
        ></textarea>

        <div class="input-controls">
            <button id="btn-submit-action" class="btn-primary">
                Submit Action
            </button>
            <span id="timeout-counter">Time remaining: 60s</span>
        </div>
    </div>
</div>
```

**File**: `src/ui/frontend/app.js` (MODIFICA)

#### Logica JavaScript

##### Mostra Input Form quando è Turno Umano
```javascript
ws.onmessage = (event) => {
    const data = JSON.parse(event.data)

    if (data.type === 'human_turn') {
        showPlayerInputForm(data.player_name, data.prompt)
        startTimeoutCounter(60)
    }
    // ... altri message handlers
}

function showPlayerInputForm(playerName, prompt) {
    document.getElementById('current-player-name').textContent = playerName
    document.getElementById('dm-prompt').textContent = prompt
    document.getElementById('player-input-section').classList.remove('hidden')
    document.getElementById('player-action-text').focus()
}
```

##### Submit Player Response
```javascript
document.getElementById('btn-submit-action').onclick = () => {
    const text = document.getElementById('player-action-text').value

    if (!text.trim()) {
        alert('Please enter an action')
        return
    }

    ws.send(JSON.stringify({
        type: 'player_response',
        player_name: currentPlayerName,
        text: text
    }))

    hidePlayerInputForm()
}
```

##### Timeout Counter
```javascript
let timeoutInterval

function startTimeoutCounter(seconds) {
    let remaining = seconds
    const counterEl = document.getElementById('timeout-counter')

    timeoutInterval = setInterval(() => {
        remaining--
        counterEl.textContent = `Time remaining: ${remaining}s`

        if (remaining <= 10) {
            counterEl.classList.add('warning')
        }

        if (remaining <= 0) {
            clearInterval(timeoutInterval)
            autoSubmitFallback()
        }
    }, 1000)
}

function autoSubmitFallback() {
    alert('Time expired. Generating automatic action...')
    hidePlayerInputForm()
}
```

---

### 1.6 WebSocket Message Handling

**File**: `src/ui/server.py` (MODIFICA)

#### Handler per Player Response

```python
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()

            if data["type"] == "player_response":
                player_name = data["player_name"]
                text = data["text"]

                # Find HumanPlayerAgent and submit response
                human_agent = orchestrator.get_player_by_name(player_name)
                if isinstance(human_agent, HumanPlayerAgent):
                    human_agent.submit_response(text)

            elif data["type"] == "start_game":
                await start_game()

            # ... altri handlers
    except WebSocketDisconnect:
        manager.disconnect(websocket)
```

---

## File da Creare/Modificare

### Nuovi File
| File | LOC | Descrizione |
|------|-----|-------------|
| `src/agents/human_agent.py` | ~100 | HumanPlayerAgent wrapper |
| `src/ui/frontend/lobby.html` | ~200 | Lobby UI per game setup |
| `tests/test_human_player.py` | ~150 | Test human player scenarios |

### File da Modificare
| File | LOC Aggiunte | Descrizione |
|------|--------------|-------------|
| `src/orchestration/orchestrator.py` | ~50 | Riconoscimento human vs AI |
| `src/ui/server.py` | ~120 | Endpoints + WebSocket handlers |
| `src/ui/frontend/index.html` | ~80 | Input form + turn indicator |
| `src/ui/frontend/app.js` | ~150 | WebSocket handling + timeout |
| `src/ui/frontend/style.css` | ~60 | Styling per input form |

**Totale**: ~910 righe (~450 nuove + ~460 modifiche)

---

## Deliverables

### Funzionalità Complete
- ✅ Lobby system per selezionare 0-3 giocatori umani
- ✅ HumanPlayerAgent con async input handling
- ✅ UI mostra input form durante turno umano
- ✅ Timeout 60s con fallback AI-generato
- ✅ WebSocket communication per player responses
- ✅ Orchestrator gestisce mix AI/Human senza blocchi
- ✅ Visual indicators (turno corrente, countdown timer)

### Test Coverage
- ✅ Test 1 human + 2 AI (scenario base)
- ✅ Test 2 humans + 1 AI (multiple humans)
- ✅ Test 3 humans + 0 AI (all human party)
- ✅ Test timeout handling (60s no response)
- ✅ Test WebSocket disconnect durante turno umano

### Documentazione
- ✅ API endpoints documentati (lobby + player_response)
- ✅ HumanPlayerAgent interface documentata
- ✅ User guide: come configurare partita con giocatori umani

---

## Rischi e Mitigazioni

### Rischio 1: Deadlock se Human non Risponde
**Mitigazione**: Timeout 60s + fallback AI-generato

### Rischio 2: WebSocket Disconnect durante Turno
**Mitigazione**: Reconnect logic + recovery del turno in corso

### Rischio 3: Multiple Humans Confusione di Turni
**Mitigazione**: Clear visual indicator di chi è il turno attivo

---

## Passaggio alla Phase 02

Una volta completata Phase 01, il sistema supporterà giocatori umani con **input testuale**.

La **Phase 02** aggiungerà la possibilità di usare **input vocale** (Speech-to-Text) come alternativa o complemento all'input testuale, permettendo al giocatore di scegliere liberamente tra:
- Digitare testo nella textarea
- Registrare un messaggio vocale (hold-to-speak)
- Combinare entrambi (voice → transcribe → edit → submit)
