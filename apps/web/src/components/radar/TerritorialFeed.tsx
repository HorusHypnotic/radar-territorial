import { useServerFn } from "@tanstack/react-start";
import { useQuery } from "@tanstack/react-query";
import { getTerritorialFeed, type FeedItem } from "@/lib/feed.functions";

function fmtBRT(iso: string) {
  return new Date(iso).toLocaleTimeString("pt-BR", {
    hour: "2-digit",
    minute: "2-digit",
    timeZone: "America/Sao_Paulo",
  });
}

function isFresh(iso: string) {
  return Date.now() - new Date(iso).getTime() < 2 * 60 * 60 * 1000;
}

export function TerritorialFeed() {
  const fetchFeed = useServerFn(getTerritorialFeed);
  const { data } = useQuery({
    queryKey: ["territorial-feed"],
    queryFn: () => fetchFeed(),
    refetchInterval: 30_000,
  });

  const items = data?.items ?? [];

  return (
    <div className="flex h-full flex-col">
      <div className="mb-4 flex items-baseline justify-between">
        <div>
          <h3 className="font-display text-2xl">Feed territorial</h3>
          <p className="text-xs text-muted-foreground">
            Sinais validados · ordem cronológica
          </p>
        </div>
        <div className="flex items-center gap-1.5 text-[10px] uppercase tracking-wider text-muted-foreground">
          <span className="animate-pulse-dot h-1.5 w-1.5 rounded-full bg-ember" />
          ao vivo
        </div>
      </div>

      {!data ? (
        <p className="text-xs text-muted-foreground">Carregando sinais…</p>
      ) : items.length === 0 ? (
        <div className="flex flex-1 items-center justify-center rounded-lg border border-dashed border-border bg-surface/40 p-6 text-center">
          <div>
            <div className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">
              aguardando primeiros sinais
            </div>
            <p className="mt-1.5 text-sm text-foreground">
              Pipeline armado para <span className="text-ember">06:00 BRT</span>
            </p>
            <p className="mt-1 text-xs text-muted-foreground">
              Eventos validados aparecem aqui em ordem cronológica.
            </p>
          </div>
        </div>
      ) : (
        <ul className="flex-1 space-y-px overflow-hidden">
          {items.map((it) => (
            <FeedRow key={it.id} item={it} />
          ))}
        </ul>
      )}
    </div>
  );
}

function FeedRow({ item }: { item: FeedItem }) {
  const fresh = isFresh(item.occurredAt);
  const severe = item.severity === "high" || item.severity === "critical";
  return (
    <li className="group flex items-center gap-3 border-b border-border/60 py-2.5 last:border-0">
      <span className="w-12 shrink-0 font-mono text-[11px] text-muted-foreground">
        {fmtBRT(item.occurredAt)}
      </span>
      <span
        className={`inline-flex w-20 shrink-0 justify-center rounded-sm border py-0.5 font-mono text-[9px] uppercase tracking-wider ${
          severe
            ? "border-ember/60 bg-ember/10 text-ember"
            : "border-border bg-surface text-muted-foreground"
        }`}
      >
        {item.typeLabel}
      </span>
      <span className="min-w-0 flex-1 truncate text-sm text-foreground">
        {item.bairro ?? "—"}
      </span>
      {fresh && (
        <span
          className="shrink-0 text-ember"
          title="detectado nas últimas 2 horas"
        >
          ✦
        </span>
      )}
    </li>
  );
}
