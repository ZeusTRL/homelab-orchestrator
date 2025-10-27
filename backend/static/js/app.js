// Simple hash-router + shared helpers

const API_BASE = window.location.origin;

// Tabs routing
function setActiveTab(route) {
  document.querySelectorAll('.tab').forEach(a => {
    a.classList.toggle('active', a.dataset.route === route);
  });
}

async function getJSON(path) {
  const res = await fetch(`${API_BASE}${path}`);
  if (!res.ok) throw new Error(`${path} failed: ${res.status}`);
  return res.json();
}

async function postJSON(path, body) {
  const res = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  });
  if (!res.ok) throw new Error(`${path} failed: ${res.status}`);
  return res.json();
}

// Optional: WebSocket (live updates) – backend endpoint can be added later.
// If not available, it fails silently.
let topoSocket = null;
function openTopologySocket(onMessage) {
  try {
    const proto = window.location.protocol === 'https:' ? 'wss' : 'ws';
    topoSocket = new WebSocket(`${proto}://${window.location.host}/ws/topology`);
    topoSocket.onmessage = (ev) => {
      try { const msg = JSON.parse(ev.data); onMessage?.(msg); } catch {}
    };
    topoSocket.onerror = () => {};
  } catch {}
}

function mount(view) {
  const viewEl = document.getElementById('view');
  viewEl.innerHTML = '';
  viewEl.appendChild(view);
}

function route() {
  const hash = (location.hash || '#topology').replace('#','');
  setActiveTab(hash);

  if (hash === 'topology') {
    mount(buildTopologyView());
  } else {
    const div = document.createElement('div');
    div.style.display = 'grid';
    div.style.placeItems = 'center';
    div.innerHTML = `<div class="muted" style="text-align:center;">${hash} view coming soon</div>`;
    mount(div);
  }
}

window.addEventListener('hashchange', route);
window.addEventListener('load', route);

// Export helpers for other modules
window.AppHelpers = { getJSON, postJSON, openTopologySocket, API_BASE };
