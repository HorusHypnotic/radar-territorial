"""Monta o artefato mínimo e sanitizado para o GitHub Pages."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parents[2]
PUBLIC_OUTPUT_FILES = (
    "dashboard_data.json",
    "radar_geojson.geojson",
    "zonas_poligonos.geojson",
    "auditoria.json",
    "livro_razao.json",
    "validacao_gis_lc128.json",
)


def load_json(path: Path, fallback: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return fallback


def sanitized_snapshots(source: Path) -> dict[str, Any]:
    """Publica somente metadados não sensíveis e hashes verificáveis."""
    index = load_json(source / "index.json", {})
    items = index.get("snapshots", []) if isinstance(index, dict) else []
    public_items = []
    for item in items:
        timestamp = str(item.get("timestamp", ""))
        metadata = load_json(source / f"radar_{timestamp}_metadata.json", {})
        public_items.append(
            {
                "timestamp": timestamp,
                "total_registros": item.get("total_registros", metadata.get("total_registros", 0)),
                "indicadores": item.get("indicadores", {}),
                "hashes": metadata.get("hashes", item.get("hashes", {})),
            }
        )
    return {"snapshots": public_items}


def build(output_dir: Path) -> Path:
    """Cria um site autocontido sem código backend, segredos ou dados brutos."""
    resolved = output_dir.resolve()
    if resolved == BASE_DIR or BASE_DIR not in resolved.parents:
        raise ValueError("O diretório do artefato deve ficar dentro do projeto e não pode ser a raiz")
    if resolved.exists():
        shutil.rmtree(resolved)
    (resolved / "data" / "output").mkdir(parents=True)
    (resolved / "data" / "snapshots").mkdir(parents=True)
    shutil.copy2(BASE_DIR / "index.html", resolved / "index.html")
    shutil.copytree(BASE_DIR / "frontend", resolved / "frontend")
    for name in PUBLIC_OUTPUT_FILES:
        source = BASE_DIR / "data" / "output" / name
        if source.is_file():
            shutil.copy2(source, resolved / "data" / "output" / name)
    snapshot_index = sanitized_snapshots(BASE_DIR / "data" / "snapshots")
    (resolved / "data" / "snapshots" / "index.json").write_text(json.dumps(snapshot_index, ensure_ascii=False, indent=2), encoding="utf-8")
    (resolved / ".nojekyll").touch()
    return resolved


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=BASE_DIR / "_site")
    args = parser.parse_args()
    print(build(args.output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
