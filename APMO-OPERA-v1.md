# APMO — Auditoria de Preservação da Memória Operacional
## Ecossistema OPERA (Atlas · Control · Copiloto de Obras) — v1.0

**Data**: 11 de julho de 2026
**Sistema auditado**: OPERA Territorial (estado atual, pós-Iteração 1 de responsividade)
**Auditor**: Análise técnica baseada em schema, políticas RLS e código-fonte
**Método**: Evidência direta do banco e do código. Nenhuma capacidade foi presumida.

---

## 1. Sumário Executivo

### Veredito

> **O OPERA hoje é um sistema de Registro Operacional.
> Não é ainda um sistema de Memória Operacional Preservada.**

O ecossistema atual permite **cadastrar, visualizar e importar** dados territoriais (zonas, obras, fornecedores). Ele **não** permite reconstruir o estado da obra em uma data passada, provar que nada foi adulterado, versionar decisões, preservar contexto operacional ou custodiar evidências. Toda alteração **sobrescreve** o registro anterior de forma irreversível.

### IPMO Global

| Domínio                       | Nota (0–100) |
| ----------------------------- | ------------ |
| Integridade                   | 15           |
| Temporalidade                 | 10           |
| Contexto                      | 20           |
| Versionamento                 | 5            |
| Cadeia de Custódia            | 0            |
| Auditabilidade                | 10           |
| Reconstrução Histórica        | 5            |
| Preservação Semântica         | 15           |
| Assinaturas                   | 0            |
| Inteligência Temporal         | 5            |
| **IPMO Global (média)**       | **8,5**      |

**Classificação**: **0–40 → Registro operacional**.
Distância até "Memória operacional preservada" (71–90): **~63 pontos**.
Distância até "Arquitetura de preservação verificável" (91–100): **~83 pontos**.

### Três achados críticos

1. **Não existe trilha de auditoria.** Nenhum `UPDATE` ou `DELETE` é registrado. Um editor pode alterar o polígono de uma zona ou o custo de uma obra e o sistema não guarda **quem, quando, o que era antes**. Impacto jurídico-probatório: severo.
2. **Não existe versionamento.** `zonas` e `obras` usam `UPDATE` direto. O único carimbo temporal é `updated_at`, que é **sobrescrito** a cada alteração — perde-se o histórico na segunda edição.
3. **Não existe custódia de evidências.** O sistema não armazena fotos, vídeos, áudios, PDFs, checklists, assinaturas ou ECOs/REOs. Storage buckets: **zero**.

---

## 2. Inventário da Informação

### 2.1 Objetos esperados pelo APMO × objetos existentes no OPERA

| Objeto esperado          | Existe? | Tabela / Local            | ID único | Versão | Histórico | Soft-delete | Auditoria |
| ------------------------ | ------- | ------------------------- | -------- | ------ | --------- | ----------- | --------- |
| Obras                    | Sim     | `public.obras`            | uuid     | Não    | Não       | Não         | Não       |
| Zonas territoriais       | Sim     | `public.zonas`            | uuid     | Não    | Não       | Não         | Não       |
| Fornecedores             | Sim     | `public.fornecedores`     | uuid     | Não    | Não       | Não         | Não       |
| Jobs de importação       | Sim     | `public.import_jobs`      | uuid     | N/A    | Sim¹      | N/A         | Parcial²  |
| Papéis de usuário        | Sim     | `public.user_roles`       | uuid     | Não    | Não       | Não         | Não       |
| Allowlist                | Sim     | `public.allowed_emails`   | email    | Não    | Não       | Não         | Não       |
| Atividades               | **Não** | —                         | —        | —      | —         | —           | —         |
| Cronogramas              | **Não** | —                         | —        | —      | —         | —           | —         |
| Presenças / diário       | **Não** | —                         | —        | —      | —         | —           | —         |
| Produção diária          | **Não** | —                         | —        | —      | —         | —           | —         |
| Materiais / estoque      | **Não** | —                         | —        | —      | —         | —           | —         |
| Equipamentos             | **Não** | —                         | —        | —      | —         | —           | —         |
| Equipes                  | **Não** | —                         | —        | —      | —         | —           | —         |
| Ocorrências              | **Não** | —                         | —        | —      | —         | —           | —         |
| ECOs (Evento Contratual) | **Não** | —                         | —        | —      | —         | —           | —         |
| ICO (Índice)             | **Não** | —                         | —        | —      | —         | —           | —         |
| REOs (Relatório)         | **Não** | —                         | —        | —      | —         | —           | —         |
| Fotos / vídeos / áudios  | **Não** | Nenhum bucket             | —        | —      | —         | —           | —         |
| PDFs / documentos        | **Não** | Nenhum bucket             | —        | —      | —         | —           | —         |
| Checklists               | **Não** | —                         | —        | —      | —         | —           | —         |
| Aprovações               | **Não** | —                         | —        | —      | —         | —           | —         |
| Assinaturas              | **Não** | —                         | —        | —      | —         | —           | —         |
| Logs (application)       | **Não** | Apenas console            | —        | —      | —         | —           | —         |
| Dashboards / indicadores | Parcial | `/indicadores` (calculado ao vivo) | N/A | Não | Não | N/A | Não |

