# OPERA Territorial — Radar de Redenção

Dashboard territorial inteligente com polígonos interativos, KPIs dinâmicos e auditoria APMO (Auditoria de Preservação da Memória Operacional).

## Visão

O OPERA Territorial é o módulo de inteligência geoespacial do Ecossistema OPERA. Ele mapeia zonas urbanas, calcula indicadores de coerência operacional (ICO) por zona e mantém uma cadeia de hashes para auditoria completa.

## Stack

- **Frontend:** HTML + CSS + JavaScript vanilla (sem frameworks)
- **Mapa:** SVG nativo (sem CDN) — funciona offline
- **Backend:** Python HTTP Server (stdlib, sem dependências)
- **Dados:** GeoJSON, Parquet, JSON

## Estrutura

```
radar-territorial/
├── frontend/
│   ├── index.html          # Dashboard principal
│   ├── css/style.css       # Estilos
│   └── js/
│       ├── app.js          # Lógica principal
│       ├── chart.js        # Gráficos canvas nativo
│       └── data.js         # Dados e API
├── python/
│   ├── audit.py            # Auditoria
│   ├── snapshots.py        # Snapshots
│   ├── restore.py          # Restauração
│   └── export/
│       └── dashboard_data.py
├── data/
│   ├── output/             # Dados processados
│   ├── snapshots/          # Snapshots parquet
│   └── schemas/
│       └── migrations/     # SQL migrations
├── server.py               # Servidor HTTP com API APMO
└── docs/                   # Documentação
```

## Endpoints API

| Endpoint | Descrição |
|----------|-----------|
| `/` | Dashboard frontend |
| `/api/audit` | Audit log com hash chain |
| `/api/snapshots` | Lista de snapshots |
| `/api/integrity` | Verificação de integridade |
| `/api/ico` | ICO por zona |
| `/api/dashboard` | Dados completos do dashboard |
| `/api/restore?timestamp=X` | Restaurar snapshot |

## Rodar Localmente

```bash
python3 server.py
# Abre em http://127.0.0.1:8001
```

## Deploy

Ative GitHub Pages: Settings > Pages > branch main > / (root)

## APMO — Índice de Preservação da Memória Operacional

| Domínio | Nota (v1.0) | Nota (v2.0 meta) |
|---------|-------------|------------------|
| Integridade | 15 | 80 |
| Temporalidade | 10 | 75 |
| Contexto | 20 | 85 |
| Versionamento | 5 | 70 |
| Cadeia de Custódia | 0 | 90 |
| Auditabilidade | 10 | 85 |
| Reconstrução Histórica | 5 | 75 |

## Repositórios Relacionados

- [opera-atlas](https://github.com/HorusHypnotic/opera-atlas) — Sistema SaaS completo
- [tpc-paper](https://github.com/HorusHypnotic/tpc-paper) — Pré-print da TPC
- [informodinamica-canonical](https://github.com/HorusHypnotic/informodinamica-canonical) — Teoria completa

## Licença

MIT © 2026 Eduardo Martins
