import hashlib
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd

from config.settings import DATA_DIR, OUTPUT_DIR

SNAPSHOTS_DIR = DATA_DIR / "snapshots"
SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)


def calcular_hash_arquivo(caminho: Path | str) -> str:
    """Calcula o hash SHA-256 de um arquivo."""
    path = Path(caminho)
    if not path.exists():
        return ""

    sha256 = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(4096), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def salvar_snapshot(
    df: pd.DataFrame,
    metadata_extra: Optional[Dict[str, Any]] = None,
    geojson_path: Optional[Path | str] = None,
) -> Dict[str, Any]:
    """Salva uma versão histórica dos dados em parquet e registra metadados."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    parquet_path = SNAPSHOTS_DIR / f"radar_{timestamp}.parquet"
    df.to_parquet(parquet_path, index=False)

    geojson_target = None
    if geojson_path is None:
        geojson_path = OUTPUT_DIR / "radar_geojson.geojson"

    geojson_source = Path(geojson_path)
    if geojson_source.exists():
        geojson_target = SNAPSHOTS_DIR / f"radar_{timestamp}.geojson"
        shutil.copy2(geojson_source, geojson_target)

    indicadores = {}
    if "indicador_ajustado" in df.columns:
        indicadores = {
            "media": float(df["indicador_ajustado"].mean()) if not df.empty else None,
            "max": float(df["indicador_ajustado"].max()) if not df.empty else None,
            "min": float(df["indicador_ajustado"].min()) if not df.empty else None,
        }

    metadata = {
        "timestamp": timestamp,
        "total_registros": int(len(df)),
        "arquivos": {
            "parquet": str(parquet_path),
            "geojson": str(geojson_target) if geojson_target is not None else None,
        },
        "indicadores": indicadores,
        "extra": metadata_extra or {},
        "hashes": {},
    }

    if parquet_path.exists():
        metadata["hashes"]["parquet"] = calcular_hash_arquivo(parquet_path)
    if geojson_target is not None and geojson_target.exists():
        metadata["hashes"]["geojson"] = calcular_hash_arquivo(geojson_target)

    metadata_path = SNAPSHOTS_DIR / f"radar_{timestamp}_metadata.json"
    metadata_path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")

    index_path = SNAPSHOTS_DIR / "index.json"
    if index_path.exists():
        try:
            index = json.loads(index_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            index = {"snapshots": []}
    else:
        index = {"snapshots": []}

    if not isinstance(index.get("snapshots"), list):
        index["snapshots"] = []

    index["snapshots"].append(metadata)
    index_path.write_text(json.dumps(index, indent=2, ensure_ascii=False), encoding="utf-8")

    return metadata


def verificar_integridade(timestamp: str) -> Dict[str, Any]:
    """Verifica se os arquivos de um snapshot foram alterados."""
    metadata_path = SNAPSHOTS_DIR / f"radar_{timestamp}_metadata.json"
    if not metadata_path.exists():
        return {"timestamp": timestamp, "integridade": "indisponivel"}

    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    hashes = metadata.get("hashes", {})
    resultado = {"timestamp": timestamp, "integridade": "ok"}

    for nome, hash_esperado in hashes.items():
        candidato = None
        if nome == "parquet":
            candidato = SNAPSHOTS_DIR / f"radar_{timestamp}.parquet"
        elif nome == "geojson":
            candidato = SNAPSHOTS_DIR / f"radar_{timestamp}.geojson"
        if candidato and candidato.exists():
            hash_atual = calcular_hash_arquivo(candidato)
            resultado[nome] = hash_atual == hash_esperado
        else:
            resultado[nome] = False

    if resultado.get("parquet") is False or resultado.get("geojson") is False:
        resultado["integridade"] = "comprometida"
    return resultado


def carregar_snapshots() -> list[Dict[str, Any]]:
    """Carrega o índice de snapshots históricos."""
    index_path = SNAPSHOTS_DIR / "index.json"
    if not index_path.exists():
        return []

    try:
        data = json.loads(index_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []

    return data.get("snapshots", []) if isinstance(data, dict) else []
