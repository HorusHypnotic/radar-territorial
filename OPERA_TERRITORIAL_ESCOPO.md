# OPERA Territorial — Escopo, Contexto e Conceito
## Documento de Referência para Desenvolvimento no VS Code

**Versão**: 2.0  
**Base**: `HorusHypnotic/radar-territorial` — auditado em 29/07/2026  
**Referência técnica**: APMO-OPERA-v1.md (IPMO atual: 8,5/100)  
**Stack confirmada**: Python + Supabase + HTML/CSS/JS + Leaflet + GitHub Pages  

---

## 1. O QUE EXISTE HOJE (estado real do repo)

### Estrutura de pastas

```
radar-territorial/
├── .github/workflows/     # CI/CD (GitHub Actions) — existe mas não auditado
├── .vscode/               # Configurações do editor
├── config/                # Parâmetros e logs
├── data/                  # dados brutos, staging, saída
│   └── output/
│       ├── dashboard_data.json    # alimenta o index.html
│       └── radar_geojson.geojson  # pontos no mapa Leaflet
├── docs/                  # documentação (vazia ou incipiente)
├── python/                # pipeline de ingestão/processamento
│   └── pipeline.py        # ponto de entrada
├── tests/                 # testes automatizados
├── .env.example
├── .gitignore
├── APMO-OPERA-v1.md       # auditoria de memória operacional — documento âncora
├── README.md              # mínimo (526 bytes)
├── index.html             # frontend atual — Leaflet + JS vanilla
├── requirements.txt
└── server.py              # servidor local (porta 8001)
```

### O que o `index.html` atual faz

- Leaflet com `setView([-8.0, -50.0], 6)` — zoom 6, região do Pará
- Lê `data/output/dashboard_data.json` via `fetch()`
- Renderiza pontos `circleMarker` coloridos por categoria (Alto/Médio/Baixo)
- Painéis laterais: Resumo, Regiões, Auditoria, Snapshots, Comparação, Integridade, Contexto Semântico
- Botão "Restaurar snapshot" chama `http://127.0.0.1:8001/api/restore`
- **Problema crítico**: depende de Leaflet via CDN (`unpkg.com`) — falha offline e no iframe do Claude

### O que o `server.py` faz (estimado)

- Serve `data/output/` via HTTP
- Endpoint `/api/restore?timestamp=` para restaurar snapshots
- Porta 8001

### O que o pipeline Python faz (estimado)

- Ingestão de dados brutos → staging → output
- Gera `dashboard_data.json` e `radar_geojson.geojson`
- Calcula indicadores de prioridade por zona

---

## 2. O QUE ESTÁ FALTANDO (gaps confirmados)

### 2.1 Gaps críticos no banco (APMO GAP-01 a GAP-10)

| Gap | Descrição | Prioridade |
|-----|-----------|-----------|
| GAP-01 | Trilha de auditoria `audit_log` com hash encadeado | CRÍTICA |
| GAP-02 | Versionamento `*_versions` — upsert atual sobrescreve tudo | CRÍTICA |
| GAP-03 | Storage de evidências (fotos, PDFs, checklists) — bucket zero | ALTA |
| GAP-04 | Snapshot operacional diário (EOV) | ALTA |
| GAP-05 | Retificação com motivo obrigatório e preservação | ALTA |
| GAP-06 | Preservação semântica (ontologia, responsável, motivo) | MÉDIA |
| GAP-07 | Controle de concorrência otimista (`version int`) | MÉDIA |
| GAP-08 | Vínculo `import_jobs → linha inserida` | MÉDIA |
| GAP-09 | Timestamp confiável RFC 3161 / OpenTimestamps | BAIXA |
| GAP-10 | Modo offline / PWA para campo | BAIXA agora |

### 2.2 Gaps no frontend (`index.html`)

