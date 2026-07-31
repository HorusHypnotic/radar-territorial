# API local

Base padrão: `http://127.0.0.1:8001`.

| Método | Rota | Finalidade |
|---|---|---|
| GET | `/api/health` | Saúde e versão do serviço |
| GET | `/api/data` | Dados consolidados do dashboard |
| GET | `/api/geojson/zonas` | Polígonos territoriais |
| GET | `/api/geojson/pontos` | Pontos operacionais |
| GET | `/api/kpis` | Oito KPIs territoriais e ICO médio |
| GET | `/api/zonas` | Lista zonas normalizadas |
| GET | `/api/zonas/{id}` | Detalhes de uma zona |
| GET | `/api/audit?limit=&offset=` | Auditoria paginada |
| GET | `/api/snapshots` | Metadados dos snapshots |
| GET | `/api/snapshot?timestamp=` | Metadados de um snapshot |
| GET | `/api/integrity` | Situação dos hashes de snapshots |
| GET | `/api/integrity/{obra_id}` | Verificação autoritativa das três cadeias no Supabase |
| GET | `/api/ico?obra_id=` | ICO geral ou por obra |
| POST | `/api/import` | Valida e grava lote JSON em staging |
| POST | `/api/restore?timestamp=...` | Restauração controlada de snapshot |
| POST | `/api/retify/{tipo}/{id}` | Retificação versionada com motivo e versão esperada |
| POST | `/api/generate-snapshot/{obra_id}` | Gera EOV de uma obra |
| POST | `/api/snapshot/generate-all` | Gera EOV das obras ativas |
| POST | `/api/snapshot/restore` | Restaura por retificação, preservando a história |

`/api/import` aceita até 5 MB e 10.000 objetos. A resposta contém o SHA-256 do lote persistido. `/api/restore` exige timestamp no formato `YYYYMMDD_HHMMSS`.

A retificação exige `updates`, `reason` com pelo menos 20 caracteres e `expected_version` positivo. Conflitos de versão são rejeitados no PostgreSQL. As rotas Supabase exigem `SUPABASE_URL` e `SUPABASE_SERVICE_KEY` somente no processo backend.
