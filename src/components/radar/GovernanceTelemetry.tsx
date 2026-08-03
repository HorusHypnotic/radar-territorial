import { useServerFn } from "@tanstack/react-start";
import { useQuery } from "@tanstack/react-query";
import { Link } from "@tanstack/react-router";
import { getGovernanceTelemetry } from "@/lib/governance.functions";

function fmtTime(iso: string) {
  return new Date(iso).toLocaleTimeString("pt-BR", {
    hour: "2-digit",
    minute: "2-digit",
    timeZone: "America/Sao_Paulo",
  });
}

function fmtDate(iso: string) {
  return new Date(iso).toLocaleDateString("pt-BR", { day: "2-digit", month: "2-digit" });
}

export function GovernanceTelemetry() {
  const fetchTelemetry = useServerFn(getGovernanceTelemetry);
  const { data } = useQuery({
    queryKey: ["governance-telemetry"],
    queryFn: () => fetchTelemetry(),
    refetchInterval: 60_000,
  });

  return (
    <div className="flex h-full flex-col">
      <div className="flex items-baseline justify-between gap-3">
        <h3 className="font-display text-2xl">Governança operacional</h3>
        <span className="font-mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground">
          telemetria viva
        </span>
      </div>

      {/* Estado de carregamento / vazio */}
      {!data ? (
        <p className="mt-3 text-xs text-muted-foreground">Carregando telemetria…</p>
      ) : !data.hasRun || !data.lastRun ? (
        <div className="mt-4 rounded-lg border border-dashed border-border bg-surface/40 p-4">
          <div className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">
            aguardando primeira execução
          </div>
          <p className="mt-1.5 text-sm text-foreground">
            Pipeline armado. Próxima coleta: <span className="text-ember">06:00 BRT</span>
          </p>
          <p className="mt-1 text-xs text-muted-foreground">
            Nenhum ciclo registrado ainda — métricas aparecem aqui após a primeira ingestão.
          </p>
        </div>
      ) : (
        <>
          <StatusStrip run={data.lastRun} />

          <div className="mt-4 grid grid-cols-2 gap-3 sm:gap-4">
            <Metric
              label="Sinais detectados"
              value={String(data.lastRun.itemsInserted)}
              sub={`${data.lastRun.itemsFound} brutos · ${data.lastRun.itemsQueued} em fila`}
            />
            <Metric
              label="Confiança média"
              value={data.avgConfidence != null ? `${Math.round(data.avgConfidence * 100)}%` : "—"}
              sub={data.avgConfidence != null ? "extração assistida" : "sem amostra"}
            />
            <Metric
              label="Revisão humana"
              value={String(data.needsReviewCount)}
              sub={data.needsReviewCount > 0 ? "pendentes" : "fila zerada"}
              accent={data.needsReviewCount > 0 ? "warn" : "ok"}
            />
            <Metric
              label="Duplicidades"
              value={String(data.lastRun.duplicatesCount)}
              sub={data.lastRun.duplicatesCount === 0 ? "0 críticas" : "deduplicadas"}
              accent="ok"
            />
          </div>
        </>
      )}

      {/* Rodapé: selos legais + link operador */}
      <div className="mt-auto pt-4">
        <div className="flex flex-wrap items-center gap-x-3 gap-y-1.5 border-t border-border/60 pt-3 font-mono text-[10px] uppercase tracking-[0.14em] text-muted-foreground">
          <span>LGPD</span>
          <span className="text-border">·</span>
          <span>auditoria append-only</span>
          <span className="text-border">·</span>
          <span>trilha de origem</span>
          <span className="text-border">·</span>
          <span>APIs públicas</span>
          <Link
            to="/operador"
            className="ml-auto text-ember normal-case tracking-normal hover:underline"
          >
            ver execuções →
          </Link>
        </div>
      </div>
    </div>
  );
}

function StatusStrip({ run }: { run: NonNullable<ReturnType<typeof useTelemetryRunType>> }) {
  const isSuccess = run.status === "success" && run.errorsCount === 0;
  const isPartial = run.status === "partial" || (run.status === "success" && run.errorsCount > 0);
  const isFailed = run.status === "failed";
  const isRunning = run.status === "running";

  const { icon, label, tone } = isFailed
    ? { icon: "✕", label: "Falha na execução", tone: "text-destructive" }
    : isPartial
      ? { icon: "⚠", label: "Extração parcial", tone: "text-amber-400" }
      : isRunning
        ? { icon: "◔", label: "Executando agora", tone: "text-ember" }
        : isSuccess
          ? { icon: "✔", label: "Processado com sucesso", tone: "text-ember" }
          : { icon: "·", label: run.status, tone: "text-muted-foreground" };

  const durStr = run.durationMs != null ? `${(run.durationMs / 1000).toFixed(1)}s` : "—";

  return (
    <div className="mt-3 rounded-lg border border-border bg-surface/40 p-3">
      <div className="flex items-baseline justify-between gap-3">
        <span className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">
          última ingestão
        </span>
        <span className="font-mono text-[10px] text-muted-foreground">
          {fmtDate(run.startedAt)} · {fmtTime(run.startedAt)} BRT
        </span>
      </div>
      <div className="mt-1.5 text-sm text-foreground">
        {run.sourceName ?? "Fonte desconhecida"}
      </div>
      <div className={`mt-1 flex items-center gap-2 text-xs ${tone}`}>
        <span>{icon}</span>
        <span>{label}</span>
        <span className="text-muted-foreground">· {durStr}</span>
      </div>
      {run.firstError && (
        <p className="mt-2 truncate text-[11px] text-muted-foreground" title={run.firstError}>
          {run.firstError}
        </p>
      )}
    </div>
  );
}

// helper type alias for StatusStrip prop typing
function useTelemetryRunType() {
  return null as unknown as import("@/lib/governance.functions").GovernanceTelemetry["lastRun"];
}

function Metric({
  label,
  value,
  sub,
  accent = "neutral",
}: {
  label: string;
  value: string;
  sub: string;
  accent?: "ok" | "warn" | "neutral";
}) {
  const subColor =
    accent === "warn" ? "text-amber-400" : accent === "ok" ? "text-ember" : "text-muted-foreground";
  return (
    <div className="rounded-lg border border-border/60 bg-card/60 p-3">
      <div className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">
        {label}
      </div>
      <div className="mt-1 font-display text-2xl leading-none text-foreground">{value}</div>
      <div className={`mt-1.5 text-[11px] ${subColor}`}>{sub}</div>
    </div>
  );
}
