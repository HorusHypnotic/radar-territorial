import pytest

from scripts.convert_utm_to_geojson import convert_text, parse_brazilian_number, parse_vertices


def test_brazilian_numbers_preserve_decimals():
    assert parse_brazilian_number("9.121.647,78") == 9121647.78
    assert parse_brazilian_number("601.668,493") == 601668.493


def test_both_coordinate_orders_are_supported():
    text = """vértice P.01, coordenadas N 9.121.647,78m e E 603.909,57m;
    vértice P.02, definido pelas coordenadas E: 604.119,950 m e N: 9.121.619,680 m;
    vértice P.03, coordenadas N 9.121.293,41m e E 604.387,36m"""
    vertices = parse_vertices(text)
    assert [(v.number, v.easting, v.northing) for v in vertices] == [
        (1, 603909.57, 9121647.78), (2, 604119.95, 9121619.68), (3, 604387.36, 9121293.41)
    ]


def test_common_ocr_artifacts_are_normalized():
    text = """vértice P.01, coordenadas N 9.121.255,23m e E 604,734,65m;
    vértice P.02, coordenadas N 9.121.234,4im e E 604.870,10m;
    vértice P.03, coordenadas E: 606.676,943 m
    [PDD OCR HEADER NOISE]
    e N: 9.113.759,440 m"""
    vertices = parse_vertices(text)
    assert vertices[0].easting == 604734.65
    assert vertices[1].northing == 9121234.41
    assert vertices[2].easting == 606676.943


def test_missing_vertex_is_rejected():
    text = """vértice P.01, coordenadas N 9.121.647,78m e E 603.909,57m;
    vértice P.03, coordenadas N 9.121.293,41m e E 604.387,36m;
    vértice P.04, coordenadas N 9.120.900,00m e E 604.500,00m"""
    with pytest.raises(ValueError, match="vértices ausentes"):
        parse_vertices(text)


def test_partial_mode_reports_unreadable_memorials():
    document = convert_text("MEMORIAL DESCRITIVO - 6\nsem coordenadas", strict=False)
    assert document["features"] == []
    assert document["metadata"]["ocr_review_required"] is True
