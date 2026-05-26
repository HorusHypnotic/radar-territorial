import { createServerFn } from "@tanstack/react-start";
import { supabaseAdmin } from "@/integrations/supabase/client.server";

export type FeedItem = {
  id: string;
  eventType: string;
  typeLabel: string;
  severity: string;
  bairro: string | null;
  occurredAt: string;
  confidence: number;
  source: string | null;
};

export type TerritorialFeed = {
  items: FeedItem[];
  generatedAt: string;
};

const TYPE_LABELS: Record<string, string> = {
  permit: "alvará",
  habite_se: "habite-se",
  art: "ART",
  bid: "licitação",
  edital: "edital",
  supply_signal: "fornecedor",
  inspection: "fiscalização",
  regularization: "regularização",
  works_start: "início de obra",
};

function labelOf(t: string) {
  return TYPE_LABELS[t] ?? t.replace(/_/g, " ");
}

export const getTerritorialFeed = createServerFn({ method: "GET" }).handler(
  async (): Promise<TerritorialFeed> => {
    const { data } = await supabaseAdmin
      .from("urban_events")
      .select(
        "id,event_type,severity,bairro_label,occurred_at,confidence,data_sources(name)",
      )
      .eq("needs_review", false)
      .order("occurred_at", { ascending: false })
      .limit(12);

    const items: FeedItem[] = (data ?? []).map((r) => {
      const row = r as {
        id: string;
        event_type: string;
        severity: string;
        bairro_label: string | null;
        occurred_at: string;
        confidence: number;
        data_sources: { name: string } | null;
      };
      return {
        id: row.id,
        eventType: row.event_type,
        typeLabel: labelOf(row.event_type),
        severity: row.severity,
        bairro: row.bairro_label,
        occurredAt: row.occurred_at,
        confidence: Number(row.confidence ?? 0),
        source: row.data_sources?.name ?? null,
      };
    });

    return { items, generatedAt: new Date().toISOString() };
  },
);
