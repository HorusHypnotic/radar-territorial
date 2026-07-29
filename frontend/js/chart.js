// OPERA Territorial v2.0 — Gráfico de barras com Canvas nativo (sem Chart.js)

function renderICOChart(setores) {
  const canvas = document.getElementById('icoChart');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  const width = canvas.width;
  const height = canvas.height;
  const padding = { top: 20, right: 10, bottom: 30, left: 40 };
  const chartWidth = width - padding.left - padding.right;
  const chartHeight = height - padding.top - padding.bottom;

  // Clear
  ctx.clearRect(0, 0, width, height);

  // Background
  ctx.fillStyle = '#0B1A2F';
  ctx.fillRect(0, 0, width, height);

  if (!setores || setores.length === 0) {
    ctx.fillStyle = '#9bb1cc';
    ctx.font = '12px Inter, sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('Nenhum dado disponível', width / 2, height / 2);
    return;
  }

  const maxVal = 100;
  const barWidth = (chartWidth / setores.length) * 0.6;
  const gap = (chartWidth / setores.length) * 0.4;

  // Y-axis
  ctx.strokeStyle = '#1e3a5f';
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.moveTo(padding.left, padding.top);
  ctx.lineTo(padding.left, height - padding.bottom);
  ctx.lineTo(width - padding.right, height - padding.bottom);
  ctx.stroke();

  // Y labels
  ctx.fillStyle = '#9bb1cc';
  ctx.font = '10px Inter, sans-serif';
  ctx.textAlign = 'right';
  for (let i = 0; i <= 4; i++) {
    const val = (maxVal / 4) * i;
    const y = height - padding.bottom - (chartHeight * val / maxVal);
    ctx.fillText(val.toString(), padding.left - 5, y + 3);
    ctx.strokeStyle = '#1e3a5f';
    ctx.beginPath();
    ctx.moveTo(padding.left, y);
    ctx.lineTo(width - padding.right, y);
    ctx.stroke();
  }

  // Bars
  setores.forEach((s, i) => {
    const x = padding.left + i * (barWidth + gap) + gap / 2;
    const barHeight = (chartHeight * s.ico) / maxVal;
    const y = height - padding.bottom - barHeight;

    // Color based on ICO
    if (s.ico >= 80) ctx.fillStyle = '#4ade80';
    else if (s.ico >= 60) ctx.fillStyle = '#facc15';
    else ctx.fillStyle = '#f87171';

    // Draw bar
    ctx.fillRect(x, y, barWidth, barHeight);

    // X label
    ctx.fillStyle = '#9bb1cc';
    ctx.font = '10px Inter, sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText(s.zona, x + barWidth / 2, height - padding.bottom + 15);
  });

  // Title
  ctx.fillStyle = '#F5B041';
  ctx.font = 'bold 11px Inter, sans-serif';
  ctx.textAlign = 'left';
  ctx.fillText('ICO (%)', 5, 12);
}
