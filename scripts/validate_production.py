"""Valida os arquivos essenciais publicados no GitHub Pages."""

from __future__ import annotations

import argparse
import json
import urllib.request
from dataclasses import asdict, dataclass
from urllib.parse import urljoin


DEFAULT_BASE_URL = "https://horushypnotic.github.io/radar-territorial/"


@dataclass
class Result:
    path: str
    ok: bool
    detail: str


def inspect_payload(path: str, body: bytes) -> str | None:
    """Retorna uma mensagem de erro ou ``None`` para um payload válido."""
    if not body:
        return "resposta vazia"
    text = body.decode("utf-8", errors="replace")
    markers = {
        "frontend/index.html": ("Dados demonstrativos", "theme-dark.css", "js/main.js"),
        "frontend/css/theme-dark.css": ("--shadow",),
        "frontend/js/data/sample.js": ("SAMPLE_DATA",),
        "frontend/js/mapa.js": ("TerritorialMap",),
        "frontend/sw.js": ("CACHE_NAME",),
        "frontend/manifest.webmanifest": ('"display": "standalone"', '"start_url": "./"'),
    }
    for marker in markers.get(path, ()):
        if marker not in text:
            return f"marcador ausente: {marker}"
    if path.endswith(".geojson"):
        try:
            payload = json.loads(text)
        except json.JSONDecodeError as exc:
            return f"JSON inválido: {exc.msg}"
        if payload.get("type") != "FeatureCollection" or not payload.get("features"):
            return "FeatureCollection vazia ou inválida"
    return None


def validate(base_url: str = DEFAULT_BASE_URL, timeout: float = 15) -> list[Result]:
    paths = (
        "",
        "frontend/index.html",
        "frontend/css/theme-dark.css",
        "frontend/js/data/sample.js",
        "frontend/js/mapa.js",
        "frontend/sw.js",
        "frontend/manifest.webmanifest",
        "frontend/icons/icon-192.png",
        "frontend/icons/icon-512.png",
        "data/output/zonas_poligonos.geojson",
        "data/output/livro_razao.json",
    )
    results: list[Result] = []
    base_url = base_url.rstrip("/") + "/"
    for path in paths:
        url = urljoin(base_url, path)
        request = urllib.request.Request(
            url,
            headers={"Cache-Control": "no-cache", "User-Agent": "OPERA-production-validator/1.0"},
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                body = response.read()
                error = inspect_payload(path, body)
                status = getattr(response, "status", 200)
                ok = status == 200 and error is None
                detail = error or f"HTTP {status}, {len(body)} bytes"
        except Exception as exc:  # urllib agrupa falhas HTTP, TLS e rede.
            ok, detail = False, f"{type(exc).__name__}: {exc}"
        results.append(Result(path or "/", ok, detail))
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--timeout", type=float, default=15)
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()
    results = validate(args.base_url, args.timeout)
    if args.as_json:
        print(json.dumps([asdict(result) for result in results], ensure_ascii=False, indent=2))
    else:
        for result in results:
            print(f"{'OK' if result.ok else 'ERRO':4} {result.path}: {result.detail}")
    return 0 if all(result.ok for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
