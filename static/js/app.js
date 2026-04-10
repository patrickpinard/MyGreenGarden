/**
 * MyGreenGarden V7.0 — JavaScript principal
 * Utilitaires partagés : polling, DOM helpers, toasts, contrôle actionneurs.
 */

'use strict';

// ─── État connexion Pi ────────────────────────────────────────────────────────

let _piConnected = null;

function _setPiStatus(connected) {
  if (_piConnected === connected) return;
  _piConnected = connected;
  const dot = document.getElementById('pi-status-dot');
  const label = document.getElementById('pi-status-label');
  if (dot) {
    dot.classList.remove('bg-slate-300', 'bg-emerald-400', 'bg-rose-400');
    dot.classList.add(connected ? 'bg-emerald-400' : 'bg-rose-400');
  }
  if (label) {
    label.textContent = connected ? 'En ligne' : 'Hors ligne';
    label.className = 'text-xs font-medium hidden sm:inline ' + (connected ? 'text-emerald-600' : 'text-rose-500');
  }
}


// ─── Polling AJAX ────────────────────────────────────────────────────────────

const _pollingIntervals = {};

/**
 * Démarre un polling AJAX vers `url` toutes les `intervalMs` ms.
 * Exécute `callback(data)` à chaque réponse JSON réussie.
 * Exécute immédiatement au démarrage.
 */
function startPolling(url, callback, intervalMs = 30000) {
  const _fetch = () => {
    fetch(url)
      .then(r => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then(data => {
        _setPiStatus(true);
        callback(data);
      })
      .catch(err => {
        _setPiStatus(false);
        console.warn(`[Polling] ${url} →`, err.message);
      });
  };

  _fetch(); // premier appel immédiat
  const id = setInterval(_fetch, intervalMs);
  _pollingIntervals[url] = id;
  return id;
}

function stopPolling(url) {
  if (_pollingIntervals[url]) {
    clearInterval(_pollingIntervals[url]);
    delete _pollingIntervals[url];
  }
}


// ─── DOM Helpers ─────────────────────────────────────────────────────────────

function setVal(id, value) {
  const el = document.getElementById(id);
  if (el) el.textContent = value;
}

function setWidth(id, pct) {
  const el = document.getElementById(id);
  if (el) el.style.width = Math.max(0, Math.min(100, pct || 0)) + '%';
}

function setCheck(id, checked) {
  const el = document.getElementById(id);
  if (el) el.checked = !!checked;
}

function setBadge(el, type, text) {
  if (!el) return;
  el.textContent = text;
  el.className = el.className
    .replace(/badge-on|badge-off|badge-warn|badge-err/g, '')
    .trim();
  el.classList.add(`badge-${type}`);
}

function setBadgeByState(id, isOn, onLabel, offLabel) {
  const el = document.getElementById(id);
  if (!el) return;
  if (isOn) {
    setBadge(el, 'on', onLabel);
  } else {
    setBadge(el, 'off', offLabel);
  }
}

function setToggle(id, isOn) {
  const el = document.getElementById(id);
  if (el) el.checked = !!isOn;
}


// ─── Toast notification ───────────────────────────────────────────────────────

let _toastTimer = null;

function showToast(message, duration = 3000) {
  const toast = document.getElementById('toast');
  if (!toast) return;
  toast.textContent = message;
  toast.classList.remove('hidden');
  toast.style.opacity = '1';
  clearTimeout(_toastTimer);
  _toastTimer = setTimeout(() => {
    toast.style.opacity = '0';
    setTimeout(() => toast.classList.add('hidden'), 300);
  }, duration);
}


// ─── Alertes ─────────────────────────────────────────────────────────────────

// Alertes locales persistantes — ne disparaissent que sur validation manuelle
let _localAlerts = [];
let _acknowledgedIds = new Set();

function updateAlertBanner(alerts) {
  if (!alerts || alerts.length === 0) return; // Ne jamais cacher automatiquement

  // Ajouter uniquement les nouvelles alertes non déjà connues
  alerts.forEach(a => {
    const id = a.id || a.message;
    if (!_acknowledgedIds.has(id) && !_localAlerts.find(x => (x.id || x.message) === id)) {
      _localAlerts.push({ ...a, _id: id, _ts: new Date() });
    }
  });

  _renderAlerts();
}

function _renderAlerts() {
  const pending = _localAlerts.filter(a => !_acknowledgedIds.has(a._id));

  const banner  = document.getElementById('alert-banner');
  const text    = document.getElementById('alert-banner-text');
  const bell    = document.getElementById('alert-bell');
  const count   = document.getElementById('alert-count');
  const countBadge = document.getElementById('alert-count-badge');
  const list    = document.getElementById('alert-list');

  if (pending.length === 0) {
    banner?.classList.add('hidden');
    bell?.classList.add('hidden');
    return;
  }

  // Bannière — montre la dernière alerte non acquittée
  const latest = pending[pending.length - 1];
  if (banner && text) {
    banner.classList.remove('hidden');
    text.textContent = latest.message;
  }

  // Cloche
  if (bell) bell.classList.remove('hidden');
  const n = pending.length;
  if (count) count.textContent = n;
  if (countBadge) countBadge.textContent = n;

  // Liste détaillée avec bouton "Valider" par alerte
  if (list) {
    const levelColor = { ERROR: 'bg-rose-500', WARNING: 'bg-amber-400', INFO: 'bg-sky-400' };
    list.innerHTML = pending.map(a => `
      <div class="flex items-start gap-3 px-4 py-3" data-alert-id="${a._id}">
        <span class="mt-1.5 h-2 w-2 flex-shrink-0 rounded-full ${levelColor[a.level] || 'bg-rose-400'}"></span>
        <div class="flex-1 min-w-0">
          <p class="text-sm text-slate-700 leading-snug">${a.message}</p>
          <p class="mt-0.5 text-xs text-slate-400">${a._ts.toLocaleTimeString('fr-CH', {hour:'2-digit',minute:'2-digit'})}</p>
        </div>
        <button onclick="acknowledgeAlert('${a._id}')"
                class="flex-shrink-0 rounded-lg bg-emerald-50 px-2.5 py-1 text-xs font-semibold text-emerald-700 hover:bg-emerald-100 transition active:scale-95">
          ✓ Valider
        </button>
      </div>`).join('');
  }
}

function acknowledgeAlert(id) {
  _acknowledgedIds.add(id);
  _renderAlerts();
}

function acknowledgeBanner() {
  // Valide la dernière alerte visible dans la bannière
  const pending = _localAlerts.filter(a => !_acknowledgedIds.has(a._id));
  if (pending.length > 0) {
    acknowledgeAlert(pending[pending.length - 1]._id);
  }
}

function clearAlerts() {
  // Valide toutes les alertes localement + nettoie côté serveur
  _localAlerts.forEach(a => _acknowledgedIds.add(a._id));
  _localAlerts = [];
  _acknowledgedIds.clear();
  document.getElementById('alert-banner')?.classList.add('hidden');
  document.getElementById('alert-bell')?.classList.add('hidden');
  document.getElementById('alert-panel')?.classList.add('hidden');
  fetch('/api/system/clear_alerts', { method: 'POST' }).catch(() => {});
}


// ─── Contrôle actionneurs ─────────────────────────────────────────────────────

async function apiPost(url, body = {}) {
  const r = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!r.ok) throw new Error(`HTTP ${r.status}`);
  return r.json();
}

