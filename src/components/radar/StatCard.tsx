type Stat = { label: string; value: string; sub: string; trend?: "up" | "down" | "flat" };

export function StatCard({ label, value, sub, trend = "up" }: Stat) {
  const arrow = trend === "up" ? "↑" : trend === "down" ? "↓" : "→";
  const color = trend === "up" ? "text-ember" : trend === "down" ? "text-destructive" : "text-muted-foreground";
  return (
    <div className="flex h-full flex-col justify-between">
      <span className="text-[11px] uppercase tracking-[0.14em] text-muted-foreground">{label}</span>
      <div className="mt-2">
        <div className="font-display text-5xl leading-none text-foreground">{value}</div>
        <div className={`mt-2 flex items-center gap-1.5 text-xs ${color}`}>
          <span>{arrow}</span>
          <span className="text-muted-foreground">{sub}</span>
        </div>
      </div>
    </div>
  );
}
