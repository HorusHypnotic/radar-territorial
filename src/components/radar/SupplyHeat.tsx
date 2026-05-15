const SUPPLIERS = [
  { name: "Concreto", value: 92, units: "m³ × 1k" },
  { name: "Aço CA-50", value: 78, units: "ton" },
  { name: "Drywall", value: 64, units: "m²" },
  { name: "Steel frame", value: 41, units: "ton" },
  { name: "Locação grua", value: 56, units: "diárias" },
];

export function SupplyHeat() {
  return (
    <div className="flex h-full flex-col">
      <div className="mb-4">
        <h3 className="font-display text-2xl">Radar econômico</h3>
        <p className="text-xs text-muted-foreground">Movimentação de fornecedores · 30d</p>
      </div>
      <div className="grid flex-1 grid-cols-5 items-end gap-3">
        {SUPPLIERS.map((s) => (
          <div key={s.name} className="flex h-full flex-col items-center justify-end gap-2">
            <span className="font-mono text-[10px] text-muted-foreground">{s.value}</span>
            <div className="relative w-full max-w-[28px] overflow-hidden rounded-sm bg-surface" style={{ height: "100%" }}>
              <div
                className="absolute inset-x-0 bottom-0 bg-ember-gradient"
                style={{ height: `${s.value}%` }}
              />
            </div>
            <span className="text-center text-[10px] leading-tight text-muted-foreground">{s.name}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
