// Orquestrador: scrape -> extract -> normalize -> persist.
// Idempotente via dedupe_hash.
import { supabaseAdmin } from "@/integrations/supabase/client.server";
import { geocodeAddress } from "@/lib/geocode.server";
import { fetchDiarioGoianiaToday } from "./diario-goiania.server";
import { extractEvents, type ExtractedItem } from "./extract.server";
import { matchNeighborhood, dedupeHash } from "./normalize.server";

export type IngestionResult = {
  run_id: string;
  status: "success" | "partial" | "error";
  items_found: number;
  items_inserted: number;
  items_queued: number;
  errors: string[];
};

export async function runDiarioGoianiaIngestion(): Promise<IngestionResult> {
  // Resolve source id
  const { data: source } = await supabaseAdmin
    .from("data_sources")
    .select("id")
    .eq("slug", "diario-oficial-goiania")
    .maybeSingle();
  const sourceId = source?.id ?? null;

  // Open run
  const { data: runRow, error: runErr } = await supabaseAdmin
    .from("ingestion_runs")
    .insert({ source_id: sourceId, status: "running" })
    .select("id")
    .single();
  if (runErr || !runRow) throw new Error(`Could not open ingestion_run: ${runErr?.message}`);
  const runId = runRow.id as string;

  const errors: string[] = [];
  let itemsFound = 0;
  let inserted = 0;
  let queued = 0;
  let scrapedUrl: string | null = null;

  try {
    const doc = await fetchDiarioGoianiaToday();
    scrapedUrl = doc.source_url;
    let items: ExtractedItem[] = [];
    try {
      items = await extractEvents(doc.markdown);
    } catch (e) {
      errors.push(`extract: ${e instanceof Error ? e.message : String(e)}`);
    }
    itemsFound = items.length;

    for (const item of items) {
      try {
        const hash = dedupeHash([
          "diario-goiania",
          new Date().toISOString().slice(0, 10),
          item.event_type,
          item.title,
          item.address ?? "",
          item.document_number ?? "",
        ]);

        // Dedup check
        const { data: existing } = await supabaseAdmin
          .from("urban_events")
          .select("id")
          .eq("dedupe_hash", hash)
          .maybeSingle();
        if (existing) continue;

        const matched = await matchNeighborhood(item.neighborhood ?? item.address ?? null);

        let lat: number | null = null;
        let lng: number | null = null;
        let geoConf: number | null = null;
        if (item.address) {
          try {
            const geo = await geocodeAddress(`${item.address}, Goiânia, GO, Brasil`);
            if (geo) {
              lat = geo.lat;
              lng = geo.lng;
              geoConf = geo.confidence;
            }
          } catch (e) {
            errors.push(`geocode: ${e instanceof Error ? e.message : String(e)}`);
          }
          // Politeness: 1 req/s Nominatim
          await new Promise((r) => setTimeout(r, 1100));
        }

        // Optional entity (when we have name + location signal)
        let entityId: string | null = null;
        if (item.company || item.address) {
          const entityType =
            item.event_type === "bid"
              ? "obra"
              : item.event_type === "supply_signal"
                ? "fornecedor"
                : "obra";
          const { data: ent } = await supabaseAdmin
            .from("urban_entities")
            .insert({
              entity_type: entityType,
              name: item.company ?? item.title,
              address: item.address ?? null,
              neighborhood_id: matched?.id ?? null,
              company: item.company ?? null,
              responsible_technical: item.responsible_technical ?? null,
              lat,
              lng,
              geocode_confidence: geoConf,
              geocode_provider: lat ? "nominatim" : null,
              metadata: { source: "diario-oficial-goiania", run_id: runId },
            })
            .select("id")
            .single();
          entityId = ent?.id ?? null;
        }

        const needsReview = item.confidence < 0.85 || lat === null;

        const { error: evErr } = await supabaseAdmin.from("urban_events").insert({
          event_type: item.event_type,
          severity: item.severity,
          source_id: sourceId,
          entity_id: entityId,
          neighborhood_id: matched?.id ?? null,
          bairro_label: matched?.name ?? item.neighborhood ?? null,
          title: item.title,
          description: item.description ?? null,
          lat,
          lng,
          payload: {
            company: item.company,
            responsible_technical: item.responsible_technical,
            document_number: item.document_number,
            estimated_value_brl: item.estimated_value_brl,
            source_url: scrapedUrl,
            run_id: runId,
          },
          confidence: item.confidence,
          needs_review: needsReview,
          dedupe_hash: hash,
          raw_excerpt: item.raw_excerpt,
        });

        if (evErr) {
          errors.push(`insert: ${evErr.message}`);
          continue;
        }
        inserted += 1;
        if (needsReview) queued += 1;
      } catch (e) {
        errors.push(`item: ${e instanceof Error ? e.message : String(e)}`);
      }
    }
  } catch (e) {
    errors.push(`fetch: ${e instanceof Error ? e.message : String(e)}`);
  }

  const status: "success" | "partial" | "error" =
    errors.length === 0 ? "success" : inserted > 0 ? "partial" : "error";

  await supabaseAdmin
    .from("ingestion_runs")
    .update({
      finished_at: new Date().toISOString(),
      status,
      items_found: itemsFound,
      items_inserted: inserted,
      items_queued: queued,
      errors,
      meta: { source_url: scrapedUrl },
    })
    .eq("id", runId);

  await supabaseAdmin.from("governance_logs").insert({
    actor: null,
    action: "ingestion_run",
    target_table: "ingestion_runs",
    target_id: runId,
    source_id: sourceId,
    payload: { status, items_found: itemsFound, items_inserted: inserted, items_queued: queued },
  });

  return {
    run_id: runId,
    status,
    items_found: itemsFound,
    items_inserted: inserted,
    items_queued: queued,
    errors,
  };
}
