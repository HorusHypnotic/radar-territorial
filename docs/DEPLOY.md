# Deploy

O workflow `deploy-pages.yml` publica o repositório como artefato estático no GitHub Pages. Configure a origem do Pages como **GitHub Actions** e faça push para `master` ou `main`.

O arquivo raiz `index.html` redireciona para `frontend/`. O build não depende de CDN; Leaflet é mantido em `frontend/vendor/leaflet/`.

## Snapshot diário

Agende o job diretamente no host do backend, sem expor chave de serviço ou endpoint administrativo:

```cron
59 23 * * * cd /caminho/radar-territorial && .venv/bin/python -m python.modules.eov_job
```

No Windows, crie uma tarefa no Agendador executando `.venv\Scripts\python.exe -m python.modules.eov_job` às 23:59.

## Validação integrada

Antes do merge, execute `python scripts/validate_deploy.py`. O comando monta `_site`, confirma os assets obrigatórios, valida o GeoJSON e rejeita dependências externas ou arquivos privados. Em Linux/macOS, `scripts/deploy-fase3.sh` executa testes e essa validação em sequência.

Depois do deploy, execute `python scripts/validate_production.py`. O comando consulta o endereço público e falha se um asset essencial, marcador da interface ou GeoJSON válido não estiver disponível. Use `--json` para obter uma saída adequada a automações.

## Conexão Supabase

Copie `.env.example` para `.env.local`, preencha as credenciais reais e execute `python scripts/check_supabase.py`. O verificador faz somente uma consulta de leitura e nunca imprime a chave. Arquivos `.env.local`, `.env.codex` e `.env.production` são ignorados pelo Git.

As migrations devem ser aplicadas, em ordem, pelo SQL Editor do Supabase ou por uma conexão PostgreSQL administrativa controlada. O projeto não cria uma função RPC genérica `exec_sql`, pois isso ampliaria desnecessariamente a superfície privilegiada. A migration `000_core_schema.sql` cria os pré-requisitos; as migrations `001`–`005` adicionam auditoria, versionamento, snapshots e APMO.

Para gerar um único arquivo pronto para o SQL Editor, execute `python scripts/build_migration_bundle.py --output opera_full_migration.sql`. Revise o arquivo gerado e execute-o no projeto correto. Todo o lote roda em uma transação: um erro provoca rollback, evitando schema parcialmente aplicado.

## Atividade do projeto Free

O workflow `supabase-keep-alive.yml` chama diariamente a função somente leitura `opera_keep_alive`, criada pela migration `006`. Configure `SUPABASE_URL` e `SUPABASE_ANON_KEY` como GitHub Actions secrets. A função não insere eventos artificiais no log de auditoria.

Isso reduz o risco de pausa por baixa atividade, mas não constitui garantia de disponibilidade. Segundo o Supabase, projetos Free com baixa atividade por sete dias podem ser pausados e algumas consultas de usuário por dia normalmente são suficientes; a única prevenção garantida é um plano pago. Além disso, o GitHub pode desativar workflows agendados de repositórios públicos após 60 dias sem atividade no próprio repositório. Monitore falhas do workflow e os avisos enviados pelo Supabase.

O utilitário `scripts/extract_polygons.py` aceita SVG/HTML com elementos `polygon`. Por segurança cartográfica, o CRS padrão é `LOCAL:SVG`; um EPSG só pode ser informado junto de uma transformação explícita. Pixels de um desenho nunca são tratados como coordenadas UTM automaticamente.
