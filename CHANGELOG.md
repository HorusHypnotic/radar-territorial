# Changelog

## [Unreleased]

- Estrutura modular inicial do frontend.
- Base documental de arquitetura, API, schema, APMO e deploy.
- Migration inicial da trilha de auditoria.
- Publicação pelo fluxo oficial do GitHub Pages.
- Mapa poligonal Leaflet com fallback SVG, seleção de zonas, filtros e busca.
- KPIs territoriais, ICO e quatro gráficos Canvas nativos.
- Tabela paginada, ordenável, filtrável e exportável em CSV.
- Importação CSV com validação, prévia e persistência em staging com SHA-256.
- Painéis locais de auditoria, snapshots, integridade e comparação.
- APIs de zonas, KPIs, ICO, auditoria, snapshots, integridade e importação.
- Migrations de auditoria automática, versões append-only e snapshots EOV.
- Concorrência otimista por `expected_version` e vínculo opcional a `import_jobs`.
- Hash chain Python determinística para arquivos e evidências.
- Job de backend para geração diária de EOV sem chamada HTTP privilegiada.
- Migration 005 com nove entidades operacionais APMO, índices, RLS e auditoria.
- Modelos validados de atividade, ICO, evidência e ECO.
- APIs de atividades, ICO, ECOs e evidências com retificação versionada.
- Tema escuro aprimorado, conformidade visual e fallback de dados embutido.
- Mapa híbrido: Leaflet em telas amplas e SVG com pan/zoom em dispositivos móveis.
- Cache offline versionado e validação automatizada do artefato público.
- Extrator SVG seguro, sem atribuição fictícia de CRS geográfico.
