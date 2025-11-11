# Phase 02 - Dual Input Mode (Voice + Text)

**Data Inizio**: TBD (dopo Phase 01)
**Durata Stimata**: 1-1.5 giorni
**Status**: 🔵 Pianificata

---

## Recap Fase Precedente

**Phase 01 - Human Player Integration** (Da Completare)

Nella Phase 01 abbiamo integrato la possibilità di avere giocatori umani nel sistema:
- ✅ HumanPlayerAgent wrapper per input async
- ✅ Lobby system per configurare 0-3 giocatori umani
- ✅ Turn management con riconoscimento Human vs AI
- ✅ UI con input form (textarea + submit button)
- ✅ Timeout 60s con fallback AI
- ✅ WebSocket communication per player responses

**Limitazione attuale**: I giocatori umani possono solo **digitare testo** nella textarea. Non c'è supporto per input vocale.

---

## Obiettivi Phase 02

Questa fase aggiunge **input vocale (Speech-to-Text)** come alternativa flessibile all'input testuale. Il giocatore può scegliere liberamente ad ogni turno:

- **Type**: Digitare l'azione nella textarea (modalità attuale)
- **Voice**: Registrare un messaggio vocale (hold-to-speak)
- **Hybrid**: Voice → transcribe → edit text → submit

La scelta è **per singola azione**, non per tutta la sessione. Il giocatore può alternare liberamente tra voice e text durante la partita.

### Tecnologia Scelta
**Web Speech API** (browser-based):
- ✅ Gratis (no API costs)
- ✅ Rapido (~1-2s latency)
- ✅ Nessun setup server-side
- ✅ Supporto lingue multiple (it-IT, en-US)
- ⚠️ Richiede browser moderno (Chrome, Edge best support)
- ⚠️ HTTPS richiesto (localhost ok per dev)

---

## Componenti da Implementare

### 2.1 Web Speech API Integration

**File**: `src/ui/frontend/app.js` (MODIFICA)

#### Setup SpeechRecognition

```javascript
// Inizializza Web Speech API
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
let recognition = null

function initSpeechRecognition() {
    if (!SpeechRecognition) {
        console.warn('Speech Recognition not supported in this browser')
        return null
    }

    recognition = new SpeechRecognition()
    recognition.continuous = false  // Stop dopo singolo risultato
    recognition.interimResults = false  // Solo risultato finale
    recognition.lang = localStorage.getItem('voiceLang') || 'it-IT'

    recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript
        handleVoiceTranscript(transcript)
    }

    recognition.onerror = (event) => {
        console.error('Speech recognition error:', event.error)
        showError('Voice recognition failed. Please try again or use text input.')
        stopVoiceRecording()
    }

    recognition.onend = () => {
        stopVoiceRecording()
    }

    return recognition
}
```

#### Hold-to-Speak Button Behavior

```javascript
const voiceBtn = document.getElementById('btn-voice-input')

voiceBtn.addEventListener('mousedown', () => {
    startVoiceRecording()
})

voiceBtn.addEventListener('mouseup', () => {
    stopVoiceRecording()
})

// Touch support per mobile
voiceBtn.addEventListener('touchstart', (e) => {
    e.preventDefault()
    startVoiceRecording()
})

voiceBtn.addEventListener('touchend', (e) => {
    e.preventDefault()
    stopVoiceRecording()
})

function startVoiceRecording() {
    if (!recognition) {
        showError('Voice input not available')
        return
    }

    voiceBtn.classList.add('recording')
    voiceBtn.innerHTML = '🔴 Recording...'

    try {
        recognition.start()
    } catch (e) {
        console.error('Failed to start recognition:', e)
    }
}

function stopVoiceRecording() {
    if (!recognition) return

    voiceBtn.classList.remove('recording')
    voiceBtn.innerHTML = '🎤 Hold to Speak'

    try {
        recognition.stop()
    } catch (e) {
        // Recognition already stopped
    }
}

function handleVoiceTranscript(transcript) {
    const textarea = document.getElementById('player-action-text')

    // Opzione 1: Replace text (default)
    if (settings.voiceMode === 'replace') {
        textarea.value = transcript
    }
    // Opzione 2: Append text
    else if (settings.voiceMode === 'append') {
        textarea.value += (textarea.value ? ' ' : '') + transcript
    }

    // Auto-submit se setting enabled
    if (settings.autoSubmitAfterVoice) {
        submitPlayerAction()
    } else {
        // Focus su textarea per permettere edit
        textarea.focus()
        textarea.setSelectionRange(textarea.value.length, textarea.value.length)
    }
}
```

