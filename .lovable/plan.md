
# Pipeline real de ingestão — MVP em 1 leva

Objetivo: um sinal real do Diário Oficial de Goiânia, todo dia, navegando do crawler até virar `urban_event` geocodificado no mapa — passando por uma fila de validação humana. Esse é o "Hello World" do motor que falta.

---

## Escopo desta entrega

**Dentro:**
- Crawler diário do Diário Oficial do Município de Goiânia
- Extração estruturada (alvarás, habite-se, licitações, embargos) via Lovable AI
- Fila de revisão no `/operador` (eventos com `needs_review = true`)
- Geocoding automático + persistência em `urban_events` / `urban_entities`
- Dashboard lendo **só** dados reais (sem fallback decorativo)
- Trilha completa em `governance_logs` (toda extração, edição, aprovação)

**Fora (próximas levas):**
- CREA-GO / ARTs — exige login + captcha; tratado como **ingestão assistida** (operador cola ART manualmente, parser estrutura). Crawler automático fica para depois.
- Licitações estaduais / outras prefeituras.
- Motor de regras (Fase 3) e IA preditiva (Fase 4).

---

## Arquitetura

```text
pg_cron (06:00 diário)
    │
    ▼
POST /api/public/cron/ingest-diario-goiania     (server route, apikey header)
    │
    ├─► Firecrawl scrape do PDF/HTML do dia
    │
    ├─► Lovable AI (gemini-2.5-flash) → extrai array tipado:
    │     [{ tipo, titulo, endereco, empresa, rt, valor?, processo? }]
    │
    ├─► Para cada item:
    │     • dedupe (hash do trecho + data)
    │     • normaliza bairro (dicionário + fuzzy)
    │     • geocode (Nominatim) → urban_entities
    │     • insert urban_events (needs_review = confidence < 0.85)
    │     • governance_logs (action=auto_extracted)
    │
    └─► Retorna { ingested, queued_for_review, errors }
```

Fila humana: `/operador` ganha aba **Revisão** listando `urban_events.needs_review = true`. Operador aprova/edita/descarta → cada ação grava em `governance_logs`.

---

## Detalhes técnicos

**Banco (migration):**
- `data_sources`: seed `diario-oficial-goiania` (kind=`gazette`, reliability=0.9)
- `urban_events`: adicionar `dedupe_hash text unique` + `raw_excerpt text` + índice em `(occurred_at desc, needs_review)`
- `ingestion_runs` (nova): `id, source_id, started_at, finished_at, items_found, items_inserted, items_queued, errors jsonb, status` — visível no card Governança

**Server routes / functions:**
- `src/routes/api/public/cron/ingest-diario-goiania.ts` — handler do cron, valida `apikey`, dispara o pipeline
- `src/lib/ingestion/diario-goiania.server.ts` — fetch + parse via Firecrawl
- `src/lib/ingestion/extract.server.ts` — chamada Lovable AI com schema Zod (formato JSON estruturado)
- `src/lib/ingestion/normalize.server.ts` — bairro fuzzy match, dedupe hash
- `src/lib/review.functions.ts` — `listReviewQueue`, `approveEvent`, `rejectEvent`, `editEvent`

**Cron (via `supabase--insert`, não migration):**
```sql
select cron.schedule(
  'ingest-diario-goiania-daily', '0 9 * * *', -- 06:00 BRT
  $$ select net.http_post(
    url := 'https://project--d732a045-12c3-48cd-8a51-33ac2f52784e.lovable.app/api/public/cron/ingest-diario-goiania',
    headers := '{"Content-Type":"application/json","apikey":"<ANON>"}'::jsonb,
    body := '{}'::jsonb) $$
);
```

**Dependências externas:**
- **Firecrawl** (connector já suportado) — necessário porque o Diário sai como PDF/HTML pesado, com anti-bot. `fetch()` puro do Worker não dá conta.
- **Lovable AI Gateway** (já habilitado, `LOVABLE_API_KEY` presente) — `google/gemini-2.5-flash` para extração JSON estruturada.
- **Nominatim** (já em uso, gratuito).

**Frontend:**
- `/operador` → nova aba `Fila de Revisão` (tabela com trecho original + campos extraídos editáveis + ações)
- Dashboard `index.tsx` → remove qualquer fallback mockado; estado vazio honesto quando sem dados ("aguardando primeira execução do crawler — próxima às 06:00")
- Card Governança passa a mostrar última `ingestion_run` (sucesso/erro/itens)

---

## Critério de "pronto"

1. `pg_cron` rodou e há ≥ 1 registro em `ingestion_runs` com `status=success`
2. ≥ 1 `urban_events` real (não-seed) no banco, geocodificado, com pin visível no mapa
3. Fila de revisão funcional: operador consegue aprovar/editar/descartar
4. Trilha em `governance_logs` para cada ação (auto + humana)
5. Dashboard exibe contadores reais subindo após cada run

---

## O que preciso confirmar antes de implementar

1. **Conectar o Firecrawl** (Connectors → Firecrawl). É bloqueante para o crawler real do Diário. Sem ele, alternativa é cair para upload manual do PDF pelo operador (perde o "automático" do MVP).
2. **URL do Diário**: posso usar `https://www.goiania.go.gov.br/diariooficial/`? Se você tiver uma URL canônica preferida (estadual, ou um agregador), me diga.
3. **CREA/ART confirmado fora**: você ok em deixar ARTs para uma leva seguinte com modo assistido (paste do conteúdo), já que o portal CREA-GO exige login?
