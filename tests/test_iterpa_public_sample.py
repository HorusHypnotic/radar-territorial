import importlib.util
import json
from io import BytesIO
from pathlib import Path
from unittest.mock import patch

path = Path(__file__).resolve().parents[1] / "scripts" / "fetch_iterpa_public_sample.py"
spec = importlib.util.spec_from_file_location("iterpa_sample", path)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def test_disallowed_layer_is_rejected():
    try:
        mod.fetch_sample(93)
        assert False, "Expected ValueError"
    except ValueError:
        pass


def test_sample_strips_personal_properties():
    data = {"type": "FeatureCollection", "features": [{"type": "Feature", "properties": {"cpf": "123", "nome": "EXAMPLE"}, "geometry": {"type": "Point", "coordinates": [-49, -8]}}]}
    with patch.object(mod, "urlopen", return_value=BytesIO(json.dumps(data).encode())):
        result = mod.fetch_sample(87)
    assert result["features"][0]["properties"] == {}
    assert result["metadata"]["sample_only"] is True
    assert result["metadata"]["not_a_redencao_geographic_clip"] is True
