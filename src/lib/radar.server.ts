// Server-only helpers that read curated, non-PII aggregates for the dashboard.
import { supabaseAdmin } from "@/integrations/supabase/client.server";

export type Snapshot = {
  stats: {
    activeEntities: number;
    eventsLast24h: number;
    sourcesCount: number;
    neighborhoodsCount: number;
    estimatedVolumeBrl: number;
    deltaEvents24h: number;
  };
  scores: Array<{
    name: string;
    slug: string;
    score: number;
    trend: number;
    events: number;
  }>;
  growthCurve: Array<{ label: string; value: number }>;
  events: Array<{
    id: string;
    event_type: string;
    severity: string;
    title: string | null;
    description: string | null;
    bairro_label: string | null;
    source: string | null;
    occurred_at: string;
  }>;
  mapPins: Array<{
    id: string;
    entity_type: string;
    name: string | null;
    lat: number;
    lng: number;
    neighborhood: string | null;
  }>;
  sources: Array<{
    slug: string;
    name: string;
    kind: string;
    reliability_score: number;
    active: boolean;
  }>;
  generatedAt: string;
};

export async function buildSnapshot(): Promise<Snapshot> {
  const now = new Date();
  const since24h = new Date(now.getTime() - 24 * 60 * 60 * 1000).toISOString();
  const since48h = new Date(now.getTime() - 48 * 60 * 60 * 1000).toISOString();
  const since12w = new Date(now.getTime() - 12 * 7 * 24 * 60 * 60 * 1000);

  const [
    entitiesCount,
    events24h,
    eventsPrev24h,
    sourcesAll,
    neighborhoodsAll,
    recentEvents,
    pins,
    growthRows,
    scoreRows,
  ] = await Promise.all([
    supabaseAdmin.from("urban_entities").select("id", { count: "exact", head: true }).eq("status", "active"),
    supabaseAdmin.from("urban_events").select("id", { count: "exact", head: true }).gte("occurred_at", since24h),
    supabaseAdmin
      .from("urban_events")
      .select("id", { count: "exact", head: true })
      .gte("occurred_at", since48h)
      .lt("occurred_at", since24h),
    supabaseAdmin.from("data_sources").select("slug,name,kind,reliability_score,active"),
    supabaseAdmin.from("neighborhoods").select("id,name,slug"),
    supabaseAdmin
      .from("urban_events")
      .select(
        "id,event_type,severity,title,description,bairro_label,occurred_at,source_id,data_sources(name)",
      )
      .order("occurred_at", { ascending: false })
      .limit(15),
    supabaseAdmin
      .from("urban_entities")
      .select("id,entity_type,name,lat,lng,neighborhoods(name)")
      .not("lat", "is", null)
      .not("lng", "is", null)
      .eq("status", "active")
      .limit(200),
    supabaseAdmin
      .from("urban_events")
      .select("occurred_at")
      .gte("occurred_at", since12w.toISOString()),
    supabaseAdmin
      .from("urban_events")
      .select("neighborhood_id,event_type,neighborhoods(name,slug)")
      .gte("occurred_at", new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000).toISOString()),
  ]);

  // Growth curve: bucket into 12 weeks
  const buckets = Array.from({ length: 12 }).map((_, i) => {
    const start = new Date(since12w.getTime() + i * 7 * 24 * 60 * 60 * 1000);
    return { start, count: 0 };
  });
  for (const r of growthRows.data ?? []) {
    const t = new Date((r as { occurred_at: string }).occurred_at).getTime();
    const idx = Math.min(11, Math.max(0, Math.floor((t - since12w.getTime()) / (7 * 24 * 60 * 60 * 1000))));
    buckets[idx].count += 1;
  }
  const monthLetters = ["J", "F", "M", "A", "M", "J", "J", "A", "S", "O", "N", "D"];
  const growthCurve = buckets.map((b) => ({
    label: monthLetters[b.start.getMonth()],
    value: b.count,
  }));

  // Scores per neighborhood: count events in the last 30d as a proxy.
  const weights: Record<string, number> = {
    new_permit: 3,
    habite_se: 2,
    art: 2,
    bid: 4,
    observation: 2,
    supply_signal: 5,
    alert: 1,
  };
  const scoreMap = new Map<
    string,
    { name: string; slug: string; score: number; events: number }
  >();
  for (const r of scoreRows.data ?? []) {
    const row = r as {
      neighborhood_id: string | null;
      event_type: string;
      neighborhoods: { name: string; slug: string } | null;
    };
    if (!row.neighborhoods) continue;
    const cur =
      scoreMap.get(row.neighborhoods.slug) ?? {
        name: row.neighborhoods.name,
        slug: row.neighborhoods.slug,
        score: 0,
        events: 0,
      };
    cur.score += weights[row.event_type] ?? 1;
    cur.events += 1;
    scoreMap.set(row.neighborhoods.slug, cur);
  }
  const scores = [...scoreMap.values()]
    .sort((a, b) => b.score - a.score)
    .slice(0, 5)
    .map((s) => ({ ...s, trend: 0 }));

  const events = (recentEvents.data ?? []).map((e) => {
    const row = e as {
      id: string;
      event_type: string;
      severity: string;
      title: string | null;
      description: string | null;
      bairro_label: string | null;
      occurred_at: string;
      data_sources: { name: string } | null;
    };
    return {
      id: row.id,
      event_type: row.event_type,
      severity: row.severity,
      title: row.title,
      description: row.description,
      bairro_label: row.bairro_label,
      source: row.data_sources?.name ?? null,
      occurred_at: row.occurred_at,
    };
  });

  const mapPins = (pins.data ?? []).map((p) => {
    const row = p as {
      id: string;
      entity_type: string;
      name: string | null;
      lat: number;
      lng: number;
      neighborhoods: { name: string } | null;
    };
    return {
      id: row.id,
      entity_type: row.entity_type,
      name: row.name,
      lat: row.lat,
      lng: row.lng,
      neighborhood: row.neighborhoods?.name ?? null,
    };
  });

  const e24 = events24h.count ?? 0;
  const ePrev = eventsPrev24h.count ?? 0;

  return {
    stats: {
      activeEntities: entitiesCount.count ?? 0,
      eventsLast24h: e24,
      sourcesCount: (sourcesAll.data ?? []).filter((s) => s.active).length,
      neighborhoodsCount: (neighborhoodsAll.data ?? []).length,
      // Rough proxy: each active entity ~ R$ 250k of estimated movement.
      // Will be replaced by a real estimator in Fase 3.
      estimatedVolumeBrl: (entitiesCount.count ?? 0) * 250_000,
      deltaEvents24h: e24 - ePrev,
    },
    scores,
    growthCurve,
    events,
    mapPins,
    sources: (sourcesAll.data ?? []).map((s) => ({
      slug: s.slug as string,
      name: s.name as string,
      kind: s.kind as string,
      reliability_score: Number(s.reliability_score),
      active: Boolean(s.active),
    })),
    generatedAt: now.toISOString(),
  };
}
