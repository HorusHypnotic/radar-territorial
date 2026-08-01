"""Converte memoriais descritivos da LC 128/2022 de UTM 22S para GeoJSON.

O extrator aceita as duas grafias presentes na lei (``N ... e E ...`` e
``E: ... e N: ...``), associa cada coordenada ao vértice P.xx e rejeita
sequências incompletas. OCR deve ser revisado: o script não tenta adivinhar
dígitos ilegíveis.
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pyproj import Transformer

SOURCE_CRS = "EPSG:31983"  # SIRGAS 2000 / UTM zone 22S
TARGET_CRS = "EPSG:4326"
TRANSFORMER = Transformer.from_crs(SOURCE_CRS, TARGET_CRS, always_xy=True)

ZONE_MEMORIALS = {
    6: ("ZUM-01", "Zona de Uso Misto — Área 01"),
    7: ("ZUM-02", "Zona de Uso Misto — Área 02"),
    8: ("ZUM-03", "Zona de Uso Misto — Área 03"),
    9: ("ZIR-PLI", "ZIR — Parque Logístico Industrial"),
    10: ("ZIR-MIL-01", "ZIR — Micro Industrial Leste — Área 01"),
    11: ("ZIR-MIL-02", "ZIR — Micro Industrial Leste — Área 02"),
    12: ("ZOR-ZACR", "ZOR — Zona de Abastecimento e Chácaras de Recreio"),
    13: ("ZOR-ZPA", "ZOR — Zona de Proteção do Aeródromo"),
}

NUMBER = r"(?:[0-9]{1,3}(?:\.[0-9]{3})+,[0-9]{2,3}|[0-9]{3,7},[0-9]{2,3}|[0-9]+\.[0-9]{2,3})"
VERTEX = re.compile(r"v\S{0,8}rtice\s+P[.\s]*(\d{1,3})", re.IGNORECASE)
NE_PAIR = re.compile(
    rf"N\s*:*\s*({NUMBER})\s*m?\s*(?:e|,|;)\s*E\s*:*\s*({NUMBER})",
    re.IGNORECASE,
)
EN_PAIR = re.compile(
    rf"E\s*:*\s*({NUMBER})\s*m?\s*(?:e|,|;)\s*N\s*:*\s*({NUMBER})",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class Vertex:
    number: int
    easting: float
    northing: float


def parse_brazilian_number(value: str) -> float:
    """Interpreta 9.121.647,78 e 601.668,493 sem perder casas decimais."""
    value = value.strip().replace(" ", "")
    if "," in value:
        return float(value.replace(".", "").replace(",", "."))
    head, dot, tail = value.rpartition(".")
    if dot and len(tail) in (2, 3) and head.count(".") >= 1:
        return float(head.replace(".", "") + "." + tail)
    return float(value)


def split_memorials(text: str) -> dict[int, str]:
    markers = list(re.finditer(r"MEMORIAL\s+DESCRITIVO\s*-\s*(\d+)", text, re.IGNORECASE))
    result: dict[int, str] = {}
    for index, marker in enumerate(markers):
        end = markers[index + 1].start() if index + 1 < len(markers) else len(text)
        result[int(marker.group(1))] = text[marker.start():end]
    return result


def _coordinate_after(section: str, start: int, end: int) -> tuple[float, float] | None:
    fragment = section[start:end]
    candidates: list[tuple[int, float, float]] = []
    for match in NE_PAIR.finditer(fragment):
        candidates.append((match.start(), parse_brazilian_number(match.group(2)), parse_brazilian_number(match.group(1))))
    for match in EN_PAIR.finditer(fragment):
        candidates.append((match.start(), parse_brazilian_number(match.group(1)), parse_brazilian_number(match.group(2))))
    if not candidates:
        return None
    _, easting, northing = min(candidates, key=lambda item: item[0])
    return easting, northing


def parse_vertices(section: str) -> list[Vertex]:
    """Extrai uma sequência P.01..P.nn; falha diante de lacunas ou OCR ambíguo."""
    # Cabeçalhos/rodapés interrompem pares E/N quando uma coordenada cruza página.
    section = "\n".join(
        line for line in section.splitlines()
        if not re.search(r"Rua Guarant|ESTADO DO PAR|PREFEITURA DE REDEN|GABINETE DO PREFEITO", line, re.I)
        and not re.fullmatch(r"\s*\d{1,3}\s*", line)
        and not line.lstrip().startswith("[PDD")
        and not (line.count("â") > 4 or line.count("Ã") > 8)
    )
    # Erro recorrente e visualmente inequívoco do Tesseract: o algarismo 1
    # imediatamente antes da unidade ``m`` é reconhecido como ``i``.
    section = re.sub(r"(?<=\d)i(?=m\b)", "1", section, flags=re.IGNORECASE)
    section = re.sub(r"\b(\d{3}),(\d{3}),(\d{2,3})(?!\d)", r"\1.\2,\3", section)
    matches = list(VERTEX.finditer(section))
    found: dict[int, Vertex] = {}
    for index, match in enumerate(matches):
        number = int(match.group(1))
        limit = matches[index + 1].start() if index + 1 < len(matches) else min(len(section), match.end() + 500)
        coordinate = _coordinate_after(section, match.end(), limit)
        if coordinate and number not in found:
            found[number] = Vertex(number, *coordinate)
    if len(found) < 3:
        raise ValueError("menos de três vértices legíveis")
    expected = list(range(1, max(found) + 1))
    missing = [number for number in expected if number not in found]
    if missing:
        raise ValueError(f"vértices ausentes/ilegíveis: {missing}")
    vertices = [found[number] for number in expected]
    for vertex in vertices:
        if not (500_000 <= vertex.easting <= 700_000 and 9_000_000 <= vertex.northing <= 9_300_000):
            raise ValueError(f"P.{vertex.number:02d} fora da faixa esperada: E={vertex.easting}, N={vertex.northing}")
    return vertices


def feature_from_vertices(memorial: int, vertices: list[Vertex]) -> dict[str, Any]:
    code, name = ZONE_MEMORIALS[memorial]
    ring = [list(TRANSFORMER.transform(vertex.easting, vertex.northing)) for vertex in vertices]
    ring.append(ring[0].copy())
    return {
        "type": "Feature",
        "properties": {
            "id": code.lower(), "sigla": code.split("-")[0], "nome": name,
            "memorial": memorial, "vertex_count": len(vertices),
            "source_crs": SOURCE_CRS, "source": "Lei Complementar nº 128/2022 — Anexo II-B",
        },
        "geometry": {"type": "Polygon", "coordinates": [ring]},
    }


def convert_text(text: str, strict: bool = True) -> dict[str, Any]:
    sections = split_memorials(text)
    features, errors = [], []
    for memorial in ZONE_MEMORIALS:
        try:
            features.append(feature_from_vertices(memorial, parse_vertices(sections[memorial])))
        except (KeyError, ValueError) as exc:
            errors.append({"memorial": memorial, "error": str(exc)})
    if strict and errors:
        detail = "; ".join(f"{item['memorial']}: {item['error']}" for item in errors)
        raise ValueError(f"extração incompleta; revise o OCR ({detail})")
    return {
        "type": "FeatureCollection",
        "metadata": {
            "source": "Lei Complementar nº 128/2022 — Plano Diretor de Redenção-PA",
            "source_crs": SOURCE_CRS, "crs": TARGET_CRS,
            "official_source": "https://redencao.pa.gov.br/publicacoes/legislacoes/lei/4165/lei-complementar-no-1282022",
            "ocr_review_required": bool(errors), "errors": errors,
            "note": "ZUPA não é um anel único: o Memorial 14 a define por faixas ambientais de 15 a 100 m.",
        },
        "features": features,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="Texto UTF-8 extraído/OCR da lei")
    parser.add_argument("output", type=Path)
    parser.add_argument("--allow-partial", action="store_true", help="Grava apenas memoriais completos e lista erros")
    args = parser.parse_args()
    document = convert_text(args.source.read_text(encoding="utf-8-sig"), strict=not args.allow_partial)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(document, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Polígonos: {len(document['features'])}; pendências: {len(document['metadata']['errors'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
