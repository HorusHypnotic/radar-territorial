type Alert = {
  id: string;
  time: string;
  type: "alvara" | "habite" | "edital" | "art";
  title: string;
  bairro: string;
  source: string;
};

const ALERTS: Alert[] = [
  { id: "a1", time: "agora", type: "alvara", title: "Novo alvará — torre 24 pav.", bairro: "Centro", source: "Diário Oficial" },
  { id: "a2", time: "12 min", type: "edital", title: "Edital de pavimentação R$ 14,2M", bairro: "Sul", source: "Portal Transparência" },
  { id: "a3", time: "47 min", type: "art", title: "ART registrada — estrutural", bairro: "Setor Industrial", source: "CREA" },
  { id: "a4", time: "1 h", type: "habite", title: "Habite-se — conjunto 32 un.", bairro: "Vila Nova", source: "Prefeitura" },
  { id: "a5", time: "2 h", type: "alvara", title: "Loteamento aprovado · 84 lotes", bairro: "Sul", source: "Diário Oficial" },
  { id: "a6", time: "3 h", type: "edital", title: "Concorrência drenagem urbana", bairro: "Jardim América", source: "Licitações" },
];

const TYPE_LABEL: Record<Alert["type"], string> = {
  alvara: "ALVARÁ",
  habite: "HABITE-SE",
  edital: "EDITAL",
  art: "ART",
};

export function AlertFeed() {
  return (
    <div className="flex h-full flex-col">
      <div className="mb-4 flex items-baseline justify-between">
        <div>
          <h3 className="font-display text-2xl">Sinais ao vivo</h3>
          <p className="text-xs text-muted-foreground">Coleta pública · trilha auditável</p>
        </div>
        <div className="flex items-center gap-1.5 text-[10px] uppercase tracking-wider text-muted-foreground">
          <span className="animate-pulse-dot h-1.5 w-1.5 rounded-full bg-ember" />
          ao vivo
        </div>
      </div>

      <div className="flex-1 space-y-px overflow-hidden">
        {ALERTS.map((a) => (
          <div key={a.id} className="group flex items-start gap-3 border-b border-border/60 py-2.5 last:border-0">
            <span className="mt-1 inline-flex w-16 shrink-0 justify-center rounded-sm border border-border bg-surface py-0.5 font-mono text-[9px] tracking-wider text-muted-foreground">
              {TYPE_LABEL[a.type]}
            </span>
            <div className="min-w-0 flex-1">
              <div className="truncate text-sm text-foreground">{a.title}</div>
              <div className="truncate text-[11px] text-muted-foreground">
                {a.bairro} · <span className="italic">{a.source}</span>
              </div>
            </div>
            <span className="shrink-0 font-mono text-[10px] text-muted-foreground">{a.time}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
