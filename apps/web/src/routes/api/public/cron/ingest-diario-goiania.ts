// Public route called by pg_cron daily.
// Auth: requires Supabase `apikey` header (anon key bypasses Lovable preview auth via /api/public/*).
// This endpoint kicks off the Diário Oficial ingestion pipeline.
import { createFileRoute } from "@tanstack/react-router";
import { runDiarioGoianiaIngestion } from "@/lib/ingestion/orchestrator.server";

export const Route = createFileRoute("/api/public/cron/ingest-diario-goiania")({
  server: {
    handlers: {
      POST: async ({ request }) => {
        const apiKey = request.headers.get("apikey") ?? request.headers.get("x-api-key");
        const expected =
          process.env.SUPABASE_PUBLISHABLE_KEY ??
          process.env.SUPABASE_ANON_KEY ??
          process.env.VITE_SUPABASE_PUBLISHABLE_KEY;
        if (!apiKey || !expected || apiKey !== expected) {
          return new Response(JSON.stringify({ error: "unauthorized" }), {
            status: 401,
            headers: { "Content-Type": "application/json" },
          });
        }

        try {
          const result = await runDiarioGoianiaIngestion();
          return new Response(JSON.stringify(result), {
            status: 200,
            headers: { "Content-Type": "application/json" },
          });
        } catch (e) {
          console.error("ingest-diario-goiania failed:", e);
          return new Response(
            JSON.stringify({
              error: "ingestion_failed",
              detail: e instanceof Error ? e.message : String(e),
            }),
            { status: 500, headers: { "Content-Type": "application/json" } },
          );
        }
      },
      GET: async () =>
        new Response(JSON.stringify({ ok: true, note: "POST with apikey header to trigger" }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
    },
  },
});
