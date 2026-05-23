import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useServerFn } from "@tanstack/react-start";
import { useEffect, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useAuth } from "@/hooks/use-auth";
import { supabase } from "@/integrations/supabase/client";
import {
  getMyRoles,
  claimBootstrapAdmin,
  createSignal,
  listNeighborhoods,
  listSources,
} from "@/lib/operator.functions";
import {
  listReviewQueue,
  approveEvent,
  rejectEvent,
  editEvent,
  triggerIngestion,
  listIngestionRuns,
} from "@/lib/review.functions";

export const Route = createFileRoute("/operador")({
  component: OperadorPage,
  head: () => ({ meta: [{ title: "Operador · Radar Urbano" }] }),
});

type Tab = "signal" | "review" | "runs";

function OperadorPage() {
  const { user, loading } = useAuth();
  const navigate = useNavigate();
  const qc = useQueryClient();

  const rolesFn = useServerFn(getMyRoles);
  const claimFn = useServerFn(claimBootstrapAdmin);
  const signalFn = useServerFn(createSignal);
  const nbhFn = useServerFn(listNeighborhoods);
  const srcFn = useServerFn(listSources);

  useEffect(() => {
    if (!loading && !user) navigate({ to: "/login" });
  }, [user, loading, navigate]);

  const rolesQ = useQuery({
    queryKey: ["my-roles", user?.id],
    queryFn: () => rolesFn(),
    enabled: !!user,
  });

  const roles = rolesQ.data?.roles ?? [];
  const isOperator = roles.includes("operator") || roles.includes("admin");

  const [tab, setTab] = useState<Tab>("review");
  const [bootErr, setBootErr] = useState<string | null>(null);

  async function handleBootstrap() {
    setBootErr(null);
    try {
      const res = await claimFn();
      if (res.claimed) await rolesQ.refetch();
      else setBootErr("Já existe um administrador. Peça acesso a ele.");
    } catch (e) {
      setBootErr(e instanceof Error ? e.message : String(e));
    }
  }

  if (loading || !user) {
    return (
      <div className="min-h-screen bg-background p-8 text-sm text-muted-foreground">
        Carregando…
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background text-foreground">
      <header className="sticky top-0 z-20 border-b border-border bg-background/80 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-3 px-4 py-3 sm:px-6">
          <Link to="/" className="flex items-center gap-2.5">
            <div className="relative h-6 w-6">
              <div className="absolute inset-0 rounded-full border border-ember/60" />
              <div className="absolute inset-1 rounded-full border border-ember/40" />
              <div className="absolute left-1/2 top-1/2 h-1 w-1 -translate-x-1/2 -translate-y-1/2 rounded-full bg-ember" />
            </div>
            <span className="font-display text-lg">Radar Urbano · Operador</span>
          </Link>
          <div className="flex items-center gap-3 text-xs text-muted-foreground">
            <span className="hidden sm:inline">{user.email}</span>
            <button
              onClick={async () => {
                await supabase.auth.signOut();
                navigate({ to: "/login" });
              }}
              className="rounded-md border border-border px-2.5 py-1 hover:bg-surface"
            >
              Sair
            </button>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-4 py-8 sm:px-6">
        <div className="mb-6 flex flex-wrap items-baseline justify-between gap-3">
          <h1 className="font-display text-3xl sm:text-4xl">Painel do operador</h1>
          <div className="flex flex-wrap gap-1.5">
            {roles.length === 0 ? (
              <span className="rounded-full border border-border bg-surface px-2.5 py-0.5 text-[10px] uppercase tracking-wider text-muted-foreground">
                sem papel atribuído
              </span>
            ) : (
              roles.map((r) => (
                <span
                  key={r}
                  className="rounded-full border border-ember/60 px-2.5 py-0.5 text-[10px] uppercase tracking-wider text-ember"
                >
                  {r}
                </span>
              ))
            )}
          </div>
        </div>

        {!isOperator && (
          <div className="mb-6 rounded-xl border border-border bg-surface p-5">
            <h2 className="font-display text-xl">Acesso ao operador</h2>
            <p className="mt-1 text-sm text-muted-foreground">
              Você ainda não tem papel <code>operator</code> ou <code>admin</code>. Se este é o primeiro
              acesso, reivindique o papel de administrador — funciona apenas se nenhum admin existir ainda.
            </p>
            {bootErr && <p className="mt-2 text-xs text-red-400">{bootErr}</p>}
            <button
              onClick={handleBootstrap}
              className="mt-4 rounded-md bg-ember-gradient px-4 py-2 text-sm font-medium text-primary-foreground shadow-glow"
            >
              Reivindicar admin (apenas 1ª vez)
            </button>
          </div>
        )}

        {isOperator && (
          <>
            <nav className="mb-6 flex flex-wrap gap-1 border-b border-border">
              {([
                ["review", "Fila de revisão"],
                ["signal", "Novo sinal"],
                ["runs", "Execuções"],
              ] as const).map(([id, label]) => (
                <button
                  key={id}
                  onClick={() => setTab(id)}
                  className={`-mb-px border-b-2 px-3 py-2 text-sm transition ${
                    tab === id
                      ? "border-ember text-foreground"
                      : "border-transparent text-muted-foreground hover:text-foreground"
                  }`}
                >
                  {label}
                </button>
              ))}
            </nav>

            {tab === "review" && <ReviewQueue onChange={() => qc.invalidateQueries()} />}
            {tab === "signal" && (
              <SignalForm signalFn={signalFn} nbhFn={nbhFn} srcFn={srcFn} userEnabled={!!user} />
            )}
            {tab === "runs" && <RunsPanel />}
          </>
        )}

        <div className="mt-10 text-xs text-muted-foreground">
          <Link to="/" className="hover:text-ember">← voltar ao painel público</Link>
        </div>
      </main>
    </div>
  );
}

// ---------- Review Queue ----------

function ReviewQueue({ onChange }: { onChange: () => void }) {
  const listFn = useServerFn(listReviewQueue);
  const approveFn = useServerFn(approveEvent);
  const rejectFn = useServerFn(rejectEvent);
  const editFn = useServerFn(editEvent);
  const triggerFn = useServerFn(triggerIngestion);

  const q = useQuery({ queryKey: ["review-queue"], queryFn: () => listFn() });
  const [busy, setBusy] = useState<string | null>(null);
  const [triggering, setTriggering] = useState(false);
  const [triggerMsg, setTriggerMsg] = useState<string | null>(null);

  async function act(fn: () => Promise<unknown>, id: string) {
    setBusy(id);
    try {
      await fn();
      await q.refetch();
      onChange();
    } finally {
      setBusy(null);
    }
  }

  async function runNow() {
    setTriggering(true);
    setTriggerMsg(null);
    try {
      const res = await triggerFn();
      setTriggerMsg(
        `Run ${res.status}: ${res.items_inserted} inseridos, ${res.items_queued} na fila.`,
      );
      await q.refetch();
      onChange();
    } catch (e) {
      setTriggerMsg(e instanceof Error ? e.message : String(e));
    } finally {
      setTriggering(false);
    }
  }

  const items = q.data?.items ?? [];

  return (
    <section className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="font-display text-2xl">Fila de revisão</h2>
          <p className="text-xs text-muted-foreground">
            Eventos extraídos automaticamente do Diário Oficial que precisam de validação humana
            (baixa confiança ou geocoding falhou).
          </p>
        </div>
        <button
          onClick={runNow}
          disabled={triggering}
          className="rounded-md border border-ember/60 px-3 py-1.5 text-xs font-medium text-ember hover:bg-ember/10 disabled:opacity-60"
        >
          {triggering ? "Rodando crawler…" : "Rodar crawler agora"}
        </button>
      </div>
      {triggerMsg && <p className="text-xs text-muted-foreground">{triggerMsg}</p>}

      {q.isLoading ? (
        <p className="text-sm text-muted-foreground">Carregando…</p>
      ) : items.length === 0 ? (
        <div className="rounded-xl border border-dashed border-border bg-surface/40 p-8 text-center">
          <p className="text-sm text-muted-foreground">
            Nenhum evento aguardando revisão. Rode o crawler para coletar do Diário Oficial.
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {items.map((it) => (
            <ReviewCard
              key={it.id}
              item={it}
              busy={busy === it.id}
              onApprove={() => act(() => approveFn({ data: { id: it.id } }), it.id)}
              onReject={() => act(() => rejectFn({ data: { id: it.id } }), it.id)}
              onEdit={(patch) =>
                act(() => editFn({ data: { id: it.id, ...patch } }), it.id)
              }
            />
          ))}
        </div>
      )}
    </section>
  );
}

type ReviewItem = {
  id: string;
  event_type: string;
  severity: string;
  title: string | null;
  description: string | null;
  bairro_label: string | null;
  raw_excerpt: string | null;
  confidence: number;
  occurred_at: string;
  lat: number | null;
  lng: number | null;
  data_sources?: { name: string } | null;
};

function ReviewCard({
  item,
  busy,
  onApprove,
  onReject,
  onEdit,
}: {
  item: ReviewItem;
  busy: boolean;
  onApprove: () => void;
  onReject: () => void;
  onEdit: (patch: { title?: string; bairro_label?: string }) => void;
}) {
  const [editing, setEditing] = useState(false);
  const [title, setTitle] = useState(item.title ?? "");
  const [bairro, setBairro] = useState(item.bairro_label ?? "");

  return (
    <article className="rounded-xl border border-border bg-card p-4">
      <div className="mb-2 flex flex-wrap items-center gap-2 text-[10px] uppercase tracking-wider">
        <span className="rounded-sm border border-border bg-surface px-1.5 py-0.5 font-mono text-muted-foreground">
          {item.event_type}
        </span>
        <span className="rounded-sm border border-border bg-surface px-1.5 py-0.5 font-mono text-muted-foreground">
          {item.severity}
        </span>
        <span className="text-muted-foreground">
          confiança {item.confidence.toFixed(2)}
        </span>
        {item.lat == null && (
          <span className="text-red-400">sem geocoding</span>
        )}
        <span className="ml-auto text-muted-foreground">
          {item.data_sources?.name ?? "—"}
        </span>
      </div>

      {editing ? (
        <div className="space-y-2">
          <input
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="w-full rounded-md border border-border bg-surface px-2.5 py-1.5 text-sm"
          />
          <input
            value={bairro}
            onChange={(e) => setBairro(e.target.value)}
            placeholder="Bairro"
            className="w-full rounded-md border border-border bg-surface px-2.5 py-1.5 text-sm"
          />
        </div>
      ) : (
        <>
          <h3 className="text-base text-foreground">{item.title ?? "(sem título)"}</h3>
          {item.bairro_label && (
            <p className="text-xs text-muted-foreground">Bairro: {item.bairro_label}</p>
          )}
        </>
      )}

      {item.raw_excerpt && (
        <p className="mt-2 line-clamp-3 border-l-2 border-border pl-3 text-xs italic text-muted-foreground">
          {item.raw_excerpt}
        </p>
      )}

      <div className="mt-3 flex flex-wrap gap-2">
        {editing ? (
          <>
            <button
              onClick={() => {
                onEdit({ title, bairro_label: bairro || undefined });
                setEditing(false);
              }}
              disabled={busy}
              className="rounded-md bg-ember-gradient px-3 py-1.5 text-xs font-medium text-primary-foreground disabled:opacity-60"
            >
              Salvar
            </button>
            <button
              onClick={() => setEditing(false)}
              className="rounded-md border border-border px-3 py-1.5 text-xs"
            >
              Cancelar
            </button>
          </>
        ) : (
          <>
            <button
              onClick={onApprove}
              disabled={busy}
              className="rounded-md bg-ember-gradient px-3 py-1.5 text-xs font-medium text-primary-foreground disabled:opacity-60"
            >
              Aprovar
            </button>
            <button
              onClick={() => setEditing(true)}
              disabled={busy}
              className="rounded-md border border-border px-3 py-1.5 text-xs hover:bg-surface"
            >
              Editar
            </button>
            <button
              onClick={onReject}
              disabled={busy}
              className="rounded-md border border-red-500/40 px-3 py-1.5 text-xs text-red-400 hover:bg-red-500/10"
            >
              Descartar
            </button>
          </>
        )}
      </div>
    </article>
  );
}

// ---------- Runs Panel ----------

function RunsPanel() {
  const fn = useServerFn(listIngestionRuns);
  const q = useQuery({ queryKey: ["ingestion-runs"], queryFn: () => fn() });
  const runs = q.data?.runs ?? [];

  return (
    <section className="space-y-3">
      <div>
        <h2 className="font-display text-2xl">Execuções do crawler</h2>
        <p className="text-xs text-muted-foreground">
          Trilha auditável de cada coleta do Diário Oficial — agendada diariamente às 06:00 BRT.
        </p>
      </div>
      {q.isLoading ? (
        <p className="text-sm text-muted-foreground">Carregando…</p>
      ) : runs.length === 0 ? (
        <p className="text-sm text-muted-foreground">Nenhuma execução registrada ainda.</p>
      ) : (
        <div className="overflow-hidden rounded-xl border border-border">
          <table className="w-full text-sm">
            <thead className="bg-surface text-[10px] uppercase tracking-wider text-muted-foreground">
              <tr>
                <th className="px-3 py-2 text-left">Início</th>
                <th className="px-3 py-2 text-left">Status</th>
                <th className="px-3 py-2 text-right">Encontrados</th>
                <th className="px-3 py-2 text-right">Inseridos</th>
                <th className="px-3 py-2 text-right">Na fila</th>
                <th className="px-3 py-2 text-left">Erros</th>
              </tr>
            </thead>
            <tbody>
              {runs.map((r) => (
                <tr key={r.id} className="border-t border-border">
                  <td className="px-3 py-2 font-mono text-xs">
                    {new Date(r.started_at).toLocaleString("pt-BR")}
                  </td>
                  <td className="px-3 py-2">
                    <span
                      className={`rounded-sm px-1.5 py-0.5 text-[10px] uppercase ${
                        r.status === "success"
                          ? "bg-ember/20 text-ember"
                          : r.status === "partial"
                            ? "bg-yellow-500/20 text-yellow-400"
                            : r.status === "error"
                              ? "bg-red-500/20 text-red-400"
                              : "bg-surface text-muted-foreground"
                      }`}
                    >
                      {r.status}
                    </span>
                  </td>
                  <td className="px-3 py-2 text-right font-mono text-xs">{r.items_found}</td>
                  <td className="px-3 py-2 text-right font-mono text-xs">{r.items_inserted}</td>
                  <td className="px-3 py-2 text-right font-mono text-xs">{r.items_queued}</td>
                  <td className="px-3 py-2 text-xs text-muted-foreground">
                    {Array.isArray(r.errors) && r.errors.length > 0
                      ? `${r.errors.length} erro(s)`
                      : "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}

// ---------- Signal Form ----------

function SignalForm({
  signalFn,
  nbhFn,
  srcFn,
  userEnabled,
}: {
  signalFn: ReturnType<typeof useServerFn<typeof createSignal>>;
  nbhFn: ReturnType<typeof useServerFn<typeof listNeighborhoods>>;
  srcFn: ReturnType<typeof useServerFn<typeof listSources>>;
  userEnabled: boolean;
}) {
  const nbhQ = useQuery({ queryKey: ["nbh"], queryFn: () => nbhFn(), enabled: userEnabled });
  const srcQ = useQuery({ queryKey: ["src"], queryFn: () => srcFn(), enabled: userEnabled });
  const [submitting, setSubmitting] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);

  async function handle(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setErr(null);
    setMsg(null);
    setSubmitting(true);
    try {
      const fd = new FormData(e.currentTarget);
      const payload = {
        event_type: fd.get("event_type") as
          | "new_permit" | "habite_se" | "art" | "bid" | "observation" | "supply_signal",
        severity: (fd.get("severity") as "low" | "medium" | "high") || "medium",
        title: String(fd.get("title") || ""),
        description: String(fd.get("description") || "") || undefined,
        address: String(fd.get("address") || "") || undefined,
        neighborhood_slug: String(fd.get("neighborhood_slug") || "") || undefined,
        entity_type: (String(fd.get("entity_type") || "") || undefined) as
          | "obra" | "empresa" | "fornecedor" | "loteamento" | "galpao" | undefined,
        entity_name: String(fd.get("entity_name") || "") || undefined,
        source_slug: String(fd.get("source_slug") || "obs-operacional"),
      };
      const res = await signalFn({ data: payload });
      setMsg(`Sinal registrado${res.geocoded ? " e geocodificado" : ""}.`);
      (e.target as HTMLFormElement).reset();
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <section className="rounded-2xl border border-border bg-card p-5 sm:p-6">
      <div className="mb-4">
        <h2 className="font-display text-2xl">Novo sinal territorial</h2>
        <p className="text-xs text-muted-foreground">
          Coleta humana assistida. Vira evento auditável em <code>urban_events</code>.
        </p>
      </div>

      <form onSubmit={handle} className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        <Field label="Tipo do evento">
          <select name="event_type" required className={inputCls}>
            <option value="observation">observation — observação urbana</option>
            <option value="new_permit">new_permit — alvará</option>
            <option value="habite_se">habite_se — habite-se</option>
            <option value="art">art — ART</option>
            <option value="bid">bid — licitação</option>
            <option value="supply_signal">supply_signal — sinal econômico</option>
          </select>
        </Field>

        <Field label="Severidade">
          <select name="severity" defaultValue="medium" className={inputCls}>
            <option value="low">low</option>
            <option value="medium">medium</option>
            <option value="high">high</option>
          </select>
        </Field>

        <Field label="Título" full>
          <input
            name="title"
            required
            minLength={2}
            maxLength={200}
            className={inputCls}
            placeholder="Ex.: Nova concreteira no Setor Industrial"
          />
        </Field>

        <Field label="Descrição" full>
          <textarea
            name="description"
            rows={3}
            maxLength={2000}
            className={inputCls}
            placeholder="Contexto, fonte secundária, link…"
          />
        </Field>

        <Field label="Bairro">
          <select name="neighborhood_slug" className={inputCls} defaultValue="">
            <option value="">— selecione —</option>
            {(nbhQ.data?.neighborhoods ?? []).map((n) => (
              <option key={n.slug} value={n.slug}>{n.name}</option>
            ))}
          </select>
        </Field>

        <Field label="Endereço (geocodificado)">
          <input
            name="address"
            maxLength={300}
            className={inputCls}
            placeholder="Rua, nº, bairro"
          />
        </Field>

        <Field label="Tipo de entidade (opcional)">
          <select name="entity_type" className={inputCls} defaultValue="">
            <option value="">— nenhuma —</option>
            <option value="obra">obra</option>
            <option value="empresa">empresa</option>
            <option value="fornecedor">fornecedor</option>
            <option value="loteamento">loteamento</option>
            <option value="galpao">galpão</option>
          </select>
        </Field>

        <Field label="Nome da entidade (opcional)">
          <input name="entity_name" maxLength={200} className={inputCls} />
        </Field>

        <Field label="Fonte" full>
          <select name="source_slug" defaultValue="obs-operacional" className={inputCls}>
            {(srcQ.data?.sources ?? []).map((s) => (
              <option key={s.slug} value={s.slug}>
                {s.name} · conf. {Number(s.reliability_score).toFixed(2)}
              </option>
            ))}
          </select>
        </Field>

        <div className="mt-2 flex flex-wrap items-center justify-between gap-3 sm:col-span-2">
          {msg && <p className="text-xs text-ember">{msg}</p>}
          {err && <p className="text-xs text-red-400">{err}</p>}
          <button
            type="submit"
            disabled={submitting}
            className="ml-auto rounded-md bg-ember-gradient px-5 py-2 text-sm font-medium text-primary-foreground shadow-glow disabled:opacity-60"
          >
            {submitting ? "Registrando…" : "Registrar sinal"}
          </button>
        </div>
      </form>
    </section>
  );
}

const inputCls =
  "w-full rounded-md border border-border bg-surface px-3 py-2 text-sm outline-none focus:border-ember/60";

function Field({
  label,
  children,
  full,
}: {
  label: string;
  children: React.ReactNode;
  full?: boolean;
}) {
  return (
    <label className={`block ${full ? "sm:col-span-2" : ""}`}>
      <span className="mb-1 block text-[10px] uppercase tracking-[0.18em] text-muted-foreground">
        {label}
      </span>
      {children}
    </label>
  );
}
