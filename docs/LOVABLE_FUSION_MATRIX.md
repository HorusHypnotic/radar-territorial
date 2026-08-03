# Matriz de fusão — Radar Territorial × Radar Urbano Operador

Data: 3 de agosto de 2026

## Fontes preservadas

| Fonte | Branch/HEAD | Histórico | Papel |
|---|---|---:|---|
| `HorusHypnotic/radar-territorial` | `master` / `a005081` | 27 commits antes da integração | Autoridade técnica, GIS, dados, backend, testes e governança |
| Alterações legais locais | `integration/lovable-fusion` / `8a142c5` | 1 commit novo | Ressalva legal obrigatória e teste de regressão |
| `HorusHypnotic/radarurbanooperador` | `main` / `aad0cc5` | 63 commits após saneamento | Aplicação Lovable nativa |
| Histórico Lovable no repositório oficial | `lovable-source` / `aad0cc5` | Histórico completo | Proveniência e recuperação |
| Aplicação importada | `apps/web/` | Subtree squash | Base web candidata para integração |

`master` não foi alterada nesta etapa. A fusão ocorre somente em `integration/lovable-fusion`.

## Componentes

| Componente | Radar oficial | Aplicação Lovable | Decisão atual |
|---|---|---|---|
| Interface | HTML/CSS/JavaScript estático em `frontend/` | TanStack Start/React em `apps/web/` | Manter ambos durante a validação; Lovable é candidato à interface principal |
| Mapa e visualização | Dados GIS/GeoJSON e mapa estático | `TerritorialMap`, feed, scores e alertas | Adaptar a interface Lovable aos dados oficiais; não substituir dados automaticamente |
| Backend | `server.py` e pipeline Python | Server functions TanStack | Manter serviços separados até definir API de integração |
| GIS/QGIS | `python/`, `scripts/`, `requirements-qgis.txt` | Ausente | Preservar integralmente no Radar oficial |
| Dados e manifestos | `data/`, hashes, snapshots e manifestos | Supabase orientado a eventos urbanos | Preservar os dois modelos; criar adaptadores explícitos |
| Autenticação | Não é o foco do frontend estático | Supabase Auth e papéis | Candidato para a camada web, sujeito a revisão de RLS e bootstrap de administrador |
| Ingestão | Pipeline Python e importações GIS | Feed urbano e Diário de Goiânia | Tratar como pipelines complementares com proveniência comum |
| Testes | 73 testes Python após a ressalva legal | Sem script de testes configurado | Python é gate obrigatório; criar testes web antes da promoção |
| Governança | Documentação, validação, integridade e ressalvas | Telemetria e logs Supabase | Integrar sem reduzir os controles existentes |

## Contratos do Radar oficial

### HTTP e arquivos

- `/api/health`
- `/api/data`
- `/api/kpis`
- `/api/zonas` e `/api/zonas/{id}`
- `/api/geojson/zonas`
- `/api/geojson/pontos`
- `/api/audit`
- `/api/snapshots`, `/api/snapshot` e operações de restauração
- `/api/integrity` e `/api/integrity/{obra_id}`
- `/api/ledger`
- endpoints de obras, atividades, ECO, ICO e evidências
- `dashboard_data.json`, `radar_geojson.geojson`, `zonas_poligonos.geojson` e manifestos com hashes

### Supabase

O backend usa credenciais server-side e contratos para zonas, obras, atividades, ECO, ICO, snapshots, versões e integridade. `SUPABASE_SERVICE_KEY` nunca deve ser exposta ao navegador.

## Contratos da aplicação Lovable

### Rotas e funções

- rotas `/`, `/login` e `/operador`;
- endpoint de cron para ingestão do Diário de Goiânia;
- server functions para dashboard, feed, geocodificação, operação, revisão e governança;
- Supabase Auth com papéis e bootstrap administrativo;
- ingestão, normalização e revisão de eventos urbanos.

### Supabase

O schema Lovable inclui:

- `user_roles`;
- `data_sources`;
- `neighborhoods`;
- `urban_entities`;
- `urban_events`;
- `permits`, `licenses` e `technical_records`;
- `territorial_scores`;
- `alert_rules`;
- `governance_logs`;
- `ingestion_runs`.

