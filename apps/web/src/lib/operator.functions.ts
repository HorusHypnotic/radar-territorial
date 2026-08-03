import { createServerFn } from "@tanstack/react-start";
import { z } from "zod";
import { requireSupabaseAuth } from "@/integrations/supabase/auth-middleware";
import { supabaseAdmin } from "@/integrations/supabase/client.server";
import { geocodeAddress } from "./geocode.server";

// --- Role helpers -----------------------------------------------------

export const getMyRoles = createServerFn({ method: "GET" })
  .middleware([requireSupabaseAuth])
  .handler(async ({ context }) => {
    const { userId } = context;
    const { data } = await supabaseAdmin
      .from("user_roles")
      .select("role")
      .eq("user_id", userId);
    return { roles: (data ?? []).map((r) => r.role as string) };
  });

/**
 * Bootstrap: if no admin exists yet, the current user becomes admin + operator.
 * Safe to call repeatedly; no-op once an admin exists.
 */
export const claimBootstrapAdmin = createServerFn({ method: "POST" })
  .middleware([requireSupabaseAuth])
  .handler(async ({ context }) => {
    const { userId } = context;
    const { count } = await supabaseAdmin
      .from("user_roles")
      .select("id", { count: "exact", head: true })
      .eq("role", "admin");
    if ((count ?? 0) > 0) return { claimed: false, reason: "admin_exists" as const };

    await supabaseAdmin.from("user_roles").insert([
      { user_id: userId, role: "admin" },
      { user_id: userId, role: "operator" },
    ]);
    await supabaseAdmin.from("governance_logs").insert({
      actor: userId,
      action: "bootstrap_admin_claimed",
      target_table: "user_roles",
      target_id: userId,
    });
    return { claimed: true };
  });

// --- New signal (assisted observation) --------------------------------

const NewSignalSchema = z.object({
  event_type: z.enum([
    "new_permit",
    "habite_se",
    "art",
    "bid",
    "observation",
    "supply_signal",
  ]),
  severity: z.enum(["low", "medium", "high"]).default("medium"),
  title: z.string().min(2).max(200),
  description: z.string().max(2000).optional(),
  address: z.string().min(3).max(300).optional(),
  neighborhood_slug: z.string().min(1).max(100).optional(),
  entity_type: z
    .enum(["obra", "empresa", "fornecedor", "loteamento", "galpao"]) 
    .optional(),
  entity_name: z.string().max(200).optional(),
  source_slug: z.string().min(1).max(100).default("obs-operacional"),
});

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

export const createSignal = createServerFn({ method: "POST" })
  .middleware([requireSupabaseAuth])
  .inputValidator((input: unknown) => NewSignalSchema.parse(input))
  .handler(async ({ data, context }) => {
    const { userId } = context;
    await requireOperator(userId);

    // Resolve source + neighborhood
    const { data: source } = await supabaseAdmin
      .from("data_sources")
      .select("id")
      .eq("slug", data.source_slug)
      .maybeSingle();

    let neighborhood_id: string | null = null;
    let bairro_label: string | null = null;
    if (data.neighborhood_slug) {
      const { data: n } = await supabaseAdmin
        .from("neighborhoods")
        .select("id,name")
        .eq("slug", data.neighborhood_slug)
        .maybeSingle();
      neighborhood_id = n?.id ?? null;
      bairro_label = n?.name ?? null;
    }

    // Geocode if address provided
    let lat: number | null = null;
    let lng: number | null = null;
    let geocode_confidence: number | null = null;
    if (data.address) {
      try {
        const geo = await geocodeAddress(`${data.address}, Goiânia, GO, Brasil`);
        if (geo) {
          lat = geo.lat;
          lng = geo.lng;
          geocode_confidence = geo.confidence;
        }
      } catch (err) {
        console.error("Geocoding failed:", err);
      }
    }

    // Create entity if a type was provided
    let entity_id: string | null = null;
    if (data.entity_type) {
      const { data: ent, error: entErr } = await supabaseAdmin
        .from("urban_entities")
        .insert({
          entity_type: data.entity_type,
          name: data.entity_name ?? data.title,
          address: data.address ?? null,
          neighborhood_id,
          lat,
          lng,
          geocode_confidence,
          geocode_provider: lat ? "nominatim" : null,
          metadata: { created_by: userId },
        })
        .select("id")
        .single();
      if (entErr) throw entErr;
      entity_id = ent.id;
    }

    const { data: event, error: evErr } = await supabaseAdmin
      .from("urban_events")
      .insert({
        event_type: data.event_type,
        severity: data.severity,
        source_id: source?.id ?? null,
        entity_id,
        neighborhood_id,
        bairro_label,
        title: data.title,
        description: data.description ?? null,
        lat,
        lng,
        payload: { input_by: userId },
        confidence: data.source_slug === "obs-operacional" ? 0.85 : 0.75,
        needs_review: false,
      })
      .select("id")
      .single();
    if (evErr) throw evErr;

    await supabaseAdmin.from("governance_logs").insert({
      actor: userId,
      action: "signal_created",
      target_table: "urban_events",
      target_id: event.id,
      source_id: source?.id ?? null,
      payload: { event_type: data.event_type, bairro: bairro_label },
    });

    return { event_id: event.id, entity_id, geocoded: lat !== null };
  });

export const listNeighborhoods = createServerFn({ method: "GET" }).handler(async () => {
  const { data } = await supabaseAdmin
    .from("neighborhoods")
    .select("slug,name")
    .order("name");
  return { neighborhoods: data ?? [] };
});

export const listSources = createServerFn({ method: "GET" }).handler(async () => {
  const { data } = await supabaseAdmin
    .from("data_sources")
    .select("slug,name,kind,reliability_score")
    .eq("active", true)
    .order("name");
  return { sources: data ?? [] };
});
