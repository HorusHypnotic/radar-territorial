
# Governança Operacional — telemetria viva do pipeline

Transformar o card "Conformidade & trilha" (hoje estático, 4 bullets LGPD/Auditoria/Acesso/Coleta) em um painel de **saúde sistêmica** alimentado por `ingestion_runs` + `urban_events`, sem esconder falhas.

## O que muda visualmente

Mesmo card (col-span-5, 2 row-span), nova hierarquia:

```text
┌─ Governança Operacional ─────────── Governança ┐
│                                                │
│ Última ingestão                                │
│ 06:00 BRT · Diário Oficial Goiânia             │
│ ✔ processado · 1.4s                            │
│                                                │
│ ── grid 2x2 ──                                 │
│ Sinais detectados      Confiança média         │
│ 14                     92%                     │
│                                                │
│ Revisão humana         Duplicidades            │
│ 3 pendentes            0 críticas              │
│                                                │
│ ── rodapé ──                                   │
│ LGPD · Auditoria · Trilha · APIs públicas      │
│            [ver execuções →]                   │
└────────────────────────────────────────────────┘
```

Quando o último run falhou ou foi parcial, o topo vira:
- `⚠ Extração parcial · 2 eventos requerem validação manual`
- `✕ Falha · Firecrawl timeout às 06:00` (com timestamp)

Honestidade sistêmica é regra: nunca mascarar erro, nunca mostrar "OK" falso quando `status != 'success'`.

## Como os números são calculados

Tudo via uma server function nova, sem tocar em `radar.server.ts` (mantém separação):

`src/lib/governance.functions.ts` → `getGovernanceTelemetry()`
- **Última run**: `ingestion_runs` ordenado por `started_at desc limit 1`, join com `data_sources` para o nome.
- **Sinais detectados**: `items_inserted` do último run.
- **Confiança média**: `avg(confidence)` em `urban_events` criados durante a janela `[started_at, finished_at]` do último run.
- **Revisão humana**: `count(*)` de `urban_events where needs_review = true`.
- **Duplicidades**: `errors` jsonb do último run filtrado por `type = 'duplicate'` (já gravamos isso no orquestrador) — fallback `0` se ainda não houver chave.
- **Latência**: `finished_at - started_at`.

Se não houver nenhuma run ainda → estado honesto "aguardando primeira execução · próxima 06:00 BRT".

## Arquivos

- **Novo** `src/lib/governance.functions.ts` — server fn `getGovernanceTelemetry` com `supabaseAdmin` (snapshot agregado, sem PII, segue padrão de `radar.functions.ts`).
- **Novo** `src/components/radar/GovernanceTelemetry.tsx` — componente que consome via `useServerFn` + `useQuery` (refetch 60s, igual ao dashboard snapshot).
- **Editado** `src/routes/index.tsx` — substituir o conteúdo do Card "Governança" pelo novo componente. Label do card vira `Telemetria`. Os 4 selos legais (LGPD/Auditoria/Acesso/Coleta) viram um rodapé inline compacto (chips), não somem.

## O que NÃO entra agora

- Feed territorial vivo ("[06:02] Novo alvará…") — fica como próximo passo natural, conforme você indicou.
- Histórico/sparkline de runs — só faz sentido depois de acumular dias de execução; placeholder visual seria desonesto.
- Métricas de cobertura urbana, latência média móvel — mesma razão.

## Critério de "pronto"

1. Card mostra dados reais do último `ingestion_runs` (ou estado vazio honesto).
2. Erro/parcial é exibido com ícone e mensagem, não escondido.
3. Confiança média e revisão pendente refletem o banco em tempo real (refetch 60s).
4. Selos LGPD/Auditoria continuam presentes (compliance narrativa preservada).
5. Zero mudança em `radar.server.ts`, zero mock.

Depois disso, próximo movimento sugerido: **Feed territorial vivo** lendo `urban_events` em ordem cronológica com tipo + bairro.