| Item | Estado atual | O que precisa |
|------|-------------|---------------|
| Mapa | Leaflet via CDN — quebra offline | SVG próprio ou Leaflet bundled |
| Zoneamento | Pontos simples (circleMarker) | Polígonos de zona com dados normativos |
| Card de zona | Popup básico | Card completo: índices, atividades, viabilidade |
| Filtros | Alto/Médio/Baixo | Por macrozona, por zona, por setor |
| KPIs | 4 cards estáticos | 8+ KPIs dinâmicos calculados do backend |
| Gráficos | Nenhum | Barras, donut, série temporal |
| Tabela | Não existe | Tabela paginada com busca e filtros |
| Upload | Não existe | Drag & drop CSV/Excel → alimenta KPIs |
| Responsividade | Grid básico | Mobile-first com sidebar colapsável |
| APMO no frontend | Painéis presentes mas sem dados reais | Conectar ao backend Python/Supabase |

### 2.3 Gaps no pipeline Python

| Item | Estado | O que precisa |
|------|--------|---------------|
| Entidades faltando | Apenas zonas/obras/fornecedores | atividades, cronograma, presenças, materiais, equipes, ocorrências, ECOs, REOs, ICO |
| Audit log | Não existe | Trigger Postgres ou equivalente Python |
| Snapshot diário | Não existe | Job cron que persiste EOV |
| Hash encadeado | Não existe | SHA-256 encadeado por registro |
| Evidências | Não existe | Upload + hash + metadados EXIF/GPS |

### 2.4 Gaps na estrutura do repo

| Item | Estado | O que precisa |
|------|--------|---------------|
| `docs/` | Vazia | Documentação técnica das rotas, schema, pipeline |
| `data/schemas/` | Não existe | JSON Schema / DDL de cada tabela |
| `data/geojson/` | Não separado | GeoJSON de zonas (polígonos, não pontos) |
| `python/modules/` | Plano | Módulos separados por domínio |
| `tests/` | Existe mas conteúdo desconhecido | Testes do pipeline e do servidor |
| `.github/workflows/` | Existe | Verificar se deploy Pages está ativo |
| `CHANGELOG.md` | Não existe | Histórico de versões |
| `CONTRIBUTING.md` | Não existe | Guia de contribuição |

---

## 3. CONCEITO COMPLETO DO SISTEMA

### Missão

O Radar Territorial não é um mapa. Não é um dashboard. É uma **camada de inteligência territorial** que responde à pergunta:

> *"Neste local, o que pode ser feito segundo o Plano Diretor — e o que está acontecendo agora?"*

### Três produtos em um

```
OPERA Territorial
├── Radar Territorial   → "O que o território permite?"  (normas → consulta)
├── OPERA Control       → "O que está acontecendo?"      (obras → gestão)
└── OPERA Atlas         → "Como chegamos até aqui?"      (evidências → memória)
```

### Personas e perguntas-chave

| Stakeholder | Pergunta principal | Resposta esperada |
|-------------|-------------------|-------------------|
| Gestor público | Onde estão as carências? | Mapa de déficit por setor/equipamento |
| Investidor | Onde há potencial não aproveitado? | Viabilidade construtiva por lote |
| Construtor | Quais índices se aplicam ao meu lote? | TO, CA, permeabilidade, altura |
| Cidadão | O que pode existir perto da minha casa? | Usos permitidos por zona |
| Cartório | Esse lote está em conformidade? | Situação normativa auditável |
| Gestor de obra | O que está atrasado? | ICO por frente, alertas, missões |
| Auditor/TCU | O que aconteceu em março de 2025? | Snapshot histórico verificável |

---

## 4. ARQUITETURA TÉCNICA ALVO

### Stack

```
Frontend (GitHub Pages)
└── HTML + CSS + JS vanilla (sem framework)
    ├── SVG próprio para mapa territorial (sem Leaflet como dependência crítica)
    ├── Leaflet bundled localmente (fallback para mapa base online)
    ├── Canvas nativo para gráficos (sem Chart.js como dependência crítica)
    └── Parser CSV nativo (sem SheetJS como dependência crítica)

Backend
├── Python (FastAPI ou Flask)
│   ├── server.py — API REST + servir arquivos
│   ├── python/pipeline.py — ETL principal
│   ├── python/audit.py — trilha de auditoria
│   ├── python/snapshot.py — EOV diário
│   └── python/hash_chain.py — integridade SHA-256
└── Supabase (PostgreSQL)
    ├── Tabelas existentes: zonas, obras, fornecedores, import_jobs, user_roles
    └── Tabelas a criar: ver Seção 5

Dados
├── data/raw/           — arquivos brutos (CSV, shapefiles)
├── data/staging/       — dados intermediários
├── data/output/        — JSON consumido pelo frontend
│   ├── dashboard_data.json
│   ├── radar_geojson.geojson    — PONTOS (existente)
│   ├── zonas_poligonos.geojson  — POLÍGONOS (a criar)
│   └── snapshots/               — EOV por data
└── data/schemas/       — DDL e JSON Schema
```

