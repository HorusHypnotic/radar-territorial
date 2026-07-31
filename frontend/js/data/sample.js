/** Fallback demonstrativo embutido. Não representa zoneamento legal. */
export const SAMPLE_DATA = {
  metadata: { status: "demonstrativo", aviso: "Dados ilustrativos; não usar para decisão urbanística." },
  zonas: [
    { id:"demo-zum-centro", sigla:"ZUM", nome:"Zona de Uso Misto — Centro (demonstração)", tipo:"ZUM", categoria:"Médio", macrozona:"Urbana", to_max:70, ca_basico:1.5, ca_maximo:3, permeabilidade:20, altura_max:18, conformidade:84, EducacaoInfantil:"Prioritário", Saude:"Médio", atividades_permitidas:["Residencial","Comércio local"], atividades_condicionadas:["Serviços de impacto"], atividades_proibidas:["Indústria pesada"] },
    { id:"demo-zeis-norte", sigla:"ZEIS", nome:"ZEIS Norte (demonstração)", tipo:"ZEIS", categoria:"Alto", macrozona:"Urbana", to_max:65, ca_basico:1.2, ca_maximo:2, permeabilidade:25, altura_max:12, conformidade:68, EducacaoInfantil:"Prioritário", Saude:"Prioritário", atividades_permitidas:["Habitação social","Equipamento público"], atividades_condicionadas:["Comércio vicinal"], atividades_proibidas:["Uso industrial"] },
    { id:"demo-zr-sul", sigla:"ZR", nome:"Zona Residencial Sul (demonstração)", tipo:"ZR", categoria:"Baixo", macrozona:"Urbana", to_max:60, ca_basico:1, ca_maximo:1.8, permeabilidade:30, altura_max:10, conformidade:91, EducacaoInfantil:"Adequado", Saude:"Adequado", atividades_permitidas:["Residencial"], atividades_condicionadas:["Comércio local"], atividades_proibidas:["Atividade de alto impacto"] },
    { id:"demo-zpa-leste", sigla:"ZPA", nome:"Zona de Proteção Ambiental Leste (demonstração)", tipo:"ZPA", categoria:"Alto", macrozona:"Ambiental", to_max:15, ca_basico:.2, ca_maximo:.4, permeabilidade:75, altura_max:6, conformidade:76, EducacaoInfantil:"N/A", Saude:"N/A", atividades_permitidas:["Conservação","Pesquisa"], atividades_condicionadas:["Ecoturismo"], atividades_proibidas:["Parcelamento urbano"] }
  ],
  obras: [
    { id:"obra-demo-1", nome:"Unidade de Saúde (demonstração)", zona:"ZEIS", status:"andamento", ico:78 },
    { id:"obra-demo-2", nome:"Praça Central (demonstração)", zona:"ZUM", status:"andamento", ico:88 },
    { id:"obra-demo-3", nome:"Drenagem Sul (demonstração)", zona:"ZR", status:"planejada", ico:61 }
  ],
  fornecedores: [
    { id:"forn-demo-1", nome:"Fornecedor A (demonstração)", zona:"ZUM", ativo:true },
    { id:"forn-demo-2", nome:"Fornecedor B (demonstração)", zona:"ZEIS", ativo:true }
  ]
};

export const SAMPLE_ZONES_GEOJSON = {
  type:"FeatureCollection",
  metadata:{ status:"demonstrativo" },
  features:SAMPLE_DATA.zonas.map((properties,index) => {
    const col=index%2,row=Math.floor(index/2),west=-50.047+col*.017,south=-8.040+row*.016;
    return { type:"Feature", properties, geometry:{ type:"Polygon", coordinates:[[[west,south],[west+.017,south],[west+.017,south+.016],[west,south+.016],[west,south]]] } };
  })
};
