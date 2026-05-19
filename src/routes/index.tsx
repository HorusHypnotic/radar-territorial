import { createFileRoute, Link } from "@tanstack/react-router";
import { useServerFn } from "@tanstack/react-start";
import { useQuery } from "@tanstack/react-query";
import { TerritorialMap } from "@/components/radar/TerritorialMap";
import { ScoreTerritorial } from "@/components/radar/ScoreTerritorial";
import { GrowthChart } from "@/components/radar/GrowthChart";
import { AlertFeed } from "@/components/radar/AlertFeed";
import { StatCard } from "@/components/radar/StatCard";
import { SupplyHeat } from "@/components/radar/SupplyHeat";
import { InstallButton } from "@/components/radar/InstallButton";
import { getDashboardSnapshot } from "@/lib/radar.functions";

export const Route = createFileRoute("/")({
  component: Dashboard,
});

function Card({
  children,
  className = "",
  span = "",
  label,
}: {
  children: React.ReactNode;
  className?: string;
  span?: string;
  label?: string;
}) {
  return (
    <section
      className={`relative overflow-hidden rounded-2xl border border-border bg-card p-5 shadow-elevated ${span} ${className}`}
    >
      {label && (
        <div className="absolute right-4 top-4 font-mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground">
          {label}
        </div>
      )}
      {children}
    </section>
  );
}