### Fluxo de dados

```
Plano Diretor (PDF/SHP)
        ↓ Python pipeline
    Supabase (PostgreSQL)
        ↓ server.py /api/data
    data/output/*.json
        ↓ fetch() no browser
    index.html (SVG + Canvas)
        ↓ interação do usuário
    Cards de zona + KPIs + Tabela
```

---

## 5. SCHEMA DO BANCO — O QUE CRIAR

### Tabelas existentes (manter, adicionar colunas)

```sql
-- Adicionar em zonas, obras, fornecedores:
ALTER TABLE zonas ADD COLUMN version INT NOT NULL DEFAULT 1;
ALTER TABLE zonas ADD COLUMN source_import_job_id UUID REFERENCES import_jobs(id);
ALTER TABLE zonas ADD COLUMN owner_id UUID;
ALTER TABLE zonas ADD COLUMN created_reason TEXT;

-- Mesmo padrão para obras e fornecedores
```

### Tabelas novas — Fase 1 (Fundamento auditável)

```sql
-- Trilha de auditoria universal
CREATE TABLE audit_log (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  table_name TEXT NOT NULL,
  row_id UUID NOT NULL,
  op TEXT NOT NULL CHECK (op IN ('INSERT','UPDATE','DELETE')),
  actor_id UUID,
  at TIMESTAMPTZ DEFAULT now(),
  old_row JSONB,
  new_row JSONB,
  prev_hash TEXT,
  curr_hash TEXT  -- SHA-256(prev_hash || new_row || at || actor_id)
);
-- RLS: INSERT apenas por trigger (SECURITY DEFINER), SELECT para admin
```

### Tabelas novas — Fase 2 (Versionamento)

```sql
-- Padrão para cada entidade mutável
CREATE TABLE zonas_versions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  entity_id UUID NOT NULL REFERENCES zonas(id),
  version INT NOT NULL,
  snapshot JSONB NOT NULL,
  reason TEXT NOT NULL,  -- mínimo 20 chars
  edited_by UUID,
  edited_at TIMESTAMPTZ DEFAULT now(),
  approved_by UUID,
  approved_at TIMESTAMPTZ,
  valid_from TIMESTAMPTZ NOT NULL,
  valid_to TIMESTAMPTZ   -- NULL = versão atual
);
-- Mesmo padrão: obras_versions, fornecedores_versions
```

### Tabelas novas — Fase 3 (Entidades faltando — APMO §8.2)

