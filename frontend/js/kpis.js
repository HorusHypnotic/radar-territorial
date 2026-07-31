const getCollections = (data = {}) => ({ zonas: data.zonas || [], obras: data.obras || [], fornecedores: data.fornecedores || [] });

export function calculateKpis(data) {
  const { zonas, obras, fornecedores } = getCollections(data);
  const type = (zone) => String(zone.tipo || zone.sigla || "").toUpperCase();
  const coverage = (fields) => {
    const values = zonas.flatMap((zone) => fields.filter((field) => field in zone).slice(0, 1).map((field) => zone[field]));
    return values.length ? Math.round(values.filter((value) => ["prioritário", "prioritario", "alta"].includes(String(value).toLowerCase())).length / values.length * 100) : 0;
  };
  const icoValues = obras.map((obra) => Number(obra.ico)).filter(Number.isFinite);
  return {
    setores_mapeados: zonas.length,
    obras_andamento: obras.filter((obra) => ["andamento", "ativa", "ativo"].includes(String(obra.status).toLowerCase())).length,
    fornecedores_ativos: fornecedores.filter((item) => item.ativo !== false).length,
    demandas_prioritarias: zonas.filter((zone) => JSON.stringify(zone.demandas || zone.prioridades || zone).toLowerCase().includes("priorit")).length,
    zonas_zum: zonas.filter((zone) => type(zone) === "ZUM").length,
    zeis: zonas.filter((zone) => type(zone) === "ZEIS").length,
    cobertura_creche: coverage(["educacao_infantil", "EducacaoInfantil"]),
    cobertura_saude: coverage(["saude", "Saude"]),
    ico_medio: icoValues.length ? Math.round(icoValues.reduce((sum, value) => sum + value, 0) / icoValues.length) : 0,
  };
}

export function renderKpis(target, icoTarget, data, remoteKpis = null) {
  const kpis = remoteKpis || calculateKpis(data);
  const cards = [["Setores", "setores_mapeados"], ["Obras ativas", "obras_andamento"], ["Fornecedores", "fornecedores_ativos"], ["Prioridades", "demandas_prioritarias"], ["ZUM", "zonas_zum"], ["ZEIS", "zeis"], ["Creche", "cobertura_creche", "%"], ["Saúde", "cobertura_saude", "%"]];
  target.innerHTML = cards.map(([label, key, suffix = ""]) => `<div class="kpi"><strong>${Number(kpis[key] || 0)}${suffix}</strong><span>${label}</span></div>`).join("");
  const ico = Number(kpis.ico_medio || 0); const level = ico >= 80 ? "good" : ico >= 60 ? "warn" : "bad";
  icoTarget.innerHTML = `<div class="ico ${level}"><span>ICO médio</span><strong>${ico}</strong><small>${ico >= 80 ? "Excelente" : ico >= 60 ? "Atenção" : "Crítico"}</small></div>`;
}
