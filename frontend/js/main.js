import { initApmo } from "./apmo.js";
import { renderCharts } from "./graficos.js";
import { renderKpis } from "./kpis.js";
import { TerritorialMap } from "./mapa.js";
import { DataTable } from "./tabela.js";
import { initUpload } from "./upload.js";
import { SAMPLE_DATA, SAMPLE_ZONES_GEOJSON } from "./data/sample.js";

const EMPTY_GEOJSON = { type: "FeatureCollection", features: [] };
const fetchJson = async (paths, fallback) => { for (const path of paths) { try { const response = await fetch(path); if (response.ok) return response.json(); } catch (_error) { /* fallback seguinte */ } } return fallback; };

async function boot() {
  const [data, zones, points, health, remoteKpis] = await Promise.all([fetchJson(["/api/data", "../data/output/dashboard_data.json"], SAMPLE_DATA), fetchJson(["/api/geojson/zonas", "../data/output/zonas_poligonos.geojson", "data/zonas_redencao.geojson"], SAMPLE_ZONES_GEOJSON), fetchJson(["/api/geojson/pontos", "../data/output/radar_geojson.geojson"], EMPTY_GEOJSON), fetchJson(["/api/health"], null), fetchJson(["/api/kpis"], null)]);
  const status = document.getElementById("connection-status"); status.textContent = health ? `API ${health.version}` : "Modo estático"; status.classList.toggle("offline", !health);
  renderKpis(document.getElementById("kpi-container"), document.getElementById("ico-container"), data, remoteKpis); renderCharts(data);
  const map = new TerritorialMap("map", document.getElementById("zone-card")); map.init(zones, points); document.getElementById("zoom-in").addEventListener("click", () => map.zoomIn()); document.getElementById("zoom-out").addEventListener("click", () => map.zoomOut()); document.getElementById("zone-search").addEventListener("input", (event) => map.search(event.target.value)); document.getElementById("zone-filters").addEventListener("click", (event) => { if (event.target.dataset.zoneType) map.filter(event.target.dataset.zoneType); });
  const rows = [...(data.zonas || []), ...(data.obras || []), ...(data.fornecedores || [])]; const table = new DataTable(document.getElementById("data-table"), document.getElementById("table-pagination"), rows); table.render(); document.getElementById("table-search").addEventListener("input", (event) => table.setQuery(event.target.value)); document.getElementById("table-zone").innerHTML += [...new Set(rows.map((row) => row.zona || row.sigla).filter(Boolean))].map((zone) => `<option>${zone}</option>`).join(""); document.getElementById("table-zone").addEventListener("change", (event) => table.setZone(event.target.value)); document.getElementById("export-csv").addEventListener("click", () => table.exportCsv());
  initUpload({ dropzone: document.getElementById("upload-dropzone"), input: document.getElementById("upload-input"), preview: document.getElementById("upload-preview"), feedback: document.getElementById("upload-feedback"), submit: document.getElementById("upload-submit"), apiAvailable: Boolean(health) }); await initApmo(Boolean(health));
  document.querySelectorAll(".tab").forEach((button) => button.addEventListener("click", () => { document.querySelectorAll(".tab,.view").forEach((item) => item.classList.remove("active")); button.classList.add("active"); document.getElementById(`view-${button.dataset.view}`).classList.add("active"); if (button.dataset.view === "territorio" && map.map) setTimeout(() => map.map.invalidateSize(), 0); }));
  document.getElementById("sidebar-toggle").addEventListener("click", (event) => { const collapsed = document.body.classList.toggle("sidebar-collapsed"); event.currentTarget.setAttribute("aria-expanded", String(!collapsed)); if (map.map) setTimeout(() => map.map.invalidateSize(), 220); });
}

boot().catch((error) => { document.getElementById("connection-status").textContent = `Falha: ${error.message}`; document.getElementById("connection-status").classList.add("offline"); });

if ("serviceWorker" in navigator && (location.protocol === "https:" || location.hostname === "localhost")) navigator.serviceWorker.register("./sw.js").catch(() => {});