```sql
-- Atividades de obra
CREATE TABLE atividades (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  obra_id UUID REFERENCES obras(id),
  nome TEXT NOT NULL,
  tipo TEXT,  -- fundacao, estrutura, instalacao, acabamento
  responsavel_id UUID,
  inicio_previsto DATE,
  fim_previsto DATE,
  inicio_real DATE,
  fim_real DATE,
  progresso_pct NUMERIC(5,2),
  custo_previsto NUMERIC(12,2),
  custo_real NUMERIC(12,2),
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now(),
  version INT NOT NULL DEFAULT 1
);

-- Cronograma
CREATE TABLE cronograma (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  obra_id UUID REFERENCES obras(id),
  atividade_id UUID REFERENCES atividades(id),
  baseline_inicio DATE,
  baseline_fim DATE,
  revisao_inicio DATE,
  revisao_fim DATE,
  motivo_revisao TEXT,
  version INT NOT NULL DEFAULT 1
);

-- ICO — Índice de Conformidade Operacional
CREATE TABLE ico_registros (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  obra_id UUID REFERENCES obras(id),
  atividade_id UUID REFERENCES atividades(id),
  data_referencia DATE NOT NULL,
  ico_valor NUMERIC(5,2),  -- 0 a 100
  componentes JSONB,       -- {qualidade, prazo, custo, seguranca}
  calculado_por TEXT,
  calculado_at TIMESTAMPTZ DEFAULT now()
);

-- Evidências
CREATE TABLE evidencias (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  obra_id UUID REFERENCES obras(id),
  atividade_id UUID REFERENCES atividades(id),
  tipo TEXT NOT NULL CHECK (tipo IN ('foto','video','audio','pdf','checklist','reo','eco')),
  storage_path TEXT NOT NULL,
  hash_sha256 TEXT NOT NULL,
  exif JSONB,
  gps_lat NUMERIC(10,7),
  gps_lng NUMERIC(10,7),
  captured_at TIMESTAMPTZ,
  device TEXT,
  uploaded_by UUID,
  uploaded_at TIMESTAMPTZ DEFAULT now()
);

-- ECO — Evento Contratual Operacional
CREATE TABLE ecos (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  obra_id UUID REFERENCES obras(id),
  tipo TEXT,  -- aditivo, distrato, ocorrencia, medicao
  descricao TEXT NOT NULL,
  impacto_prazo_dias INT,
  impacto_custo NUMERIC(12,2),
  evidencias_ids UUID[],
  status TEXT DEFAULT 'pendente',
  criado_por UUID,
  criado_at TIMESTAMPTZ DEFAULT now(),
  aprovado_por UUID,
  aprovado_at TIMESTAMPTZ,
  version INT NOT NULL DEFAULT 1
);

-- Snapshot operacional diário (EOV)
CREATE TABLE snapshot_operacional (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  obra_id UUID REFERENCES obras(id),
  snapshot_date DATE NOT NULL,
  payload JSONB NOT NULL,  -- estado completo da obra naquela data
  prev_hash TEXT,
  curr_hash TEXT,
  gerado_at TIMESTAMPTZ DEFAULT now(),
  UNIQUE(obra_id, snapshot_date)
);

-- Materiais / estoque
CREATE TABLE materiais (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  obra_id UUID REFERENCES obras(id),
  nome TEXT NOT NULL,
  unidade TEXT,
  quantidade_prevista NUMERIC(12,3),
  quantidade_real NUMERIC(12,3),
  custo_unitario NUMERIC(12,2),
  fornecedor_id UUID REFERENCES fornecedores(id),
  data_entrada DATE,
  version INT NOT NULL DEFAULT 1
);

-- Equipes
CREATE TABLE equipes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  obra_id UUID REFERENCES obras(id),
  nome TEXT NOT NULL,
  encarregado TEXT,
  membros INT,
  especialidade TEXT,
  ativa BOOLEAN DEFAULT true
);

-- Ocorrências
CREATE TABLE ocorrencias (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  obra_id UUID REFERENCES obras(id),
  atividade_id UUID REFERENCES atividades(id),
  tipo TEXT,  -- acidente, nao_conformidade, atraso, retrabalho
  descricao TEXT NOT NULL,
  gravidade TEXT CHECK (gravidade IN ('baixa','media','alta','critica')),
  evidencias_ids UUID[],
  resolvida BOOLEAN DEFAULT false,
  registrada_por UUID,
  registrada_at TIMESTAMPTZ DEFAULT now()
);

-- Checklists
CREATE TABLE checklists (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  obra_id UUID REFERENCES obras(id),
  atividade_id UUID REFERENCES atividades(id),
  template_nome TEXT,
  itens JSONB NOT NULL,   -- [{item, ok, obs}]
  preenchido_por UUID,
  preenchido_at TIMESTAMPTZ DEFAULT now(),
  assinatura_hash TEXT
);
```

---

## 6. ESTRUTURA DE ARQUIVOS ALVO (VS Code)

