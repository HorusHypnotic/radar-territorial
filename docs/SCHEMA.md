# Schema de dados

Schemas JSON ficam em `data/schemas/` e migrations Supabase em `data/schemas/migrations/`. A migration `001_audit_log.sql` cria a trilha universal, sua função de trigger e a política restritiva inicial.

Os triggers são declarados como comandos comentados para que a migration possa ser instalada antes de `zonas`, `obras` e `fornecedores` existirem. Ative-os após validar as tabelas alvo.

## Ordem da Fase 2

Execute `001_audit_log.sql`, `002_audit_trigger.sql`, `003_versioning.sql` e `004_snapshot_eov.sql`, nessa ordem, pelo SQL Editor do Supabase ou `psql`. As migrations 002–004 detectam tabelas opcionais; rode-as novamente depois de criar novas entidades para instalar colunas e triggers nelas.

Faça primeiro backup do schema e teste em um projeto Supabase de homologação. As funções administrativas concedem execução ao papel `service_role`; essa chave nunca deve sair do backend.

## Fase 3

`005_entidades_apmo.sql` cria atividades, cronograma, ICO, evidências, ECOs, materiais, equipes, ocorrências e checklists. Todas têm RLS restritiva e trigger `opera_audit_row`; acesso direto é reservado ao `service_role`.

Atividades, cronograma, ECOs, materiais, equipes e ocorrências participam da retificação genérica append-only. ICO, evidências e checklists são registros probatórios: não são aceitos pela função genérica `retify_entity`; correções futuras deverão criar novo registro ou usar um fluxo específico de aprovação, preservando o original.