RLS está habilitado nas tabelas declaradas pelas migrations, mas as políticas e o fluxo de bootstrap devem ser auditados antes de qualquer aplicação em banco compartilhado.

## Incompatibilidades que bloqueiam fusão direta

1. Os schemas Supabase modelam domínios diferentes e não possuem chaves comuns formalizadas.
2. O backend Python usa chave de serviço; a interface web deve usar apenas credenciais públicas e funções server-side protegidas.
3. O frontend Lovable ainda não consome os contratos GIS, GeoJSON, snapshots e integridade do Radar oficial.
4. A aplicação Lovable possui ingestão própria sem manifesto compatível com a cadeia de proveniência Python.
5. Não existem testes automatizados web configurados.
6. A ressalva legal obrigatória do Radar oficial precisa aparecer também na aplicação Lovable.

## Arquitetura de transição

```text
radar-territorial/
├── apps/
│   └── web/                 # aplicação Lovable importada
├── frontend/                # interface estática atual, preservada
├── python/                  # pipeline, GIS, snapshots e integridade
├── scripts/                 # importação, validação e publicação
├── data/                    # fontes, schemas, saídas e manifestos
├── tests/                   # gates Python
├── docs/                    # governança e matriz de integração
└── server.py                # API/servidor atual
```

## Contrato de adaptação proposto

Antes de compartilhar banco ou promover `apps/web/`, criar uma camada de API que exponha ao frontend apenas dados validados:

| Capacidade web | Fonte oficial | Contrato candidato |
|---|---|---|
| Zonas e polígonos | GeoJSON oficial | `GET /api/geojson/zonas` |
| Pontos e oportunidades | Pipeline territorial | `GET /api/geojson/pontos` |
| KPIs | Dashboard validado | `GET /api/kpis` |
| Integridade | Cadeia de hashes | `GET /api/integrity` |
| Proveniência | Manifestos e ledger | `GET /api/ledger` |
| Feed urbano | `urban_events` revisados | Novo contrato versionado após aprovação |
| Operação/revisão | Server functions Lovable | Manter isoladas até auditoria de autorização e RLS |

## Gates para promoção

- [x] Preservar as duas alterações legais e aprovar 73 testes Python.
- [x] Remover `.env` versionado da fonte Lovable e criar exemplo vazio.
- [x] Preservar o histórico Lovable completo em `lovable-source`.
- [x] Importar a aplicação em `apps/web/` sem sobrescrever `frontend/`.
- [x] Revalidar 73 testes Python depois da importação.
- [x] Aprovar `npm ci` e build em `apps/web/`.
- [ ] Tratar ou aceitar formalmente lint, vulnerabilidades e avisos de bundle.
- [ ] Inserir e testar a ressalva legal na aplicação Lovable.
- [ ] Criar testes web para autenticação, mapa, feed e autorização.
- [ ] Definir contratos versionados entre Python/GIS e `apps/web/`.
- [ ] Auditar RLS, bootstrap administrativo e migrations antes de usar banco compartilhado.
- [ ] Confirmar estratégia de deploy e rollback.
- [ ] Revisar a integração antes de abrir PR para `master`.

## Pendências de segurança

- O `.env` removido continua no histórico de `radarurbanooperador`; avaliar rotação das chaves Supabase.
- `npm audit` reportou 12 vulnerabilidades transitivas na fonte Lovable: 10 altas e 2 baixas.
- O lint da fonte reportou 8.618 erros de formatação Prettier e 6 avisos de Fast Refresh.
- Nenhuma correção automática ou reescrita de histórico foi aplicada.

## Validação da árvore integrada

- `python -m pytest`: 73 testes aprovados, com 1 aviso de depreciação externo.
- `npm ci`: 518 pacotes instalados; auditoria manteve 12 vulnerabilidades (10 altas e 2 baixas).
- `npm run build`: cliente e SSR gerados com sucesso.
- Avisos não bloqueantes: Node 22.12.0 abaixo do requisito de uma dependência de lint e chunks acima de 500 kB.
- A promoção continua bloqueada pelos gates funcionais, jurídicos, de segurança e de contratos ainda abertos acima.
