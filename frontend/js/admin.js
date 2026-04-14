/**
 * NPC Actor System — Admin Dashboard JavaScript
 * Handles: Attendee/Character CRUD, stats refresh, interaction log.
 */

const API = window.location.origin + '/api';

// ── State ──
let attendees = [];
let characters = [];
let interactions = [];

// ── Utilities ──
function $(sel) { return document.querySelector(sel); }
function $$(sel) { return document.querySelectorAll(sel); }

function showToast(message, type = 'info') {
    const container = $('#toast-container');
    const icons = { success: '✅', error: '❌', info: 'ℹ️' };
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `<span>${icons[type] || 'ℹ️'}</span><span>${message}</span>`;
    container.appendChild(toast);
    setTimeout(() => toast.remove(), 4000);
}

async function apiFetch(endpoint, options = {}) {
    try {
        const res = await fetch(`${API}${endpoint}`, {
            headers: { 'Content-Type': 'application/json' },
            ...options,
        });
        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw new Error(err.detail || `HTTP ${res.status}`);
        }
        return await res.json();
    } catch (e) {
        console.error(`API error (${endpoint}):`, e);
        throw e;
    }
}

// ── Data Loading ──
async function loadAttendees() {
    try {
        attendees = await apiFetch('/attendees');
        renderAttendees();
        $('#stat-attendees').textContent = attendees.length;
    } catch (e) {
        showToast('Failed to load attendees', 'error');
    }
}

async function loadCharacters() {
    try {
        characters = await apiFetch('/characters');
        renderCharacters();
        $('#stat-characters').textContent = characters.length;
    } catch (e) {
        showToast('Failed to load characters', 'error');
    }
}

async function loadInteractions() {
    try {
        interactions = await apiFetch('/interactions?limit=20');
        renderInteractions();
        $('#stat-interactions').textContent = interactions.length;
    } catch (e) {
        showToast('Failed to load interactions', 'error');
    }
}

async function loadHealth() {
    try {
        const health = await apiFetch('/health');
        const count = health.connected_actors ? health.connected_actors.length : 0;
        $('#stat-actors').textContent = count;
    } catch {
        $('#stat-actors').textContent = '—';
    }
}

// ── Render: Attendees Table ──
function renderAttendees() {
    const tbody = $('#attendees-tbody');
    if (attendees.length === 0) {
        tbody.innerHTML = `<tr><td colspan="5"><div class="empty-state">
            <div class="icon">👥</div><div class="title">No attendees registered</div>
        </div></td></tr>`;
        return;
    }
    tbody.innerHTML = attendees.map(a => `
        <tr>
            <td>
                <strong>${escapeHtml(a.name)}</strong>
                <br><span style="font-size:0.75rem; color:var(--text-muted)">${escapeHtml(a.company || '')} • ${escapeHtml(a.role || '')}</span>
            </td>
            <td><code style="color:var(--accent-cyan)">${escapeHtml(a.badge_id)}</code></td>
            <td>${(a.interests || []).slice(0, 3).map(i => `<span class="tag">${escapeHtml(i)}</span>`).join('')}</td>
            <td><span style="color:var(--accent-amber); font-weight:700; font-family:var(--font-mono)">${a.xp_points || 0}</span></td>
            <td>
                <button class="btn btn-sm btn-danger" onclick="deleteAttendee('${a.id}')" aria-label="Delete ${escapeHtml(a.name)}">🗑</button>
            </td>
        </tr>
    `).join('');
}

// ── Render: Characters ──
function renderCharacters() {
    const container = $('#characters-list');
    if (characters.length === 0) {
        container.innerHTML = `<div class="empty-state">
            <div class="icon">🎭</div><div class="title">No characters created</div>
        </div>`;
        return;
    }

    const archetypeEmojis = {
        wizard: '🧙', oracle: '🔮', inventor: '⚡',
        historian: '📚', trickster: '🃏', mentor: '🎓', custom: '✨'
    };

    container.innerHTML = characters.map(c => `
        <div class="interaction-item" style="border-radius: var(--radius-sm);">
            <div class="interaction-avatar" style="font-size: 1.4rem;">${archetypeEmojis[c.archetype] || '🎭'}</div>
            <div class="interaction-content">
                <div class="interaction-header">
                    <strong>${escapeHtml(c.name)}</strong>
                    <span class="badge badge-indigo">${c.archetype}</span>
                </div>
                <div class="interaction-text" style="-webkit-line-clamp: 1;">
                    ${escapeHtml(c.catchphrase || c.backstory || '—')}
                </div>
                <div style="margin-top: 6px; font-size: 0.75rem; color: var(--text-muted);">
                    ${c.assigned_actor ? `👤 ${escapeHtml(c.assigned_actor)}` : 'Unassigned'} •
                    ${c.active ? '<span style="color:var(--accent-emerald)">Active</span>' : '<span style="color:var(--text-muted)">Inactive</span>'}
                </div>
            </div>
            <button class="btn btn-sm btn-danger" onclick="deleteCharacter('${c.id}')" aria-label="Delete ${escapeHtml(c.name)}" style="flex-shrink:0;">🗑</button>
        </div>
    `).join('');
}

