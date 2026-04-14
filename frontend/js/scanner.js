/**
 * NPC Actor System — Badge Scanner Simulator JavaScript
 * Handles: Attendee/Character selection, badge scan → API call, result display, history.
 */

const API = window.location.origin + '/api';

// ── State ──
let attendees = [];
let characters = [];
let scanHistory = [];
let isScanning = false;

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

// ── Load Data ──
async function loadAttendees() {
    try {
        const res = await fetch(`${API}/attendees`);
        attendees = await res.json();
        const select = $('#scan-attendee');
        select.innerHTML = '<option value="">— Select an attendee —</option>';
        attendees.forEach(a => {
            const opt = document.createElement('option');
            opt.value = a.badge_id;
            opt.textContent = `${a.name} (${a.badge_id}) — ${a.company || 'N/A'}`;
            opt.dataset.attendee = JSON.stringify(a);
            select.appendChild(opt);
        });
    } catch (e) {
        showToast('Failed to load attendees', 'error');
    }
}

async function loadCharacters() {
    try {
        const res = await fetch(`${API}/characters`);
        characters = await res.json();
        const select = $('#scan-character');
        select.innerHTML = '<option value="">— Select a character —</option>';
        const archetypeEmojis = {
            wizard: '🧙', oracle: '🔮', inventor: '⚡',
            historian: '📚', trickster: '🃏', mentor: '🎓', custom: '✨'
        };
        characters.forEach(c => {
            const emoji = archetypeEmojis[c.archetype] || '🎭';
            const opt = document.createElement('option');
            opt.value = c.id;
            opt.textContent = `${emoji} ${c.name} (${c.archetype})`;
            select.appendChild(opt);
        });
    } catch (e) {
        showToast('Failed to load characters', 'error');
    }
}

// ── Attendee Preview ──
$('#scan-attendee').addEventListener('change', (e) => {
    const select = e.target;
    const option = select.selectedOptions[0];
    const previewCard = $('#attendee-preview-card');

    if (!select.value || !option.dataset.attendee) {
        previewCard.style.display = 'none';
        return;
    }

    const attendee = JSON.parse(option.dataset.attendee);
    previewCard.style.display = 'block';
    $('#attendee-preview').innerHTML = `
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
            <div>
                <div style="font-size: 0.75rem; color: var(--text-muted); text-transform: uppercase; margin-bottom: 4px;">Name</div>
                <div style="font-weight: 600;">${escapeHtml(attendee.name)}</div>
            </div>
            <div>
                <div style="font-size: 0.75rem; color: var(--text-muted); text-transform: uppercase; margin-bottom: 4px;">Badge</div>
                <code style="color: var(--accent-cyan);">${escapeHtml(attendee.badge_id)}</code>
            </div>
            <div>
                <div style="font-size: 0.75rem; color: var(--text-muted); text-transform: uppercase; margin-bottom: 4px;">Company</div>
                <div>${escapeHtml(attendee.company || '—')}</div>
            </div>
            <div>
                <div style="font-size: 0.75rem; color: var(--text-muted); text-transform: uppercase; margin-bottom: 4px;">Role</div>
                <div>${escapeHtml(attendee.role || '—')}</div>
            </div>
            <div>
                <div style="font-size: 0.75rem; color: var(--text-muted); text-transform: uppercase; margin-bottom: 4px;">XP Points</div>
                <div style="color: var(--accent-amber); font-weight: 700;">${attendee.xp_points || 0} XP</div>
            </div>
            <div>
                <div style="font-size: 0.75rem; color: var(--text-muted); text-transform: uppercase; margin-bottom: 4px;">Interactions</div>
                <div>${attendee.interaction_count || 0}</div>
            </div>
        </div>
        <div style="margin-top: 12px;">
            <div style="font-size: 0.75rem; color: var(--text-muted); text-transform: uppercase; margin-bottom: 6px;">Interests</div>
            <div>${(attendee.interests || []).map(i => `<span class="tag">${escapeHtml(i)}</span>`).join(' ') || '<span class="tag">none</span>'}</div>
        </div>
        <div style="margin-top: 10px;">
            <div style="font-size: 0.75rem; color: var(--text-muted); text-transform: uppercase; margin-bottom: 6px;">Sessions Attended</div>
            <div>${(attendee.sessions_attended || []).map(s => `<span class="badge badge-blue" style="margin: 2px;">${escapeHtml(s)}</span>`).join(' ') || '<span class="tag">none</span>'}</div>
        </div>
    `;
});

