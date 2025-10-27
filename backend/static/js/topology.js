/* global cytoscape */
(function(){
  // Register plugins ONLY if they’re functions (prevents undefined.apply errors)
  if (typeof window.cytoscapePanzoom === 'function') {
    try { cytoscape.use(window.cytoscapePanzoom); } catch (e) {}
  }
  if (typeof window.cytoscapeMinimap === 'function') {
    try { cytoscape.use(window.cytoscapeMinimap); } catch (e) {}
  }


  const { getJSON, postJSON, openTopologySocket, API_BASE } = window.AppHelpers;

  const ICONS = {
    juniper: '/static/icons/juniper.png',
    pfsense: '/static/icons/pfsense.png',
    server:  '/static/icons/server.png',
    switch:  '/static/icons/switch.png',
    unknown: '/static/icons/unknown.png'
  };

  const debounce = (fn, ms = 600) => {
    let t; return (...args) => { clearTimeout(t); t = setTimeout(() => fn(...args), ms); };
  };

  function vendorKey(vendor) {
    const v = (vendor || '').toLowerCase();
    if (v.includes('juniper')) return 'juniper';
    if (v.includes('pfsense')) return 'pfsense';
    if (v.includes('switch')) return 'switch';
    if (v.includes('server')) return 'server';
    return 'unknown';
  }

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
  const pts = map.points || {};
  let applied = 0;
  Object.entries(pts).forEach(([id, pos]) => {
    const node = cy.$id(String(id));
    if (node.length > 0) {
      node.position({ x: pos.x, y: pos.y });
      applied++;
    }
  });
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
        <button id="lockBtn" class="">Lock</button>
        <button id="unlockBtn" class="">Unlock</button>
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

  function setKV(kvEl, entries) {
    kvEl.innerHTML = entries.map(([k,v]) => `<div class="k">${k}</div><div>${v ?? ''}</div>`).join('');
  }

  function buildTopologyView() {
    const container = document.createElement('div');
    container.style.display = 'contents';

    const root = makeRoot();
    const side = makeSidebar();

    container.appendChild(root);
    container.appendChild(side);

    (async () => {
      const topo = await fetchTopology();
      const layoutMap = await fetchLayout();

      const nodes = topo.nodes.map(n => ({
        data: {
          id: String(n.id),
          label: n.label || n.ip,
          vendor: n.vendor || 'unknown',
          ip: n.ip,
          icon: ICONS[vendorKey(n.vendor)]
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
        layout: { name: 'preset' }, // use saved positions if present
        style: [
          {
            selector: 'node',
            style: {
              'background-color': '#888',           // fallback if no image
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

      // Minimap & panzoom
      cy.minimap({ position: 'right-bottom', width: 200, height: 120 });
      cy.panzoom({ });

      // Apply saved positions
      const applied = applySavedPositions(cy, layoutMap);
      if (applied === 0) cy.layout({ name: 'cose', animate: false }).run();
      const legend = document.getElementById('legend');
      legend.textContent = `Loaded ${nodes.length} devices, ${edges.length} links • restored ${applied} positions`;

      // Sidebar interactions
      const kvEl = side.querySelector('#kv');
      const status = side.querySelector('#statusBadge');
      const lockBtn = side.querySelector('#lockBtn');
      const unlockBtn = side.querySelector('#unlockBtn');
      const saveBtn = side.querySelector('#saveBtn');

      let editing = false;
      cy.autoungrabify(!editing);

      lockBtn.onclick = () => { editing = false; cy.autoungrabify(true); status.textContent = 'Locked'; };
      unlockBtn.onclick = () => { editing = true; cy.autoungrabify(false); status.textContent = 'Unlocked (drag to move)'; };
      saveBtn.onclick = async () => {
        status.textContent = 'Saving...';
        await postJSON('/topology/layout', collectPositions(cy));
        status.textContent = 'Saved ✔';
      };

      // Click a node → details in side panel
      cy.on('tap', 'node', (evt) => {
        const d = evt.target.data();
        setKV(kvEl, [
          ['Label', d.label],
          ['Vendor', d.vendor || 'unknown'],
          ['IP', d.ip || ''],
          ['ID', evt.target.id()],
        ]);
      });

      // Auto-save on drag end (if unlocked)
      const debouncedSave = debounce(async () => {
        status.textContent = 'Saving...';
        await postJSON('/topology/layout', collectPositions(cy));
        status.textContent = 'Saved ✔';
      }, 750);

      cy.on('dragfree', 'node', () => { if (editing) debouncedSave(); });

      // Optional live updates: refetch on WS message
      openTopologySocket(async (msg) => {
        if (msg?.event === 'update_topology') {
          legend.textContent = 'Updating topology...';
          const newTopo = await fetchTopology();
          // Naive refresh: rebuild elements (fine for now)
          cy.elements().remove();
          cy.add({
            nodes: newTopo.nodes.map(n => ({
              data: { id: String(n.id), label: n.label || n.ip, vendor: n.vendor || 'unknown', ip: n.ip, icon: ICONS[vendorKey(n.vendor)] }
            })),
            edges: newTopo.edges.map(e => ({
              data: { source: String(e.source), target: String(e.target), label: e.local_if || e.remote_port || '' }
            }))
          });
          applySavedPositions(cy, await fetchLayout());
          legend.textContent = 'Topology updated';
        }
      });
    })().catch(err => {
      const legend = document.getElementById('legend');
      if (legend) legend.textContent = 'Failed to load: ' + err.message;
    });

    return container;
  }

  window.buildTopologyView = buildTopologyView;
})();