// ── Render: Interactions ──
function renderInteractions() {
    const container = $('#interactions-list');
    if (interactions.length === 0) {
        container.innerHTML = `<div class="empty-state">
            <div class="icon">📡</div><div class="title">No interactions yet</div>
            <div class="description">Scan a badge to generate NPC dialogue</div>
        </div>`;
        return;
    }

    const typeEmojis = {
        greeting: '👋', quest: '⚔️', advice: '💡',
        riddle: '🧩', lore: '📖', farewell: '🌟'
    };

    container.innerHTML = interactions.map(i => `
        <div class="interaction-item">
            <div class="interaction-avatar">${typeEmojis[i.interaction_type] || '💬'}</div>
            <div class="interaction-content">
                <div class="interaction-header">
                    <strong>${escapeHtml(i.character_name)} → ${escapeHtml(i.attendee_name)}</strong>
                    <span class="badge badge-${i.interaction_type === 'quest' ? 'emerald' : 'indigo'}">${i.interaction_type}</span>
                    <span class="time">${formatTime(i.timestamp)}</span>
                </div>
                <div class="interaction-text">${escapeHtml(i.dialogue_generated || '—')}</div>
                ${i.quest_given ? `<div style="margin-top:4px; font-size:0.8rem; color:var(--accent-emerald);">🎯 Quest: ${escapeHtml(i.quest_given)}</div>` : ''}
            </div>
        </div>
    `).join('');
}

// ── CRUD Actions ──
async function deleteAttendee(id) {
    if (!confirm('Delete this attendee?')) return;
    try {
        await apiFetch(`/attendees/${id}`, { method: 'DELETE' });
        showToast('Attendee deleted', 'success');
        loadAttendees();
    } catch (e) {
        showToast('Failed to delete attendee', 'error');
    }
}

async function deleteCharacter(id) {
    if (!confirm('Delete this character?')) return;
    try {
        await apiFetch(`/characters/${id}`, { method: 'DELETE' });
        showToast('Character deleted', 'success');
        loadCharacters();
    } catch (e) {
        showToast('Failed to delete character', 'error');
    }
}

// ── Modals ──
function openModal(id) {
    $(`#${id}`).classList.add('active');
}

function closeModal(id) {
    $(`#${id}`).classList.remove('active');
}

// Close modals on backdrop click or cancel
$$('.modal-overlay').forEach(overlay => {
    overlay.addEventListener('click', e => {
        if (e.target === overlay) overlay.classList.remove('active');
    });
});

$$('.modal-close, .modal-cancel').forEach(btn => {
    btn.addEventListener('click', () => {
        btn.closest('.modal-overlay').classList.remove('active');
    });
});

// ── Form: Add Attendee ──
$('#btn-add-attendee').addEventListener('click', () => openModal('modal-attendee'));

$('#form-attendee').addEventListener('submit', async (e) => {
    e.preventDefault();
    const form = e.target;
    const data = {
        name: form.name.value.trim(),
        badge_id: form.badge_id.value.trim(),
        email: form.email.value.trim() || null,
        company: form.company.value.trim() || null,
        role: form.role.value.trim() || null,
        interests: form.interests.value.split(',').map(s => s.trim()).filter(Boolean),
        sessions_attended: form.sessions_attended.value.split(',').map(s => s.trim()).filter(Boolean),
    };

    if (!data.name || !data.badge_id) {
        showToast('Name and Badge ID are required', 'error');
        return;
    }

    try {
        await apiFetch('/attendees', {
            method: 'POST',
            body: JSON.stringify(data),
        });
        showToast('Attendee created!', 'success');
        closeModal('modal-attendee');
        form.reset();
        loadAttendees();
    } catch (e) {
        showToast(`Failed: ${e.message}`, 'error');
    }
});

// ── Form: Add Character ──
$('#btn-add-character').addEventListener('click', () => openModal('modal-character'));

$('#form-character').addEventListener('submit', async (e) => {
    e.preventDefault();
    const form = e.target;
    const data = {
        name: form.name.value.trim(),
        archetype: form.archetype.value,
        personality_prompt: form.personality_prompt.value.trim(),
        backstory: form.backstory.value.trim() || null,
        catchphrase: form.catchphrase.value.trim() || null,
        assigned_actor: form.assigned_actor.value.trim() || null,
    };

    if (!data.name || !data.personality_prompt) {
        showToast('Name and personality prompt are required', 'error');
        return;
    }

    try {
        await apiFetch('/characters', {
            method: 'POST',
            body: JSON.stringify(data),
        });
        showToast('Character created!', 'success');
        closeModal('modal-character');
        form.reset();
        loadCharacters();
    } catch (e) {
        showToast(`Failed: ${e.message}`, 'error');
    }
});

// ── Refresh Button ──
$('#btn-refresh-interactions').addEventListener('click', () => {
    loadInteractions();
    showToast('Interactions refreshed', 'info');
});

// ── Helpers ──
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text || '';
    return div.innerHTML;
}

function formatTime(ts) {
    if (!ts) return '';
    try {
        const d = new Date(ts);
        return d.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
    } catch {
        return '';
    }
}

// ── Initialize ──
async function init() {
    await Promise.all([
        loadAttendees(),
        loadCharacters(),
        loadInteractions(),
        loadHealth(),
    ]);

    // Auto-refresh every 15 seconds
    setInterval(() => {
        loadInteractions();
        loadHealth();
    }, 15000);
}

init();
