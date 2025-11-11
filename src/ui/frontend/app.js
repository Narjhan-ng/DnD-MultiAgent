// WebSocket connection
let ws = null;
let messageCount = 0;
let turnCount = 0;

// DOM elements
const messageBoard = document.getElementById('message-board');
const connectionStatus = document.getElementById('connection-status');
const btnStart = document.getElementById('btn-start');
const btnPause = document.getElementById('btn-pause');
const btnStop = document.getElementById('btn-stop');
const btnReset = document.getElementById('btn-reset');

// Connect to WebSocket
function connect() {
    ws = new WebSocket('ws://localhost:8000/ws');

    ws.onopen = () => {
        console.log('Connected to server');
        connectionStatus.textContent = 'Connected';
        connectionStatus.className = 'status connected';
    };

    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        handleMessage(data);
    };

    ws.onclose = () => {
        console.log('Disconnected from server');
        connectionStatus.textContent = 'Disconnected';
        connectionStatus.className = 'status disconnected';
        setTimeout(connect, 3000); // Reconnect after 3s
    };

    ws.onerror = (error) => {
        console.error('WebSocket error:', error);
    };
}

// Handle incoming messages
function handleMessage(data) {
    if (data.type === 'game_message') {
        addMessage(data.speaker, data.text);
        messageCount++;
        document.getElementById('message-count').textContent = messageCount;

        // Update turn count if message contains turn info
        if (data.metadata && data.metadata.turn) {
            turnCount = data.metadata.turn;
            document.getElementById('turn-count').textContent = turnCount;
        }
    } else if (data.type === 'system') {
        addSystemMessage(data.message);
    }
}

// Add message to board
function addMessage(speaker, text) {
    const messageDiv = document.createElement('div');
    const messageType = speaker === 'DM' ? 'dm' : speaker.startsWith('Player') || isPlayerName(speaker) ? 'player' : 'system';
    messageDiv.className = `message message-${messageType}`;

    messageDiv.innerHTML = `
        <div class="message-speaker">[${speaker}]</div>
        <div class="message-text">${escapeHtml(text)}</div>
    `;

    messageBoard.appendChild(messageDiv);
    messageBoard.scrollTop = messageBoard.scrollHeight; // Auto-scroll
}

// Add system message
function addSystemMessage(text) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message message-system';
    messageDiv.innerHTML = `<div class="message-text">${escapeHtml(text)}</div>`;
    messageBoard.appendChild(messageDiv);
    messageBoard.scrollTop = messageBoard.scrollHeight;
}

// Check if speaker is a player name (not "DM" or "System")
function isPlayerName(speaker) {
    return speaker !== 'DM' && speaker !== 'System';
}

// Escape HTML to prevent XSS
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Send command to server
function sendCommand(command) {
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: command }));
    }
}

// Button handlers
btnStart.onclick = () => {
    sendCommand('start_game');
    btnStart.disabled = true;
    btnPause.disabled = false;
    btnStop.disabled = false;
    btnReset.disabled = false;
};

btnPause.onclick = () => {
    sendCommand('pause_game');
};

btnStop.onclick = () => {
    sendCommand('stop_game');
    btnStart.disabled = false;
    btnPause.disabled = true;
    btnStop.disabled = true;
};

btnReset.onclick = () => {
    sendCommand('reset_game');
    messageBoard.innerHTML = '';
    messageCount = 0;
    turnCount = 0;
    document.getElementById('message-count').textContent = '0';
    document.getElementById('turn-count').textContent = '0';
    btnStart.disabled = false;
    btnPause.disabled = true;
    btnStop.disabled = true;
    btnReset.disabled = true;
};

// Initialize
connect();
