import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

from config.settings import DATA_DIR, OUTPUT_DIR
from python.audit import registrar_evento
from python.snapshots import SNAPSHOTS_DIR


def restaurar_snapshot(timestamp: str, output_dir: Optional[Path] = None) -> dict:
    """Restaura um snapshot parquet/geojson como versão atual."""
    target_dir = output_dir or OUTPUT_DIR
    target_dir.mkdir(parents=True, exist_ok=True)

    parquet_source = SNAPSHOTS_DIR / f"radar_{timestamp}.parquet"
    geojson_source = SNAPSHOTS_DIR / f"radar_{timestamp}.geojson"

    if not parquet_source.exists() or not geojson_source.exists():
        raise FileNotFoundError(f"Snapshot {timestamp} não encontrado em {SNAPSHOTS_DIR}")

    backup_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_geojson = SNAPSHOTS_DIR / f"backup_{backup_timestamp}.geojson"
    backup_parquet = SNAPSHOTS_DIR / f"backup_{backup_timestamp}.parquet"

    if (target_dir / "radar_geojson.geojson").exists():
        shutil.copy2(target_dir / "radar_geojson.geojson", backup_geojson)
    if (target_dir / "radar_atual.parquet").exists():
        shutil.copy2(target_dir / "radar_atual.parquet", backup_parquet)

    shutil.copy2(geojson_source, target_dir / "radar_geojson.geojson")
    shutil.copy2(parquet_source, target_dir / "radar_atual.parquet")

    registrar_evento(
        "restauracao_snapshot",
        detalhes={"timestamp": timestamp, "backup": backup_timestamp},
        output_dir=target_dir,
    )

    return {
        "timestamp": timestamp,
        "restaurado": True,
        "backup": backup_timestamp,
        "geojson_path": str(target_dir / "radar_geojson.geojson"),
        "parquet_path": str(target_dir / "radar_atual.parquet"),
    }
