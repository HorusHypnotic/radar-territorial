# RADAR TERRITORIAL — Radar de Geointeligência Urbana

**Site demonstrativo:** [horushypnotic.github.io/radar-territorial](https://horushypnotic.github.io/radar-territorial/)

Camada de inteligência territorial para consultar regras urbanísticas, acompanhar obras e preservar memória operacional verificável. Ferramenta de engenharia e análise de dados urbanos construída por um engenheiro de software com vivência de canteiro — não é um produto comercial e não representa aconselhamento jurídico-urbanístico.

## O que este projeto é (e o que não é)

Este repositório demonstra um pipeline de geointeligência completo: extração e normalização de dados urbanísticos oficiais, modelagem dimensional (dim/fato), visualização em dashboard e mapa, e auditoria de dados via livro-razão encadeado por SHA-256. **Não é um software de produção para consultas legais de zoneamento.** A instância pública usa dados demonstrativos e não representa o zoneamento legal de Redenção (PA) nem de qualquer outro município.

## Fonte dos dados

| Camada | Origem | Status |
|---|---|---|
| Zoneamento | Lei Complementar 128/2022 (Redenção-PA), digitalizada a partir dos polígonos do Plano Diretor (376 vértices convertidos para GeoJSON EPSG:4326) | Base legal real; instância pública usa dados demonstrativos |
| Atividades econômicas | 297 atividades CNAE do Anexo VI | Classificação nacional oficial |
| Dados de obras/fornecedores | Gerados por gerador determinístico de dados sintéticos | Não são dados reais |

## Recursos principais

Dashboard executivo com métricas calculadas a partir da base carregada; mapa interativo (Leaflet, com fallback SVG); KPIs, gráficos Canvas, tabela pesquisável e exportação CSV; importação CSV com validação e prévia; PWA instalável com cache offline versionado; livro-razão JSON encadeado por SHA-256 exportável; conversão conservadora de shapefile/QGIS para GeoJSON em EPSG:4326; gerador determinístico de dados sintéticos para testes.

## Stack e testes

Python 3.11+, Supabase/PostgreSQL preparado, HTML/CSS/JavaScript nativos, Leaflet local e GitHub Pages. A suíte de testes (`pytest`) e os workflows de CI (`pipeline-test.yml`, `deploy-pages.yml`, `supabase-keep-alive.yml`) são executados automaticamente a cada push; os badges acima refletem o estado atual.

## Instalação e execução local

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

O backend Supabase/PostgreSQL está preparado, porém o ambiente público usa dados estáticos; para rodar com o backend é necessária uma instância Supabase local (ver `docs/` para instruções de preparação).

## Limitações

A instância pública não usa o banco de dados em tempo real (dados estáticos gerados pelo pipeline); o schema Supabase v3.0 com Flask API e pipeline ETL está aberto como issue (#2) e não faz parte da versão publicada; o livro-razão audita os artefatos gerados, não substitui verificação legal; e o Supabase de produção do repositório não foi verificado para operação contínua.

## Status

Demo pública ativa via GitHub Pages. Pipeline de dados e testes em funcionamento. Backend v3.0 em planejamento (issues #1 e #2). Sem licença definida — todos os direitos reservados; a reprodução dos textos legais citados é de responsabilidade de quem os consultar na fonte oficial.

## Colaboração

Repositório com contribuições de Dirceu Santos e Eduardo Martins.
