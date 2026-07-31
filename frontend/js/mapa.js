const COLORS = { ZUM: "#3498db", ZEIS: "#9b59b6", ALTO: "#e74c3c", "MÉDIO": "#f39c12", MEDIO: "#f39c12", BAIXO: "#27ae60" };
const escapeHtml = (value) => String(value ?? "N/D").replace(/[&<>'"]/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;" })[char]);
const colorFor = (props) => COLORS[String(props.tipo || props.sigla || props.categoria || "").toUpperCase()] || "#6d8aa8";

export class TerritorialMap {
  constructor(containerId, cardTarget) { this.container = document.getElementById(containerId); this.cardTarget = cardTarget; this.map = null; this.zoneLayer = null; this.pointLayer = null; this.zones = []; }

  init(zonesGeoJson, pointsGeoJson) {
    this.zones = zonesGeoJson.features || [];
    if (window.L) this.initLeaflet(zonesGeoJson, pointsGeoJson); else this.initSvg(zonesGeoJson);
    this.renderFilters();
  }

  initLeaflet(zones, points) {
    this.map = window.L.map(this.container, { center: [-8.03, -50.03], zoom: 12, zoomControl: false });
    this.zoneLayer = window.L.geoJSON(zones, { style: (feature) => ({ color: "#fff", weight: 1.5, fillColor: colorFor(feature.properties || {}), fillOpacity: 0.58 }), onEachFeature: (feature, layer) => { layer.on("click", () => this.selectZone(feature.properties || {})); layer.bindTooltip(escapeHtml(feature.properties?.sigla || feature.properties?.nome || "Zona")); } }).addTo(this.map);
    this.pointLayer = window.L.geoJSON(points, { pointToLayer: (_feature, latlng) => window.L.circleMarker(latlng, { radius: 6, color: "#f4a829", fillOpacity: 0.9 }) }).addTo(this.map);
    const bounds = window.L.featureGroup([this.zoneLayer, this.pointLayer]).getBounds(); if (bounds.isValid()) this.map.fitBounds(bounds.pad(0.08));
    this.map.on("mousemove", (event) => { document.getElementById("map-coordinates").textContent = `${event.latlng.lat.toFixed(5)}, ${event.latlng.lng.toFixed(5)}`; });
    document.getElementById("layer-zonas").addEventListener("change", (event) => event.target.checked ? this.zoneLayer.addTo(this.map) : this.map.removeLayer(this.zoneLayer));
    document.getElementById("layer-pontos").addEventListener("change", (event) => event.target.checked ? this.pointLayer.addTo(this.map) : this.map.removeLayer(this.pointLayer));
  }

  initSvg(zones) {
    const features = zones.features || []; this.container.innerHTML = '<svg id="svg-map" viewBox="0 0 1000 600" aria-label="Mapa territorial offline"></svg>'; const svg = this.container.firstElementChild;
    const coordinates = features.flatMap((feature) => feature.geometry?.coordinates?.flat(2) || []).filter((pair) => Array.isArray(pair));
    if (!coordinates.length) { svg.innerHTML = '<text x="500" y="300" text-anchor="middle" fill="#8ba5bc">Adicione zonas_poligonos.geojson</text>'; return; }
    const xs = coordinates.map(([x]) => x), ys = coordinates.map(([, y]) => y); const minX = Math.min(...xs), maxX = Math.max(...xs), minY = Math.min(...ys), maxY = Math.max(...ys); const project = ([x, y]) => [40 + ((x - minX) / (maxX - minX || 1)) * 920, 560 - ((y - minY) / (maxY - minY || 1)) * 520];
    features.forEach((feature) => { const rings = feature.geometry?.type === "MultiPolygon" ? feature.geometry.coordinates.flat() : feature.geometry?.coordinates || []; rings.slice(0, 1).forEach((ring) => { const polygon = document.createElementNS("http://www.w3.org/2000/svg", "polygon"); polygon.setAttribute("points", ring.map(project).map((point) => point.join(",")).join(" ")); polygon.setAttribute("fill", colorFor(feature.properties || {})); polygon.setAttribute("stroke", "#fff"); polygon.setAttribute("tabindex", "0"); polygon.addEventListener("click", () => this.selectZone(feature.properties || {})); svg.appendChild(polygon); }); });
  }

  selectZone(zone) {
    const list = (items, className) => (items || []).map((item) => `<span class="tag ${className}">${escapeHtml(item)}</span>`).join("") || '<span class="empty-state">Não informado</span>';
    this.cardTarget.innerHTML = `<div class="zone-title"><div><strong>${escapeHtml(zone.nome || "Zona")}</strong><small>${escapeHtml(zone.sigla)} · ${escapeHtml(zone.macrozona)}</small></div><span class="badge" style="--badge:${colorFor(zone)}">${escapeHtml(zone.tipo || zone.categoria)}</span></div><dl class="indices"><div><dt>TO máxima</dt><dd>${escapeHtml(zone.to_max)}%</dd></div><div><dt>CA básico</dt><dd>${escapeHtml(zone.ca_basico)}</dd></div><div><dt>CA máximo</dt><dd>${escapeHtml(zone.ca_maximo)}</dd></div><div><dt>Permeabilidade</dt><dd>${escapeHtml(zone.permeabilidade)}%</dd></div><div><dt>Altura</dt><dd>${escapeHtml(zone.altura_max)} m</dd></div><div><dt>Conformidade</dt><dd>${escapeHtml(zone.conformidade)}%</dd></div></dl><h3>Atividades</h3><div class="tags">${list(zone.atividades_permitidas, "allowed")}${list(zone.atividades_condicionadas, "conditional")}${list(zone.atividades_proibidas, "forbidden")}</div><p><strong>Viabilidade:</strong> ${escapeHtml(zone.viabilidade?.recomendacao || zone.recomendacao || "A confirmar na legislação vigente.")}</p>`;
  }

  renderFilters() { const types = [...new Set(this.zones.map((feature) => feature.properties?.tipo || feature.properties?.sigla).filter(Boolean))]; document.getElementById("zone-filters").innerHTML = types.map((type) => `<button data-zone-type="${escapeHtml(type)}">${escapeHtml(type)}</button>`).join(""); }
  search(query) { const normalized = query.toLocaleLowerCase("pt-BR"); if (!this.zoneLayer) return; this.zoneLayer.eachLayer((layer) => { const props = layer.feature.properties || {}; const match = !query || `${props.nome} ${props.sigla}`.toLocaleLowerCase("pt-BR").includes(normalized); layer.setStyle({ fillOpacity: match ? 0.72 : 0.08, weight: match ? 2 : 1 }); if (match && query) layer.bringToFront(); }); }
  filter(type) { if (!this.zoneLayer) return; this.zoneLayer.eachLayer((layer) => { const props = layer.feature.properties || {}; const match = !type || [props.tipo, props.sigla].includes(type); layer.setStyle({ fillOpacity: match ? 0.65 : 0.05 }); }); }
  zoomIn() { if (this.map) this.map.zoomIn(); }
  zoomOut() { if (this.map) this.map.zoomOut(); }
}
