/* global cytoscape */
(function(){
  // --- SAFE PLUGIN REGISTRATION (handles UMD default too) ---
  const panzoomPlugin = (window.cytoscapePanzoom && typeof window.cytoscapePanzoom === 'function')
    ? window.cytoscapePanzoom
    : (window.cytoscapePanzoom && window.cytoscapePanzoom.default && typeof window.cytoscapePanzoom.default === 'function')
      ? window.cytoscapePanzoom.default
      : null;

  const minimapPlugin = (window.cytoscapeMinimap && typeof window.cytoscapeMinimap === 'function')
    ? window.cytoscapeMinimap
    : (window.cytoscapeMinimap && window.cytoscapeMinimap.default && typeof window.cytoscapeMinimap.default === 'function')
      ? window.cytoscapeMinimap.default
      : null;

  try { if (panzoomPlugin) cytoscape.use(panzoomPlugin); } catch {}
  try { if (minimapPlugin) cytoscape.use(minimapPlugin); } catch {}

  const { getJSON, postJSON, openTopologySocket } = window.AppHelpers;

  const ICONS = {
    juniper: '/static/icons/juniper.png',
    pfsense: '/static/icons/pfsense.png',
    server:  '/static/icons/server.png',
    switch:  '/static/icons/switch.png',
    unknown: '/static/icons/unknown.png'
  };

  const debounce = (fn, ms = 600) => { let t; return (...a) => { clearTimeout(t); t = setTimeout(() => fn(...a), ms); }; };
  const vkey = v => (v||'').toLowerCase().includes('juniper') ? 'juniper'
               : (v||'').toLowerCase().includes('pfsense') ? 'pfsense'
               : (v||'').toLowerCase().includes('switch')  ? 'switch'
               : (v||'').toLowerCase().includes('server')  ? 'server'
               : 'unknown';

  async function fetchTopology() { return getJSON('/topology'); }
  async function fetchLayout()   { return getJSON('/topology/layout'); }

  function collectPositions(cy) {
    return { points: cy.nodes().map(n => ({
      device_id: Number(n.id()),
      x: n.position('x'),
      y: n.position('y')
    })) };
  }

  function applySavedPositions(cy, map) {
    const pts = (map && map.points) || {};
    let applied = 0;
    for (const [id, pos] of Object.entries(pts)) {
      const node = cy.$id(String(id));
      if (node.length > 0 && pos && typeof pos.x === 'number' && typeof pos.y === 'number') {
        node.position({ x: pos.x, y: pos.y });
        applied++;
      }
    }
    return applied;
  }

  function makeSidebar() {
    const side = document.createElement('aside');
    side.className = 'sidebar';
    side.innerHTML = `
      <h2>Details</h2>
      <div class="muted">Click a node to view device info.</div>
      <div class="kv" id="kv"></div>
      <div class="buttonbar">
        <button id="lockBtn">Lock</button>
        <button id="unlockBtn">Unlock</button>
        <button id="saveBtn" class="primary">Save Positions</button>
      </div>
      <div><span class="badge" id="statusBadge">Idle</span></div>
    `;
    return side;
  }

  function makeRoot() {
    const root = document.createElement('div');
    root.id = 'topology-root';
    root.innerHTML = `<div id="cy"></div><div class="legend" id="legend">Loading...</div>`;
    return root;
  }

  function setKV(el, entries) {
    el.innerHTML = entries.map(([k,v]) => `<div class="k">${k}</div><div>${v ?? ''}</div>`).join('');
  }

  function buildTopologyView() {
    const container = document.createElement('div');
    container.style.display = 'contents';

    const root = makeRoot();
    const side = makeSidebar();
    container.appendChild(root);
    container.appendChild(side);

    (async () => {
      const legend = document.getElementById('legend');
      const topo = await fetchTopology();
      const layoutMap = await fetchLayout();

      const nodes = topo.nodes.map(n => ({
        data: {
          id: String(n.id),
          label: n.label || n.ip,
          vendor: n.vendor || 'unknown',
          ip: n.ip,
          icon: ICONS[vkey(n.vendor)]
        }
      }));
      const edges = topo.edges.map(e => ({
        data: {
          source: String(e.source),
          target: String(e.target),
          label: e.local_if || e.remote_port || ''
        }
      }));

      const cy = cytoscape({
        container: document.getElementById('cy'),
        elements: { nodes, edges },
        layout: { name: 'preset' },
        style: [
          {
            selector: 'node',
            style: {
              'background-color': '#888',
              'background-image': 'data(icon)',
              'background-fit': 'cover',
              'shape': 'round-rectangle',
              'border-width': 2,
              'border-color': '#2f3a4a',
              'label': 'data(label)',
              'color': '#fff',
              'font-size': '11px',
              'text-valign': 'center',
              'text-outline-color': '#111',
              'text-outline-width': 2,
              'width': 64, 'height': 36
            }
          },
          {
            selector: 'edge',
            style: {
              'width': 2, 'line-color': '#7a8699', 'curve-style': 'bezier',
              'label': 'data(label)', 'font-size': '9px', 'color': '#cbd5e1',
              'text-background-opacity': 1, 'text-background-color': '#0d1117'
            }
          },
          { selector: ':selected', style: { 'border-width': 3, 'border-color': '#3b82f6' } }
        ]
      });

      // Init extras (only if plugin actually registered)
      try { if (typeof cy.minimap === 'function') cy.minimap({ position: 'right-bottom', width: 200, height: 120 }); } catch {}
      try { if (typeof cy.panzoom === 'function') cy.panzoom({}); } catch {}

      // Apply positions or run initial layout
      const applied = applySavedPositions(cy, layoutMap);
      if (applied === 0) cy.layout({ name: 'cose', animate: false }).run();
      legend.textContent = `Loaded ${nodes.length} devices, ${edges.length} links • restored ${applied} positions`;

      // Sidebar controls
      const kvEl = side.querySelector('#kv');
      const status = side.querySelector('#statusBadge');
      const lockBtn = side.querySelector('#lockBtn');
      const unlockBtn = side.querySelector('#unlockBtn');
      const saveBtn = side.querySelector('#saveBtn');

      let editing = false;
      cy.autoungrabify(!editing);
      lockBtn.onclick = () => { editing = false; cy.autoungrabify(true); status.textContent = 'Locked'; };
      unlockBtn.onclick = () => { editing = true; cy.autoungrabify(false); status.textContent = 'Unlocked (drag to move)'; };

      async function saveNow() {
        try {
          status.textContent = 'Saving...';
          await postJSON('/topology/layout', collectPositions(cy));
          status.textContent = 'Saved ✔';
        } catch (e) {
          status.textContent = 'Save failed ✖';
          console.error('Save positions failed:', e);
        }
      }
      saveBtn.onclick = saveNow;

      const debouncedSave = debounce(saveNow, 750);
      cy.on('dragfree', 'node', () => { if (editing) debouncedSave(); });

      // Live updates (optional)
      openTopologySocket(async (msg) => {
        if (msg?.event === 'update_topology') {
          legend.textContent = 'Updating topology...';
          const newTopo = await fetchTopology();
          cy.elements().remove();
          cy.add({
            nodes: newTopo.nodes.map(n => ({ data: { id: String(n.id), label: n.label || n.ip, vendor: n.vendor || 'unknown', ip: n.ip, icon: ICONS[vkey(n.vendor)] } })),
            edges: newTopo.edges.map(e => ({ data: { source: String(e.source), target: String(e.target), label: e.local_if || e.remote_port || '' } }))
          });
          applySavedPositions(cy, await fetchLayout());
          legend.textContent = 'Topology updated';
        }
      });

      // Click node → info
      cy.on('tap', 'node', (evt) => {
        const d = evt.target.data();
        setKV(kvEl, [['Label', d.label], ['Vendor', d.vendor||'unknown'], ['IP', d.ip||''], ['ID', evt.target.id()]]);
      });
    })().catch(err => {
      const legend = document.getElementById('legend');
      if (legend) legend.textContent = 'Failed to load: ' + err.message;
      console.error(err);
    });

    return container;
  }

  window.buildTopologyView = buildTopologyView;
})();
