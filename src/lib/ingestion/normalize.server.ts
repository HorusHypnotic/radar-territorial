// Normalização de bairro e dedupe.
import { createHash } from "crypto";
import { supabaseAdmin } from "@/integrations/supabase/client.server";

let _cache: Array<{ id: string; slug: string; name: string; norm: string }> | null = null;

function norm(s: string) {
  return s
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[^a-z0-9 ]+/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

async function loadNeighborhoods() {
  if (_cache) return _cache;
  const { data } = await supabaseAdmin.from("neighborhoods").select("id,slug,name");
  _cache = (data ?? []).map((n) => ({
    id: n.id as string,
    slug: n.slug as string,
    name: n.name as string,
    norm: norm(n.name as string),
  }));
  return _cache;
}

export async function matchNeighborhood(
  hint: string | null | undefined,
): Promise<{ id: string; name: string; slug: string } | null> {
  if (!hint) return null;
  const list = await loadNeighborhoods();
  const target = norm(hint);
  if (!target) return null;
  // exact
  let hit = list.find((n) => n.norm === target);
  if (hit) return { id: hit.id, name: hit.name, slug: hit.slug };
  // contains
  hit = list.find((n) => target.includes(n.norm) || n.norm.includes(target));
  if (hit) return { id: hit.id, name: hit.name, slug: hit.slug };
  return null;
}

export function dedupeHash(parts: Array<string | null | undefined>): string {
  const payload = parts.map((p) => (p ?? "").trim().toLowerCase()).join("|");
  return createHash("sha256").update(payload).digest("hex").slice(0, 32);
}
