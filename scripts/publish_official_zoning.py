"""Valida e publica o zoneamento extraído da LC 128/2022 no dashboard."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import date
from pathlib import Path
from typing import Any

EXPECTED_IDS = {"zum-01", "zum-02", "zum-03", "zir-pli", "zir-mil-01", "zir-mil-02", "zor-zacr", "zor-zpa"}


def validate(document: dict[str, Any]) -> None:
    if document.get("type") != "FeatureCollection":
        raise ValueError("GeoJSON deve ser uma FeatureCollection")
    metadata = document.get("metadata", {})
    if metadata.get("errors") or metadata.get("ocr_review_required"):
        raise ValueError("GeoJSON ainda possui pendências de OCR")
    ids = {feature.get("properties", {}).get("id") for feature in document.get("features", [])}
    if ids != EXPECTED_IDS:
        raise ValueError(f"memoriais divergentes: ausentes={sorted(EXPECTED_IDS - ids)}, extras={sorted(ids - EXPECTED_IDS)}")
    for feature in document["features"]:
        ring = feature.get("geometry", {}).get("coordinates", [[]])[0]
        expected = feature["properties"].get("vertex_count", 0) + 1
        if len(ring) != expected or not ring or ring[0] != ring[-1]:
            raise ValueError(f"anel inválido em {feature['properties'].get('id')}")
        if any(not (-180 <= point[0] <= 180 and -90 <= point[1] <= 90) for point in ring):
            raise ValueError(f"coordenada WGS84 inválida em {feature['properties'].get('id')}")


def build_dashboard(document: dict[str, Any], digest: str) -> dict[str, Any]:
    zones = []
    for feature in document["features"]:
        props = feature["properties"]
        zones.append({
            "id": props["id"], "sigla": props["sigla"], "tipo": props["sigla"],
            "nome": props["nome"], "macrozona": "Urbana", "memorial": props["memorial"],
            "vertices": props["vertex_count"], "referencia_legal": "LC 128/2022, Anexo II-B",
            "recomendacao": "Consulta informativa; confirme a legislação vigente e as regras aplicáveis ao lote.",
        })
    return {
        "metadata": {
            "status": "oficial", "source": document["metadata"]["source"],
            "updated_at": date.today().isoformat(), "sha256": digest,
            "coverage": "8/8 memoriais de zoneamento com coordenadas", "total_vertices": sum(z["vertices"] for z in zones),
            "notice": "ZUPA é definida por faixas ambientais no Memorial 14 e não integra estes oito anéis.",
        },
        "zonas": zones, "obras": [], "fornecedores": [],
    }


def publish(source: Path, root: Path) -> list[Path]:
    document = json.loads(source.read_text(encoding="utf-8"))
    validate(document)
    canonical = json.dumps(document, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    digest = hashlib.sha256(canonical).hexdigest()
    document["metadata"].update({
        "status": "oficial", "coverage": "8/8", "total_features": 8,
        "total_vertices": sum(f["properties"]["vertex_count"] for f in document["features"]),
        "sha256": digest, "published_at": date.today().isoformat(),
    })
    dashboard = build_dashboard(document, digest)
    targets = {
        root / "data/output/zonas_oficiais_consolidado.geojson": document,
        root / "data/output/zonas_poligonos.geojson": document,
        root / "frontend/data/zonas_oficiais_consolidado.geojson": document,
        root / "data/output/dashboard_data.json": dashboard,
        root / "frontend/data/dashboard_oficial.json": dashboard,
    }
    for path, payload in targets.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return list(targets)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=Path("data/output/zonas_oficiais_lc128.geojson"))
    parser.add_argument("--root", type=Path, default=Path("."))
    args = parser.parse_args()
    paths = publish(args.source, args.root.resolve())
    print(f"Publicação validada: {len(paths)} arquivos; cobertura 8/8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
