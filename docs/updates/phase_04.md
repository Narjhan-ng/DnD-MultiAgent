# Phase 04 - Integration & Testing

**Data Inizio**: TBD (dopo Phase 03)
**Durata Stimata**: 1 giorno
**Status**: 🔵 Pianificata

---

## Recap Fase Precedente

**Phase 03 - Dynamic Character Creator** (Da Completare)

Nella Phase 03 abbiamo implementato il character creator dinamico:
- ✅ Character Creator UI con form completo
- ✅ LLM-based generation (AI genera stats, skills, equipment)
- ✅ Validation layer (garantisce conformità D&D 5e)
- ✅ Character gallery nella lobby (default + custom)
- ✅ CRUD API endpoints per character management
- ✅ YAML persistence per custom characters

**Situazione attuale**: Tutte le feature principali sono implementate **ma non ancora testate in modo integrato**. Ogni componente è stato sviluppato e testato in isolamento.

---

## Obiettivi Phase 04

Questa fase **valida l'intero sistema end-to-end** con focus su:

1. **Integration Testing**: Testare tutte le feature insieme (human player + voice + custom character)
2. **Performance Validation**: Misurare latenze, token usage, stabilità
3. **UI/UX Polish**: Migliorare usabilità, animazioni, feedback
4. **Bug Fixing**: Identificare e risolvere problemi emersi dai test
5. **Documentation**: Aggiornare docs con nuove feature

**Output**: Sistema completo, testato e pronto per uso reale.

---

## Test Scenarios da Validare

### 4.1 End-to-End Test Scenarios

**File**: `tests/test_integration.py` (NUOVO)

#### Scenario 1: Full Human Flow
```python
"""
Test completo del flusso umano:
1. Lobby: select 1 human + 2 AI
2. Character: create custom character via UI
3. Start game
4. Human's turn: use voice input
5. Submit action
6. Verify DM responds
7. Verify AI players respond
8. Complete 5 turns
"""

async def test_full_human_flow():
    # Setup: start server
    server = await start_test_server()

    # Step 1: Configure game via API
    config = {
        "players": [
            {"slot": 1, "type": "human", "character_file": "data/characters/custom_hero.yaml"},
            {"slot": 2, "type": "ai", "character_file": "data/characters/character1.yaml"},
            {"slot": 3, "type": "ai", "character_file": "data/characters/character2.yaml"}
        ]
    }
    response = await client.post("/api/configure_game", json=config)
    assert response.status_code == 200

    # Step 2: Start game
    await client.post("/api/start_game")

    # Step 3: Wait for human turn
    message = await websocket.receive_json()
    assert message["type"] == "human_turn"
    assert message["player_name"] == "Custom Hero"

    # Step 4: Submit human action
    await websocket.send_json({
        "type": "player_response",
        "player_name": "Custom Hero",
        "text": "I investigate the ancient door for traps"
    })

    # Step 5: Verify DM response
    dm_response = await wait_for_message(speaker="DM", timeout=30)
    assert "roll" in dm_response["text"].lower() or "door" in dm_response["text"].lower()

    # Step 6: Continue for 5 turns
    for turn in range(4):
        await progress_one_turn()

    # Validation
    assert game_orchestrator.turn_count >= 5
    assert not game_orchestrator.has_errors()
```

#### Scenario 2: Voice Input Test
```python
"""
Test input vocale (mock):
1. Human's turn
2. Simulate voice transcription
3. Verify textarea populated
4. Submit action
5. Verify accepted
"""

async def test_voice_input_flow():
    # Setup
    await setup_game_with_human()

    # Wait for human turn
    await wait_for_human_turn()

    # Simulate voice transcript (mock Web Speech API)
    transcript = "I cast Detect Magic on the chest"
    await simulate_voice_input(transcript)

    # Verify textarea updated
    textarea_value = await get_element_value("#player-action-text")
    assert textarea_value == transcript

    # Submit
    await click_submit_button()

    # Verify accepted
    dm_response = await wait_for_dm_response()
    assert "magic" in dm_response.lower() or "arcana" in dm_response.lower()
```

