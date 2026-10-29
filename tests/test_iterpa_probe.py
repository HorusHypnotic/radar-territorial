"""Testes offline da sonda de metadados, sem conexão externa."""
import importlib.util
from pathlib import Path
from unittest.mock import patch
from io import BytesIO

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "probe_iterpa_layers.py"
spec = importlib.util.spec_from_file_location("probe_iterpa_layers", MODULE_PATH)
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)


def test_layer_ids_are_pinned():
    assert probe.LAYERS == (87, 72, 73, 63, 64, 93, 98)


def test_fetch_metadata_only_returns_schema_and_flags_sensitive_fields():
    payload = b'{"name":"Teste","geometryType":"esriGeometryPolygon","capabilities":"Map,Query","fields":[{"name":"cpf_requerente"},{"name":"OBJECTID"}]}'
    with patch.object(probe, "urlopen", return_value=BytesIO(payload)):
        result = probe.fetch_metadata(93)
    assert result["has_personal_data_risk"] is True
    assert result["field_names"] == ["cpf_requerente", "OBJECTID"]
    assert result["supportsQuery"] is True