function Dashboard() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* Top bar */}
      <header className="sticky top-0 z-20 border-b border-border bg-background/80 backdrop-blur">
        <div className="mx-auto flex max-w-[1440px] items-center justify-between gap-3 px-4 py-3 sm:px-6 sm:py-4">
          <div className="flex min-w-0 items-center gap-4 lg:gap-8">
            <div className="flex min-w-0 items-center gap-2.5">
              <div className="relative h-7 w-7 shrink-0">
                <div className="absolute inset-0 rounded-full border border-ember/60" />
                <div className="absolute inset-1 rounded-full border border-ember/40" />
                <div className="absolute left-1/2 top-1/2 h-1.5 w-1.5 -translate-x-1/2 -translate-y-1/2 rounded-full bg-ember animate-pulse-dot" />
              </div>
              <div className="min-w-0 leading-none">
                <div className="truncate font-display text-lg sm:text-xl">Radar Urbano</div>
                <div className="hidden text-[10px] uppercase tracking-[0.18em] text-muted-foreground sm:block">
                  inteligência territorial
                </div>
              </div>
            </div>
            <nav className="hidden items-center gap-6 text-sm text-muted-foreground lg:flex">
              <a className="text-foreground" href="#">Panorama</a>
              <a href="#">Obras</a>
              <a href="#">Licenciamento</a>
              <a href="#">Econômico</a>
              <a href="#">Territorial</a>
            </nav>
          </div>
          <div className="flex shrink-0 items-center gap-2 sm:gap-3">
            <div className="hidden items-center gap-2 rounded-full border border-border bg-surface px-3 py-1.5 text-xs text-muted-foreground xl:flex">
              <span className="h-1.5 w-1.5 rounded-full bg-ember animate-pulse-dot" />
              Goiânia · GO
              <span className="text-border">|</span>
              <span className="font-mono">v0.1 · MVP</span>
            </div>
            <InstallButton />
            <button className="whitespace-nowrap rounded-full bg-ember-gradient px-3 py-1.5 text-xs font-medium text-primary-foreground shadow-glow transition hover:brightness-110 sm:px-4 sm:text-sm">
              <span className="hidden sm:inline">Acesso operacional</span>
              <span className="sm:hidden">Acessar</span>
            </button>
          </div>
        </div>
      </header>

      {/* Hero strip */}
      <section className="border-b border-border">
        <div className="mx-auto max-w-[1440px] px-4 py-8 sm:px-6 sm:py-10">
          <div className="flex flex-col items-start justify-between gap-8 lg:flex-row lg:items-end">
            <div className="max-w-3xl">
              <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-border bg-surface px-3 py-1 text-[10px] uppercase tracking-[0.16em] text-muted-foreground sm:text-[11px] sm:tracking-[0.18em]">
                <span className="h-1 w-1 rounded-full bg-ember" />
                <span className="hidden sm:inline">sistema de observabilidade territorial</span>
                <span className="sm:hidden">observabilidade territorial</span>
              </div>
              <h1 className="font-display text-[2.25rem] leading-[1.05] text-foreground sm:text-5xl md:text-6xl">
                Interprete o movimento da <em className="text-ember">construção civil</em>{" "}
                <span className="hidden md:inline"><br /></span>
                antes que ele se torne óbvio para o mercado.
              </h1>
              <p className="mt-5 max-w-xl text-sm text-muted-foreground sm:text-base">
                O Radar Urbano cruza diários oficiais, alvarás, ARTs, licitações e sinais econômicos
                em uma única leitura territorial — ética, auditável e juridicamente defensável.
              </p>
            </div>
            <div className="grid w-full grid-cols-3 gap-4 font-mono text-xs text-muted-foreground sm:flex sm:w-auto sm:gap-6">
              <Pill k="fontes" v="142" />
              <Pill k="bairros" v="86" />
              <Pill k="eventos/24h" v="1.284" />
            </div>
          </div>
        </div>
      </section>

      {/* Bento grid */}
      <main className="mx-auto max-w-[1440px] px-4 py-6 sm:px-6 sm:py-8">
        <div className="grid grid-cols-12 gap-3 sm:gap-4 lg:auto-rows-[minmax(0,_140px)]">
          {/* Map — large hero */}
          <Card span="col-span-12 lg:col-span-8 lg:row-span-4 min-h-[360px] sm:min-h-[420px] lg:min-h-0" label="Radar territorial">
            <div className="mb-3 flex flex-wrap items-baseline justify-between gap-x-4 pr-24 sm:pr-32">
              <h3 className="font-display text-xl sm:text-2xl">Mapa vivo · Goiânia</h3>
              <p className="text-[11px] text-muted-foreground sm:text-xs">8 sinais ativos</p>
            </div>
            <div className="h-[calc(100%-2.5rem)] min-h-[280px]">
              <TerritorialMap />
            </div>
          </Card>

          {/* Stats column */}
          <Card span="col-span-6 lg:col-span-4 lg:row-span-1 min-h-[140px]" label="24h">
            <StatCard label="Obras ativas" value="1.847" sub="+62 últimas 24h" trend="up" />
          </Card>
          <Card span="col-span-6 lg:col-span-4 lg:row-span-1 min-h-[140px]" label="07d">
            <StatCard label="Volume estimado" value="R$ 412M" sub="+18% semana" trend="up" />
          </Card>
          <Card span="col-span-12 lg:col-span-4 lg:row-span-2 min-h-[260px]" label="12m">
            <GrowthChart />
          </Card>

          {/* Score */}
          <Card span="col-span-12 lg:col-span-5 lg:row-span-3 min-h-[360px]" label="Score">
            <ScoreTerritorial />
          </Card>

          {/* Alerts */}
          <Card span="col-span-12 lg:col-span-7 lg:row-span-3 min-h-[360px]" label="Feed">
            <AlertFeed />
          </Card>

          {/* Supply heat */}
          <Card span="col-span-12 lg:col-span-7 lg:row-span-2 min-h-[260px]" label="Mercado">
            <SupplyHeat />
          </Card>

          {/* Compliance card */}
          <Card span="col-span-12 lg:col-span-5 lg:row-span-2 min-h-[260px]" label="Governança">
            <div className="flex h-full flex-col">
              <h3 className="font-display text-2xl">Conformidade & trilha</h3>
              <p className="mt-1 text-xs text-muted-foreground">
                Apenas dados públicos, observáveis e legalmente coletáveis.
              </p>
              <ul className="mt-4 space-y-2.5 text-sm">
                {[
                  ["LGPD", "Sem perfilamento pessoal · sem dados sensíveis"],
                  ["Auditoria", "Logs append-only · origem rastreável por evento"],
                  ["Acesso", "RBAC · MFA · separação de ambientes"],
                  ["Coleta", "APIs públicas · diários oficiais · transparência"],
                ].map(([k, v]) => (
                  <li key={k} className="flex items-start gap-3 border-t border-border/60 pt-2.5 first:border-0 first:pt-0">
                    <span className="mt-0.5 inline-flex w-20 shrink-0 font-mono text-[10px] uppercase tracking-wider text-ember">
                      {k}
                    </span>
                    <span className="text-muted-foreground">{v}</span>
                  </li>
                ))}
              </ul>
            </div>
          </Card>
        </div>

        {/* Modules strip */}
        <section className="mt-10 sm:mt-12">
          <div className="mb-5 flex flex-wrap items-baseline justify-between gap-2 sm:mb-6">
            <h2 className="font-display text-2xl sm:text-3xl">Módulos do sistema</h2>
            <span className="font-mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground">
              04 radares ativos · 01 em roadmap
            </span>
          </div>
          <div className="grid grid-cols-1 gap-px overflow-hidden rounded-2xl border border-border bg-border sm:grid-cols-2 lg:grid-cols-4">
            {MODULES.map((m, i) => (
              <div key={m.title} className="group bg-card p-5 transition hover:bg-surface-elevated sm:p-6">
                <div className="mb-5 flex items-center justify-between sm:mb-6">
                  <span className="font-mono text-[10px] tracking-[0.2em] text-muted-foreground">
                    0{i + 1}
                  </span>
                  <span className="text-ember opacity-0 transition group-hover:opacity-100">→</span>
                </div>
                <h3 className="font-display text-xl leading-tight sm:text-2xl">{m.title}</h3>
                <p className="mt-3 text-sm text-muted-foreground">{m.desc}</p>
                <ul className="mt-4 space-y-1 text-xs text-muted-foreground sm:mt-5">
                  {m.bullets.map((b) => (
                    <li key={b} className="flex gap-2">
                      <span className="text-ember">·</span>{b}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </section>

        {/* Roadmap */}
        <section className="mt-10 sm:mt-12">
          <div className="mb-5 flex flex-wrap items-baseline justify-between gap-2 sm:mb-6">
            <h2 className="font-display text-2xl sm:text-3xl">Roadmap</h2>
            <span className="font-mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground">
              4 fases
            </span>
          </div>
          <div className="relative grid grid-cols-1 gap-3 sm:grid-cols-2 sm:gap-4 lg:grid-cols-4">
            {ROADMAP.map((p, i) => (
              <div key={p.phase} className="relative rounded-xl border border-border bg-card p-5">
                <div className="mb-3 flex items-center justify-between">
                  <span className="font-mono text-[10px] uppercase tracking-[0.2em] text-muted-foreground">
                    {p.phase}
                  </span>
                  <span
                    className={`rounded-full px-2 py-0.5 text-[10px] uppercase tracking-wider ${
                      p.status === "ativo"
                        ? "bg-ember text-primary-foreground"
                        : p.status === "em curso"
                          ? "border border-ember/60 text-ember"
                          : "border border-border text-muted-foreground"
                    }`}
                  >
                    {p.status}
                  </span>
                </div>
                <h3 className="font-display text-xl">{p.title}</h3>
                <p className="mt-2 text-xs text-muted-foreground">{p.desc}</p>
                <div className="mt-4 font-mono text-[10px] text-muted-foreground">
                  {String(i + 1).padStart(2, "0")} / 04
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Footer */}
        <footer className="mt-12 border-t border-border pb-12 pt-8 sm:mt-16">
          <div className="flex flex-col gap-8 md:flex-row md:items-end md:justify-between">
            <div className="max-w-md">
              <div className="font-display text-xl sm:text-2xl">
                Ver uma obra <em className="text-muted-foreground">vs.</em> entender para onde a cidade vai.
              </div>
              <p className="mt-2 text-xs text-muted-foreground">
                Radar Urbano · sistema de observabilidade territorial aplicado à construção civil.
              </p>
            </div>
            <div className="grid w-full grid-cols-2 gap-6 text-xs sm:grid-cols-3 sm:gap-8 md:w-auto">
              {[
                ["Plataforma", ["Obras", "Licenciamento", "Econômico", "Territorial"]],
                ["Governança", ["LGPD", "Auditoria", "Trilha de origem", "Termos de uso"]],
                ["Empresa", ["Sobre", "Clientes", "Contato", "Imprensa"]],
              ].map(([t, items]) => (
                <div key={t as string}>
                  <div className="mb-3 font-mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground">
                    {t}
                  </div>
                  <ul className="space-y-1.5 text-foreground/80">
                    {(items as string[]).map((i) => (
                      <li key={i}><a href="#" className="hover:text-ember">{i}</a></li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          </div>
        </footer>
      </main>
    </div>
  );
}

function Pill({ k, v }: { k: string; v: string }) {
  return (
    <div className="flex flex-col">
      <span className="text-[10px] uppercase tracking-[0.18em]">{k}</span>
      <span className="font-display text-2xl text-foreground">{v}</span>
    </div>
  );
}

const MODULES = [
  {
    title: "Radar de obras",
    desc: "Mapeamento de obras privadas, públicas, ampliações, galpões e loteamentos.",
    bullets: ["mapa interativo", "timeline", "responsável técnico", "documentação vinculada"],
  },
  {
    title: "Radar de licenciamento",
    desc: "Alvarás, habite-se, regularizações e aprovações em ciclo formal.",
    bullets: ["início de ciclos", "regularizações em massa", "crescimento formal"],
  },
  {
    title: "Radar econômico",
    desc: "Cruza fornecedores, concreto, aço, drywall e locações comerciais.",
    bullets: ["aquecimento por região", "ticket médio", "consumo de insumos"],
  },
  {
    title: "Radar territorial",
    desc: "Vetores de expansão urbana, corredores e zonas em verticalização.",
    bullets: ["polos industriais", "áreas saturadas", "bairros emergentes"],
  },
];

const ROADMAP = [
  { phase: "Fase 01", title: "MVP", desc: "Mapa, diário oficial, alvarás e habite-se.", status: "ativo" },
  { phase: "Fase 02", title: "Inteligência territorial", desc: "Score urbano, heatmap e alertas operacionais.", status: "em curso" },
  { phase: "Fase 03", title: "IA operacional", desc: "Previsão de crescimento e detecção automática de padrões.", status: "previsto" },
  { phase: "Fase 04", title: "Escala regional", desc: "Múltiplas cidades, comparativos e benchmarking urbano.", status: "previsto" },
];
