"""Converte um dataset vetorial autorizado para os contratos estáticos do OPERA."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping
from uuid import NAMESPACE_URL, uuid5


CANONICAL_FIELDS = (
    "sigla", "nome", "tipo", "categoria", "macrozona", "nivel", "area_m2",
    "to_max", "ca_basico", "ca_maximo", "permeabilidade", "altura_max",
    "lotes", "conformidade", "atividades_permitidas",
    "atividades_condicionadas", "atividades_proibidas",
)
NUMERIC_FIELDS = {"area_m2", "to_max", "ca_basico", "ca_maximo", "permeabilidade", "altura_max", "lotes", "conformidade"}
LIST_FIELDS = {"atividades_permitidas", "atividades_condicionadas", "atividades_proibidas"}
REQUIRED_SIDECARS = (".shp", ".shx", ".dbf", ".prj")


def require_shapefile_components(source: Path) -> list[Path]:
    if source.suffix.lower() != ".shp":
        raise ValueError("--shapefile deve apontar para um arquivo .shp")
    by_suffix = {path.suffix.lower(): path for path in source.parent.glob(f"{source.stem}.*")}
    missing = [suffix for suffix in REQUIRED_SIDECARS if suffix not in by_suffix]
    if missing:
        raise ValueError(f"componentes obrigatórios ausentes: {', '.join(missing)}")
    return [by_suffix[suffix] for suffix in sorted(by_suffix)]


def source_digest(paths: list[Path]) -> str:
    digest = hashlib.sha256()
    for path in sorted(paths, key=lambda item: item.name.lower()):
        digest.update(path.name.lower().encode("utf-8")); digest.update(b"\0")
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""): digest.update(chunk)
    return digest.hexdigest()


def load_mapping(path: Path | None) -> dict[str, str]:
    if path is None:
        return {field: field for field in CANONICAL_FIELDS}
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not payload:
        raise ValueError("mapeamento deve ser um objeto JSON não vazio")
    unknown = sorted(set(payload.values()) - set(CANONICAL_FIELDS))
    if unknown:
        raise ValueError(f"campos de destino desconhecidos: {', '.join(unknown)}")
    return {str(source): str(target) for source, target in payload.items()}


def json_value(value: Any, target: str) -> Any:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return None
    if target in LIST_FIELDS:
        if isinstance(value, (list, tuple)): return [str(item).strip() for item in value if str(item).strip()]
        return [item.strip() for item in str(value).split(";") if item.strip()]
    if target in NUMERIC_FIELDS:
        number = float(value)
        return int(number) if target == "lotes" and number.is_integer() else number
    if hasattr(value, "item"):
        value = value.item()
    return value.strip() if isinstance(value, str) else value


def validate_properties(properties: Mapping[str, Any], row_number: int) -> None:
    for field in ("sigla", "nome"):
        if not str(properties.get(field) or "").strip():
            raise ValueError(f"registro {row_number}: campo obrigatório {field} vazio")
    for field in ("to_max", "permeabilidade", "conformidade"):
        value = properties.get(field)
        if value is not None and not 0 <= float(value) <= 100:
            raise ValueError(f"registro {row_number}: {field} deve estar entre 0 e 100")
    for field in ("area_m2", "ca_basico", "ca_maximo", "altura_max", "lotes"):
        value = properties.get(field)
        if value is not None and float(value) < 0:
            raise ValueError(f"registro {row_number}: {field} não pode ser negativo")


def validate_bounds(bounds: tuple[float, float, float, float], expected: tuple[float, float, float, float] | None) -> None:
    west, south, east, north = bounds
    if not (-180 <= west < east <= 180 and -90 <= south < north <= 90):
        raise ValueError(f"limites EPSG:4326 inválidos: {bounds}")
    if expected:
        exp_west, exp_south, exp_east, exp_north = expected
        if west < exp_west or south < exp_south or east > exp_east or north > exp_north:
            raise ValueError(f"dataset fora dos limites esperados {expected}: {bounds}")


def load_table(path: Path | None) -> list[dict[str, Any]]:
    if path is None: return []
    import pandas as pd
    if not path.is_file(): raise FileNotFoundError(path)
    suffix = path.suffix.lower()
    frame = pd.read_excel(path) if suffix in {".xlsx", ".xls"} else pd.read_csv(path, sep=None, engine="python") if suffix == ".csv" else None
    if frame is None: raise ValueError(f"planilha não suportada: {suffix}")
    return [{str(key): json_value(value, str(key)) for key, value in row.items()} for row in frame.to_dict(orient="records")]


def convert_dataset(source: Path, mapping: Mapping[str, str], simplify_meters: float = 0, expected_bounds: tuple[float, float, float, float] | None = None) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    import geopandas as gpd
    from shapely.geometry import mapping as geometry_mapping

    gdf = gpd.read_file(source)
    if gdf.empty: raise ValueError("dataset vetorial vazio")
    if gdf.crs is None: raise ValueError("CRS ausente; defina-o corretamente no QGIS antes de exportar")
    if gdf.geometry.isna().any() or gdf.geometry.is_empty.any(): raise ValueError("geometrias nulas ou vazias detectadas")
    if not gdf.geometry.is_valid.all(): raise ValueError("geometrias inválidas detectadas; execute Corrigir Geometrias no QGIS")
    if not set(gdf.geometry.geom_type).issubset({"Polygon", "MultiPolygon"}): raise ValueError("somente Polygon e MultiPolygon são aceitos")
    lookup = {str(column).casefold(): str(column) for column in gdf.columns if str(column) != "geometry"}
    resolved = {lookup.get(source_name.casefold(), source_name): target for source_name, target in mapping.items()}
    missing_required = [target for target in ("sigla", "nome") if target not in resolved.values() or next((field for field, mapped in resolved.items() if mapped == target and field in gdf.columns), None) is None]
    if missing_required: raise ValueError(f"mapeamento/campos obrigatórios ausentes: {', '.join(missing_required)}")
    if simplify_meters < 0: raise ValueError("--simplify-meters não pode ser negativo")
    if simplify_meters:
        projected = gdf if gdf.crs.is_projected else gdf.to_crs(gdf.estimate_utm_crs())
        projected.geometry = projected.geometry.simplify(simplify_meters, preserve_topology=True)
        gdf = projected.to_crs(gdf.crs)
    geographic = gdf.to_crs(epsg=4326)
    validate_bounds(tuple(float(value) for value in geographic.total_bounds), expected_bounds)
    features = []
    for position, (_, row) in enumerate(geographic.iterrows(), start=1):
        properties = {target: json_value(row[field], target) for field, target in resolved.items() if field in row.index}
        properties = {key: value for key, value in properties.items() if value is not None}
        validate_properties(properties, position)
        geometry_sha256 = hashlib.sha256(row.geometry.wkb).hexdigest()
        identity = f"opera-zone:{properties['sigla']}:{geometry_sha256}"
        properties["id"] = str(uuid5(NAMESPACE_URL, identity))
        properties.setdefault("tipo", properties["sigla"])
        if "area_m2" in properties: properties["area_km2"] = round(float(properties["area_m2"]) / 1_000_000, 6)
        features.append({"type": "Feature", "id": properties["id"], "properties": properties, "geometry": geometry_mapping(row.geometry)})
    return features, {"source_crs": str(gdf.crs), "bounds_epsg4326": [float(value) for value in geographic.total_bounds]}


def build_documents(features: list[dict[str, Any]], obras: list[dict[str, Any]], fornecedores: list[dict[str, Any]], provenance: Mapping[str, Any], authority: str | None, legal_reference: str | None) -> tuple[dict[str, Any], dict[str, Any]]:
    official = bool(authority and legal_reference)
    timestamp = datetime.now(timezone.utc).isoformat()
    metadata = {"status": "oficial" if official else "candidato", "authority": authority, "legal_reference": legal_reference, "generated_at": timestamp, "crs": "EPSG:4326", **provenance}
    geojson = {"type": "FeatureCollection", "metadata": metadata, "features": features}
    dashboard = {"metadata": {**metadata, "total_zonas": len(features), "total_obras": len(obras), "total_fornecedores": len(fornecedores)}, "zonas": [feature["properties"] for feature in features], "obras": obras, "fornecedores": fornecedores}
    return geojson, dashboard


def write_documents(output: Path, geojson: Mapping[str, Any], dashboard: Mapping[str, Any], replace: bool = False) -> None:
    output.mkdir(parents=True, exist_ok=True)
    targets = {"zonas_poligonos.geojson": geojson, "dashboard_data.json": dashboard}
    output_names = (*targets, "import_manifest.json")
    existing = [name for name in output_names if (output / name).exists()]
    if existing and not replace: raise FileExistsError(f"saída já existe ({', '.join(existing)}); revise e use --replace conscientemente")
    with tempfile.TemporaryDirectory(prefix="opera-export-", dir=output.parent) as temp_name:
        temporary = Path(temp_name)
        for name, document in targets.items(): (temporary / name).write_text(json.dumps(document, ensure_ascii=False, indent=2), encoding="utf-8")
        manifest = {
            "schema": "opera-qgis-import/1.0",
            "status": geojson.get("metadata", {}).get("status"),
            "generated_at": geojson.get("metadata", {}).get("generated_at"),
            "source_sha256": geojson.get("metadata", {}).get("source_sha256"),
            "files": {name: hashlib.sha256((temporary / name).read_bytes()).hexdigest() for name in targets},
        }
        (temporary / "import_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        for name in output_names: os.replace(temporary / name, output / name)


def validate_export(path: Path) -> dict[str, Any]:
    from shapely.geometry import shape

    directory = path if path.is_dir() else path.parent
    paths = {name: directory / name for name in ("zonas_poligonos.geojson", "dashboard_data.json", "import_manifest.json")}
    missing = [name for name, candidate in paths.items() if not candidate.is_file()]
    if missing: raise ValueError(f"arquivos da exportação ausentes: {', '.join(missing)}")
    geojson = json.loads(paths["zonas_poligonos.geojson"].read_text(encoding="utf-8"))
    dashboard = json.loads(paths["dashboard_data.json"].read_text(encoding="utf-8"))
    manifest = json.loads(paths["import_manifest.json"].read_text(encoding="utf-8"))
    if geojson.get("type") != "FeatureCollection" or not isinstance(geojson.get("features"), list) or not geojson["features"]: raise ValueError("GeoJSON vazio ou inválido")
    if not all(isinstance(dashboard.get(key), list) for key in ("zonas", "obras", "fornecedores")): raise ValueError("dashboard não atende ao contrato")
    metadata = geojson.get("metadata") or {}
    if metadata.get("crs") != "EPSG:4326": raise ValueError("saída deve declarar EPSG:4326")
    if metadata.get("status") not in {"candidato", "oficial"}: raise ValueError("status de publicação inválido")
    if metadata.get("status") == "oficial" and (not metadata.get("authority") or not metadata.get("legal_reference")): raise ValueError("saída oficial sem autoridade/referência legal")
    if len(str(metadata.get("source_sha256") or "")) != 64: raise ValueError("SHA-256 da origem ausente")
    ids = set()
    for position, feature in enumerate(geojson["features"], start=1):
        properties = feature.get("properties") or {}; validate_properties(properties, position)
        if not properties.get("id") or properties["id"] in ids: raise ValueError(f"registro {position}: id ausente ou duplicado")
        ids.add(properties["id"])
        geometry = shape(feature.get("geometry"));
        if geometry.geom_type not in {"Polygon", "MultiPolygon"} or geometry.is_empty or not geometry.is_valid: raise ValueError(f"registro {position}: geometria inválida")
    if len(dashboard["zonas"]) != len(geojson["features"]): raise ValueError("quantidade de zonas diverge entre GeoJSON e dashboard")
    for name in ("zonas_poligonos.geojson", "dashboard_data.json"):
        actual = hashlib.sha256(paths[name].read_bytes()).hexdigest()
        if manifest.get("files", {}).get(name) != actual: raise ValueError(f"hash de saída divergente: {name}")
    return {"valid": True, "status": metadata["status"], "zonas": len(geojson["features"]), "obras": len(dashboard["obras"]), "fornecedores": len(dashboard["fornecedores"]), "source_sha256": metadata["source_sha256"]}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--shapefile", type=Path)
    parser.add_argument("--validate", type=Path, help="valida um diretório exportado e não converte dados")
    parser.add_argument("--field-map", "--map", dest="field_map", type=Path, help="JSON campo_do_shapefile -> campo_OPERA")
    parser.add_argument("--obras", "--planilha-obras", dest="obras", type=Path, help="CSV/XLSX opcional")
    parser.add_argument("--fornecedores", "--planilha-fornecedores", dest="fornecedores", type=Path, help="CSV/XLSX opcional")
    parser.add_argument("--output", type=Path, default=Path("data/candidate"))
    parser.add_argument("--simplify-meters", type=float, default=0)
    parser.add_argument("--expected-bounds", type=float, nargs=4, metavar=("WEST", "SOUTH", "EAST", "NORTH"))
    parser.add_argument("--authority", help="órgão que autorizou a publicação")
    parser.add_argument("--legal-reference", help="lei/decreto/processo de origem")
    parser.add_argument("--replace", action="store_true")
    parser.add_argument("--publish", action="store_true", help="exige autoridade, referência legal e saída data/output")
    parser.add_argument("--verbose", action="store_true", help="reservado para compatibilidade; erros continuam explícitos")
    args = parser.parse_args()
    if args.validate:
        print(json.dumps(validate_export(args.validate), ensure_ascii=False)); return 0
    if not args.shapefile: parser.error("--shapefile é obrigatório fora do modo --validate")
    if bool(args.authority) != bool(args.legal_reference): raise ValueError("--authority e --legal-reference devem ser informados juntos")
    if args.publish:
        if not args.authority or not args.legal_reference: raise ValueError("--publish exige autoridade e referência legal")
        if args.output.resolve() != (Path.cwd() / "data" / "output").resolve(): raise ValueError("--publish exige --output data/output")
    components = require_shapefile_components(args.shapefile)
    features, spatial = convert_dataset(args.shapefile, load_mapping(args.field_map), args.simplify_meters, tuple(args.expected_bounds) if args.expected_bounds else None)
    provenance = {"source_files": [path.name for path in components], "source_sha256": source_digest(components), **spatial}
    geojson, dashboard = build_documents(features, load_table(args.obras), load_table(args.fornecedores), provenance, args.authority, args.legal_reference)
    write_documents(args.output, geojson, dashboard, args.replace)
    print(json.dumps({"output": str(args.output.resolve()), "status": geojson["metadata"]["status"], "zonas": len(features), "obras": len(dashboard["obras"]), "fornecedores": len(dashboard["fornecedores"]), "source_sha256": provenance["source_sha256"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