```
radar-territorial/
│
├── .github/
│   └── workflows/
│       ├── deploy-pages.yml      # GitHub Pages auto-deploy
│       └── pipeline-test.yml     # Testa Python pipeline no push
│
├── .vscode/
│   ├── settings.json
│   └── extensions.json           # Pylance, Prettier, GitLens
│
├── config/
│   ├── settings.yaml             # Parâmetros do pipeline
│   └── logging.yaml
│
├── data/
│   ├── raw/                      # Arquivos brutos (não commitar dados reais)
│   │   ├── plano_diretor/        # PDFs, shapefiles
│   │   └── importacoes/          # CSVs de obras, fornecedores
│   ├── staging/                  # Intermediários
│   ├── schemas/                  # DDL e JSON Schema
│   │   ├── zonas.schema.json
│   │   ├── obras.schema.json
│   │   └── migrations/           # SQL de migrations numeradas
│   │       ├── 001_audit_log.sql
│   │       ├── 002_versions.sql
│   │       └── 003_entidades_apmo.sql
│   └── output/                   # Gerado pelo pipeline, consumido pelo frontend
│       ├── dashboard_data.json
│       ├── zonas_poligonos.geojson    # POLÍGONOS das zonas
│       ├── radar_geojson.geojson      # Pontos de obras/fornecedores
│       └── snapshots/
│           └── YYYY-MM-DD.json
│
├── docs/
│   ├── ARQUITETURA.md            # Diagrama e decisões técnicas
│   ├── API.md                    # Rotas do server.py
│   ├── SCHEMA.md                 # Tabelas e relações
│   ├── APMO.md                   # Roadmap de memória operacional
│   └── DEPLOY.md                 # Como fazer deploy no GitHub Pages
│
├── python/
│   ├── pipeline.py               # Ponto de entrada CLI
│   ├── modules/
│   │   ├── ingestao.py           # Lê raw → staging
│   │   ├── processamento.py      # Calcula indicadores
│   │   ├── exportacao.py         # Gera output JSON/GeoJSON
│   │   ├── audit.py              # Registra audit_log
│   │   ├── snapshot.py           # Gera EOV diário
│   │   ├── hash_chain.py         # SHA-256 encadeado
│   │   └── geojson_builder.py    # Converte shapefiles → GeoJSON polígonos
│   └── requirements.txt
│
├── tests/
│   ├── test_pipeline.py
│   ├── test_audit.py
│   ├── test_hash.py
│   └── fixtures/                 # Dados de teste
│
├── frontend/                     # ← SEPARAR do index.html raiz
│   ├── index.html                # Shell principal
│   ├── css/
│   │   └── main.css
│   ├── js/
│   │   ├── main.js               # Boot e view switching
│   │   ├── mapa.js               # SVG territorial + Leaflet
│   │   ├── kpis.js               # Cálculo e renderização de KPIs
│   │   ├── graficos.js           # Canvas hand-rolled (sem Chart.js)
│   │   ├── tabela.js             # Tabela paginada
│   │   ├── upload.js             # Parser CSV nativo
│   │   └── apmo.js               # Painéis de auditoria/snapshot/integridade
│   ├── data/                     # GeoJSON bundled para fallback offline
│   │   └── zonas_redencao.geojson
│   └── vendor/
│       └── leaflet/              # Leaflet bundled localmente
│           ├── leaflet.js
│           └── leaflet.css
│
├── .env.example
├── .gitignore
├── APMO-OPERA-v1.md              # Já existe — manter
├── CHANGELOG.md                  # CRIAR
├── CONTRIBUTING.md               # CRIAR
├── README.md                     # EXPANDIR (ver Seção 9)
├── index.html                    # Redireciona para frontend/ ou é o frontend
├── requirements.txt
└── server.py
```

---

## 7. MÓDULOS DO FRONTEND — O QUE CADA UM FAZ

### 7.1 `mapa.js` — Coração do Radar

```
Responsabilidades:
- Renderizar SVG dos polígonos de zona (sem CDN externo)
- Pan & zoom via viewBox manipulation
- Clique em zona → abre card lateral com:
    * Sigla e nome
    * Macrozona e nível de incomodidade
    * Índices urbanísticos (TO, CA básico, CA máximo, permeabilidade, altura)
    * Atividades: Permitido / Condicionado / Proibido
    * Viabilidade construtiva calculada
- Filtro por tipo de zona (chips na legenda)
- Busca por nome/sigla com highlight no mapa
- Camadas toggleáveis: Zoneamento, Obras, POIs, Alertas, Grade UTM
- Coordenadas no rodapé (SVG units ou lat/lng se Leaflet ativo)
- Fallback: se online → mapa base Leaflet; se offline → SVG puro
```