#### Scenario 3: Custom Character in Game
```python
"""
Test custom character creation + gameplay:
1. Create custom character via API
2. Validate character sheet
3. Use character in game
4. Verify character traits reflected in gameplay
"""

async def test_custom_character_gameplay():
    # Step 1: Create custom character
    form_data = {
        "name": "Zephyr Stormcaller",
        "class": "Wizard",
        "race": "Half-Elf",
        "level": 3,
        "personality": "Curious and analytical, loves ancient lore",
        "background": "Former apprentice to a mad wizard, now seeking forbidden knowledge"
    }

    response = await client.post("/api/characters/create", json=form_data)
    assert response.json()["status"] == "success"
    character = response.json()["character"]

    # Step 2: Validate character
    assert character["name"] == "Zephyr Stormcaller"
    assert character["class"] == "Wizard"
    assert character["abilities"]["intelligence"] >= 14  # Wizard primary stat
    assert "Arcana" in character["skills"]  # Wizard typical skill
    assert character["hp_max"] > 0

    # Step 3: Use in game
    await configure_game_with_character(character)
    await start_game()

    # Step 4: Verify personality reflected
    # (AI player should act according to personality)
    player_response = await wait_for_player_response("Zephyr Stormcaller")
    assert any(keyword in player_response.lower() for keyword in ["lore", "ancient", "magic", "investigate"])
```

#### Scenario 4: Multiple Humans
```python
"""
Test 2+ human players:
1. Configure 2 humans + 1 AI
2. Start game
3. Verify turn alternation correct
4. Both humans input actions
5. No deadlocks
"""

async def test_multiple_humans():
    # Setup 2 humans + 1 AI
    config = {
        "players": [
            {"slot": 1, "type": "human", "character_file": "custom_hero1.yaml"},
            {"slot": 2, "type": "human", "character_file": "custom_hero2.yaml"},
            {"slot": 3, "type": "ai", "character_file": "character1.yaml"}
        ]
    }
    await client.post("/api/configure_game", json=config)
    await client.post("/api/start_game")

    # DM narrates
    await wait_for_dm_message()

    # Human 1's turn
    turn1 = await wait_for_human_turn()
    assert turn1["player_name"] == "Hero 1"
    await submit_player_action("Hero 1", "I scout ahead")

    # Human 2's turn
    turn2 = await wait_for_human_turn()
    assert turn2["player_name"] == "Hero 2"
    await submit_player_action("Hero 2", "I follow behind")

    # AI's turn (automatic)
    await wait_for_message(speaker="AI Player")

    # Verify no deadlocks
    assert orchestrator.is_running()
    assert not orchestrator.has_timeout_errors()
```

#### Scenario 5: Timeout Handling
```python
"""
Test human timeout (60s):
1. Human's turn
2. Wait 60s without input
3. Verify fallback AI action generated
4. Verify game continues
"""

async def test_human_timeout():
    await setup_game_with_human()

    # Human's turn
    await wait_for_human_turn()

    # Wait 60+ seconds (simulate timeout)
    await asyncio.sleep(61)

    # Verify fallback action generated
    system_msg = await wait_for_message(speaker="System")
    assert "timeout" in system_msg["text"].lower() or "automatic" in system_msg["text"].lower()

    # Verify AI-generated fallback action posted
    fallback_action = await wait_for_message(speaker="Hero")
    assert len(fallback_action["text"]) > 0

    # Verify game continued (DM responded)
    dm_response = await wait_for_dm_response()
    assert dm_response is not None
```

---

### 4.2 Voice Input Testing (Manual)

#### Test Matrix

| Test | Browser | Platform | Language | Expected |
|------|---------|----------|----------|----------|
| Basic recording | Chrome 120+ | macOS | it-IT | ✅ Transcription works |
| Hold-to-speak | Chrome 120+ | Windows | en-US | ✅ Button responds to hold |
| Auto-submit | Edge 120+ | Windows | en-US | ✅ Submits without edit |
| Permission denied | Chrome 120+ | macOS | it-IT | ⚠️ Fallback to text |
| Network error | Chrome 120+ | macOS | it-IT | ⚠️ Error message shown |
| Safari | Safari 16+ | macOS | en-US | ⚠️ Limited support |
| Mobile Chrome | Chrome Android | Android | it-IT | ✅ Touch-friendly |
| Mobile Safari | Safari iOS | iPhone | en-US | ⚠️ Requires gesture |

