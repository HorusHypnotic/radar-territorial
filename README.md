# OPERA Territorial — Radar de Geointeligência

> **Site demonstrativo:** [horushypnotic.github.io/radar-territorial](https://horushypnotic.github.io/radar-territorial/)

[![Deploy GitHub Pages](https://github.com/HorusHypnotic/radar-territorial/actions/workflows/deploy-pages.yml/badge.svg)](https://github.com/HorusHypnotic/radar-territorial/actions/workflows/deploy-pages.yml)
[![Testes](https://github.com/HorusHypnotic/radar-territorial/actions/workflows/pipeline-test.yml/badge.svg)](https://github.com/HorusHypnotic/radar-territorial/actions/workflows/pipeline-test.yml)

Camada de inteligência territorial para consultar regras urbanísticas, acompanhar obras e preservar memória operacional verificável. A instância pública usa dados demonstrativos; não representa o zoneamento legal de Redenção.

## Recursos principais

- dashboard executivo com métricas calculadas a partir da base carregada;
- mapa interativo Leaflet, com fallback SVG para telas menores;
- KPIs, gráficos Canvas, tabela pesquisável e exportação CSV;
- importação CSV com validação e prévia;
- PWA instalável, dependências locais e cache offline versionado;
- livro-razão JSON encadeado por SHA-256 e exportável;
- conversão conservadora de shapefile/QGIS para GeoJSON em EPSG:4326;
- gerador determinístico de dados sintéticos para testes;
- suíte automatizada e validação dos artefatos publicados.

## Stack

Python 3.11+, Supabase/PostgreSQL preparado, HTML/CSS/JavaScript nativos, Leaflet local e GitHub Pages.

## Instalação

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Preencha `.env` somente no ambiente local. Nunca coloque `SUPABASE_SERVICE_KEY` no frontend ou no Git.

Para o fluxo QGIS, instale também:

```powershell
pip install -r requirements-qgis.txt
```

## Execução local

```powershell
python python/pipeline.py
python server.py
```

Abra `http://127.0.0.1:8001`. Para servir apenas os arquivos estáticos, execute `python -m http.server 8080` na raiz.

## Estrutura

```text
frontend/          Interface PWA, módulos JavaScript e Leaflet local
python/            Pipeline, indicadores, modelos, auditoria e snapshots
scripts/           QGIS, dados sintéticos, validação e utilitários operacionais
data/output/       Contrato JSON/GeoJSON demonstrativo consumido pelo site
data/schemas/      JSON Schemas e migrations Supabase 000–007
docs/              Arquitetura, operação, produção e fluxos especializados
tests/             Testes automatizados
.github/workflows/ Testes, deploy do Pages e keep-alive preparado
```

## Testes e validação

```powershell
python -m pytest -q
python scripts/validate_deploy.py
python scripts/validate_production.py
```

`validate_production.py` verifica os recursos estáticos publicados. Ele não comprova, sozinho, Supabase, RLS, backend hospedado ou persistência real.

## Dados sintéticos

Para testar os contratos sem dados oficiais:

```powershell
python scripts/generate_test_data.py --zones 9 --obras 20 --fornecedores 10 --seed 42 --output data/test
python scripts/export_qgis_to_opera.py --validate data/test
```

O pacote é marcado como candidato e sintético. O gerador bloqueia gravação direta em `data/output` e `frontend/data`. Consulte [Dados sintéticos](docs/DADOS_SINTETICOS.md).

## Importação QGIS

Gere primeiro um candidato, usando o mapeamento revisado dos campos reais:

```powershell
python scripts/export_qgis_to_opera.py `
  --shapefile "C:\dados\zoneamento.shp" `
  --field-map config\qgis-field-map.example.json `
  --expected-bounds -52 -10 -48 -6 `
  --output data\candidate

python scripts/export_qgis_to_opera.py --validate data\candidate
```

A publicação exige nova conversão da fonte autorizada, autoridade verdadeira, referência legal e `--replace`. O roteiro completo e suas barreiras estão em [Importação segura do QGIS](docs/IMPORTACAO_QGIS.md).

## Produção e limites

O GitHub Pages publica a branch `master` ou `main`. O Supabase, o bucket privado, RLS, timestamp externo, assinatura e backend remoto estão preparados no código, mas não devem ser considerados ativos sem verificação específica.

- [Estado real de produção](docs/PRODUCAO_REAL.md)
- [Status dos recursos publicados](docs/STATUS_PRODUCAO.md)
- [Deploy](docs/DEPLOY.md)
- [Preservação verificável](docs/FASE4_PRESERVACAO.md)
- [APMO e GAPs](APMO-OPERA-v1.md)
- [Escopo territorial](OPERA_TERRITORIAL_ESCOPO.md)

## Licença

Nenhuma licença foi definida. Até sua inclusão, todos os direitos permanecem reservados aos autores.
