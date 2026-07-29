// OPERA Territorial v2.0 — Dados e API
// Carrega dados reais de /api/audit, /api/snapshots, /api/integrity

const TERRITORIAL_API = {
  async fetchAudit() {
    try {
      const res = await fetch('/api/audit');
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return await res.json();
    } catch (e) {
      console.warn('API audit indisponível:', e.message);
      return { hash_chain: [], events: [] };
    }
  },

  async fetchSnapshots() {
    try {
      const res = await fetch('/api/snapshots');
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return await res.json();
    } catch (e) {
      console.warn('API snapshots indisponível:', e.message);
      return { snapshots: [] };
    }
  },

  async fetchIntegrity() {
    try {
      const res = await fetch('/api/integrity');
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return await res.json();
    } catch (e) {
      console.warn('API integrity indisponível:', e.message);
      return { checks: [] };
    }
  },

  async fetchDashboard() {
    try {
      const res = await fetch('/api/dashboard');
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return await res.json();
    } catch (e) {
      console.warn('API dashboard indisponível:', e.message);
      return null;
    }
  }
};

// Dados mock para modo offline (quando server.py não está rodando)
const MOCK_DATA = {
  kpis: {
    setores: 4,
    obras: 12,
    fornecedores: 8,
    demandas: 22,
    zum: 1,
    zeis: 1,
    creche_cobertura: '25%',
    saude_cobertura: '50%'
  },
  setores: [
    { zona: 'ZUM-1', zona_nome: 'Zona de Uso Misto', to: 2.5, ca: 3.0, ico: 82, creche: 'Alta', saude: 'Media' },
    { zona: 'ZEIS-1', zona_nome: 'Zona Especial de Interesse Social', to: 4.0, ca: 2.0, ico: 91, creche: 'Prioritario', saude: 'Prioritario' },
    { zona: 'ZCOR-1', zona_nome: 'Zona de Corredor', to: 3.0, ca: 4.0, ico: 67, creche: 'Baixa', saude: 'Media' },
    { zona: 'ZUP-1', zona_nome: 'Zona de Uso Predominantemente Industrial', to: 2.0, ca: 1.5, ico: 54, creche: 'Baixa', saude: 'Baixa' }
  ],
  hash_chain: [
    { timestamp: '2026-09-03T10:00:00Z', hash: '0x8a7f3c9d1e2b4a5f6c7d8e9f0a1b2c3d', parent: '0x0000...' },
    { timestamp: '2026-09-03T11:30:00Z', hash: '0x1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e', parent: '0x8a7f3c9d...' }
  ],
  ipmo_global: 8.5
};
