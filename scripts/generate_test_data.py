"""Gera um pacote sintético, determinístico e nunca oficial para o OPERA."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
from pathlib import Path
from typing import Any
from uuid import NAMESPACE_URL, uuid5

try:
    from scripts.export_qgis_to_opera import build_documents, validate_export, write_documents
except ModuleNotFoundError:  # execução direta: python scripts/generate_test_data.py
    from export_qgis_to_opera import build_documents, validate_export, write_documents


PROTECTED_OUTPUTS = (Path("data/output"), Path("frontend/data"))


def _polygon(latitude: float, longitude: float, radius_km: float, points: int = 8) -> list[list[float]]:
    ring = []
    for index in range(points):
        angle = 2 * math.pi * index / points
        lat = latitude + (radius_km / 111.0) * math.cos(angle)
        lng = longitude + (radius_km / (111.0 * math.cos(math.radians(latitude)))) * math.sin(angle)
        ring.append([round(lng, 7), round(lat, 7)])
    ring.append(ring[0])
    return ring


def generate_documents(*, seed: int = 2026, zones: int = 9, works: int = 15, suppliers: int = 10, center_lat: float = -8.978, center_lng: float = -50.018) -> tuple[dict[str, Any], dict[str, Any]]:
    if not 1 <= zones <= 100:
        raise ValueError("--zones deve estar entre 1 e 100")
    if not 0 <= works <= 10_000 or not 0 <= suppliers <= 10_000:
        raise ValueError("quantidades devem estar entre 0 e 10000")
    if not -90 < center_lat < 90 or not -180 <= center_lng <= 180:
        raise ValueError("centro geográfico inválido")
    rng = random.Random(seed)
    columns = math.ceil(math.sqrt(zones))
    features = []
    for index in range(zones):
        row, column = divmod(index, columns)
        latitude = center_lat + (row - (columns - 1) / 2) * 0.045
        longitude = center_lng + (column - (columns - 1) / 2) * 0.045
        zone_id = str(uuid5(NAMESPACE_URL, f"opera:synthetic:{seed}:zone:{index + 1}"))
        properties = {
            "id": zone_id, "sigla": f"T{index + 1:03d}", "nome": f"Cenário sintético {index + 1:02d}",
            "tipo": "SINTETICO", "categoria": "Dado de teste", "area_m2": rng.randint(1_000_000, 8_000_000),
            "to_max": rng.randint(20, 75), "ca_basico": round(rng.uniform(0.5, 1.8), 1),
            "ca_maximo": round(rng.uniform(1.8, 4.0), 1), "permeabilidade": rng.randint(15, 60),
            "altura_max": rng.randint(6, 30), "lotes": rng.randint(20, 180), "conformidade": rng.randint(45, 95),
        }
        features.append({"type": "Feature", "id": zone_id, "properties": properties, "geometry": {"type": "Polygon", "coordinates": [_polygon(latitude, longitude, 1.2)]}})
    zone_ids = [feature["properties"]["id"] for feature in features]
    obras = [{"id": str(uuid5(NAMESPACE_URL, f"opera:synthetic:{seed}:work:{index + 1}")), "nome": f"Obra sintética {index + 1:03d}", "zona_id": zone_ids[index % len(zone_ids)], "status": rng.choice(["planejada", "andamento", "concluida", "paralisada"]), "ico": rng.randint(40, 95)} for index in range(works)]
    fornecedores = [{"id": str(uuid5(NAMESPACE_URL, f"opera:synthetic:{seed}:supplier:{index + 1}")), "nome": f"Fornecedor sintético {index + 1:03d}", "ativo": rng.random() > 0.2, "tipo": rng.choice(["Material", "Serviço", "Equipamento"])} for index in range(suppliers)]
    recipe = json.dumps({"seed": seed, "zones": zones, "works": works, "suppliers": suppliers, "center": [center_lat, center_lng]}, sort_keys=True)
    provenance = {"source_files": [], "source_sha256": hashlib.sha256(recipe.encode("utf-8")).hexdigest(), "source_type": "synthetic-test-data", "synthetic": True, "seed": seed}
    return build_documents(features, obras, fornecedores, provenance, None, None)


def generate_test_data(output: Path, *, replace: bool = False, **options: Any) -> dict[str, Any]:
    protected = {(Path.cwd() / path).resolve() for path in PROTECTED_OUTPUTS}
    if output.resolve() in protected:
        raise ValueError("dados sintéticos não podem ser gravados em data/output ou frontend/data")
    geojson, dashboard = generate_documents(**options)
    write_documents(output, geojson, dashboard, replace=replace)
    return validate_export(output)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("data/test"))
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--zones", type=int, default=9)
    parser.add_argument("--obras", type=int, default=15)
    parser.add_argument("--fornecedores", type=int, default=10)
    parser.add_argument("--center", type=float, nargs=2, metavar=("LAT", "LNG"), default=(-8.978, -50.018))
    parser.add_argument("--replace", action="store_true")
    args = parser.parse_args()
    result = generate_test_data(args.output, replace=args.replace, seed=args.seed, zones=args.zones, works=args.obras, suppliers=args.fornecedores, center_lat=args.center[0], center_lng=args.center[1])
    print(json.dumps({"output": str(args.output.resolve()), **result, "synthetic": True}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
