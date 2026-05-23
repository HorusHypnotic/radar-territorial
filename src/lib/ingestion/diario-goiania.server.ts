// Coleta o conteúdo textual do Diário Oficial de Goiânia via Firecrawl.
// Usamos /v2/scrape com formato markdown — handles PDF/HTML e anti-bot.
const FIRECRAWL_BASE = "https://api.firecrawl.dev/v2";

const SEED_URL =
  "https://www.goiania.go.gov.br/diariooficial/";

export type ScrapedDoc = {
  source_url: string;
  markdown: string;
  fetched_at: string;
};

export async function fetchDiarioGoianiaToday(): Promise<ScrapedDoc> {
  const apiKey = process.env.FIRECRAWL_API_KEY;
  if (!apiKey) throw new Error("FIRECRAWL_API_KEY is not configured");

  const res = await fetch(`${FIRECRAWL_BASE}/scrape`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${apiKey}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      url: SEED_URL,
      formats: ["markdown", "links"],
      onlyMainContent: true,
      waitFor: 1500,
    }),
  });

  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new Error(`Firecrawl scrape failed [${res.status}]: ${body.slice(0, 300)}`);
  }

  const json = (await res.json()) as {
    success?: boolean;
    data?: { markdown?: string; metadata?: { sourceURL?: string } };
    markdown?: string;
    metadata?: { sourceURL?: string };
  };

  const markdown = json.data?.markdown ?? json.markdown ?? "";
  const sourceURL = json.data?.metadata?.sourceURL ?? json.metadata?.sourceURL ?? SEED_URL;

  if (!markdown || markdown.length < 200) {
    throw new Error(`Firecrawl returned empty/short content (${markdown.length} chars)`);
  }

  return {
    source_url: sourceURL,
    markdown,
    fetched_at: new Date().toISOString(),
  };
}
