const COLORS = ["#1e90ff", "#8e44ad", "#27ae60", "#f4a829", "#e74c3c", "#00bcd4"];

export function drawBarChart(canvas, entries = []) {
  const context = canvas.getContext("2d"); const ratio = window.devicePixelRatio || 1; const width = canvas.clientWidth || 420; const height = 190;
  canvas.width = width * ratio; canvas.height = height * ratio; context.scale(ratio, ratio); context.clearRect(0, 0, width, height);
  if (!entries.length) { context.fillStyle = "#8ba5bc"; context.fillText("Sem dados", 12, 24); return; }
  const max = Math.max(...entries.map(([, value]) => value), 1); const slot = width / entries.length;
  entries.forEach(([label, value], index) => { const barHeight = (value / max) * 120; context.fillStyle = COLORS[index % COLORS.length]; context.fillRect(index * slot + 10, 145 - barHeight, Math.max(slot - 20, 8), barHeight); context.fillStyle = "#e5f1fb"; context.font = "11px system-ui"; context.fillText(String(value), index * slot + 10, 20); context.fillStyle = "#8ba5bc"; context.fillText(String(label).slice(0, 12), index * slot + 8, 168); });
}

const countBy = (items, getter) => Object.entries(items.reduce((result, item) => { const key = getter(item) || "N/D"; result[key] = (result[key] || 0) + 1; return result; }, {}));

export function renderCharts(data) {
  drawBarChart(document.getElementById("chart-zonas"), countBy(data.zonas || [], (item) => item.tipo || item.sigla));
  drawBarChart(document.getElementById("chart-obras"), countBy(data.obras || [], (item) => item.status));
  drawBarChart(document.getElementById("chart-demandas"), countBy(data.zonas || [], (item) => item.categoria || item.prioridade));
  drawBarChart(document.getElementById("chart-fornecedores"), countBy(data.fornecedores || [], (item) => item.zona || item.status));
}
