# OPERA Territorial — Radar de Geointeligência

> **Site em produção:** [https://horushypnotic.github.io/radar-territorial/](https://horushypnotic.github.io/radar-territorial/)

[![Deploy GitHub Pages](https://github.com/HorusHypnotic/radar-territorial/actions/workflows/deploy-pages.yml/badge.svg)](https://github.com/HorusHypnotic/radar-territorial/actions/workflows/deploy-pages.yml)

Camada de inteligência territorial para consultar regras do Plano Diretor, acompanhar obras e preservar a memória operacional verificável.

## Stack

Python, Supabase/PostgreSQL, HTML/CSS/JavaScript nativos, Leaflet local e GitHub Pages.

## Pré-requisitos e instalação

- Python 3.11+
- Git

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Preencha o `.env` com as credenciais do seu ambiente. Nunca coloque `SUPABASE_SERVICE_KEY` no frontend ou no Git.

## Rodando localmente

```powershell
python python/pipeline.py
python server.py
```

Abra `http://127.0.0.1:8001`. Para visualizar somente os arquivos estáticos, use `python -m http.server 8080` na raiz e acesse `http://127.0.0.1:8080`.

## Estrutura

- `frontend/`: interface modular e dependências locais
- `python/`: pipeline, indicadores, auditoria e snapshots
- `data/output/`: contrato JSON/GeoJSON consumido pela interface
- `data/schemas/`: JSON Schemas e migrations Supabase
- `docs/`: arquitetura, API, schema e deploy
- `tests/`: testes automatizados

## Pipeline de dados

O pipeline extrai do Supabase, transforma indicadores, grava staging em Parquet, exporta pontos em GeoJSON e cria snapshots com hashes. Execute `pytest` para validar a base.

> **Dados demonstrativos:** os polígonos e registros atualmente incluídos em `data/output/` servem somente para testar a interface. Eles não representam o zoneamento legal de Redenção e devem ser substituídos por uma exportação oficial do Plano Diretor em EPSG:4326 antes de qualquer decisão.

## Deploy

O workflow de GitHub Pages publica o site a cada push em `master` ou `main`. Consulte [`docs/DEPLOY.md`](docs/DEPLOY.md) e o [`estado de produção`](docs/STATUS_PRODUCAO.md), que separa recursos publicados de dependências ainda não ativadas.

## Roadmap

O plano auditável e os GAPs de memória operacional estão em [`APMO-OPERA-v1.md`](APMO-OPERA-v1.md) e [`OPERA_TERRITORIAL_ESCOPO.md`](OPERA_TERRITORIAL_ESCOPO.md).

A implementação e os limites criptográficos da Fase 4 estão documentados em [`docs/FASE4_PRESERVACAO.md`](docs/FASE4_PRESERVACAO.md).

O estado demonstrativo, os bloqueios e o roteiro executável para dados reais estão em [`docs/PRODUCAO_REAL.md`](docs/PRODUCAO_REAL.md).

## Licença

Nenhuma licença foi definida ainda. Até sua inclusão, todos os direitos permanecem reservados aos autores.