async function toggleActuator(name, state = undefined) {
  const body = state !== undefined ? { state } : {};
  try {
    const data = await apiPost(`/api/actuator/${name}`, body);
    const isOn = data[`${name}_on`] ?? data[`${name}_open`] ?? state;
    showToast(`${name} → ${isOn ? 'ON' : 'OFF'}`);
    return data;
  } catch (e) {
    showToast('❌ Erreur commande');
  }
}

async function toggleMode(modeName, enabled) {
  try {
    await apiPost(`/api/mode/${modeName}`, { enabled });
    showToast(`Mode ${modeName} : ${enabled ? 'AUTO' : 'MANUEL'}`);
  } catch {
    showToast('❌ Erreur mode');
  }
}

function forceCycle() {
  if (typeof showConfirm === 'function') {
    showConfirm(
      'Forcer un cycle',
      'Déclencher immédiatement un cycle d\'automation ?',
      async () => {
        try {
          await apiPost('/api/system/force_cycle');
          showToast('⚡ Cycle forcé démarré');
        } catch {
          showToast('❌ Erreur');
        }
      },
      { okLabel: 'Forcer', okClass: 'bg-teal-500 hover:bg-teal-400' }
    );
  } else {
    apiPost('/api/system/force_cycle')
      .then(() => showToast('⚡ Cycle forcé démarré'))
      .catch(() => showToast('❌ Erreur'));
  }
}


// ─── PWA Service Worker ───────────────────────────────────────────────────────

if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker
      .register('/static/sw.js')
      .then(reg => console.log('[SW] Enregistré', reg.scope))
      .catch(err => console.warn('[SW] Échec enregistrement', err));
  });
}
