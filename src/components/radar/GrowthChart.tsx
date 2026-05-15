const DATA = [62, 58, 71, 65, 78, 74, 82, 79, 88, 84, 92, 96];
const MONTHS = ["J", "F", "M", "A", "M", "J", "J", "A", "S", "O", "N", "D"];

export function GrowthChart() {
  const max = Math.max(...DATA);
  const min = Math.min(...DATA);
  const w = 100;
  const h = 40;
  const points = DATA.map((v, i) => {
    const x = (i / (DATA.length - 1)) * w;
    const y = h - ((v - min) / (max - min)) * h;
    return [x, y] as const;
  });
  const path = points.map(([x, y], i) => (i === 0 ? `M${x},${y}` : `L${x},${y}`)).join(" ");
  const area = `${path} L${w},${h} L0,${h} Z`;

  return (
    <div className="flex h-full flex-col">
      <div className="mb-3">
        <h3 className="font-display text-2xl">Curva de aquecimento</h3>
        <p className="text-xs text-muted-foreground">Índice construtivo · 12 meses</p>
      </div>

      <div className="mb-2 flex items-baseline gap-3">
        <span className="font-display text-5xl text-foreground">+38<span className="text-ember">%</span></span>
        <span className="text-xs text-muted-foreground">vs. mesmo período anterior</span>
      </div>

      <div className="relative flex-1">
        <svg viewBox={`0 0 ${w} ${h + 8}`} preserveAspectRatio="none" className="h-full w-full">
          <defs>
            <linearGradient id="g1" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="var(--ember)" stopOpacity="0.4" />
              <stop offset="100%" stopColor="var(--ember)" stopOpacity="0" />
            </linearGradient>
          </defs>
          <path d={area} fill="url(#g1)" />
          <path d={path} fill="none" stroke="var(--ember)" strokeWidth="0.6" strokeLinecap="round" strokeLinejoin="round" />
          {points.map(([x, y], i) => (
            <circle key={i} cx={x} cy={y} r={i === points.length - 1 ? 0.9 : 0.4} fill="var(--ember)" />
          ))}
        </svg>
        <div className="absolute inset-x-0 bottom-0 flex justify-between font-mono text-[9px] text-muted-foreground">
          {MONTHS.map((m, i) => <span key={i}>{m}</span>)}
        </div>
      </div>
    </div>
  );
}
