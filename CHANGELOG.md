# Changelog

As mudanças notáveis do projeto são registradas aqui. O repositório ainda não possui versões publicadas por tags; portanto, as entregas permanecem em **Não lançado**.

## Não lançado

### Interface e PWA

- Dashboard executivo com métricas dinâmicas de zonas, obras, conformidade e atualização.
- Mapa Leaflet com fallback SVG, seleção de zonas, filtros, pesquisa, pan e zoom.
- KPIs territoriais, ICO, quatro gráficos Canvas e tabela paginada e exportável.
- Tema escuro responsivo, badges de status e suporte a `prefers-reduced-motion`.
- PWA instalável com manifesto, ícones locais e cache offline `v5`.
- Fallback estático que valida contratos antes de aceitar dados remotos.

### Auditoria e preservação

- Trilha de auditoria, versionamento append-only, snapshots EOV e comparação.
- Hash chain determinística para arquivos e evidências.
- Livro-razão operacional JSON encadeado por SHA-256 e exportável pela interface.
- Schema preparado para timestamp externo, assinatura e bucket privado de evidências.

### Dados e integrações

- Migrations Supabase 000–007 e bundle consolidado, ainda dependentes de aplicação no projeto remoto.
- Entidades e APIs APMO para atividades, ICO, ECOs e evidências.
- Conversor QGIS com validação de CRS, geometria, limites, atributos, manifesto e hashes.
- Gerador determinístico de dados sintéticos, separado dos destinos de produção.
- Importação CSV com validação, prévia e persistência em staging quando o backend está disponível.

### Qualidade e documentação

- Testes automatizados no GitHub Actions e validação do artefato público.
- Deploy automático no GitHub Pages.
- Documentação do estado real, preservação, importação QGIS e dados sintéticos.
- Correção da ordenação de snapshots, do fallback estático e da dependência opcional de Parquet no CI.