// ── Badge Scan ──
async function performScan() {
    if (isScanning) return;

    const badgeId = $('#scan-attendee').value;
    const characterId = $('#scan-character').value;
    const interactionType = $('#scan-interaction').value;
    const customContext = $('#scan-context').value.trim();

    if (!badgeId) {
        showToast('Please select an attendee to scan', 'error');
        return;
    }
    if (!characterId) {
        showToast('Please select an NPC character', 'error');
        return;
    }

    isScanning = true;
    const scanZone = $('#scan-zone');
    const scanIcon = $('#scan-icon');
    const scanText = $('#scan-text');
    const btnScan = $('#btn-scan');

    // Scanning animation
    scanZone.classList.add('scanning');
    scanIcon.textContent = '⚡';
    scanText.textContent = 'Scanning badge...';
    btnScan.disabled = true;
    btnScan.innerHTML = '<span class="spinner" style="width:16px;height:16px;border-width:2px;"></span> Generating...';

    try {
        const res = await fetch(`${API}/scan`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                badge_id: badgeId,
                character_id: characterId,
                interaction_type: interactionType,
                custom_context: customContext || null,
            }),
        });

        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw new Error(err.detail || 'Scan failed');
        }

        const result = await res.json();
        displayResult(result);
        addToHistory(result);
        showToast('Dialogue generated & sent to actor!', 'success');

        // Success animation
        scanIcon.textContent = '✅';
        scanText.textContent = 'Scan complete!';
        setTimeout(() => {
            scanIcon.textContent = '📡';
            scanText.textContent = 'Tap to Simulate Badge Scan';
        }, 2000);

    } catch (e) {
        showToast(`Scan failed: ${e.message}`, 'error');
        scanIcon.textContent = '❌';
        scanText.textContent = 'Scan failed — try again';
        setTimeout(() => {
            scanIcon.textContent = '📡';
            scanText.textContent = 'Tap to Simulate Badge Scan';
        }, 2000);
    } finally {
        isScanning = false;
        scanZone.classList.remove('scanning');
        btnScan.disabled = false;
        btnScan.innerHTML = '📡 Generate NPC Dialogue';
    }
}

// ── Display Result ──
function displayResult(result) {
    const typeEmojis = {
        greeting: '👋', quest: '⚔️', advice: '💡',
        riddle: '🧩', lore: '📖', farewell: '🌟'
    };

    $('#result-type').textContent = `${typeEmojis[result.interaction_type] || '💬'} ${result.interaction_type}`;

    $('#result-content').innerHTML = `
        <div style="margin-bottom: 16px;">
            <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 12px;">
                <strong style="color: var(--accent-cyan);">${escapeHtml(result.character_name)}</strong>
                <span style="color: var(--text-muted);">→</span>
                <strong>${escapeHtml(result.attendee_name)}</strong>
            </div>
            <div style="font-size: 1.15rem; line-height: 1.8; padding: 20px; background: var(--bg-glass); border-radius: var(--radius-md); border-left: 3px solid var(--accent-primary);">
                ${escapeHtml(result.dialogue)}
            </div>
        </div>
        ${result.stage_direction ? `
            <div style="padding: 10px 14px; background: rgba(251,191,36,0.08); border-radius: var(--radius-sm); color: var(--accent-amber); font-size: 0.85rem; margin-bottom: 12px;">
                🎬 <em>${escapeHtml(result.stage_direction)}</em>
            </div>
        ` : ''}
        ${result.quest ? `
            <div style="padding: 12px 16px; background: rgba(52,211,153,0.08); border: 1px solid rgba(52,211,153,0.2); border-radius: var(--radius-sm); color: var(--accent-emerald); font-weight: 600;">
                🎯 Quest: ${escapeHtml(result.quest)}
            </div>
        ` : ''}
        <div style="margin-top: 16px; display: flex; gap: 8px;">
            <button class="btn btn-sm" onclick="playResultAudio()" title="Play dialogue audio">🔊 Play Audio</button>
            <button class="btn btn-sm" onclick="copyResult()" title="Copy dialogue to clipboard">📋 Copy</button>
        </div>
    `;

    // Store for playback
    window._lastResult = result;
}

