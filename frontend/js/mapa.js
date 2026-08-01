const COLORS = { ZUM:"#2997ff", ZEIS:"#e67e22", ZR:"#f4a829", ZPA:"#27ae60", ZOR:"#8e44ad", ZIR:"#e74c3c", ZVA:"#27ae60", ZUPA:"#2ecc71", DAT:"#8e44ad", ZEU:"#00bcd4", ALTO:"#e74c3c", "MÉDIO":"#f39c12", MEDIO:"#f39c12", BAIXO:"#27ae60" };
const escapeHtml = (value) => String(value ?? "N/D").replace(/[&<>'"]/g,(char)=>({"&":"&amp;","<":"&lt;",">":"&gt;","'":"&#39;",'"':"&quot;"})[char]);
const colorFor = (props) => COLORS[String(props.tipo||props.sigla||props.categoria||"").toUpperCase()]||"#6d8aa8";

function geometryRings(feature) {
  if (feature.geometry?.type === "Polygon") return feature.geometry.coordinates;
  if (feature.geometry?.type === "MultiPolygon") return feature.geometry.coordinates.flatMap((polygon)=>polygon);
  return [];
}

export class TerritorialMap {
  constructor(containerId,cardTarget) { this.container=document.getElementById(containerId);this.cardTarget=cardTarget;this.map=null;this.zoneLayer=null;this.pointLayer=null;this.zones=[];this.svg=null;this.svgOriginalViewBox=[0,0,1000,600]; }

  init(zonesGeoJson,pointsGeoJson) {
    this.zones=zonesGeoJson.features||[];
    if (window.L&&window.innerWidth>768) this.initLeaflet(zonesGeoJson,pointsGeoJson); else this.initSvg(zonesGeoJson);
    this.renderFilters();
  }

  initLeaflet(zones,points) {
    this.map=window.L.map(this.container,{center:[-8.03,-50.03],zoom:12,zoomControl:false,preferCanvas:true});
    this.zoneLayer=window.L.geoJSON(zones,{style:(feature)=>({color:"#fff",weight:1.5,fillColor:colorFor(feature.properties||{}),fillOpacity:.58,className:"zone"}),onEachFeature:(feature,layer)=>{layer.on("click",()=>this.selectZone(feature.properties||{},layer));layer.bindTooltip(escapeHtml(feature.properties?.sigla||feature.properties?.nome||"Zona"));}}).addTo(this.map);
    this.pointLayer=window.L.geoJSON(points,{pointToLayer:(_feature,latlng)=>window.L.circleMarker(latlng,{radius:6,color:"#f4a829",fillOpacity:.9})}).addTo(this.map);
    const bounds=window.L.featureGroup([this.zoneLayer,this.pointLayer]).getBounds();if(bounds.isValid())this.map.fitBounds(bounds.pad(.08));
    this.map.on("mousemove",(event)=>{document.getElementById("map-coordinates").textContent=`${event.latlng.lat.toFixed(5)}, ${event.latlng.lng.toFixed(5)}`;});
    document.getElementById("layer-zonas").addEventListener("change",(event)=>event.target.checked?this.zoneLayer.addTo(this.map):this.map.removeLayer(this.zoneLayer));
    document.getElementById("layer-pontos").addEventListener("change",(event)=>event.target.checked?this.pointLayer.addTo(this.map):this.map.removeLayer(this.pointLayer));
  }

  initSvg(zones) {
    this.container.innerHTML='<svg id="svg-map" viewBox="0 0 1000 600" role="img" aria-label="Mapa territorial vetorial offline"></svg>';this.svg=this.container.firstElementChild;
    const coordinates=(zones.features||[]).flatMap((feature)=>geometryRings(feature).flat()).filter((pair)=>Array.isArray(pair)&&pair.length>=2);
    if(!coordinates.length){this.svg.innerHTML='<text x="500" y="300" text-anchor="middle" fill="#8ba5bc">GeoJSON territorial indisponível</text>';return;}
    const xs=coordinates.map(([x])=>x),ys=coordinates.map(([,y])=>y),minX=Math.min(...xs),maxX=Math.max(...xs),minY=Math.min(...ys),maxY=Math.max(...ys);
    const project=([x,y])=>[40+((x-minX)/(maxX-minX||1))*920,560-((y-minY)/(maxY-minY||1))*520];
    (zones.features||[]).forEach((feature,index)=>geometryRings(feature).slice(0,1).forEach((ring)=>{const polygon=document.createElementNS("http://www.w3.org/2000/svg","polygon");polygon.setAttribute("points",ring.map(project).map((point)=>point.join(",")).join(" "));polygon.setAttribute("fill",colorFor(feature.properties||{}));polygon.setAttribute("fill-opacity",".62");polygon.setAttribute("stroke","#fff");polygon.setAttribute("stroke-width","1.5");polygon.setAttribute("tabindex","0");polygon.setAttribute("role","button");polygon.setAttribute("aria-label",String(feature.properties?.nome||`Zona ${index+1}`));polygon.classList.add("zone");polygon.dataset.index=String(index);polygon.addEventListener("click",()=>this.selectZone(feature.properties||{},polygon));polygon.addEventListener("keydown",(event)=>{if(["Enter"," "].includes(event.key)){event.preventDefault();this.selectZone(feature.properties||{},polygon);}});this.svg.appendChild(polygon);}));
    this.enableSvgNavigation();
    document.getElementById("layer-zonas").addEventListener("change",(event)=>{this.svg.style.visibility=event.target.checked?"visible":"hidden";});
    document.getElementById("layer-pontos").disabled=true;
  }

  enableSvgNavigation() {
    let drag=null;
    this.svg.addEventListener("pointerdown",(event)=>{if(event.target.classList.contains("zone"))return;const box=this.viewBox();drag={x:event.clientX,y:event.clientY,box};this.svg.setPointerCapture(event.pointerId);});
    this.svg.addEventListener("pointermove",(event)=>{if(!drag)return;const scaleX=drag.box[2]/this.svg.clientWidth,scaleY=drag.box[3]/this.svg.clientHeight;this.setViewBox([drag.box[0]-(event.clientX-drag.x)*scaleX,drag.box[1]-(event.clientY-drag.y)*scaleY,drag.box[2],drag.box[3]]);});
    this.svg.addEventListener("pointerup",()=>{drag=null;});this.svg.addEventListener("pointercancel",()=>{drag=null;});
    this.svg.addEventListener("wheel",(event)=>{event.preventDefault();this.zoomSvg(event.deltaY>0?1.12:.88);},{passive:false});
  }

  viewBox(){return this.svg.getAttribute("viewBox").split(/\s+/).map(Number);}
  setViewBox(box){this.svg.setAttribute("viewBox",box.join(" "));}
  zoomSvg(factor){const box=this.viewBox(),width=Math.min(Math.max(box[2]*factor,160),1800),height=Math.min(Math.max(box[3]*factor,100),1080);this.setViewBox([box[0]+(box[2]-width)/2,box[1]+(box[3]-height)/2,width,height]);}

  selectZone(zone,layer) {
    if(this.zoneLayer)this.zoneLayer.eachLayer((item)=>item.setStyle({weight:(item===layer)?3:1.5,fillOpacity:(item===layer)?0.72:0.48}));
    if(this.svg){this.svg.querySelectorAll(".zone").forEach((item)=>item.classList.toggle("selected",item===layer));}
    const list=(items,className)=>(items||[]).map((item)=>`<span class="tag ${className}">${escapeHtml(item)}</span>`).join("")||'<span class="empty-state">Não informado</span>';
    const conformity=Math.min(Math.max(Number(zone.conformidade)||0,0),100);
    this.cardTarget.innerHTML=`<div class="zone-title"><div><strong>${escapeHtml(zone.nome||"Zona")}</strong><small>${escapeHtml(zone.sigla)} · ${escapeHtml(zone.macrozona)}</small></div><span class="badge" style="--badge:${colorFor(zone)}">${escapeHtml(zone.tipo||zone.categoria)}</span></div><dl class="indices"><div><dt>TO máxima</dt><dd>${escapeHtml(zone.to_max)}%</dd></div><div><dt>CA básico</dt><dd>${escapeHtml(zone.ca_basico)}</dd></div><div><dt>CA máximo</dt><dd>${escapeHtml(zone.ca_maximo)}</dd></div><div><dt>Permeabilidade</dt><dd>${escapeHtml(zone.permeabilidade)}%</dd></div><div><dt>Altura</dt><dd>${escapeHtml(zone.altura_max)} m</dd></div><div><dt>Conformidade</dt><dd>${conformity}%</dd><div class="progress-bar"><div class="progress-fill" style="width:${conformity}%"></div></div></div></dl><h3>Atividades</h3><div class="tags">${list(zone.atividades_permitidas,"allowed")}${list(zone.atividades_condicionadas,"conditional")}${list(zone.atividades_proibidas,"forbidden")}</div><p><strong>Referência legal:</strong> ${escapeHtml(zone.referencia_legal||zone.source||"LC 128/2022")}</p><p><strong>Viabilidade:</strong> ${escapeHtml(zone.viabilidade?.recomendacao||zone.recomendacao||"A confirmar na legislação vigente.")}</p>`;
    document.dispatchEvent(new CustomEvent("zona-selecionada",{detail:{zona:zone,source:this.map?"leaflet":"svg"}}));
  }

  renderFilters(){const types=[...new Set(this.zones.map((feature)=>feature.properties?.tipo||feature.properties?.sigla).filter(Boolean))];document.getElementById("zone-filters").innerHTML=types.map((type)=>`<button data-zone-type="${escapeHtml(type)}">${escapeHtml(type)}</button>`).join("");}
  applyVisibility(predicate){if(this.zoneLayer)this.zoneLayer.eachLayer((layer)=>{const match=predicate(layer.feature.properties||{});layer.setStyle({fillOpacity:match?.68:.06,weight:match?2:1});});if(this.svg)this.svg.querySelectorAll(".zone").forEach((polygon)=>polygon.classList.toggle("dim",!predicate(this.zones[Number(polygon.dataset.index)]?.properties||{})));}
  search(query){const normalized=query.toLocaleLowerCase("pt-BR");this.applyVisibility((props)=>!query||`${props.nome} ${props.sigla}`.toLocaleLowerCase("pt-BR").includes(normalized));}
  filter(type){this.applyVisibility((props)=>!type||[props.tipo,props.sigla].includes(type));}
  zoomIn(){if(this.map)this.map.zoomIn();else if(this.svg)this.zoomSvg(.85);}
  zoomOut(){if(this.map)this.map.zoomOut();else if(this.svg)this.zoomSvg(1.15);}
}
