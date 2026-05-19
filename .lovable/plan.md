# Radar Urbano — do mock à infraestrutura real

Você está certo: o produto não é o dashboard, é o **motor de interpretação territorial**. A sequência abaixo segue exatamente sua ordem (pipeline → automação → IA) e respeita a estratégia semi-automatizada do MVP.

Antes de escrever uma linha de código novo, preciso **ativar o Lovable Cloud** (Postgres + Auth + Storage + Server Functions). É a fundação de tudo abaixo. Sem isso, qualquer "pipeline real" continua sendo mock.

---

## Fase 0 — Fundação (ativar agora)

1. Habilitar **Lovable Cloud**.
2. Criar o schema base (migrations):
   - `data_sources` — origem, licitude, retenção, responsável, score de confiabilidade
   - `urban_entities` — obras, empresas, bairros (com PostGIS `geography(Point)`)
   - `urban_events` — tabela-coração: `event_type`, `bairro`, `severity`, `source_id`, `payload jsonb`, `occurred_at`, `geom`
   - `permits` (alvarás), `licenses` (habite-se), `technical_records` (ARTs)
   - `territorial_scores` — histórico por bairro/semana
   - `governance_logs` — append-only, trilha auditável
3. RLS em todas: leitura pública só de agregados; escrita só via service role nos jobs.
4. Habilitar extensão `postgis` para geocoding/heatmap reais.

> Observação: PostGIS roda no Postgres do Cloud. Se algum recurso geoespacial não estiver disponível, caímos para `lat/lng` em colunas numéricas + cálculo em SQL — mesma UX, sem bloqueio.

---

## Fase 1 — Ingestão semi-automatizada (o MVP forte)

Seguindo sua matriz **Automático × Assistido**:

**Automático (server functions + cron via pg_cron):**
- Diário Oficial (Goiânia/GO): fetch → parse heurístico → extração de campos (endereço, tipo, empresa, RT) → `urban_events`.
- Geocoding: Nominatim como default (gratuito), com chave Mapbox opcional via secret. Cache em `urban_entities.geom`.
- Normalização de bairro (dicionário + fuzzy match).

**Assistido (UI operacional interna):**
- Rota `/operador` protegida por auth + role `operator`:
  - Form de "novo sinal" (concreteira nova, galpão, loteamento, expansão comercial).
  - Fila de eventos extraídos do Diário com baixa confiança → operador valida/corrige/descarta.
  - Cada ação grava em `governance_logs`.

---

## Fase 2 — Interpretação (substituir cada mock por cálculo real)

Cada card do dashboard atual ganha uma **server function** que lê do Postgres:

| Card | Substituição |
|---|---|
| Mapa territorial | `urban_entities` com `geom`, filtros por `event_type` e janela temporal |
| Score territorial | `score = 3·alvarás + 2·ARTs + 4·licitações + 2·obras + 5·crescimento_comercial` em janela de 7/30 dias, persistido em `territorial_scores` por job semanal |
| Feed ao vivo | `urban_events ORDER BY occurred_at DESC` + Supabase Realtime |
| Curva de aquecimento | `count(*) by week_trunc(occurred_at)` últimos 12 períodos |
| Radar econômico | agregação por categoria de fornecedor (input assistido + sinais automáticos) |
| Governança | leitura de `data_sources` + `governance_logs` (origem rastreável por evento) |

Stats do topo (`Obras ativas`, `Volume estimado`, `Eventos/24h`, `Fontes`, `Bairros`) viram `count`/`sum` reais.

---

## Fase 3 — Motor de regras (alertas)

- Tabela `alert_rules` (DSL simples em jsonb): condição + janela + severidade.
- Job a cada 15 min: avalia regras sobre `urban_events` agregados; gera `urban_events` do tipo `alert` (o feed já mostra).
- Exemplo embutido: *"bairro com +30% eventos e +15% ARTs em 30d"*.

---

## Fase 4 — IA operacional (depois, não agora)

- Detecção de padrões e previsão de aquecimento via Lovable AI Gateway sobre as séries de `territorial_scores`.
- Classificação automática de trechos do Diário Oficial (hoje heurística → depois LLM).

---

## Detalhes técnicos

- **Backend**: TanStack `createServerFn` + server routes em `src/routes/api/public/*` para webhooks/cron callers. Sem Edge Functions Supabase.
- **Jobs agendados**: `pg_cron` no Postgres chamando endpoint público `/api/public/cron/*` com HMAC (segredo `CRON_SECRET`).
- **Crawler do Diário Oficial**: roda dentro de server function (fetch + parse). Se houver bloqueio anti-bot, plano B é upload manual de PDF/HTML pelo operador.
- **Geocoding**: provider abstraído (`geocode(address) → {lat,lng,confidence}`); Nominatim default, Mapbox quando `MAPBOX_TOKEN` existir.
- **Realtime**: `supabase.channel('urban_events').on('postgres_changes', ...)` no `AlertFeed` e atualização incremental do mapa.
- **Confiabilidade por fonte**: cada `urban_events.source_id` referencia `data_sources.reliability_score` (0–1) — exibido no card e usado como peso no Score.

---

## O que eu preciso de você antes de começar

1. **Confirmação para ativar Lovable Cloud** (passo bloqueante).
2. **Cidade-piloto**: confirmamos Goiânia/GO? URL do Diário Oficial preferida (Municipal? Estadual? Ambos)?
3. **Escopo desta primeira entrega**: prefere que eu execute **Fase 0 + Fase 1 (Diário Oficial + geocoding + operador) + Fase 2 (cards lendo do banco)** numa primeira leva, deixando regras/alertas (Fase 3) e IA (Fase 4) para depois? Recomendo fortemente esse recorte — é onde o produto deixa de ser bonito e passa a interpretar de verdade.
4. **Mapbox token**: tem? Se não, começamos com Nominatim (grátis, rate-limited) e plugamos Mapbox quando quiser.

Assim que você confirmar, começo pela Fase 0 + schema + uma primeira ingestão do Diário Oficial ponta-a-ponta — um único evento real navegando do crawler até o pin no mapa. Esse é o "Hello World" do motor.