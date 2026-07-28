import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from config.settings import DATA_DIR

SNAPSHOTS_DIR = DATA_DIR / "snapshots"


def carregar_snapshot(timestamp: str) -> pd.DataFrame:
    """Carrega um snapshot parquet pelo timestamp."""
    path = SNAPSHOTS_DIR / f"radar_{timestamp}.parquet"
    if not path.exists():
        raise FileNotFoundError(f"Snapshot não encontrado: {path}")
    return pd.read_parquet(path)


def comparar_snapshots(snapshot_a: str, snapshot_b: str) -> Dict[str, Any]:
    """Compara dois snapshots e retorna resumo de diferenças."""
    df_a = carregar_snapshot(snapshot_a)
    df_b = carregar_snapshot(snapshot_b)

    if "id" in df_a.columns and "id" in df_b.columns:
        merged = df_a.merge(df_b, on="id", how="outer", suffixes=("_a", "_b"))
    else:
        merged = pd.concat([df_a.assign(_source="a"), df_b.assign(_source="b")], ignore_index=True)

    if "indicador_ajustado_a" in merged.columns and "indicador_ajustado_b" in merged.columns:
        alterados = merged[
            (merged["indicador_ajustado_a"].fillna(-1) != merged["indicador_ajustado_b"].fillna(-1))
            & merged["id"].notna()
        ]
    else:
        alterados = merged.iloc[0:0]

    return {
        "snapshot_a": snapshot_a,
        "snapshot_b": snapshot_b,
        "total_a": int(len(df_a)),
        "total_b": int(len(df_b)),
        "alterados": int(len(alterados)),
        "detalhes": merged.to_dict(orient="records"),
    }
