// Extração estruturada via Lovable AI Gateway (tool calling).
const AI_URL = "https://ai.gateway.lovable.dev/v1/chat/completions";

export type ExtractedItem = {
  event_type:
    | "new_permit"
    | "habite_se"
    | "art"
    | "bid"
    | "observation"
    | "supply_signal";
  severity: "low" | "medium" | "high";
  title: string;
  description?: string;
  address?: string;
  neighborhood?: string;
  company?: string;
  responsible_technical?: string;
  estimated_value_brl?: number;
  document_number?: string;
  raw_excerpt: string;
  confidence: number;
};

const SYSTEM = `Você é um analista de inteligência territorial.
Recebe trechos de um Diário Oficial municipal brasileiro e extrai
SOMENTE eventos relacionados à construção civil e expansão urbana:
- novos alvarás de construção (new_permit)
- habite-se / vistorias finais (habite_se)
- ARTs / registros técnicos (art)
- licitações de obras públicas (bid)
- embargos, autuações, observações relevantes (observation)
- sinais de fornecedor / nova operação (supply_signal)

Ignore aposentadorias, nomeações, exonerações, pagamentos administrativos,
matérias políticas e qualquer coisa não relacionada a obras/território.

Para cada evento, sempre preencha raw_excerpt com o trecho ORIGINAL
(curto, máx ~400 chars) e atribua confidence 0.0-1.0 honesta.`;

const TOOL = {
  type: "function" as const,
  function: {
    name: "extract_urban_events",
    description: "Extract urban-construction events from a gazette excerpt",
    parameters: {
      type: "object",
      properties: {
        items: {
          type: "array",
          items: {
            type: "object",
            properties: {
              event_type: {
                type: "string",
                enum: [
                  "new_permit",
                  "habite_se",
                  "art",
                  "bid",
                  "observation",
                  "supply_signal",
                ],
              },
              severity: { type: "string", enum: ["low", "medium", "high"] },
              title: { type: "string" },
              description: { type: "string" },
              address: { type: "string" },
              neighborhood: { type: "string" },
              company: { type: "string" },
              responsible_technical: { type: "string" },
              estimated_value_brl: { type: "number" },
              document_number: { type: "string" },
              raw_excerpt: { type: "string" },
              confidence: { type: "number" },
            },
            required: ["event_type", "severity", "title", "raw_excerpt", "confidence"],
            additionalProperties: false,
          },
        },
      },
      required: ["items"],
      additionalProperties: false,
    },
  },
};

export async function extractEvents(markdown: string): Promise<ExtractedItem[]> {
  const apiKey = process.env.LOVABLE_API_KEY;
  if (!apiKey) throw new Error("LOVABLE_API_KEY is not configured");

  // Limit input length to keep latency reasonable. Roughly 24k chars ~ 8k tokens.
  const content = markdown.slice(0, 24_000);

  const res = await fetch(AI_URL, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${apiKey}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      model: "google/gemini-2.5-flash",
      messages: [
        { role: "system", content: SYSTEM },
        { role: "user", content: `Trecho do Diário Oficial:\n\n${content}` },
      ],
      tools: [TOOL],
      tool_choice: { type: "function", function: { name: "extract_urban_events" } },
    }),
  });

  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new Error(`Lovable AI extract failed [${res.status}]: ${body.slice(0, 300)}`);
  }

  const json = (await res.json()) as {
    choices?: Array<{
      message?: {
        tool_calls?: Array<{ function?: { arguments?: string } }>;
      };
    }>;
  };

  const args = json.choices?.[0]?.message?.tool_calls?.[0]?.function?.arguments;
  if (!args) return [];
  try {
    const parsed = JSON.parse(args) as { items?: ExtractedItem[] };
    return Array.isArray(parsed.items) ? parsed.items : [];
  } catch {
    return [];
  }
}
