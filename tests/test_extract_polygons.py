from pathlib import Path

import pytest

from scripts.extract_polygons import convert, extract_features, parse_points


SVG = '''<svg viewBox="0 0 100 100"><polygon points="0,0 10,0 10,10 0,10" data-sigla="ZUM" data-nome="Centro" data-to="60" /></svg>'''


def test_extract_polygon_closes_ring_and_preserves_attributes():
    features = extract_features(SVG)
    assert features[0]["properties"]["sigla"] == "ZUM"
    assert features[0]["properties"]["to_max"] == 60
    ring = features[0]["geometry"]["coordinates"][0]
    assert ring[0] == ring[-1]


def test_geographic_crs_requires_explicit_transform(tmp_path):
    source = tmp_path / "map.svg"
    source.write_text(SVG, encoding="utf-8")
    with pytest.raises(ValueError, match="transformação explícita"):
        convert(source, tmp_path / "map.geojson", "EPSG:31983")
    document = convert(source, tmp_path / "map.geojson", "EPSG:31983", (2, -2, 100, 200))
    assert document["metadata"]["georeferenced"] is True


def test_invalid_points_are_rejected():
    with pytest.raises(ValueError):
        parse_points("0,0 10,0")