#### Manual Test Procedure

**Test 1: Basic Voice Input**
1. Open game in Chrome
2. Start game with 1 human player
3. Wait for your turn
4. Click and hold "🎤 Hold to Speak" button
5. Say clearly: "I check the door for traps"
6. Release button
7. **Verify**: Text appears in textarea
8. Click Submit
9. **Verify**: DM responds appropriately

**Test 2: Voice + Edit**
1. Record voice: "I attack the goblin"
2. **Verify**: Text appears
3. Edit text: "I attack the goblin with my greatsword"
4. Submit
5. **Verify**: Edited text sent

**Test 3: Language Switch**
1. Open Settings panel
2. Change Voice Language to "English (US)"
3. Save settings
4. Record in English: "I investigate the chest"
5. **Verify**: Correct English transcription

**Test 4: Permission Denied**
1. Block microphone in browser settings
2. Try to use voice button
3. **Verify**: Error message shown
4. **Verify**: Voice button hidden/disabled
5. **Verify**: Text input still works

---

### 4.3 UI/UX Polish

#### Visual Improvements

**File**: `src/ui/frontend/style.css` (MODIFICA)

##### Loading States
```css
/* Smooth loading spinner */
.spinner {
    border: 4px solid rgba(255, 255, 255, 0.3);
    border-top: 4px solid #667eea;
    border-radius: 50%;
    width: 40px;
    height: 40px;
    animation: spin 1s linear infinite;
}

@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

/* Loading overlay */
.loading-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.7);
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    z-index: 9999;
}

.loading-overlay p {
    color: white;
    margin-top: 20px;
    font-size: 18px;
}
```

##### Turn Indicator Highlight
```css
/* Pulsing border quando è il proprio turno */
.your-turn {
    animation: pulse-border 2s infinite;
}

@keyframes pulse-border {
    0%, 100% {
        border: 3px solid #667eea;
        box-shadow: 0 0 10px rgba(102, 126, 234, 0.5);
    }
    50% {
        border: 3px solid #764ba2;
        box-shadow: 0 0 20px rgba(118, 75, 162, 0.8);
    }
}
```

##### Success Feedback
```css
/* Checkmark animation dopo submit */
.success-checkmark {
    width: 60px;
    height: 60px;
    margin: 20px auto;
    border-radius: 50%;
    background: #10b981;
    display: flex;
    align-items: center;
    justify-content: center;
    animation: scale-in 0.3s ease;
}

@keyframes scale-in {
    0% { transform: scale(0); }
    50% { transform: scale(1.1); }
    100% { transform: scale(1); }
}

.success-checkmark::after {
    content: '✓';
    color: white;
    font-size: 40px;
    font-weight: bold;
}
```

#### Error Messages (User-Friendly, Italiano)

**File**: `src/ui/frontend/app.js` (MODIFICA)

```javascript
const ERROR_MESSAGES = {
    'no-speech': 'Nessun audio rilevato. Prova a parlare più chiaramente.',
    'audio-capture': 'Microfono non accessibile. Controlla le impostazioni del browser.',
    'not-allowed': 'Permesso microfono negato. Abilita il microfono nelle impostazioni.',
    'network': 'Errore di connessione. Controlla la tua rete.',
    'timeout': 'Tempo scaduto (60s). Genero azione automatica...',
    'validation-failed': 'Personaggio non valido. Controlla i dettagli e riprova.',
    'character-exists': 'Esiste già un personaggio con questo nome.',
    'server-error': 'Errore del server. Riprova tra qualche istante.'
}

function showError(errorKey) {
    const message = ERROR_MESSAGES[errorKey] || ERROR_MESSAGES['server-error']
    const errorDiv = document.createElement('div')
    errorDiv.className = 'error-toast'
    errorDiv.textContent = message

    document.body.appendChild(errorDiv)

    // Auto-remove dopo 5s
    setTimeout(() => {
        errorDiv.classList.add('fade-out')
        setTimeout(() => errorDiv.remove(), 500)
    }, 5000)
}
```

