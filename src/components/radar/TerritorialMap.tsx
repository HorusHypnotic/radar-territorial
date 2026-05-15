import { useState } from "react";

type Pin = { id: string; x: number; y: number; type: "obra" | "alvara" | "habite"; bairro: string; label: string };

const PINS: Pin[] = [
  { id: "1", x: 28, y: 34, type: "obra", bairro: "Centro", label: "Edif. residencial 18 pav." },
  { id: "2", x: 52, y: 28, type: "alvara", bairro: "Jardim América", label: "Alvará comercial 1.240m²" },
  { id: "3", x: 64, y: 56, type: "obra", bairro: "Setor Industrial", label: "Galpão logístico" },
  { id: "4", x: 38, y: 62, type: "habite", bairro: "Vila Nova", label: "Habite-se conjunto 32 un." },
  { id: "5", x: 76, y: 38, type: "obra", bairro: "Setor Industrial", label: "Ampliação fabril" },
  { id: "6", x: 22, y: 70, type: "alvara", bairro: "Sul", label: "Loteamento 84 lotes" },
  { id: "7", x: 58, y: 72, type: "obra", bairro: "Vila Nova", label: "Reforma estrutural" },
  { id: "8", x: 44, y: 44, type: "habite", bairro: "Centro", label: "Habite-se torre única" },
];

const COLORS: Record<Pin["type"], string> = {
  obra: "var(--ember)",
  alvara: "oklch(0.74 0.17 45)",
  habite: "oklch(0.85 0.05 50)",
};

export function TerritorialMap() {
  const [hover, setHover] = useState<Pin | null>(null);

  return (
    <div className="relative h-full w-full overflow-hidden rounded-xl bg-surface">
      {/* base */}
      <div className="absolute inset-0 bg-grid opacity-40" />
      <div className="absolute inset-0 bg-radar-glow" />

      {/* fake streets */}
      <svg className="absolute inset-0 h-full w-full" viewBox="0 0 100 100" preserveAspectRatio="none">
        <path d="M0,30 Q40,28 60,40 T100,55" stroke="var(--grid)" strokeWidth="0.4" fill="none" />
        <path d="M0,68 Q30,60 55,70 T100,72" stroke="var(--grid)" strokeWidth="0.4" fill="none" />
        <path d="M20,0 Q22,40 35,60 T40,100" stroke="var(--grid)" strokeWidth="0.4" fill="none" />
        <path d="M70,0 Q68,30 75,55 T78,100" stroke="var(--grid)" strokeWidth="0.4" fill="none" />
      </svg>

      {/* radar sweep */}
      <div className="pointer-events-none absolute left-1/2 top-1/2 h-[140%] w-[140%] -translate-x-1/2 -translate-y-1/2">
        <div className="animate-radar-sweep h-full w-full origin-center" style={{
          background: "conic-gradient(from 0deg, transparent 0deg, color-mix(in oklab, var(--ember) 18%, transparent) 30deg, transparent 60deg)",
        }} />
      </div>

      {/* pins */}
      {PINS.map((p) => (
        <button
          key={p.id}
          className="group absolute -translate-x-1/2 -translate-y-1/2"
          style={{ left: `${p.x}%`, top: `${p.y}%` }}
          onMouseEnter={() => setHover(p)}
          onMouseLeave={() => setHover(null)}
        >
          <span className="absolute inset-0 -z-10 animate-ping-slow rounded-full" style={{ background: COLORS[p.type], opacity: 0.5 }} />
          <span className="block h-2.5 w-2.5 rounded-full ring-2 ring-background transition-transform group-hover:scale-150" style={{ background: COLORS[p.type] }} />
        </button>
      ))}

      {/* tooltip */}
      {hover && (
        <div
          className="pointer-events-none absolute z-10 -translate-x-1/2 -translate-y-[calc(100%+12px)] rounded-md border border-border bg-surface-elevated px-3 py-2 text-xs shadow-elevated"
          style={{ left: `${hover.x}%`, top: `${hover.y}%` }}
        >
          <div className="font-medium text-foreground">{hover.label}</div>
          <div className="text-muted-foreground">{hover.bairro} · {hover.type}</div>
        </div>
      )}

      {/* legend */}
      <div className="absolute bottom-3 left-3 flex gap-3 rounded-md border border-border bg-surface-elevated/80 px-3 py-2 text-[11px] backdrop-blur">
        {(["obra", "alvara", "habite"] as const).map((k) => (
          <div key={k} className="flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full" style={{ background: COLORS[k] }} />
            <span className="text-muted-foreground capitalize">{k === "habite" ? "habite-se" : k}</span>
          </div>
        ))}
      </div>

      {/* coords */}
      <div className="absolute right-3 top-3 font-mono text-[10px] tracking-wider text-muted-foreground">
        −16.6869° S · −49.2648° W
      </div>
    </div>
  );
}
