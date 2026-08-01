const COLORS = ["#1e90ff", "#8e44ad", "#27ae60", "#f4a829", "#e74c3c", "#00bcd4"];

export function drawBarChart(canvas, entries = []) {
  const context = canvas.getContext("2d"); const ratio = window.devicePixelRatio || 1; const width = canvas.clientWidth || 420; const height = 190;
  canvas.width = width * ratio; canvas.height = height * ratio; context.scale(ratio, ratio); context.clearRect(0, 0, width, height);
  if (!entries.length) { context.fillStyle = "#8ba5bc"; context.fillText("Sem dados", 12, 24); return; }
  const max = Math.max(...entries.map(([, value]) => value), 1); const slot = width / entries.length;
  entries.forEach(([label, value], index) => { const barHeight = (value / max) * 120; context.fillStyle = COLORS[index % COLORS.length]; context.fillRect(index * slot + 10, 145 - barHeight, Math.max(slot - 20, 8), barHeight); context.fillStyle = "#e5f1fb"; context.font = "11px system-ui"; context.fillText(String(value), index * slot + 10, 20); context.fillStyle = "#8ba5bc"; context.fillText(String(label).slice(0, 12), index * slot + 8, 168); });
}

export function drawDonutChart(canvas, entries = []) {
  const context = canvas.getContext("2d"); const ratio = window.devicePixelRatio || 1; const width = canvas.clientWidth || 420; const height = 190;
  canvas.width = width * ratio; canvas.height = height * ratio; context.scale(ratio, ratio); context.clearRect(0, 0, width, height);
  const total = entries.reduce((sum, [, value]) => sum + value, 0); if (!total) { context.fillStyle = "#8ba5bc"; context.fillText("Sem dados", 12, 24); return; }
  const centerX = Math.min(width * .32, 120); const centerY = height / 2; const radius = 62; let angle = -Math.PI / 2;
  entries.forEach(([label, value], index) => { const next = angle + (value / total) * Math.PI * 2; context.beginPath(); context.arc(centerX, centerY, radius, angle, next); context.arc(centerX, centerY, radius * .58, next, angle, true); context.closePath(); context.fillStyle = COLORS[index % COLORS.length]; context.fill(); const y = 38 + index * 25; context.fillRect(width * .56, y - 8, 9, 9); context.fillStyle = "#8ba5bc"; context.font = "11px system-ui"; context.fillText(`${String(label).slice(0, 14)} · ${value}`, width * .56 + 15, y); angle = next; });
  context.fillStyle = "#e5f1fb"; context.font = "700 22px system-ui"; context.textAlign = "center"; context.fillText(String(total), centerX, centerY + 7); context.textAlign = "start";
}

const countBy = (items, getter) => Object.entries(items.reduce((result, item) => { const key = getter(item) || "N/D"; result[key] = (result[key] || 0) + 1; return result; }, {}));

export function renderCharts(data) {
  drawBarChart(document.getElementById("chart-zonas"), countBy(data.zonas || [], (item) => item.tipo || item.sigla));
  drawBarChart(document.getElementById("chart-obras"), countBy(data.obras || [], (item) => item.status));
  drawDonutChart(document.getElementById("chart-demandas"), countBy(data.zonas || [], (item) => item.categoria || item.prioridade));
  drawBarChart(document.getElementById("chart-fornecedores"), countBy(data.fornecedores || [], (item) => item.zona || item.status));
}
