import { createServerFn } from "@tanstack/react-start";
import { supabaseAdmin } from "@/integrations/supabase/client.server";

export type GovernanceTelemetry = {
  hasRun: boolean;
  lastRun: {
    id: string;
    status: string; // running | success | partial | failed
    startedAt: string;
    finishedAt: string | null;
    durationMs: number | null;
    sourceName: string | null;
    itemsFound: number;
    itemsInserted: number;
    itemsQueued: number;
    errorsCount: number;
    duplicatesCount: number;
    firstError: string | null;
  } | null;
  avgConfidence: number | null; // 0..1
  needsReviewCount: number;
  totalEvents: number;
  generatedAt: string;
};

export const getGovernanceTelemetry = createServerFn({ method: "GET" }).handler(
  async (): Promise<GovernanceTelemetry> => {
    const now = new Date().toISOString();

    const [{ data: runs }, reviewRes, totalRes] = await Promise.all([
      supabaseAdmin
        .from("ingestion_runs")
        .select("id,status,started_at,finished_at,items_found,items_inserted,items_queued,errors,source_id,data_sources(name)")
        .order("started_at", { ascending: false })
        .limit(1),
      supabaseAdmin
        .from("urban_events")
        .select("id", { count: "exact", head: true })
        .eq("needs_review", true),
      supabaseAdmin.from("urban_events").select("id", { count: "exact", head: true }),
    ]);

    const run = (runs ?? [])[0] as
      | {
          id: string;
          status: string;
          started_at: string;
          finished_at: string | null;
          items_found: number;
          items_inserted: number;
          items_queued: number;
          errors: unknown;
          data_sources: { name: string } | null;
        }
      | undefined;

    let avgConfidence: number | null = null;
    let lastRun: GovernanceTelemetry["lastRun"] = null;

    if (run) {
      const errorsArr = Array.isArray(run.errors) ? (run.errors as Array<Record<string, unknown>>) : [];
      const duplicatesCount = errorsArr.filter((e) => (e?.type ?? "") === "duplicate").length;
      const firstError =
        errorsArr.find((e) => (e?.type ?? "") !== "duplicate")?.message as string | undefined ?? null;

      const finishedAt = run.finished_at;
      const durationMs = finishedAt
        ? new Date(finishedAt).getTime() - new Date(run.started_at).getTime()
        : null;

      // Avg confidence for events created in the run window
      const upper = finishedAt ?? now;
      const { data: confRows } = await supabaseAdmin
        .from("urban_events")
        .select("confidence")
        .gte("created_at", run.started_at)
        .lte("created_at", upper);
      if (confRows && confRows.length > 0) {
        const sum = confRows.reduce((acc, r) => acc + Number((r as { confidence: number }).confidence ?? 0), 0);
        avgConfidence = sum / confRows.length;
      }

      lastRun = {
        id: run.id,
        status: run.status,
        startedAt: run.started_at,
        finishedAt,
        durationMs,
        sourceName: run.data_sources?.name ?? null,
        itemsFound: run.items_found ?? 0,
        itemsInserted: run.items_inserted ?? 0,
        itemsQueued: run.items_queued ?? 0,
        errorsCount: errorsArr.length - duplicatesCount,
        duplicatesCount,
        firstError,
      };
    }

    return {
      hasRun: Boolean(run),
      lastRun,
      avgConfidence,
      needsReviewCount: reviewRes.count ?? 0,
      totalEvents: totalRes.count ?? 0,
      generatedAt: now,
    };
  },
);