### 7.2 `kpis.js` — Indicadores Dinâmicos

```
8 KPIs calculados do dashboard_data.json:
1. Setores Mapeados
2. Obras em Andamento (soma de ObrasAtivas)
3. Fornecedores Ativos (soma de FornecedoresAtendendo)
4. Demandas Prioritárias (count de Prioritário em qualquer dimensão)
5. Zonas ZUM (count)
6. ZEIS (count)
7. Cobertura de Creche (% setores com EducacaoInfantil = Prioritário)
8. Cobertura de Saúde (% setores com Saude = Prioritário)

ICO — Índice de Conformidade Operacional:
- Por zona / por obra / por frente
- Cor semântica: >= 80 verde, >= 60 amarelo, < 60 vermelho
- Histórico temporal se snapshot disponível
```

### 7.3 `graficos.js` — Canvas Nativo

```
4 gráficos mínimos (canvas, sem dependência):
1. Barras: Setores por Zona
2. Donut: Demandas Prioritárias por tipo
3. Barras: Obras por Região
4. Barras: Fornecedores por Zona

Futuro:
5. Linha: Evolução do ICO no tempo
6. Heatmap: Conformidade por setor
```

### 7.4 `tabela.js` — Dados Brutos

```
- Lê dashboard_data.json ou dado carregado via upload
- Colunas configuráveis
- Busca global em todos os campos
- Filtro por zona e por região (selects populados dinamicamente)
- Ordenação por qualquer coluna (toggle asc/desc)
- Paginação: 20 linhas por página
- Células com estilo semântico (zonas coloridas, status pills)
- Exportar filtrado como CSV
```

### 7.5 `upload.js` — Parser Nativo

```
- Drag & drop ou clique para selecionar
- Aceita: .csv (vírgula ou ponto-e-vírgula), UTF-8 e Latin-1
- NÃO depende de SheetJS (Excel só se bundled localmente)
- Parser CSV próprio com suporte a campos quoted
- Validação de colunas esperadas
- Feedback imediato: quantas linhas, quais colunas, erros
- Alimenta KPIs, gráficos e tabela automaticamente
```

### 7.6 `apmo.js` — Memória Operacional

```
Painéis do APMO visíveis no frontend:
1. Trilha de Auditoria — últimos N eventos (tabela audit_log)
2. Histórico de Snapshots — lista de EOVs disponíveis
3. Comparação de versões — diff entre dois snapshots
4. Restauração — select + botão → POST /api/restore
5. Integridade criptográfica — verifica hash chain
6. Contexto semântico — relações entre entidades

Conecta ao server.py via fetch():
- GET /api/audit?limit=20
- GET /api/snapshots
- GET /api/snapshot?date=YYYY-MM-DD
- POST /api/restore?timestamp=
- GET /api/integrity?obra_id=
```

---

## 8. API DO SERVER.PY — ROTAS A IMPLEMENTAR

```
GET  /                              → serve frontend/index.html
GET  /api/health                    → {"status": "ok", "version": "..."}
GET  /api/data                      → dashboard_data.json completo
GET  /api/geojson/zonas             → zonas_poligonos.geojson
GET  /api/geojson/pontos            → radar_geojson.geojson
GET  /api/zonas                     → lista de zonas com atributos normativos
GET  /api/zonas/:id                 → zona específica + atividades + viabilidade
GET  /api/obras                     → lista de obras + ICO atual
GET  /api/obras/:id                 → obra + atividades + cronograma + evidências
GET  /api/fornecedores              → lista
GET  /api/kpis                      → KPIs calculados ao vivo
GET  /api/audit?limit=&offset=      → trilha de auditoria
GET  /api/snapshots                 → lista de EOVs disponíveis
GET  /api/snapshot?date=            → EOV de uma data
POST /api/restore?timestamp=        → restaura snapshot
GET  /api/integrity?obra_id=        → verifica hash chain
GET  /api/ico?obra_id=&date=        → ICO de uma obra numa data
POST /api/import                    → recebe CSV → pipeline
```