¹ `import_jobs` grava `rows_ok`, `rows_error`, `error_log`. É append-only por design (não há UPDATE), o que é bom — mas registra apenas o **evento de importação**, não as linhas resultantes por origem.
² O log não vincula cada linha inserida ao `import_job_id` que a originou. Não é possível responder "quais obras vieram do CSV X?".

### 2.2 Cobertura

- **6 tabelas existentes** contra ~24 objetos previstos pelo APMO.
- **Cobertura de inventário: ~25%**.
- Todos os 6 objetos existentes falham em pelo menos 3 dos 5 atributos de preservação (versão, histórico, soft-delete, auditoria, snapshot).

---

## 3. Achados por Etapa

### Etapa 2 — Estado Operacional Verificável (EOV)

| Reconstrução de… | Possível? | Motivo |
| ---------------- | --------- | ------ |
| Produção         | Não | Não existe entidade |
| Planejamento     | Não | Não existe cronograma |
| Custos           | Parcial | `obras.custo` existe, mas é o valor **atual**, sem histórico |
| Equipes          | Não | Não existe entidade |
| Estoque          | Não | Não existe entidade |
| Evidências       | Não | Sem storage, sem metadados |
| Clima            | Não | Sem integração meteorológica |
| Responsáveis     | Parcial | `user_roles` sabe **hoje**; não sabe quem era admin em 03/2025 |
| Decisões         | Não | Não existe log de decisão |
| IA utilizada     | Não | Sem integração com IA / sem log de prompts |

**Snapshot operacional**: inexistente.
**Congelamento temporal**: inexistente.
**Reconstrução histórica**: **impossível** — o banco só conhece o presente.

**Classificação**: Não implementado.

### Etapa 3 — Cadeia de Integridade

- **Hash**: nenhum.
- **Encadeamento entre registros**: nenhum (`obras`, `zonas` são independentes; sem coluna `prev_hash` ou `chain_id`).
- **Assinatura digital**: nenhuma.
- **Timestamp confiável (RFC 3161 / âncora externa)**: nenhum — apenas `now()` do Postgres, alterável por admin do banco.
- **Prova de integridade independente**: nenhuma.

**Classificação**: Não implementado.

### Etapa 4 — Versionamento

Evidência de código (`src/lib/obras.functions.ts`, `zonas.functions.ts`, `fornecedores.functions.ts`):

```ts
.upsert(data).select().single()
```

Toda alteração é `INSERT ... ON CONFLICT UPDATE`. **Sobrescreve.**
- Versão vigente: sim (a única).
- Versões anteriores: **não existem**.
- Motivo da alteração: **não solicitado**.
- Responsável pela alteração: **não registrado** (nem `updated_by` existe).
- Data da alteração: `updated_at` — mas é sobrescrito na próxima edição.
- Impacto: **não avaliado**.
- Visualização/restauração/comparação de versões: **impossível**.

**Classificação**: Não implementado.

### Etapa 5 — Cadeia de Custódia

Como não existem tabelas de evidência (fotos, vídeos, PDFs, checklists) nem storage buckets, **nenhum dos 10 atributos exigidos** (origem, autor, dispositivo, GPS, data, horário, hash, assinatura, histórico de alterações, histórico de acessos) está presente.

**Classificação**: Não implementado.

### Etapa 6 — Preservação do Contexto

Relações existentes: `obras.zona_id → zonas.id`. **Apenas isso.**
- Cronograma: não existe.
- Equipes: não existe.
- Produção: não existe.
- Contratos: não existe.
- ECO / REO: não existe.
- Indicadores: calculados on-the-fly, sem persistência.

