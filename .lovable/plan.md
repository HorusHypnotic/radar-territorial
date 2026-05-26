
# Feed territorial vivo

Card novo no dashboard que mostra os últimos sinais urbanos detectados em ordem cronológica reversa, com tipo + bairro + horário. Faz a cidade "respirar" dentro do sistema.

## O que aparece

```text
┌─ Feed territorial ─────────────── ao vivo ┐
│                                            │
│ 06:05 · alvará        Setor Bueno      ✦  │
│ 06:04 · ART           Jardim Goiás        │
│ 06:02 · licitação     Setor Central       │
│ 05:58 · alvará        Setor Oeste         │
│ ...                                        │
│                                            │
│ [ver todos →]                              │
└────────────────────────────────────────────┘
```

- 8–10 eventos mais recentes
- Cada linha: `HH:mm · {tipo legível} · {bairro}`
- Ícone `✦` sutil em eventos das últimas 2h (sinal de "fresco")
- Severidade `high` → cor de destaque (ember); demais neutros
- Refetch a cada 30s
- Estado vazio honesto: "aguardando primeiros sinais · pipeline armado para 06:00 BRT"

## Como os dados saem

Nova server fn `getTerritorialFeed()` em `src/lib/feed.functions.ts`:
- `SELECT id, event_type, severity, bairro_label, occurred_at, confidence FROM urban_events ORDER BY occurred_at DESC LIMIT 12`
- Filtra `needs_review = false` (só sinais validados aparecem no feed público do dashboard; pendentes vivem no `/operador`)
- Mapeia `event_type` → label PT-BR (`permit` → "alvará", `art` → "ART", `bid` → "licitação", `supply_signal` → "fornecedor", etc.)
- Retorna DTO simples: `{ items: FeedItem[], generatedAt }`

## Arquivos

- **Novo** `src/lib/feed.functions.ts` — server fn `getTerritorialFeed` com `supabaseAdmin`.
- **Novo** `src/components/radar/TerritorialFeed.tsx` — componente com `useServerFn` + `useQuery` (30s refetch), formatação de hora em BRT, mapeamento de tipos.
- **Editado** `src/routes/index.tsx` — insere o card no grid. Localização sugerida: substituir/integrar ao `AlertFeed` atual (se for mock) ou adicionar como card adjacente ao de Governança.

## Decisão pendente sobre layout

Olhando o grid do dashboard, preciso confirmar onde encaixar:
- **A**: substituir o `AlertFeed` atual (se ele ainda for mock estático).
- **B**: criar um card novo em slot adjacente — pode exigir rearranjo do grid.

Vou inspecionar `src/routes/index.tsx` + `AlertFeed.tsx` no início da build e seguir a opção que preserve melhor a hierarquia visual atual (Telemetria + Feed lado a lado funciona bem narrativamente: "o que o motor fez" + "o que a cidade emitiu").

## O que NÃO entra agora

- Filtro por bairro/tipo (vira interação futura).
- Animação de entrada/pulse (pode ser próximo polish).
- Realtime via Supabase channels (refetch 30s é suficiente nesta fase; realtime só faz sentido quando volume justificar).
- Link clicável por evento para detalhe (não há rota de detalhe ainda).

## Critério de pronto

1. Card lista os últimos eventos reais do banco em ordem cronológica reversa.
2. Hora em BRT, tipo em PT-BR, bairro do `bairro_label`.
3. Estado vazio honesto quando não há eventos validados.
4. Refetch 30s, sem mock.
5. Eventos `needs_review = true` NÃO aparecem aqui (separação clara: feed = sinal limpo, `/operador` = fila bruta).
