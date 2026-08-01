import copy
import json
from pathlib import Path

import pytest

from scripts.publish_official_zoning import EXPECTED_IDS, publish, validate


def fixture_document():
    features = []
    for index, zone_id in enumerate(sorted(EXPECTED_IDS), 1):
        features.append({"type": "Feature", "properties": {"id": zone_id, "sigla": zone_id.split("-")[0].upper(), "nome": zone_id, "memorial": index, "vertex_count": 3}, "geometry": {"type": "Polygon", "coordinates": [[[-50, -8], [-49.9, -8], [-50, -7.9], [-50, -8]]]}})
    return {"type": "FeatureCollection", "metadata": {"source": "LC 128/2022", "errors": [], "ocr_review_required": False}, "features": features}


def test_validation_rejects_incomplete_coverage():
    document = fixture_document()
    document["features"].pop()
    with pytest.raises(ValueError, match="memoriais divergentes"):
        validate(document)


def test_publish_generates_official_dashboard_and_static_copy(tmp_path):
    source = tmp_path / "source.geojson"
    source.write_text(json.dumps(fixture_document()), encoding="utf-8")
    paths = publish(source, tmp_path)
    dashboard = json.loads((tmp_path / "data/output/dashboard_data.json").read_text(encoding="utf-8"))
    geojson = json.loads((tmp_path / "frontend/data/zonas_oficiais_consolidado.geojson").read_text(encoding="utf-8"))
    assert len(paths) == 5
    assert dashboard["metadata"]["status"] == "oficial"
    assert len(dashboard["zonas"]) == len(geojson["features"]) == 8
    assert dashboard["obras"] == []


def test_validation_rejects_open_ring():
    document = copy.deepcopy(fixture_document())
    document["features"][0]["geometry"]["coordinates"][0][-1] = [-49, -7]
    with pytest.raises(ValueError, match="anel inválido"):
        validate(document)