**Classificação**: Não implementado.

### Etapa 7 — Preservação Semântica

Uma linha em `obras` hoje contém: `nome`, `status`, `x`, `y`, `custo`, `prazo`, `descricao`, `zona_id`. Sem:
- descrição estruturada (ontologia / tags),
- responsável de negócio,
- motivo de criação/alteração,
- impacto orçamentário/temporal,
- classificação (tipologia, criticidade),
- vínculo com ECO/REO.

**Cinco anos no futuro**, um auditor abrirá `obras` e verá coordenadas `x=427, y=210` sem saber a que sistema de referência pertencem, qual foi a justificativa de custo, ou quem aprovou.

**Classificação**: Implementado com limitações severas.

### Etapa 8 — Delta Operacional (ΔO)

Sem versionamento, ΔO é matematicamente indefinido no sistema atual. Não há como calcular "o que mudou entre segunda e terça" porque **segunda não existe mais**.

**Classificação**: Não implementado.

### Etapa 9 — Retificação Operacional

- Conceito de retificação: **inexistente**.
- Editar = sobrescrever direto no banco.
- Sem justificativa obrigatória, sem aprovação, sem novo estado, sem preservação do original.

**Classificação**: Não implementado.

### Etapa 10 — Inteligência Temporal

Consequência direta das etapas 2–4: **impossível** responder qualquer pergunta temporal ("como estava em 12/03/2025?"). O banco é um **snapshot único do presente**.

**Classificação**: Não implementado.

### Etapa 11 — Robustez da Arquitetura

| Item                        | Estado |
| --------------------------- | ------ |
| Perda de servidor           | Coberto (Lovable Cloud gerencia) |
| Perda de banco              | Coberto (backups gerenciados pela plataforma) |
| Falha de sincronização      | N/A — sistema **não é offline-first** |
| Modo offline                | **Não implementado** |
| Duplicidade                 | Sem detecção — `upsert` no ID resolve, mas `nome` duplicado passa |
| Conflitos concorrentes      | **Não tratados** — last-write-wins silencioso |
| Alterações simultâneas      | Sem lock otimista (nenhum `version` / `etag`) |
| Backup                      | Gerenciado (plataforma) |
| Recuperação point-in-time   | Depende do PITR da plataforma; **não exposto ao usuário** |
| Auditoria externa           | **Impossível** — sem trilha independente |

**Classificação**: Parcialmente implementado (só o que a plataforma oferece por baixo).

---

## 4. IPMO Detalhado

| Domínio                | Nota | Justificativa                                                                 |
| ---------------------- | ---- | ----------------------------------------------------------------------------- |
| Integridade            | 15   | Postgres garante ACID; nenhuma prova criptográfica; `now()` é adulterável por admin |
| Temporalidade          | 10   | `created_at`/`updated_at` existem; `updated_at` é sobrescrito ⇒ perde histórico |
| Contexto               | 20   | Uma FK (`obras.zona_id`); nenhuma outra relação semântica                     |
| Versionamento          | 5    | Inexistente; upsert sobrescreve                                               |
| Cadeia de Custódia     | 0    | Sem storage, sem metadados, sem hash                                          |
| Auditabilidade         | 10   | `import_jobs` é append-only (bom); nenhuma outra tabela é auditada           |
| Reconstrução Histórica | 5    | Impossível reconstruir qualquer estado passado                                |
| Preservação Semântica  | 15   | Campos existem mas sem ontologia, sem motivo, sem responsável de negócio      |
| Assinaturas            | 0    | Nenhuma assinatura digital; nenhum PKI                                        |
| Inteligência Temporal  | 5    | Zero capacidade temporal                                                      |

**IPMO Global: 8,5 / 100 → Registro operacional.**

---

## 5. Matriz de Requisitos

