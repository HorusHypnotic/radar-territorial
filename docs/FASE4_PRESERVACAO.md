# Fase 4 — Preservação verificável

## Entregue no código

- evidências com SHA-256, tamanho, MIME, GPS e metadados;
- bucket privado `evidencias` preparado pela migration `007`;
- campos estruturados para provas RFC 3161, OpenTimestamps e assinatura digital;
- registro de verificações append-only;
- verificação consolidada de auditoria, versões, snapshots e metadados de evidência;
- livro-razão JSON encadeado e exportável;
- PWA instalável com shell e dados demonstrativos essenciais em cache.

## Limites de confiança

Um hash SHA-256 local detecta alterações quando comparado com um valor confiável anterior. Ele não prova sozinho autoria nem data de existência. Os campos de timestamp e assinatura permanecem nulos até uma autoridade externa emitir uma prova válida; a aplicação não fabrica esses estados.

A verificação de evidências no PostgreSQL cobre metadados e formato do digest. A validação completa requer que o backend baixe o objeto privado, recalcule o SHA-256 dos bytes e compare com `hash_sha256`.

## Ativação

1. Execute `data/schemas/opera_full_migration.sql` no SQL Editor do projeto correto.
2. Configure uma `SUPABASE_SERVICE_KEY` somente no backend.
3. Execute `python scripts/export_ledger.py` para regenerar a exportação estática demonstrativa.
4. Rode `python -m pytest -q` e `python scripts/validate_deploy.py`.
5. Valide instalação e modo offline no navegador.

RFC 3161/OpenTimestamps e assinatura por identidade institucional exigem escolha de provedor, política de chaves e procedimento de renovação/revogação; não são ativados automaticamente pela migration.