---

### 2.2 UI Updates - Dual Input Interface

**File**: `src/ui/frontend/index.html` (MODIFICA)

#### Input Section con Voice Button

```html
<div id="player-input-section" class="hidden">
    <div class="turn-indicator">
        <h3>Your turn, <span id="current-player-name"></span>!</h3>
        <p id="dm-prompt"></p>
    </div>

    <div class="input-area">
        <!-- Textarea (sempre visibile) -->
        <textarea
            id="player-action-text"
            placeholder="Type your action or use voice input..."
            rows="4"
        ></textarea>

        <!-- Input Controls -->
        <div class="input-controls">
            <!-- Voice Button (hold-to-speak) -->
            <button
                id="btn-voice-input"
                class="btn-voice"
                title="Hold to speak"
            >
                🎤 Hold to Speak
            </button>

            <!-- Submit Button -->
            <button id="btn-submit-action" class="btn-primary">
                Submit Action
            </button>

            <!-- Timeout Counter -->
            <span id="timeout-counter">Time: 60s</span>
        </div>

        <!-- Voice Status Indicator -->
        <div id="voice-status" class="hidden">
            <span class="recording-indicator">🔴 Recording...</span>
        </div>
    </div>
</div>
```

**File**: `src/ui/frontend/style.css` (MODIFICA)

#### Styling per Voice UI

```css
/* Voice Button */
.btn-voice {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border: none;
    padding: 12px 24px;
    border-radius: 8px;
    cursor: pointer;
    font-size: 16px;
    transition: all 0.3s ease;
    user-select: none;
}

.btn-voice:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.btn-voice:active {
    transform: translateY(0);
}

/* Recording State */
.btn-voice.recording {
    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
    animation: pulse 1.5s infinite;
}

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.7; }
}

/* Voice Status Indicator */
#voice-status {
    margin-top: 8px;
    padding: 8px 16px;
    background: rgba(245, 87, 108, 0.1);
    border-radius: 6px;
    text-align: center;
}

.recording-indicator {
    color: #f5576c;
    font-weight: 600;
    animation: blink 1s infinite;
}

@keyframes blink {
    0%, 50%, 100% { opacity: 1; }
    25%, 75% { opacity: 0.5; }
}

/* Input Controls Layout */
.input-controls {
    display: flex;
    gap: 12px;
    align-items: center;
    margin-top: 12px;
    flex-wrap: wrap;
}

#timeout-counter {
    margin-left: auto;
    color: #666;
    font-size: 14px;
}

#timeout-counter.warning {
    color: #f5576c;
    font-weight: 600;
}

/* Mobile Responsive */
@media (max-width: 768px) {
    .btn-voice {
        width: 100%;
        padding: 16px;
        font-size: 18px;
    }

    .input-controls {
        flex-direction: column;
        gap: 8px;
    }

    #timeout-counter {
        margin-left: 0;
        width: 100%;
        text-align: center;
    }
}
```

---

### 2.3 Settings Panel per Voice Options

**File**: `src/ui/frontend/index.html` (MODIFICA)

#### Settings Panel HTML

```html
<!-- Settings Panel (collapsible) -->
<div id="settings-panel">
    <button id="btn-toggle-settings" class="btn-secondary">
        ⚙️ Settings
    </button>

    <div id="settings-content" class="hidden">
        <h3>Voice Input Settings</h3>

        <!-- Enable/Disable Voice -->
        <label class="setting-item">
            <input type="checkbox" id="setting-voice-enabled" checked>
            <span>Enable Voice Input</span>
        </label>

        <!-- Language Selection -->
        <label class="setting-item">
            <span>Voice Language:</span>
            <select id="setting-voice-lang">
                <option value="it-IT">🇮🇹 Italiano</option>
                <option value="en-US">🇺🇸 English (US)</option>
                <option value="en-GB">🇬🇧 English (UK)</option>
                <option value="es-ES">🇪🇸 Español</option>
                <option value="fr-FR">🇫🇷 Français</option>
            </select>
        </label>

        <!-- Auto-submit After Voice -->
        <label class="setting-item">
            <input type="checkbox" id="setting-auto-submit">
            <span>Auto-submit after voice (no edit)</span>
        </label>

        <!-- Voice Mode -->
        <label class="setting-item">
            <span>Voice Mode:</span>
            <select id="setting-voice-mode">
                <option value="replace">Replace text</option>
                <option value="append">Append to text</option>
            </select>
        </label>

        <button id="btn-save-settings" class="btn-primary">
            Save Settings
        </button>
    </div>
</div>
```