##### Error Toast Styling
```css
.error-toast {
    position: fixed;
    bottom: 20px;
    right: 20px;
    background: #ef4444;
    color: white;
    padding: 16px 24px;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    animation: slide-in 0.3s ease;
    z-index: 10000;
}

@keyframes slide-in {
    from {
        transform: translateX(400px);
        opacity: 0;
    }
    to {
        transform: translateX(0);
        opacity: 1;
    }
}

.error-toast.fade-out {
    animation: fade-out 0.5s ease;
}

@keyframes fade-out {
    to {
        opacity: 0;
        transform: translateY(20px);
    }
}
```

#### Mobile Responsiveness

**File**: `src/ui/frontend/style.css` (MODIFICA)

```css
/* Mobile optimizations */
@media (max-width: 768px) {
    /* Larger touch targets */
    .btn-voice {
        min-height: 56px;
        font-size: 18px;
    }

    /* Full-width controls */
    .input-controls {
        flex-direction: column;
    }

    .input-controls button {
        width: 100%;
    }

    /* Larger textarea on mobile */
    #player-action-text {
        font-size: 16px;
        min-height: 120px;
    }

    /* Simplified lobby layout */
    .player-slot {
        flex-direction: column;
        gap: 12px;
    }

    /* Stack character selector */
    .character-selector {
        flex-direction: column;
    }

    .char-dropdown {
        width: 100%;
    }
}
```

---

### 4.4 Performance Validation

#### Metrics da Misurare

**File**: `tests/test_performance.py` (NUOVO)

```python
import time
import asyncio

async def test_performance_metrics():
    """Measure key performance indicators"""

    metrics = {
        "human_turn_latency": [],
        "dm_response_latency": [],
        "ai_player_latency": [],
        "voice_transcription_time": [],
        "character_generation_time": [],
        "total_tokens_per_turn": [],
    }

    # Run 10-turn game
    for turn in range(10):
        # Measure human turn
        start = time.time()
        await submit_human_action()
        human_latency = time.time() - start
        metrics["human_turn_latency"].append(human_latency)

        # Measure DM response
        start = time.time()
        await wait_for_dm_response()
        dm_latency = time.time() - start
        metrics["dm_response_latency"].append(dm_latency)

        # Measure AI player
        start = time.time()
        await wait_for_ai_player_response()
        ai_latency = time.time() - start
        metrics["ai_player_latency"].append(ai_latency)

    # Calculate averages
    print("\n=== PERFORMANCE METRICS ===")
    print(f"Avg Human Turn Latency: {sum(metrics['human_turn_latency']) / 10:.2f}s")
    print(f"Avg DM Response Latency: {sum(metrics['dm_response_latency']) / 10:.2f}s")
    print(f"Avg AI Player Latency: {sum(metrics['ai_player_latency']) / 10:.2f}s")

    # Validate thresholds
    assert sum(metrics['dm_response_latency']) / 10 < 15, "DM too slow (>15s avg)"
    assert sum(metrics['ai_player_latency']) / 10 < 10, "AI players too slow (>10s avg)"
```

#### Target Metrics

| Metric | Target | Acceptable | Unacceptable |
|--------|--------|------------|--------------|
| Human turn submission | <1s | <2s | >3s |
| DM response latency | <10s | <15s | >20s |
| AI player latency | <7s | <10s | >15s |
| Voice transcription | <2s | <3s | >5s |
| Character generation | <8s | <12s | >20s |
| Total turn cycle | <30s | <45s | >60s |

---

### 4.5 Bug Fixing Checklist

#### Known Potential Issues

**Issue 1: WebSocket Reconnection**
- [ ] Test disconnect durante human turn
- [ ] Verify reconnection logic
- [ ] Ensure no message loss

**Issue 2: Concurrent Human Inputs**
- [ ] Test 2+ humans submitting simultaneously
- [ ] Verify no race conditions
- [ ] Ensure correct turn order

**Issue 3: Character Validation Edge Cases**
- [ ] Test ability scores sum validation
- [ ] Test invalid class/race combinations
- [ ] Test special characters in names

