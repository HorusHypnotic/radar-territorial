"""Valida o artefato estático antes do deploy."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from python.modules.build_static_site import BASE_DIR, build


def validate(output: Path = BASE_DIR / "_site") -> list[str]:
    root = build(output)
    required = ("index.html","frontend/index.html","frontend/sw.js","frontend/js/main.js","frontend/js/data/sample.js","frontend/css/theme-dark.css","frontend/vendor/leaflet/leaflet.js","data/output/dashboard_data.json","data/output/zonas_poligonos.geojson")
    errors = [f"ausente: {name}" for name in required if not (root / name).is_file()]
    html = (root / "frontend" / "index.html").read_text(encoding="utf-8")
    if re.search(r'<(?:script|link)[^>]+https?://', html, re.IGNORECASE):
        errors.append("HTML contém dependência externa")
    geojson = json.loads((root / "data" / "output" / "zonas_poligonos.geojson").read_text(encoding="utf-8"))
    if geojson.get("type") != "FeatureCollection" or not geojson.get("features"):
        errors.append("GeoJSON territorial vazio ou inválido")
    if list(root.rglob("*.parquet")) or (root / "server.py").exists():
        errors.append("artefato contém arquivos privados/backend")
    return errors


if __name__ == "__main__":
    problems = validate()
    if problems:
        raise SystemExit("\n".join(problems))
    print("Artefato estático validado com sucesso")
