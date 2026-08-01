# Roteiro para produção real

Estado consolidado em **01/08/2026**, após o commit `b13ca1c`.

## Disponível no GitHub Pages

- frontend responsivo e PWA instalável;
- mapa, KPIs, gráficos e tabela alimentados por dados demonstrativos;
- leitura, validação e pré-visualização local de CSV;
- auditoria e snapshots estáticos sanitizados;
- livro-razão demonstrativo encadeado por SHA-256;
- fallback que valida os contratos de dashboard e GeoJSON;
- 48 testes automatizados aprovados;
- 11 recursos essenciais validados com HTTP 200.

O GitHub Pages é estático. Ele não executa `server.py`, não persiste uploads e não acessa a chave administrativa do Supabase.

## Preparado no código, ainda não ativado remotamente

- migrations `000`–`007`;
- 17 tabelas operacionais e de controle;
- bucket privado `evidencias`, criado pela migration `007`;
- RLS habilitada com acesso privilegiado reservado a `service_role`;
- upload de evidências para Storage com SHA-256 e rollback;
- verificação consolidada e append-only;
- campos para provas RFC 3161, OpenTimestamps e assinatura digital.

Os campos de prova externa e assinatura permanecem nulos até a integração com uma autoridade e uma identidade institucional. Um hash local não comprova sozinho autoria ou existência em determinada data.

## Bloqueios para uso operacional

1. Aplicar `data/schemas/opera_full_migration.sql` no projeto Supabase correto.
2. Confirmar as 17 tabelas, funções, triggers e o bucket privado.
3. Definir papéis de usuário e políticas RLS antes de liberar clientes autenticados.
4. Disponibilizar `SUPABASE_SERVICE_KEY` somente no ambiente do backend.
5. Hospedar `server.py` atrás de HTTPS, proxy e política CORS explícita.
6. Configurar o frontend para a URL pública desse backend.
7. Obter e validar o GeoJSON oficial em EPSG:4326.
8. Importar somente dados aprovados, com origem e responsáveis documentados.
9. Executar testes integrados, recuperação de backup e revisão de segurança.

## Validação reproduzível disponível hoje

```powershell
python -m pytest -q
python scripts/validate_deploy.py
python scripts/validate_production.py
python scripts/check_supabase.py
python scripts/export_ledger.py
```

`check_supabase.py` exige uma credencial válida e faz consulta somente leitura. `validate_production.py` valida o GitHub Pages; ele não possui opções `--full` ou `--supabase`.

## Aplicação do schema

1. Abra o SQL Editor do projeto `mxcforphamhupizoztsk`.
2. Revise e execute `data/schemas/opera_full_migration.sql` em uma nova consulta.
3. Em caso de erro, não fragmente o lote: o arquivo usa uma transação e deve fazer rollback.
4. Execute `python scripts/check_supabase.py` depois da conclusão.
5. Inspecione RLS e privilégios antes de carregar qualquer dado real.

Não crie manualmente um segundo bucket `evidencias`: a migration `007` já o cria ou atualiza de modo idempotente.

## Dados oficiais

O repositório ainda não contém um carregador denominado `load_official_data.py`, nem um arquivo cartográfico oficial autorizado. A entrada de dados reais requer primeiro um contrato de importação, validação geométrica, identificação da fonte legal e aceite do responsável pelo Plano Diretor. Os polígonos atuais não devem orientar decisões urbanísticas.

## Critério de conclusão

O sistema só deve ser declarado operacional com dados reais quando banco migrado, backend público, autenticação/RLS, Storage privado, dados oficiais e recuperação de backup tiverem sido testados em conjunto. Timestamp externo e assinatura digital são controles adicionais e não devem ser declarados ativos antes da emissão e verificação de provas reais.