| Requisito APMO                      | Classificação                     |
| ----------------------------------- | --------------------------------- |
| Inventário de objetos               | Parcialmente implementado (25%)   |
| Identificador único                 | Implementado                      |
| Versão                              | Não implementado                  |
| Histórico                           | Não implementado                  |
| Exclusão lógica                     | Não implementado                  |
| Trilha de auditoria                 | Não implementado                  |
| EOV (snapshot operacional)          | Não implementado                  |
| Hash / cadeia de integridade        | Não implementado                  |
| Assinatura digital                  | Não implementado                  |
| Timestamp confiável                 | Não implementado                  |
| Versionamento com motivo/aprovação  | Não implementado                  |
| Cadeia de custódia de evidências    | Não implementado                  |
| Preservação de contexto relacional  | Implementado com limitações       |
| Preservação semântica               | Implementado com limitações       |
| ΔO — Delta Operacional              | Não implementado                  |
| Retificação com preservação         | Necessita revisão conceitual      |
| Inteligência temporal (as-of query) | Não implementado                  |
| Robustez (backup/PITR)              | Parcialmente implementado         |
| Modo offline                        | Não implementado                  |
| Controle de concorrência otimista   | Não implementado                  |
| Auditoria externa                   | Não implementado                  |

---

## 6. Backlog Priorizado de Gaps

### GAP-01 · Trilha de auditoria universal `audit_log` · **CRÍTICA**

1. **Diagnóstico técnico**: Nenhuma tabela mutável (`obras`, `zonas`, `fornecedores`, `user_roles`, `allowed_emails`) captura `UPDATE`/`DELETE`. Perde-se **quem, quando, valor anterior**.
2. **Risco operacional**: Alteração indevida ou maliciosa passa despercebida.
3. **Impacto na rastreabilidade**: Total — não há trilha.
4. **Impacto na decisão**: Decisões baseadas em dado alterado não podem ser reavaliadas.
5. **Impacto jurídico-probatório**: Severo. Em disputa contratual/TCU, o sistema não prova o histórico. Peça pericial inutilizada.
6. **Conceito arquitetural**: Tabela `audit_log` append-only com trigger genérica `AFTER INSERT/UPDATE/DELETE`, capturando `table_name`, `row_id`, `op`, `actor_id`, `at`, `old_row jsonb`, `new_row jsonb`, `prev_hash text`, `curr_hash text` (SHA-256 sobre `prev_hash || row jsonb || at || actor`).
7. **Contexto operacional**: Todas as tabelas de negócio; obrigatório antes de qualquer módulo de contrato/ECO.
8. **Modelo de dados**:
   ```text
   audit_log(id uuid pk, table_name text, row_id uuid, op text,
             actor_id uuid, at timestamptz default now(),
             old_row jsonb, new_row jsonb,
             prev_hash text, curr_hash text)
   ```
   RLS: leitura para `admin`, inserção apenas pelo trigger (SECURITY DEFINER).
9. **Fluxo**: trigger `AFTER` em cada tabela → insere no `audit_log` calculando `curr_hash = sha256(prev_hash || jsonb || at || actor)`.
10. **Validação**: query `SELECT * FROM audit_log WHERE row_id=? ORDER BY at` reconstrói ciclo de vida completo; verificação de hash percorre a cadeia.
11. **Dependências**: Atlas (edições de zonas), Control (edições de obras), Copiloto (decisões automatizadas devem gravar `actor='copiloto:<versão>'`).
12. **Prioridade**: **CRÍTICA** — pré-requisito para tudo.

### GAP-02 · Versionamento de entidades (`*_versions`) · **CRÍTICA**

1. **Diagnóstico**: `upsert` sobrescreve. Versão anterior perdida.
2. **Risco**: "Quem alterou o polígono da ZR-3?" — sem resposta.
3–5. **Impactos**: Sem histórico legal; sem base para ΔO; sem defesa em auditoria.
6. **Conceito**: Padrão *event-sourcing leve*. Tabela viva (`obras`) + tabela `obras_versions` append-only com `version int`, `valid_from`, `valid_to`, `reason`, `approved_by`, `snapshot jsonb`.
7. **Contexto**: Zonas, obras, fornecedores, cronograma (quando existir).
8. **Modelo**: `<tabela>_versions(id, entity_id, version, snapshot jsonb, reason text not null, edited_by, edited_at, approved_by, approved_at, valid_from, valid_to)`.
9. **Fluxo**: Edição via server fn cria nova versão + fecha `valid_to` da anterior; retificação exige `reason` obrigatório.
10. **Validação**: `SELECT snapshot FROM zonas_versions WHERE entity_id=? AND valid_from <= '2025-03-12' AND (valid_to IS NULL OR valid_to > '2025-03-12')` retorna o estado exato daquela data.
11. **Dependências**: base para Etapas 4, 8, 10 (as-of query).
12. **Prioridade**: **CRÍTICA**.

### GAP-03 · Storage de evidências com custódia · **ALTA**

