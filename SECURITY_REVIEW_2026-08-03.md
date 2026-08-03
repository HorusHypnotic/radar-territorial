# Revisão de segurança — Radar Urbano Operador

Data: 3 de agosto de 2026

## Escopo

Preparação do repositório Lovable `HorusHypnotic/radarurbanooperador` para preservação e futura integração seletiva com `HorusHypnotic/radar-territorial`.

## Ambiente

O repositório continha `.env` versionado com identificadores, URLs e chaves publicáveis do Supabase. Nesta revisão:

- `.env` foi removido da versão atual;
- `.env` e variantes foram adicionados ao `.gitignore`;
- `.env.example` foi criado somente com nomes e valores vazios;
- nenhum valor foi reproduzido neste relatório.

O arquivo permanece nos commits históricos. A rotação das chaves deve ser avaliada separadamente; nenhuma rotação foi executada.

## Limites da futura fusão

O schema deste projeto não substitui automaticamente o schema do Radar Territorial oficial. A aplicação Lovable usa entidades como `urban_events`, `urban_entities`, `neighborhoods`, `data_sources`, `user_roles` e `governance_logs`; o Radar oficial possui contratos próprios para zonas, obras, ECO/ICO, snapshots, integridade, GIS e QGIS.

A integração deve preservar os dois modelos até que adaptadores, autoridade de dados e migrações sejam aprovados explicitamente.

## Pendências

- [x] `npm ci` aprovado.
- [x] Build de produção aprovado.
- [ ] Lint reprovado: 8.618 erros de formatação Prettier, todos corrigíveis automaticamente, e 6 avisos de Fast Refresh.
- [ ] Revisar 12 vulnerabilidades transitivas: 10 altas e 2 baixas; nenhuma crítica.
- [ ] Avaliar rotação das chaves Supabase.
- [ ] Preservar este histórico como branch `lovable-source` no Radar oficial.
- [ ] Importar a aplicação em `apps/web/` sem sobrescrever o frontend estático existente.