---

## 9. README.md — O QUE PRECISA TER

O README atual tem 526 bytes. Precisa cobrir:

```markdown
# OPERA Territorial — Radar de Geointeligência

## O que é
## Stack
## Pré-requisitos
## Instalação
## Configuração (.env)
## Rodando localmente
## Estrutura do projeto
## Pipeline de dados
## Deploy (GitHub Pages)
## Roadmap (link para APMO-OPERA-v1.md)
## Licença
```

---

## 10. ROADMAP DE DESENVOLVIMENTO

### Fase 0 — Estrutura e Fundação (agora)

- [ ] Reorganizar pastas conforme Seção 6
- [ ] Separar `frontend/` com CSS e JS modulares
- [ ] Bundlar Leaflet localmente em `frontend/vendor/`
- [ ] Criar `data/schemas/migrations/001_audit_log.sql`
- [ ] Expandir README.md
- [ ] Criar CHANGELOG.md e CONTRIBUTING.md
- [ ] Verificar e corrigir `.github/workflows/deploy-pages.yml`

### Fase 1 — Frontend Funcional (1–2 semanas)

- [ ] `mapa.js`: SVG com polígonos de zona + card lateral completo
- [ ] `kpis.js`: 8 KPIs + ICO por zona
- [ ] `graficos.js`: 4 gráficos canvas
- [ ] `tabela.js`: tabela paginada com busca e filtros
- [ ] `upload.js`: parser CSV nativo
- [ ] Responsividade mobile

### Fase 2 — Backend Auditável (2–3 semanas)

- [ ] GAP-01: `audit_log` com trigger Postgres
- [ ] GAP-07: `version int` em todas as tabelas mutáveis
- [ ] GAP-08: `source_import_job_id`
- [ ] `server.py`: todas as rotas da Seção 8
- [ ] `python/modules/audit.py`
- [ ] `python/modules/hash_chain.py`
- [ ] `apmo.js`: painéis conectados ao backend

### Fase 3 — Entidades APMO (3–4 semanas)

- [ ] Migrations 002 e 003 (ver Seção 5)
- [ ] Tabelas: atividades, cronograma, ico_registros, evidencias, ecos
- [ ] GAP-02: `*_versions` append-only
- [ ] GAP-05: retificação com motivo obrigatório
- [ ] GAP-04: snapshot operacional diário (cron)
- [ ] Pipeline Python para ICO

### Fase 4 — Preservação Verificável (futuro)

- [ ] GAP-03: bucket de evidências + hash + GPS
- [ ] GAP-09: timestamp RFC 3161 externo
- [ ] Assinaturas digitais
- [ ] Exportação de "livro-razão operacional"
- [ ] GAP-10: PWA offline para campo

---

## 11. CONVENÇÕES DE CÓDIGO

### Python

```python
# Nomenclatura
snake_case para funções e variáveis
PascalCase para classes
UPPER_SNAKE_CASE para constantes

# Estrutura de função
def nome_funcao(param: tipo) -> tipo:
    """Docstring obrigatória."""
    ...

# Logging
import logging
logger = logging.getLogger(__name__)
logger.info("mensagem", extra={"obra_id": str(obra_id)})
```

### JavaScript (frontend)

```javascript
// Sem frameworks — JS vanilla ES2020
// camelCase para variáveis e funções
// PascalCase para "classes" (funções construtoras)
// UPPER_SNAKE_CASE para constantes globais

// Módulos via IIFE ou ES Modules nativos
// Nenhuma dependência CDN em produção
// Dependências bundled em vendor/
```

### SQL

```sql
-- snake_case para tabelas e colunas
-- UUIDs como PK via gen_random_uuid()
-- created_at + updated_at em toda tabela mutável
-- version int em toda tabela mutável
-- RLS habilitada em todo objeto Supabase
-- Migrations numeradas sequencialmente: 001_, 002_, ...
```

### GeoJSON

