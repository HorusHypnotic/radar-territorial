import json

import pytest

from scripts.generate_test_data import generate_documents, generate_test_data


def test_synthetic_documents_are_deterministic_and_candidate():
    first, dashboard = generate_documents(seed=7, zones=4, works=3, suppliers=2)
    second, _ = generate_documents(seed=7, zones=4, works=3, suppliers=2)
    assert first["features"] == second["features"]
    assert first["metadata"]["status"] == "candidato"
    assert first["metadata"]["synthetic"] is True
    assert len(dashboard["obras"]) == 3 and len(dashboard["fornecedores"]) == 2


def test_synthetic_package_passes_existing_validator(tmp_path):
    result = generate_test_data(tmp_path / "test", seed=9, zones=3, works=2, suppliers=1)
    assert result["valid"] is True and result["status"] == "candidato"
    payload = json.loads((tmp_path / "test" / "zonas_poligonos.geojson").read_text(encoding="utf-8"))
    assert all(feature["properties"]["tipo"] == "SINTETICO" for feature in payload["features"])


def test_synthetic_generator_rejects_invalid_counts():
    with pytest.raises(ValueError, match="--zones"):
        generate_documents(zones=0)