**File**: `src/ui/frontend/app.js` (MODIFICA)

#### Settings Management

```javascript
// Settings object
const settings = {
    voiceEnabled: true,
    voiceLang: 'it-IT',
    autoSubmitAfterVoice: false,
    voiceMode: 'replace'
}

// Load settings from localStorage
function loadSettings() {
    const saved = localStorage.getItem('dnd-settings')
    if (saved) {
        Object.assign(settings, JSON.parse(saved))
    }
    applySettings()
}

// Apply settings to UI
function applySettings() {
    document.getElementById('setting-voice-enabled').checked = settings.voiceEnabled
    document.getElementById('setting-voice-lang').value = settings.voiceLang
    document.getElementById('setting-auto-submit').checked = settings.autoSubmitAfterVoice
    document.getElementById('setting-voice-mode').value = settings.voiceMode

    // Show/hide voice button
    const voiceBtn = document.getElementById('btn-voice-input')
    if (settings.voiceEnabled && recognition) {
        voiceBtn.classList.remove('hidden')
    } else {
        voiceBtn.classList.add('hidden')
    }

    // Update recognition language
    if (recognition) {
        recognition.lang = settings.voiceLang
    }
}

// Save settings
document.getElementById('btn-save-settings').onclick = () => {
    settings.voiceEnabled = document.getElementById('setting-voice-enabled').checked
    settings.voiceLang = document.getElementById('setting-voice-lang').value
    settings.autoSubmitAfterVoice = document.getElementById('setting-auto-submit').checked
    settings.voiceMode = document.getElementById('setting-voice-mode').value

    localStorage.setItem('dnd-settings', JSON.stringify(settings))
    applySettings()

    showNotification('Settings saved!')
}

// Toggle settings panel
document.getElementById('btn-toggle-settings').onclick = () => {
    document.getElementById('settings-content').classList.toggle('hidden')
}
```

---

### 2.4 Browser Compatibility & Fallbacks

**File**: `src/ui/frontend/app.js` (MODIFICA)

#### Detection e Fallback Graceful

```javascript
// Check browser support
function checkVoiceSupport() {
    const hasSupport = !!(window.SpeechRecognition || window.webkitSpeechRecognition)

    if (!hasSupport) {
        console.warn('Speech Recognition not supported')
        document.getElementById('btn-voice-input').style.display = 'none'
        showNotification('Voice input not supported in this browser. Please use Chrome or Edge.', 'warning')
    }

    return hasSupport
}

// Check HTTPS requirement
function checkSecureContext() {
    if (location.protocol !== 'https:' && location.hostname !== 'localhost') {
        console.warn('HTTPS required for Speech Recognition')
        showNotification('Voice input requires HTTPS. Using text input only.', 'warning')
        return false
    }
    return true
}

// Initialize on page load
window.addEventListener('DOMContentLoaded', () => {
    loadSettings()

    if (checkSecureContext() && checkVoiceSupport()) {
        initSpeechRecognition()
    } else {
        // Disable voice features
        settings.voiceEnabled = false
        applySettings()
    }
})
```

#### Error Handling

```javascript
// Handle recognition errors gracefully
recognition.onerror = (event) => {
    let errorMessage = 'Voice recognition failed. '

    switch (event.error) {
        case 'no-speech':
            errorMessage += 'No speech detected. Please try again.'
            break
        case 'audio-capture':
            errorMessage += 'Microphone not accessible. Check permissions.'
            break
        case 'not-allowed':
            errorMessage += 'Microphone permission denied.'
            break
        case 'network':
            errorMessage += 'Network error. Check your connection.'
            break
        default:
            errorMessage += 'Please try again or use text input.'
    }

    showNotification(errorMessage, 'error')
    stopVoiceRecording()
}
```

---

