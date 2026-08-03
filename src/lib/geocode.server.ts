// Lightweight geocoder using Nominatim (no key needed).
// Caller is responsible for rate-limiting (1 req/s per Nominatim policy).
export type GeocodeResult = {
  lat: number;
  lng: number;
  confidence: number;
  provider: "nominatim";
  display_name: string;
} | null;

export async function geocodeAddress(address: string): Promise<GeocodeResult> {
  const url = new URL("https://nominatim.openstreetmap.org/search");
  url.searchParams.set("q", address);
  url.searchParams.set("format", "json");
  url.searchParams.set("limit", "1");
  url.searchParams.set("addressdetails", "0");

  const res = await fetch(url.toString(), {
    headers: {
      "User-Agent": "RadarUrbano/0.1 (contact: radar@lovable.app)",
      Accept: "application/json",
    },
  });
  if (!res.ok) return null;
  const data = (await res.json()) as Array<{
    lat: string;
    lon: string;
    display_name: string;
    importance?: number;
  }>;
  if (!data.length) return null;
  const top = data[0];
  return {
    lat: parseFloat(top.lat),
    lng: parseFloat(top.lon),
    confidence: Math.min(1, Math.max(0, top.importance ?? 0.6)),
    provider: "nominatim",
    display_name: top.display_name,
  };
}