// ── Audio Playback ──
function playResultAudio() {
    const result = window._lastResult;
    if (!result) return;

    if (result.audio_base64) {
        const audio = new Audio(`data:audio/mp3;base64,${result.audio_base64}`);
        audio.play().catch(() => speakBrowser(result.dialogue));
    } else {
        speakBrowser(result.dialogue);
    }
}

function speakBrowser(text) {
    if (!('speechSynthesis' in window)) {
        showToast('Text-to-speech not supported in this browser', 'error');
        return;
    }
    window.speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(text);
    u.rate = 0.95;
    u.lang = 'en-US';
    const voices = window.speechSynthesis.getVoices();
    const preferred = voices.find(v => v.name.includes('Google')) || voices.find(v => v.lang === 'en-US');
    if (preferred) u.voice = preferred;
    window.speechSynthesis.speak(u);
}

function copyResult() {
    const result = window._lastResult;
    if (!result) return;
    navigator.clipboard.writeText(result.dialogue).then(() => {
        showToast('Dialogue copied!', 'success');
    });
}

// ── Scan History ──
function addToHistory(result) {
    scanHistory.unshift(result);
    if (scanHistory.length > 20) scanHistory.pop();
    renderHistory();
}

function renderHistory() {
    const container = $('#scan-history');
    if (scanHistory.length === 0) {
        container.innerHTML = `<div class="empty-state"><div class="icon">📝</div><div class="title">No scans yet</div></div>`;
        return;
    }

    const typeEmojis = {
        greeting: '👋', quest: '⚔️', advice: '💡',
        riddle: '🧩', lore: '📖', farewell: '🌟'
    };

    container.innerHTML = scanHistory.map((r, i) => `
        <div class="interaction-item" style="cursor: pointer;" onclick="displayResult(window._scanHistory[${i}])">
            <div class="interaction-avatar">${typeEmojis[r.interaction_type] || '💬'}</div>
            <div class="interaction-content">
                <div class="interaction-header">
                    <strong>${escapeHtml(r.character_name)} → ${escapeHtml(r.attendee_name)}</strong>
                    <span class="badge badge-indigo">${r.interaction_type}</span>
                </div>
                <div class="interaction-text">${escapeHtml(r.dialogue)}</div>
            </div>
        </div>
    `).join('');

    window._scanHistory = scanHistory;
}

// ── Clear History ──
$('#btn-clear-history').addEventListener('click', () => {
    scanHistory = [];
    renderHistory();
    showToast('History cleared', 'info');
});

// ── Event Listeners ──
$('#btn-scan').addEventListener('click', performScan);

$('#scan-zone').addEventListener('click', performScan);
$('#scan-zone').addEventListener('keydown', (e) => {
    if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        performScan();
    }
});

// ── Initialize ──
async function init() {
    await Promise.all([loadAttendees(), loadCharacters()]);
}

// Load voices for browser TTS
if ('speechSynthesis' in window) {
    window.speechSynthesis.onvoiceschanged = () => window.speechSynthesis.getVoices();
}

init();
