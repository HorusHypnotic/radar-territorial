type Bairro = { name: string; score: number; trend: number; obras: number };

const BAIRROS: Bairro[] = [
  { name: "Setor Industrial", score: 91, trend: 12, obras: 47 },
  { name: "Centro", score: 82, trend: 6, obras: 38 },
  { name: "Jardim América", score: 74, trend: -3, obras: 22 },
  { name: "Vila Nova", score: 68, trend: 9, obras: 19 },
  { name: "Sul", score: 54, trend: 2, obras: 12 },
];

export function ScoreTerritorial() {
  return (
    <div className="flex h-full flex-col">
      <div className="mb-4 flex items-baseline justify-between">
        <div>
          <h3 className="font-display text-2xl">Score territorial</h3>
          <p className="text-xs text-muted-foreground">Índice composto · atualizado há 4 min</p>
        </div>
        <span className="rounded-full border border-border bg-surface px-2.5 py-0.5 text-[10px] uppercase tracking-wider text-muted-foreground">
          07 dias
        </span>
      </div>

      <div className="flex-1 space-y-3">
        {BAIRROS.map((b) => (
          <div key={b.name} className="group">
            <div className="mb-1.5 flex items-center justify-between text-sm">
              <span className="font-medium">{b.name}</span>
              <div className="flex items-center gap-3 font-mono text-xs">
                <span className={b.trend >= 0 ? "text-ember" : "text-muted-foreground"}>
                  {b.trend >= 0 ? "↑" : "↓"} {Math.abs(b.trend)}%
                </span>
                <span className="text-muted-foreground">{b.obras} obras</span>
                <span className="w-8 text-right text-base text-foreground">{b.score}</span>
              </div>
            </div>
            <div className="h-1.5 overflow-hidden rounded-full bg-surface">
              <div
                className="h-full bg-ember-gradient transition-all duration-500"
                style={{ width: `${b.score}%` }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