**Issue 4: Voice API Browser Compatibility**
- [ ] Verify fallback on Firefox
- [ ] Test Safari iOS limitations
- [ ] Ensure clear error messages

**Issue 5: Memory Leaks**
- [ ] Test 30+ turn session
- [ ] Monitor memory usage
- [ ] Verify cleanup on game end

---

## File da Creare/Modificare

### Nuovi File
| File | LOC | Descrizione |
|------|-----|-------------|
| `tests/test_integration.py` | ~300 | End-to-end integration tests |
| `tests/test_performance.py` | ~150 | Performance benchmarking |
| `docs/USER_GUIDE.md` | ~200 | User documentation |

### File da Modificare
| File | LOC Aggiunte | Descrizione |
|------|--------------|-------------|
| `src/ui/frontend/style.css` | ~150 | Polish animations, mobile |
| `src/ui/frontend/app.js` | ~100 | Error handling, feedback |
| `README.md` | ~80 | Update with new features |

**Totale**: ~980 righe (~650 nuove + ~330 modifiche)

---

## Deliverables

### Testing Complete
- ✅ 5+ end-to-end integration test scenarios passing
- ✅ Voice input tested across 3+ browsers
- ✅ Custom character generation tested (10+ characters)
- ✅ Performance metrics within targets
- ✅ No critical bugs or crashes
- ✅ Memory leaks tested (30+ turn session)

### UI/UX Polish
- ✅ Loading indicators animati
- ✅ Success feedback (checkmarks, toast messages)
- ✅ Error messages in italiano, user-friendly
- ✅ Mobile-responsive layout (tested on 3+ devices)
- ✅ Smooth transitions e animazioni

### Documentation
- ✅ USER_GUIDE.md (come usare tutte le feature)
- ✅ README.md aggiornato con screenshots
- ✅ API documentation (endpoints per character creation)
- ✅ Troubleshooting guide (errori comuni)

### Bug Fixes
- ✅ WebSocket reconnection funzionante
- ✅ Concurrent human inputs gestiti correttamente
- ✅ Character validation edge cases risolti
- ✅ Browser compatibility issues documentati

---

## Success Criteria

Il sistema è considerato **completo e pronto per l'uso** quando:

1. ✅ **Tutti i test integration passano** senza errori
2. ✅ **Performance metrics** dentro target (DM <15s, AI <10s)
3. ✅ **Voice input funziona** su Chrome e Edge
4. ✅ **Custom characters** possono essere creati e usati
5. ✅ **0 crash** in 30-turn test session
6. ✅ **UI responsiva** su desktop e mobile
7. ✅ **Documentazione completa** per utenti finali

---

## Passaggio Fase Successiva

Una volta completata Phase 04, il progetto avrà completato le **4 fasi di enhancement** pianificate:

### ✅ Feature Complete
- Human player integration (0-3 humans)
- Dual input mode (voice + text)
- Dynamic character creator (AI-assisted)
- Full integration testing

### 🎯 Next Steps (Optional - Future Enhancements)

**Phase 09 - Mobile App** (Se deciso):
- Progressive Web App (PWA) optimization
- O React Native/Flutter native app
- Mobile-first UI redesign
- Touch gestures ottimizzati

**Phase 10 - Production Deployment**:
- Deploy su cloud (Railway, Vercel, AWS)
- User authentication e accounts
- Persistent game state (database)
- Multi-party sessions (multiplayer rooms)

**Phase 11 - Advanced Features**:
- Text-to-Speech (TTS) per AI narration
- Character progression (XP, leveling)
- Inventory management system
- Battle maps e visual aids

---

## Conclusione

Con il completamento della Phase 04, il sistema D&D Multi-Agent avrà raggiunto un livello di **qualità production-ready** per uso locale.

Il progetto sarà **funzionalmente completo** con:
- Gameplay autonomo AI ✅
- Giocatori umani (flessibile 0-3) ✅
- Input vocale e testuale ✅
- Character creator dinamico ✅
- Testing completo ✅
- Documentazione utente ✅

**Stima Totale Sviluppo**: ~6-7 giorni (Phases 01-04)
**Stima Totale Codice**: ~2400 righe nuove + ~1900 righe modificate