1. **Diagnóstico**: Zero storage buckets. Fotos/vídeos/PDFs simplesmente não existem no sistema.
2–5. **Impactos**: Sem prova visual/documental; ECO/REO impossíveis; inspeção in loco não registra nada persistente.
6. **Conceito**: Bucket privado `evidencias` + tabela `evidencias(id, obra_id, atividade_id, tipo, path, hash_sha256, exif jsonb, gps point, captured_at, device, uploaded_by, uploaded_at)`. Cadeia de custódia = campos + assinatura + audit_log.
7. **Contexto**: Copiloto de Obras (captura em campo), Control (anexos de atividade).
8. **Modelo**: acima + `evidencia_access_log` para histórico de acessos.
9. **Fluxo**: Upload → cálculo do SHA-256 no cliente E servidor (comparação) → gravação de metadados → `audit_log`.
10. **Validação**: recomputar SHA-256 do arquivo baixado = hash gravado.
11. **Dependências**: Copiloto (câmera/GPS), Atlas (georreferência).
12. **Prioridade**: **ALTA**.

### GAP-04 · Snapshot operacional diário (EOV) · **ALTA**

1. **Diagnóstico**: Sem materialização de estado por data.
2–5. Sem `EOV`, "como estava em 12/03" é impossível.
6. **Conceito**: Job diário que produz `snapshot_operacional(obra_id, snapshot_date, payload jsonb, hash, prev_hash)` consolidando produção, cronograma, custos, equipes, ocorrências, indicadores daquele dia.
7. **Contexto**: Todas as obras ativas.
8. **Modelo**: acima + índice `(obra_id, snapshot_date)`.
9. **Fluxo**: cron 23:59 → server fn agrega e persiste → encadeia hash com snapshot anterior daquela obra.
10. **Validação**: `snapshot_operacional` para qualquer data devolve JSON completo reconstruível na UI.
11. **Dependências**: GAP-01, GAP-02.
12. **Prioridade**: **ALTA**.

### GAP-05 · Retificação com motivo obrigatório e preservação · **ALTA**

1. **Diagnóstico**: Não existe conceito de retificação.
2–5. Alterações silenciosas geram passivo jurídico.
6. **Conceito**: Server fn `retificar<Entidade>` distinta de `upsert`. Exige `reason` (min 20 caracteres), `approver_id` para campos críticos (custo, prazo, polígono). Cria nova versão em `*_versions`.
7. **Contexto**: Toda edição pós-publicação do registro.
8. **Modelo**: usa GAP-02.
9. **Fluxo**: UI força modal "Motivo da retificação" → server fn valida → cria versão → dispara audit.
10. **Validação**: nenhuma linha de `*_versions` com `reason IS NULL` após publicação.
11. **Dependências**: GAP-02.
12. **Prioridade**: **ALTA**.

### GAP-06 · Preservação semântica (ontologia + responsáveis) · **MÉDIA**

1. **Diagnóstico**: Registros sem motivo, sem responsável de negócio, sem classificação.
2–5. Cinco anos depois, dado sem contexto é dado morto.
6. **Conceito**: Tabelas `tipologia`, `classificacao`, `responsavel_negocio` + colunas `created_reason`, `owner_id`, `sistema_referencia` (para `x`, `y`).
7. **Contexto**: Todas as entidades de negócio.
8. **Modelo**: FKs + enum de tipologia.
9. **Fluxo**: Formulários exigem preenchimento.
10. **Validação**: `NOT NULL` nas colunas contextuais.
11. **Dependências**: independente.
12. **Prioridade**: **MÉDIA**.

### GAP-07 · Concorrência otimista (`version int`) · **MÉDIA**

1. **Diagnóstico**: Duas edições simultâneas → última vence silenciosamente.
2–5. Perda de trabalho, conflito não detectado.
6. **Conceito**: Coluna `version int` incrementada por trigger; `UPDATE ... WHERE id=? AND version=?` retorna 0 linhas se conflito.
7. **Contexto**: Todas as tabelas mutáveis.
8. **Modelo**: `+ version int not null default 1`.
9. **Fluxo**: UI envia `version` que leu; servidor rejeita se divergente e força reload.
10. **Validação**: teste concorrente de 2 sessões editando mesma linha.
11. **Dependências**: independente.
12. **Prioridade**: **MÉDIA**.

### GAP-08 · Vínculo `import_jobs → linha inserida` · **MÉDIA**

