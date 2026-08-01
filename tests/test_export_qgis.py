import json
from pathlib import Path

import pytest

from scripts.export_qgis_to_opera import (
    build_documents,
    convert_dataset,
    json_value,
    load_mapping,
    require_shapefile_components,
    source_digest,
    validate_bounds,
    validate_properties,
    write_documents,
)


def make_shapefile_set(tmp_path: Path) -> Path:
    source = tmp_path / "zoneamento.shp"
    for suffix in (".shp", ".shx", ".dbf", ".prj"):
        (tmp_path / f"zoneamento{suffix}").write_bytes(suffix.encode())
    return source


def test_shapefile_requires_prj_and_has_stable_digest(tmp_path):
    source = make_shapefile_set(tmp_path)
    paths = require_shapefile_components(source)
    assert len(paths) == 4 and len(source_digest(paths)) == 64
    (tmp_path / "zoneamento.prj").unlink()
    with pytest.raises(ValueError, match=".prj"):
        require_shapefile_components(source)


def test_mapping_and_values_do_not_invent_legal_attributes(tmp_path):
    mapping_path = tmp_path / "map.json"
    mapping_path.write_text(json.dumps({"COD": "sigla", "DESCR": "nome"}), encoding="utf-8")
    assert load_mapping(mapping_path) == {"COD": "sigla", "DESCR": "nome"}
    assert json_value("Residencial; Comércio ;", "atividades_permitidas") == ["Residencial", "Comércio"]
    props = {"sigla": "ZUM", "nome": "Uso misto"}
    validate_properties(props, 1)
    assert "categoria" not in props and "atividades_permitidas" not in props


def test_bounds_and_percentages_are_rejected_when_invalid():
    validate_bounds((-51, -9, -49, -7), (-52, -10, -48, -6))
    with pytest.raises(ValueError, match="fora dos limites"):
        validate_bounds((-60, -9, -49, -7), (-52, -10, -48, -6))
    with pytest.raises(ValueError, match="entre 0 e 100"):
        validate_properties({"sigla": "Z", "nome": "Zona", "conformidade": 110}, 3)


def test_candidate_and_official_metadata_and_safe_replace(tmp_path):
    feature = {"type": "Feature", "properties": {"id": "id", "sigla": "Z", "nome": "Zona"}, "geometry": {"type": "Polygon", "coordinates": []}}
    candidate, dashboard = build_documents([feature], [], [], {"source_sha256": "a" * 64}, None, None)
    assert candidate["metadata"]["status"] == "candidato"
    official, _ = build_documents([feature], [], [], {"source_sha256": "a" * 64}, "Prefeitura", "Lei 123")
    assert official["metadata"]["status"] == "oficial"
    write_documents(tmp_path, candidate, dashboard)
    with pytest.raises(FileExistsError):
        write_documents(tmp_path, candidate, dashboard)
    write_documents(tmp_path, official, dashboard, replace=True)
    assert json.loads((tmp_path / "zonas_poligonos.geojson").read_text(encoding="utf-8"))["metadata"]["status"] == "oficial"


def test_real_shapefile_reprojects_polygon_and_multipolygon(tmp_path):
    geopandas = pytest.importorskip("geopandas")
    shapely = pytest.importorskip("shapely.geometry")
    polygon_a = shapely.Polygon([(-50.05, -8.05), (-50.04, -8.05), (-50.04, -8.04), (-50.05, -8.04), (-50.05, -8.05)])
    polygon_b = shapely.Polygon([(-50.03, -8.03), (-50.02, -8.03), (-50.02, -8.02), (-50.03, -8.02), (-50.03, -8.03)])
    polygon_c = shapely.Polygon([(-50.015, -8.015), (-50.01, -8.015), (-50.01, -8.01), (-50.015, -8.01), (-50.015, -8.015)])
    frame = geopandas.GeoDataFrame({"SIGLA": ["Z1", "Z2"], "NOME": ["Zona um", "Zona dois"]}, geometry=[polygon_a, shapely.MultiPolygon([polygon_b, polygon_c])], crs="EPSG:4326").to_crs("EPSG:31982")
    source = tmp_path / "zoneamento.shp"; frame.to_file(source)
    features, spatial = convert_dataset(source, {"SIGLA": "sigla", "NOME": "nome"}, expected_bounds=(-51, -9, -49, -7))
    assert [feature["geometry"]["type"] for feature in features] == ["Polygon", "MultiPolygon"]
    assert spatial["source_crs"].upper() == "EPSG:31982"
    assert all(feature["properties"]["id"] for feature in features)
