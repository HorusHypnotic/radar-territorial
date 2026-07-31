from pathlib import Path

import pandas as pd

from python.audit import carregar_auditoria, registrar_evento
from python.pipeline import PipelineRadar
from python.restore import restaurar_snapshot
from python.snapshots import salvar_snapshot


def test_project_structure_exists():
    base = Path(__file__).resolve().parent.parent
    assert (base / "python" / "pipeline.py").exists()
    assert (base / "config" / "settings.py").exists()
    assert (base / "requirements.txt").exists()


def test_transform_creates_staging_file(tmp_path, monkeypatch):
    monkeypatch.setattr("python.pipeline.STAGING_DIR", tmp_path)
    monkeypatch.setattr("python.pipeline.registrar_evento", lambda *args, **kwargs: None)
    pipeline = PipelineRadar.__new__(PipelineRadar)
    df = pd.DataFrame(
        [{"id": 1, "nome": "A", "indicador": 1.0, "data_coleta": "2026-01-01", "latitude": -15.0, "longitude": -47.0}]
    )
    transformed = pipeline.transform(df)
    assert not transformed.empty
    assert (tmp_path / "radar_staging.parquet").exists()


def test_registrar_evento_cria_auditoria_json(tmp_path):
    output_dir = tmp_path / "output"
    entry = registrar_evento("teste", detalhes={"status": "ok"}, output_dir=output_dir)

    assert entry["evento"] == "teste"
    assert (output_dir / "auditoria.json").exists()
    assert len(carregar_auditoria(output_dir=output_dir)) == 1


def test_restaurar_snapshot_cria_arquivos(tmp_path):
    output_dir = tmp_path / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "radar_geojson.geojson").write_text('{"type": "FeatureCollection", "features": []}', encoding="utf-8")
    (output_dir / "radar_atual.parquet").write_bytes(b"original")

    snapshot_dir = tmp_path / "snapshots"
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    (snapshot_dir / "radar_20260101_010101.geojson").write_text('{"type": "FeatureCollection", "features": []}', encoding="utf-8")
    (snapshot_dir / "radar_20260101_010101.parquet").write_bytes(b"snapshot")

    import python.restore as restore_module
    restore_module.SNAPSHOTS_DIR = snapshot_dir

    result = restaurar_snapshot("20260101_010101", output_dir=output_dir)

    assert result["restaurado"] is True
    assert (output_dir / "radar_geojson.geojson").exists()
    assert (output_dir / "radar_atual.parquet").exists()


def test_salvar_snapshot_inclui_hashes(tmp_path):
    import python.snapshots as snapshots_module

    snapshots_module.SNAPSHOTS_DIR = tmp_path / "snapshots"
    snapshots_module.SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    snapshots_module.OUTPUT_DIR = tmp_path / "output"
    snapshots_module.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (snapshots_module.OUTPUT_DIR / "radar_geojson.geojson").write_text('{"type": "FeatureCollection", "features": []}', encoding="utf-8")

    df = pd.DataFrame([{"id": 1, "indicador_ajustado": 1.2}])
    metadata = salvar_snapshot(df)

    assert metadata["hashes"].get("parquet")
    assert metadata["hashes"].get("geojson")