1. **Diagnóstico**: `import_jobs` sabe **que houve** import; não sabe **quais linhas** vieram dele.
2–5. Rollback de importação errada é manual e propenso a erro.
6. **Conceito**: Coluna `source_import_job_id uuid` em `zonas`, `obras`, `fornecedores`.
7–12. Prioridade **MÉDIA** (baixo custo, alto valor forense).

### GAP-09 · Timestamp confiável (âncora externa) · **BAIXA**

1. **Diagnóstico**: `now()` é confiável apenas se ninguém acessa o banco como superuser.
2–5. Em contexto probatório de alto valor, um perito questiona a hora.
6. **Conceito**: Batch diário envia hash do dia a um serviço RFC 3161 (ou OpenTimestamps sobre Bitcoin) e persiste o token.
7–12. Prioridade **BAIXA** (só justifica quando as etapas anteriores estiverem prontas).

### GAP-10 · Modo offline / sincronização · **BAIXA (para agora)**

1. **Diagnóstico**: Copiloto de Obras precisa funcionar em canteiros sem sinal — hoje o app quebra sem rede.
2–5. Perda de registro em campo = perda operacional real.
6. **Conceito**: PWA + IndexedDB + fila de sincronização com resolução de conflito por `version` (GAP-07).
7–12. Prioridade **BAIXA agora, ALTA quando Copiloto for iniciado**.

---

## 7. Roadmap Conceitual — do 8,5 ao 91+

```text
Fase 1 · Fundamento auditável        (meta IPMO 35)
   GAP-01  audit_log com hash encadeado
   GAP-07  version int (concorrência)
   GAP-08  source_import_job_id

Fase 2 · Versão e retificação        (meta IPMO 55)
   GAP-02  *_versions append-only
   GAP-05  retificação com motivo obrigatório
   GAP-06  ontologia + responsável de negócio

Fase 3 · Evidências e temporalidade  (meta IPMO 75)
   GAP-03  storage evidencias + custódia
   GAP-04  snapshot_operacional diário
   As-of queries expostas na UI (viewer "Como estava em __/__/____")

Fase 4 · Preservação verificável     (meta IPMO 91+)
   GAP-09  timestamp externo (RFC 3161 / OpenTimestamps)
   Assinaturas digitais (autor + aprovador) com PKI
   Exportação anual de "livro-razão operacional" assinado

Fase 5 · Campo e resiliência         (independente)
   GAP-10  modo offline no Copiloto
   Auditoria externa (endpoint read-only para peritos)
```

---

## 8. Anexos

### 8.1 Mapeamento por tabela existente

| Tabela            | Precisa `_versions`? | Precisa audit_log? | Precisa `source_import_job_id`? | Precisa `version int`? |
| ----------------- | -------------------- | ------------------ | -------------------------------- | ----------------------- |
| `zonas`           | **Sim (crítico)**    | Sim                | Sim                              | Sim                     |
| `obras`           | **Sim (crítico)**    | Sim                | Sim                              | Sim                     |
| `fornecedores`    | Sim                  | Sim                | Sim                              | Sim                     |
| `import_jobs`     | Não (append-only)    | Não (é a fonte)    | N/A                              | Não                     |
| `user_roles`      | Sim (histórico de permissão é obrigatório para reconstruir "quem podia o quê") | Sim | N/A | Não |
| `allowed_emails`  | Sim                  | Sim                | N/A                              | Não                     |

### 8.2 Lacunas de schema (o que **não existe** e precisa nascer)

`atividades`, `cronograma`, `presencas`, `producao_diaria`, `materiais`, `equipamentos`, `equipes`, `ocorrencias`, `ecos`, `reos`, `ico`, `evidencias`, `checklists`, `aprovacoes`, `assinaturas`, `audit_log`, `snapshot_operacional`, `<tabela>_versions` (para cada mutável).

### 8.3 Observação final

O OPERA hoje é um **excelente ponto de partida**: RLS bem configurado, papéis separados por tabela dedicada, import com log append-only, TanStack Start + Supabase estáveis. A arquitetura permite crescer no rumo do APMO **sem refazer o que já existe** — as tabelas atuais receberão colunas e triggers, e novas tabelas se somam ao redor. A distância até "memória operacional preservada" é grande em requisitos, mas o caminho é linear e cada Fase entrega valor forense verificável.

*Fim do relatório.*
