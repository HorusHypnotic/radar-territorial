"""Extrai polígonos SVG/HTML sem inventar um sistema de referência geográfica."""

from __future__ import annotations

import argparse
import json
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Optional


class PolygonParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.polygons: list[dict[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, Optional[str]]]) -> None:
        if tag.lower() == "polygon":
            self.polygons.append({key: value or "" for key, value in attrs})


def parse_points(value: str) -> list[list[float]]:
    normalized = value.replace("\n", " ").replace("\t", " ").strip()
    points = []
    for pair in normalized.split():
        parts = pair.split(",")
        if len(parts) != 2:
            raise ValueError(f"Par de coordenadas SVG inválido: {pair}")
        points.append([float(parts[0]), float(parts[1])])
    if len(points) < 3:
        raise ValueError("Polígono deve ter ao menos três vértices")
    if points[0] != points[-1]:
        points.append(points[0].copy())
    return points


def extract_features(content: str, transform: Optional[tuple[float, float, float, float]] = None) -> list[dict[str, Any]]:
    parser = PolygonParser()
    parser.feed(content)
    features = []
    for index, attrs in enumerate(parser.polygons):
        if not attrs.get("points"):
            continue
        points = parse_points(attrs["points"])
        if transform:
            scale_x, scale_y, offset_x, offset_y = transform
            points = [[x * scale_x + offset_x, y * scale_y + offset_y] for x, y in points]
        properties = {
            "id": attrs.get("data-id") or f"svg-zone-{index + 1}",
            "sigla": attrs.get("data-sigla") or attrs.get("id") or f"Z{index + 1}",
            "nome": attrs.get("data-nome") or attrs.get("aria-label") or f"Zona {index + 1}",
            "macrozona": attrs.get("data-macro") or None,
        }
        numeric = {"data-to":"to_max","data-cab":"ca_basico","data-cam":"ca_maximo","data-perm":"permeabilidade","data-alt":"altura_max","data-area":"area_m2","data-lotes":"lotes","data-conf":"conformidade"}
        for source, target in numeric.items():
            if attrs.get(source):
                properties[target] = float(attrs[source])
        features.append({"type":"Feature","properties":properties,"geometry":{"type":"Polygon","coordinates":[points]}})
    return features


def convert(source: Path, output: Path, crs: str = "LOCAL:SVG", transform: Optional[tuple[float, float, float, float]] = None) -> dict[str, Any]:
    if crs != "LOCAL:SVG" and transform is None:
        raise ValueError("CRS geográfico exige transformação explícita; pixels SVG não são coordenadas reais")
    features = extract_features(source.read_text(encoding="utf-8"), transform)
    if not features:
        raise ValueError("Nenhum elemento <polygon points=...> encontrado")
    document = {"type":"FeatureCollection","metadata":{"crs":crs,"source":source.name,"georeferenced":transform is not None,"total_features":len(features)},"features":features}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(document, ensure_ascii=False, indent=2), encoding="utf-8")
    return document


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--crs", default="LOCAL:SVG")
    parser.add_argument("--transform", nargs=4, type=float, metavar=("SCALE_X","SCALE_Y","OFFSET_X","OFFSET_Y"))
    args = parser.parse_args()
    document = convert(args.source, args.output, args.crs, tuple(args.transform) if args.transform else None)
    print(f"Polígonos extraídos: {len(document['features'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
