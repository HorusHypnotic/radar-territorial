// Server functions for the operator review queue + manual trigger.
import { createServerFn } from "@tanstack/react-start";
import { z } from "zod";
import { requireSupabaseAuth } from "@/integrations/supabase/auth-middleware";
import { supabaseAdmin } from "@/integrations/supabase/client.server";
import { runDiarioGoianiaIngestion } from "@/lib/ingestion/orchestrator.server";

async function requireOperator(userId: string) {
  const { data } = await supabaseAdmin
    .from("user_roles")
    .select("role")
    .eq("user_id", userId);
  const roles = (data ?? []).map((r) => r.role as string);
  if (!roles.includes("operator") && !roles.includes("admin")) {
    throw new Error("Forbidden: operator role required");
  }
}

export const listReviewQueue = createServerFn({ method: "GET" })
  .middleware([requireSupabaseAuth])
  .handler(async ({ context }) => {
    await requireOperator(context.userId);
    const { data } = await supabaseAdmin
      .from("urban_events")
      .select(
        "id,event_type,severity,title,description,bairro_label,raw_excerpt,confidence,occurred_at,lat,lng,payload,data_sources(name)",
      )
      .eq("needs_review", true)
      .order("occurred_at", { ascending: false })
      .limit(50);
    return { items: data ?? [] };
  });

export const approveEvent = createServerFn({ method: "POST" })
  .middleware([requireSupabaseAuth])
  .inputValidator((d: unknown) => z.object({ id: z.string().uuid() }).parse(d))
  .handler(async ({ data, context }) => {
    await requireOperator(context.userId);
    await supabaseAdmin
      .from("urban_events")
      .update({
        needs_review: false,
        reviewed_by: context.userId,
        reviewed_at: new Date().toISOString(),
      })
      .eq("id", data.id);
    await supabaseAdmin.from("governance_logs").insert({
      actor: context.userId,
      action: "event_approved",
      target_table: "urban_events",
      target_id: data.id,
    });
    return { ok: true };
  });

export const rejectEvent = createServerFn({ method: "POST" })
  .middleware([requireSupabaseAuth])
  .inputValidator((d: unknown) =>
    z.object({ id: z.string().uuid(), reason: z.string().max(500).optional() }).parse(d),
  )
  .handler(async ({ data, context }) => {
    await requireOperator(context.userId);
    await supabaseAdmin.from("urban_events").delete().eq("id", data.id);
    await supabaseAdmin.from("governance_logs").insert({
      actor: context.userId,
      action: "event_rejected",
      target_table: "urban_events",
      target_id: data.id,
      payload: { reason: data.reason ?? null },
    });
    return { ok: true };
  });

export const editEvent = createServerFn({ method: "POST" })
  .middleware([requireSupabaseAuth])
  .inputValidator((d: unknown) =>
    z
      .object({
        id: z.string().uuid(),
        title: z.string().min(2).max(200).optional(),
        description: z.string().max(2000).optional(),
        bairro_label: z.string().max(120).optional(),
        severity: z.enum(["low", "medium", "high"]).optional(),
      })
      .parse(d),
  )
  .handler(async ({ data, context }) => {
    await requireOperator(context.userId);
    const { id, ...patch } = data;
    await supabaseAdmin.from("urban_events").update(patch).eq("id", id);
    await supabaseAdmin.from("governance_logs").insert({
      actor: context.userId,
      action: "event_edited",
      target_table: "urban_events",
      target_id: id,
      payload: patch,
    });
    return { ok: true };
  });

export const triggerIngestion = createServerFn({ method: "POST" })
  .middleware([requireSupabaseAuth])
  .handler(async ({ context }) => {
    await requireOperator(context.userId);
    const result = await runDiarioGoianiaIngestion();
    await supabaseAdmin.from("governance_logs").insert({
      actor: context.userId,
      action: "ingestion_triggered_manually",
      target_table: "ingestion_runs",
      target_id: result.run_id,
      payload: { items_inserted: result.items_inserted, status: result.status },
    });
    return result;
  });

export const listIngestionRuns = createServerFn({ method: "GET" })
  .middleware([requireSupabaseAuth])
  .handler(async ({ context }) => {
    await requireOperator(context.userId);
    const { data } = await supabaseAdmin
      .from("ingestion_runs")
      .select("id,started_at,finished_at,status,items_found,items_inserted,items_queued,errors,meta")
      .order("started_at", { ascending: false })
      .limit(10);
    return { runs: data ?? [] };
  });
