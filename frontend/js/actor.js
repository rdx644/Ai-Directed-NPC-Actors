/**
 * NPC Actor System — Actor Earpiece JavaScript
 * Handles: WebSocket connection, real-time dialogue feed, TTS playback.
 */

const API = window.location.origin + '/api';

// ── State ──
let ws = null;
let selectedCharacterId = null;
let selectedCharacter = null;
let audioEnabled = true;
let largeText = false;
let linesDelivered = 0;
let dialogueHistory = [];

// ── Utilities ──
function $(sel) { return document.querySelector(sel); }

function showToast(message, type = 'info') {
    const container = $('#toast-container');
    const icons = { success: '✅', error: '❌', info: 'ℹ️' };
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `<span>${icons[type]}</span><span>${message}</span>`;
    container.appendChild(toast);
    setTimeout(() => toast.remove(), 4000);
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text || '';
    return div.innerHTML;
}

// ── Load Characters ──
async function loadCharacters() {
    try {
        const res = await fetch(`${API}/characters`);
        const characters = await res.json();
        const select = $('#select-character');
        select.innerHTML = '<option value="">— Select your character —</option>';
        characters.forEach(c => {
            const archetypeEmojis = {
                wizard: '🧙', oracle: '🔮', inventor: '⚡',
                historian: '📚', trickster: '🃏', mentor: '🎓', custom: '✨'
            };
            const emoji = archetypeEmojis[c.archetype] || '🎭';
            const opt = document.createElement('option');
            opt.value = c.id;
            opt.textContent = `${emoji} ${c.name} (${c.archetype})`;
            opt.dataset.character = JSON.stringify(c);
            select.appendChild(opt);
        });
    } catch (e) {
        showToast('Failed to load characters', 'error');
    }
}

