import { createFileRoute, Link, useNavigate, useRouter } from "@tanstack/react-router";
import { useServerFn } from "@tanstack/react-start";
import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useAuth } from "@/hooks/use-auth";
import { supabase } from "@/integrations/supabase/client";
import {
  getMyRoles,
  claimBootstrapAdmin,
  createSignal,
  listNeighborhoods,
  listSources,
} from "@/lib/operator.functions";

export const Route = createFileRoute("/operador")({
  component: OperadorPage,
  head: () => ({ meta: [{ title: "Operador · Radar Urbano" }] }),
});

function OperadorPage() {
  const { user, loading } = useAuth();
  const navigate = useNavigate();
  const router = useRouter();

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

  const nbhQ = useQuery({ queryKey: ["nbh"], queryFn: () => nbhFn(), enabled: !!user });
  const srcQ = useQuery({ queryKey: ["src"], queryFn: () => srcFn(), enabled: !!user });

  const roles = rolesQ.data?.roles ?? [];
  const isOperator = roles.includes("operator") || roles.includes("admin");

  const [submitting, setSubmitting] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);

  async function handleBootstrap() {
    setErr(null);
    try {
      const res = await claimFn();
      if (res.claimed) {
        setMsg("Você agora é administrador. Recarregando…");
        await rolesQ.refetch();
      } else {
        setErr("Já existe um administrador. Peça acesso a ele.");
      }
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    }
  }

  async function handleSignal(e: React.FormEvent<HTMLFormElement>) {
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
      setMsg(`Sinal registrado${res.geocoded ? " e geocodificado" : ""}. id=${res.event_id.slice(0, 8)}…`);
      (e.target as HTMLFormElement).reset();
      router.invalidate();
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    } finally {
      setSubmitting(false);
    }
  }

  if (loading || !user) {
    return <div className="min-h-screen bg-background text-foreground p-8 text-sm text-muted-foreground">Carregando…</div>;
  }

  return (
    <div className="min-h-screen bg-background text-foreground">
      <header className="sticky top-0 z-20 border-b border-border bg-background/80 backdrop-blur">
        <div className="mx-auto flex max-w-5xl items-center justify-between gap-3 px-4 py-3 sm:px-6">
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

      <main className="mx-auto max-w-5xl px-4 py-8 sm:px-6">
        <div className="mb-6 flex flex-wrap items-baseline justify-between gap-3">
          <h1 className="font-display text-3xl sm:text-4xl">Painel do operador</h1>
          <div className="flex flex-wrap gap-1.5">
            {roles.length === 0 ? (
              <span className="rounded-full border border-border bg-surface px-2.5 py-0.5 text-[10px] uppercase tracking-wider text-muted-foreground">
                sem papel atribuído
              </span>
            ) : (
              roles.map((r) => (
                <span key={r} className="rounded-full border border-ember/60 px-2.5 py-0.5 text-[10px] uppercase tracking-wider text-ember">
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
              acesso ao sistema, reivindique o papel de administrador agora — funciona apenas se nenhum
              admin existir ainda.
            </p>
            <button
              onClick={handleBootstrap}
              className="mt-4 rounded-md bg-ember-gradient px-4 py-2 text-sm font-medium text-primary-foreground shadow-glow"
            >
              Reivindicar admin (apenas 1ª vez)
            </button>
          </div>
        )}

        {isOperator && (
          <section className="rounded-2xl border border-border bg-card p-5 sm:p-6">
            <div className="mb-4">
              <h2 className="font-display text-2xl">Novo sinal territorial</h2>
              <p className="text-xs text-muted-foreground">
                Tudo que entra aqui vira evento auditável em <code>urban_events</code>, com origem e
                trilha registradas em <code>governance_logs</code>.
              </p>
            </div>

            <form onSubmit={handleSignal} className="grid grid-cols-1 gap-3 sm:grid-cols-2">
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
                <input name="title" required minLength={2} maxLength={200} className={inputCls} placeholder="Ex.: Nova concreteira no Setor Industrial" />
              </Field>

              <Field label="Descrição" full>
                <textarea name="description" rows={3} maxLength={2000} className={inputCls} placeholder="Contexto, fonte secundária, link…" />
              </Field>

              <Field label="Bairro">
                <select name="neighborhood_slug" className={inputCls} defaultValue="">
                  <option value="">— selecione —</option>
                  {(nbhQ.data?.neighborhoods ?? []).map((n) => (
                    <option key={n.slug} value={n.slug}>{n.name}</option>
                  ))}
                </select>
              </Field>

              <Field label="Endereço (será geocodificado)">
                <input name="address" maxLength={300} className={inputCls} placeholder="Rua, nº, bairro" />
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

              <div className="sm:col-span-2 mt-2 flex flex-wrap items-center justify-between gap-3">
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
        )}

        <div className="mt-10 text-xs text-muted-foreground">
          <Link to="/" className="hover:text-ember">← voltar ao painel público</Link>
        </div>
      </main>
    </div>
  );
}

const inputCls =
  "w-full rounded-md border border-border bg-surface px-3 py-2 text-sm outline-none focus:border-ember/60";

function Field({ label, children, full }: { label: string; children: React.ReactNode; full?: boolean }) {
  return (
    <label className={`block ${full ? "sm:col-span-2" : ""}`}>
      <span className="mb-1 block text-[10px] uppercase tracking-[0.18em] text-muted-foreground">{label}</span>
      {children}
    </label>
  );
}
