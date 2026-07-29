// OPERA Territorial v2.0 — App Logic

document.addEventListener('DOMContentLoaded', () => {
  initKPIs();
  initTabela();
  initMapa();
  initAPMO();
  initChart();
});

// ---- KPIS ----
function initKPIs() {
  const k = MOCK_DATA.kpis;
  const el = document.getElementById('kpisContainer');
  if (!el) return;
  el.innerHTML = `
    <div class="kpi"><small>Setores</small><strong>${k.setores}</strong></div>
    <div class="kpi"><small>Obras</small><strong>${k.obras}</strong></div>
    <div class="kpi"><small>Fornecedores</small><strong>${k.fornecedores}</strong></div>
    <div class="kpi"><small>Demandas</small><strong>${k.demandas}</strong></div>
    <div class="kpi"><small>ZUM</small><strong>${k.zum}</strong></div>
    <div class="kpi"><small>ZEIS</small><strong>${k.zeis}</strong></div>
    <div class="kpi"><small>Creche</small><strong>${k.creche_cobertura}</strong></div>
    <div class="kpi"><small>Saúde</small><strong>${k.saude_cobertura}</strong></div>
  `;
}

// ---- TABELA ----
function initTabela() {
  const busca = document.getElementById('buscaZona');
  if (busca) {
    busca.addEventListener('input', (e) => renderTabela(e.target.value));
  }
  renderTabela('');
}

function renderTabela(filtro = '') {
  const rows = MOCK_DATA.setores.filter(s =>
    s.zona.toLowerCase().includes(filtro.toLowerCase()) ||
    s.zona_nome.toLowerCase().includes(filtro.toLowerCase())
  );
  const body = document.getElementById('tabelaBody');
  if (!body) return;
  body.innerHTML = rows.map(s => {
    const color = s.ico > 80 ? '#4ade80' : s.ico > 60 ? '#facc15' : '#f87171';
    return `<tr>
      <td><b>${s.zona}</b><br><span style="font-size:10px;color:#9bb1cc">${s.zona_nome}</span></td>
      <td>${s.to}</td>
      <td>${s.ca}</td>
      <td style="color:${color};font-weight:700">${s.ico}%</td>
    </tr>`;
  }).join('');
}

// ---- MAPA ----
function initMapa() {
  const polygons = document.querySelectorAll('.zone-polygon');
  polygons.forEach(p => {
    p.addEventListener('click', (e) => showZoneTooltip(e, p.dataset.zona));
    p.addEventListener('mouseenter', () => {
      p.style.fill = '#F5B041';
      p.style.opacity = '0.7';
    });
    p.addEventListener('mouseleave', () => {
      p.style.fill = '';
      p.style.opacity = '';
    });
  });
}

function showZoneTooltip(e, zonaNome) {
  const found = MOCK_DATA.setores.find(s => s.zona === zonaNome);
  if (!found) return;
  // Remove tooltip anterior
  const old = document.querySelector('.zone-tooltip');
  if (old) old.remove();

  const tooltip = document.createElement('div');
  tooltip.className = 'zone-tooltip visible';
  tooltip.style.left = (e.clientX + 10) + 'px';
  tooltip.style.top = (e.clientY + 10) + 'px';
  tooltip.innerHTML = `
    <div class="tt-title">${found.zona} — ${found.zona_nome}</div>
    <div class="tt-row">TO: ${found.to} | CA: ${found.ca}</div>
    <div class="tt-row">ICO: <b style="color:#F5B041">${found.ico}%</b></div>
    <div class="tt-row">Creche: ${found.creche} | Saúde: ${found.saude}</div>
  `;
  document.body.appendChild(tooltip);
  setTimeout(() => tooltip.remove(), 5000);
}

// ---- APMO ----
function initAPMO() {
  // Hash chain mock
  const lastHash = MOCK_DATA.hash_chain[MOCK_DATA.hash_chain.length - 1];
  const hashEl = document.getElementById('hashDisplay');
  if (hashEl) hashEl.textContent = lastHash ? lastHash.hash : 'Nenhum hash registrado';

  const snapEl = document.getElementById('snapshotDisplay');
  if (snapEl) snapEl.textContent = MOCK_DATA.hash_chain.length + ' snapshot(s)';

  const ipmoEl = document.getElementById('ipmoDisplay');
  if (ipmoEl) ipmoEl.textContent = MOCK_DATA.ipmo_global + '/10';

  // Botões
  const btnAudit = document.getElementById('btnAudit');
  if (btnAudit) btnAudit.addEventListener('click', showAuditModal);

  const btnSnap = document.getElementById('btnSnapshots');
  if (btnSnap) btnSnap.addEventListener('click', showSnapshotsModal);

  const btnIntegrity = document.getElementById('btnIntegrity');
  if (btnIntegrity) btnIntegrity.addEventListener('click', showIntegrityModal);
}

function showAuditModal() {
  const events = MOCK_DATA.hash_chain.map(h =>
    `${h.timestamp} → ${h.hash.substring(0, 16)}...`
  ).join('\n');
  alert('📋 Audit Log:\n\n' + (events || 'Nenhum evento registrado.') +
    '\n\n(Em produção, isso será carregado via /api/audit)');
}

function showSnapshotsModal() {
  alert('📸 Snapshots:\n\n' + MOCK_DATA.hash_chain.map(h => h.timestamp).join('\n') +
    '\n\n(Em produção, isso será carregado via /api/snapshots)');
}

function showIntegrityModal() {
  alert('🔐 Integridade:\n\nTodos os hashes verificados com sucesso.\nNenhuma adulteração detectada.\n\n' +
    '(Em produção, isso será verificado via /api/integrity)');
}

// ---- CHART ----
function initChart() {
  renderICOChart(MOCK_DATA.setores);
}

// ---- TENTATIVA DE CARREGAR DADOS REAIS ----
async function tryLoadRealData() {
  try {
    const data = await TERRITORIAL_API.fetchDashboard();
    if (data && data.kpis) {
      // Atualizar KPIS com dados reais
      const k = data.kpis;
      const el = document.getElementById('kpisContainer');
      if (el) {
        el.innerHTML = Object.entries(k).map(([key, val]) =>
          `<div class="kpi"><small>${key}</small><strong>${val}</strong></div>`
        ).join('');
      }
    }
  } catch (e) {
    console.log('Modo offline: usando dados mock.');
  }
}

// Tenta carregar dados reais após 1s
setTimeout(tryLoadRealData, 1000);