// ── WebSocket Connection ──
function connectWebSocket(characterId) {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/actor/${characterId}`;

    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
        console.log('WebSocket connected');
        showToast('Earpiece connected!', 'success');
        $('#connection-dot').className = 'status-dot online';
        $('#connection-status').textContent = 'Connected';
        $('#connection-status').style.color = 'var(--accent-emerald)';
    };

    ws.onmessage = (event) => {
        try {
            const msg = JSON.parse(event.data);
            handleCueMessage(msg);
        } catch (e) {
            console.error('Failed to parse WS message:', e);
        }
    };

    ws.onclose = (e) => {
        console.log('WebSocket closed:', e.code, e.reason);
        $('#connection-dot').className = 'status-dot offline';
        $('#connection-status').textContent = 'Disconnected';
        $('#connection-status').style.color = 'var(--accent-rose)';

        if (selectedCharacterId) {
            showToast('Connection lost — reconnecting...', 'error');
            setTimeout(() => {
                if (selectedCharacterId) connectWebSocket(selectedCharacterId);
            }, 3000);
        }
    };

    ws.onerror = (e) => {
        console.error('WebSocket error:', e);
        showToast('Connection error', 'error');
    };
}

function disconnectWebSocket() {
    selectedCharacterId = null;
    if (ws) {
        ws.close();
        ws = null;
    }
}

// ── Handle Incoming Cue Messages ──
function handleCueMessage(msg) {
    console.log('Received cue:', msg);

    if (msg.type === 'system') {
        addSystemMessage(msg.dialogue);
        return;
    }

    if (msg.type === 'pong') return;

    if (msg.type === 'cue') {
        linesDelivered++;
        $('#lines-count').textContent = linesDelivered;
        dialogueHistory.push(msg);
        renderDialogueCue(msg);

        // Play TTS audio
        if (audioEnabled) {
            if (msg.audio_base64) {
                playAudioBase64(msg.audio_base64);
            } else {
                speakWithBrowser(msg.dialogue);
            }
        }
    }
}

// ── Render Dialogue Cue ──
function renderDialogueCue(cue) {
    // Remove waiting card
    const waitingCard = $('#waiting-card');
    if (waitingCard) waitingCard.remove();

    // Remove 'latest' class from previous cues
    document.querySelectorAll('.dialogue-card.latest').forEach(el => {
        el.classList.remove('latest');
    });

    const container = $('#dialogue-container');
    const card = document.createElement('div');
    card.className = 'dialogue-card latest';

    const fontSize = largeText ? '1.6rem' : '1.25rem';

    card.innerHTML = `
        <div class="dialogue-meta">
            <span>
                <span class="badge badge-cyan">${escapeHtml(cue.interaction_type || 'greeting')}</span>
                <strong style="margin-left: 8px;">→ ${escapeHtml(cue.attendee_name || 'Unknown')}</strong>
            </span>
            <span class="time" style="font-family: var(--font-mono); font-size: 0.75rem; color: var(--text-muted);">
                ${new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
            </span>
        </div>
        <div class="dialogue-text" style="font-size: ${fontSize};">${escapeHtml(cue.dialogue)}</div>
        ${cue.stage_direction ? `<div class="stage-direction">🎬 ${escapeHtml(cue.stage_direction)}</div>` : ''}
        ${cue.quest ? `<div class="quest-info">🎯 Quest: ${escapeHtml(cue.quest)}</div>` : ''}
    `;

    container.prepend(card);

    // Keep only last 20 cues
    const cards = container.querySelectorAll('.dialogue-card');
    if (cards.length > 20) {
        cards[cards.length - 1].remove();
    }
}

function addSystemMessage(text) {
    const container = $('#dialogue-container');
    const waitingCard = $('#waiting-card');
    if (waitingCard) waitingCard.remove();

    const div = document.createElement('div');
    div.style.cssText = 'padding: 12px 16px; background: var(--bg-glass); border-radius: var(--radius-sm); color: var(--text-secondary); font-size: 0.85rem; margin-bottom: 8px; border-left: 3px solid var(--accent-primary);';
    div.innerHTML = `<span style="color: var(--accent-primary); font-weight: 600;">SYSTEM</span> — ${escapeHtml(text)}`;
    container.prepend(div);
}

// ── Audio Playback ──
function playAudioBase64(base64Audio) {
    try {
        const audio = new Audio(`data:audio/mp3;base64,${base64Audio}`);
        audio.play().catch(e => console.warn('Audio playback failed:', e));
    } catch (e) {
        console.error('Audio error:', e);
    }
}

function speakWithBrowser(text) {
    if (!('speechSynthesis' in window)) return;
    window.speechSynthesis.cancel();

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = selectedCharacter?.speaking_rate || 1.0;
    utterance.pitch = 1.0 + ((selectedCharacter?.pitch || 0) / 20);
    utterance.lang = 'en-US';

    // Try to find a good voice
    const voices = window.speechSynthesis.getVoices();
    const preferred = voices.find(v => v.name.includes('Google')) || voices.find(v => v.lang === 'en-US') || voices[0];
    if (preferred) utterance.voice = preferred;

    window.speechSynthesis.speak(utterance);
}

// Load voices (they load asynchronously)
if ('speechSynthesis' in window) {
    window.speechSynthesis.onvoiceschanged = () => {
        window.speechSynthesis.getVoices();
    };
}

// ── Event Handlers ──

// Connect button
$('#btn-connect').addEventListener('click', () => {
    const select = $('#select-character');
    const charId = select.value;
    if (!charId) {
        showToast('Please select a character first', 'error');
        return;
    }

    selectedCharacterId = charId;
    const option = select.selectedOptions[0];
    try {
        selectedCharacter = JSON.parse(option.dataset.character);
    } catch { selectedCharacter = null; }

    // Update UI
    if (selectedCharacter) {
        const archetypeEmojis = {
            wizard: '🧙', oracle: '🔮', inventor: '⚡',
            historian: '📚', trickster: '🃏', mentor: '🎓', custom: '✨'
        };
        $('#character-avatar').textContent = archetypeEmojis[selectedCharacter.archetype] || '🎭';
        $('#character-name').textContent = selectedCharacter.name;
        $('#character-archetype').textContent = selectedCharacter.archetype;
        $('#character-catchphrase').textContent = `"${selectedCharacter.catchphrase || '...'}"`;
    }

    $('#connect-screen').style.display = 'none';
    $('#earpiece-screen').style.display = 'block';

    connectWebSocket(charId);
});

// Disconnect button
$('#btn-disconnect').addEventListener('click', () => {
    disconnectWebSocket();
    $('#connect-screen').style.display = 'block';
    $('#earpiece-screen').style.display = 'none';
    showToast('Earpiece disconnected', 'info');
});

// Test cue
$('#btn-test-cue').addEventListener('click', () => {
    const testCue = {
        type: 'cue',
        character_name: selectedCharacter?.name || 'Test Character',
        attendee_name: 'Test Attendee',
        dialogue: 'Greetings, traveler! This is a test of your earpiece connection. The enchanted frequencies are flowing clearly through the digital void.',
        stage_direction: 'Gesture dramatically while testing the connection.',
        interaction_type: 'greeting',
        quest: null,
    };
    handleCueMessage(testCue);
});

// Clear feed
$('#btn-clear-feed').addEventListener('click', () => {
    const container = $('#dialogue-container');
    container.innerHTML = `
        <div class="card" id="waiting-card">
            <div class="waiting-indicator">
                <div class="radar"></div>
                <div style="font-size: 1.1rem; font-weight: 600;">Awaiting Badge Scan</div>
                <div style="font-size: 0.85rem;">Feed cleared. Ready for new interactions.</div>
            </div>
        </div>
    `;
    showToast('Feed cleared', 'info');
});

// Toggle audio
$('#btn-toggle-audio').addEventListener('click', () => {
    audioEnabled = !audioEnabled;
    $('#btn-toggle-audio').textContent = audioEnabled ? '🔊 Audio: ON' : '🔇 Audio: OFF';
    showToast(`Audio ${audioEnabled ? 'enabled' : 'disabled'}`, 'info');
    if (!audioEnabled && 'speechSynthesis' in window) {
        window.speechSynthesis.cancel();
    }
});

// Toggle text size
$('#btn-toggle-size').addEventListener('click', () => {
    largeText = !largeText;
    $('#btn-toggle-size').textContent = largeText ? '🔤 Normal Text' : '🔤 Large Text';
    document.querySelectorAll('.dialogue-text').forEach(el => {
        el.style.fontSize = largeText ? '1.6rem' : '1.25rem';
    });
});

// ── Initialize ──
loadCharacters();
