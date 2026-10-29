"""Três cenários locais, sem rede e sem atributos pessoais."""
import importlib.util
from pathlib import Path

path = Path(__file__).resolve().parents[1] / "scripts" / "validate_iterpa_response.py"
spec = importlib.util.spec_from_file_location("iterpa_response", path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_valid_response():
    result = module.validate({"features": [{"geometry": {"rings": []}}], "spatialReference": {"wkid": 4326}})
    assert result["status"] == "PARSED"
    assert result["features"] == 1
    assert result["geometries"] == 1


def test_arcgis_error():
    assert module.validate({"error": {"code": 403}})["status"] == "BLOCKED"


def test_missing_features():
    assert module.validate({"foo": "bar"})["reason"] == "missing_features"
