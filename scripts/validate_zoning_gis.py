"""Valida o zoneamento da LC 128/2022 com Shapely/GEOS e PyProj."""
from __future__ import annotations
import argparse, hashlib, importlib.util, json
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path
from typing import Any
from pyproj import Transformer
from shapely.geometry import shape
from shapely.ops import transform
from shapely.validation import explain_validity

EXPECTED_IDS={"zum-01","zum-02","zum-03","zir-pli","zir-mil-01","zir-mil-02","zor-zacr","zor-zpa"}
TO_UTM=Transformer.from_crs("EPSG:4326","EPSG:31983",always_xy=True).transform

def validate_document(document:dict[str,Any],source_bytes:bytes=b"")->dict[str,Any]:
    features=document.get("features",[]);errors=[];records=[];projected=[]
    ids={item.get("properties",{}).get("id") for item in features}
    if document.get("type")!="FeatureCollection":errors.append({"type":"contract","message":"Documento não é FeatureCollection"})
    if ids!=EXPECTED_IDS:errors.append({"type":"coverage","missing":sorted(EXPECTED_IDS-ids),"extra":sorted(ids-EXPECTED_IDS)})
    for feature in features:
        props=feature.get("properties",{});zone_id=props.get("id","sem-id");geometry=shape(feature.get("geometry"));geometry_utm=transform(TO_UTM,geometry);ring=feature.get("geometry",{}).get("coordinates",[[]])[0];valid=geometry.is_valid and not geometry.is_empty;vertices=max(len(ring)-1,0)
        if not valid:errors.append({"type":"geometry","id":zone_id,"message":explain_validity(geometry)})
        if ring and ring[0]!=ring[-1]:errors.append({"type":"ring","id":zone_id,"message":"anel aberto"})
        if props.get("vertex_count") is not None and vertices!=props["vertex_count"]:errors.append({"type":"vertices","id":zone_id,"expected":props["vertex_count"],"actual":vertices})
        records.append({"id":zone_id,"valid":valid,"vertices":vertices,"area_m2":round(geometry_utm.area,3),"area_km2":round(geometry_utm.area/1_000_000,6)})
        if valid:projected.append((zone_id,geometry_utm))
    overlaps=[]
    for (id_a,geom_a),(id_b,geom_b) in combinations(projected,2):
        area=geom_a.intersection(geom_b).area
        if area>0.01:overlaps.append({"a":id_a,"b":id_b,"area_m2":round(area,3)})
    return {"metadata":{"generated_at":datetime.now(timezone.utc).isoformat(),"engine":"Shapely/GEOS + PyProj","pyqgis_available":importlib.util.find_spec("qgis") is not None,"source_crs":"EPSG:4326","measurement_crs":"EPSG:31983","source_sha256":hashlib.sha256(source_bytes).hexdigest() if source_bytes else None,"note":"Sobreposições são reportadas e não corrigidas automaticamente; devem ser interpretadas conforme os memoriais e exclusões legais."},"summary":{"features":len(features),"valid":sum(item["valid"] for item in records),"invalid":sum(not item["valid"] for item in records),"vertices":sum(item["vertices"] for item in records),"overlaps":len(overlaps),"errors":len(errors)},"features":records,"overlaps":overlaps,"errors":errors}

def main()->int:
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("--input",type=Path,default=Path("data/output/zonas_oficiais_consolidado.geojson"));parser.add_argument("--report",type=Path,default=Path("data/output/validacao_gis_lc128.json"));parser.add_argument("--fail-on-overlap",action="store_true");args=parser.parse_args();source=args.input.read_bytes();report=validate_document(json.loads(source),source);args.report.parent.mkdir(parents=True,exist_ok=True);args.report.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8");print(json.dumps(report["summary"],ensure_ascii=False));print(f"Relatório: {args.report}");return 1 if report["errors"] or (args.fail_on_overlap and report["overlaps"]) else 0
if __name__=="__main__":raise SystemExit(main())
