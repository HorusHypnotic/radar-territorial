import json

from scripts.validate_production import inspect_payload


def test_inspect_payload_accepts_required_markers():
    assert inspect_payload(
        "frontend/index.html",
        b"Dados demonstrativos theme-dark.css js/main.js",
    ) is None


def test_inspect_payload_rejects_missing_marker():
    assert inspect_payload("frontend/js/mapa.js", b"const map = {}") == (
        "marcador ausente: TerritorialMap"
    )


def test_inspect_payload_validates_geojson():
    valid = {"type": "FeatureCollection", "features": [{"type": "Feature"}]}
    assert inspect_payload("data/output/zonas_poligonos.geojson", json.dumps(valid).encode()) is None
    assert "vazia" in inspect_payload(
        "data/output/zonas_poligonos.geojson",
        b'{"type":"FeatureCollection","features":[]}',
    )