```json
{
  "type": "Feature",
  "properties": {
    "sigla": "ZUM",
    "nome": "Zona de Uso Misto — Centro",
    "macrozona": "Urbana",
    "nivel": "N3",
    "to_max": 60,
    "ca_basico": 1.5,
    "ca_maximo": 3.0,
    "permeabilidade": 20,
    "altura_max": 15,
    "area_m2": 1247000,
    "lotes": 89,
    "conformidade": 91
  },
  "geometry": {
    "type": "Polygon",
    "coordinates": [[ ... ]],
    "crs": "EPSG:4326"
  }
}
```

---

## 12. VARIÁVEIS DE AMBIENTE (.env)

```env
# Supabase
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_ANON_KEY=eyJ...
SUPABASE_SERVICE_KEY=eyJ...   # apenas no backend, nunca no frontend

# Pipeline
DATA_RAW_PATH=data/raw
DATA_OUTPUT_PATH=data/output
PIPELINE_LOG_LEVEL=INFO
SNAPSHOT_CRON=23:59           # hora do EOV diário

# Servidor
SERVER_PORT=8001
SERVER_HOST=127.0.0.1
CORS_ORIGINS=http://localhost:3000,https://horushipnotic.github.io

# Hash chain
HASH_SALT=opera_territorial_v2  # muda por ambiente

# Opcional: timestamp externo
OPENTIMESTAMPS_ENABLED=false
```

---

## 13. TESTES MÍNIMOS RECOMENDADOS

```python
# tests/test_pipeline.py
def test_pipeline_gera_dashboard_json():
def test_pipeline_gera_geojson():
def test_pipeline_com_csv_valido():
def test_pipeline_rejeita_csv_invalido():

# tests/test_audit.py
def test_audit_log_registra_insert():
def test_audit_log_registra_update_com_old_row():
def test_audit_log_registra_delete():
def test_hash_chain_valida():
def test_hash_chain_detecta_adulteracao():

# tests/test_hash.py
def test_sha256_encadeado_consistente():
def test_sha256_encadeado_detecta_alteracao():
def test_snapshot_hash_igual_ao_recalculado():
```

---

## 14. PONTOS DE ATENÇÃO CRÍTICOS

**1. Nunca usar CDN externo em produção**  
Leaflet, Chart.js e SheetJS devem estar em `vendor/` ou reimplementados nativamente. O `index.html` atual quebra sempre que o CDN fica indisponível ou é bloqueado.

**2. Nunca expor `SUPABASE_SERVICE_KEY` no frontend**  
O `index.html` deve usar apenas `SUPABASE_ANON_KEY` com RLS configurada. Toda operação privilegiada passa pelo `server.py`.

**3. O `upsert` atual sobrescreve — nunca usar para edição**  
Toda edição pós-publicação deve usar a server function `retificar<Entidade>` que cria nova versão em `*_versions` e exige motivo.

**4. GeoJSON de polígonos é diferente de pontos**  
O `radar_geojson.geojson` atual tem `circleMarker` (pontos). O mapa de zoneamento precisa de polígonos das zonas exportados do QGIS em EPSG:4326. São dois arquivos distintos com propósitos distintos.

**5. O APMO existe e está documentado — seguir o roadmap**  
O `APMO-OPERA-v1.md` é o documento técnico mais importante do repo. Cada feature nova deve ser cruzada com os GAPs do APMO antes de implementar.

---

## 15. REFERÊNCIAS INTERNAS DO REPO

| Arquivo | Função |
|---------|--------|
| `APMO-OPERA-v1.md` | Auditoria de memória operacional — IPMO 8,5/100 — gaps e roadmap |
| `index.html` | Frontend atual — 344 linhas — base para refatoração |
| `server.py` | Backend local — porta 8001 — expandir rotas |
| `python/pipeline.py` | ETL principal — expandir com módulos |
| `data/output/dashboard_data.json` | Contrato de dados frontend ↔ backend |
| `data/output/radar_geojson.geojson` | GeoJSON de pontos — manter + adicionar polígonos |

---

*Documento gerado em 29/07/2026 com base na auditoria do repo `HorusHypnotic/radar-territorial`.*  
*IPMO atual: 8,5/100 — meta Fase 1: 35 — meta Fase 4: 91+*