### 2.5 Testing & Browser Compatibility

#### Browser Support Matrix

| Browser | Version | Status | Notes |
|---------|---------|--------|-------|
| Chrome | 25+ | ✅ Full Support | Best experience |
| Edge | 79+ | ✅ Full Support | Chromium-based |
| Safari | 14.1+ | ⚠️ Partial | Requires user gesture |
| Firefox | 🚫 No Support | Fallback only | |
| Opera | 27+ | ✅ Full Support | Chromium-based |

#### Test Scenarios

**Test 1: Basic Voice Input**
- User holds voice button
- Speaks action ("I check the door")
- Releases button
- Text appears in textarea
- User submits

**Test 2: Voice + Edit**
- User records voice ("I attack the goblin")
- Text appears in textarea
- User edits text ("I attack the goblin with my sword")
- User submits

**Test 3: Auto-Submit**
- User enables auto-submit in settings
- User records voice
- Action automatically submitted (no edit)

**Test 4: Language Switch**
- User changes language to English (en-US)
- Recognition switches to English
- User speaks in English
- Correct transcription

**Test 5: Microphone Permission Denied**
- User denies microphone access
- Error message shown
- Voice button hidden
- Text input still available

**Test 6: Network Error**
- Network disconnects mid-recording
- Error handled gracefully
- User can retry or use text

---

## File da Creare/Modificare

### File da Modificare
| File | LOC Aggiunte | Descrizione |
|------|--------------|-------------|
| `src/ui/frontend/app.js` | ~250 | Web Speech API + settings |
| `src/ui/frontend/index.html` | ~100 | Voice button + settings panel |
| `src/ui/frontend/style.css` | ~100 | Styling voice UI + animations |

**Totale**: ~450 righe modificate

**Note**: Nessun file backend da modificare, tutta l'implementazione è client-side.

---

## Deliverables

### Funzionalità Complete
- ✅ Web Speech API integration (browser-based STT)
- ✅ Hold-to-speak button con visual feedback
- ✅ Voice transcription → textarea (editable)
- ✅ Settings panel:
  - Enable/disable voice input
  - Language selection (5+ languages)
  - Auto-submit toggle
  - Voice mode (replace/append)
- ✅ Browser compatibility detection + fallback
- ✅ Error handling (permissions, network, no speech)
- ✅ Mobile-responsive voice button (touch-friendly)

### Test Coverage
- ✅ Test basic voice input (record → transcribe → submit)
- ✅ Test voice + edit (record → edit text → submit)
- ✅ Test auto-submit mode
- ✅ Test language switching (it-IT, en-US)
- ✅ Test error scenarios (permission denied, network error)
- ✅ Test browser compatibility (Chrome, Edge, Safari)

### User Experience
- ✅ Clear visual feedback durante recording (pulsing button)
- ✅ Smooth animations (fade-in, pulse)
- ✅ Helpful error messages in italiano
- ✅ Settings salvate in localStorage (persist tra sessioni)
- ✅ Touch-friendly controls per mobile

---

## Rischi e Mitigazioni

### Rischio 1: Browser non Supporta Web Speech API
**Mitigazione**: Detection automatico + fallback graceful (nascondi voice button, mostra solo textarea)

### Rischio 2: Microphone Permission Negata
**Mitigazione**: Clear error message + istruzioni per abilitare permessi

### Rischio 3: Accuratezza Trascrizione (Accenti, Rumori)
**Mitigazione**: Permettere sempre edit prima di submit (default: no auto-submit)

### Rischio 4: HTTPS Requirement in Production
**Mitigazione**: Deploy con HTTPS enabled (Vercel, Railway, Netlify default HTTPS)

### Rischio 5: Mobile Safari Limitazioni
**Mitigazione**: Test estensivi su Safari iOS, documentare limitazioni

---

## Passaggio alla Phase 03

Una volta completata Phase 02, i giocatori umani potranno usare **input vocale o testuale** in modo flessibile durante la partita.

La **Phase 03** aggiungerà un **character creator dinamico** per permettere agli utenti di creare personaggi personalizzati invece di usare solo quelli predefiniti:
- Form UI per inserire nome, classe, razza, personalità
- LLM-based generation (AI genera stats, skills, equipment)
- Validation layer D&D 5e (garantisce conformità alle regole)
- Character gallery (default + custom characters)
