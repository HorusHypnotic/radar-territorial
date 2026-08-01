import json
import threading
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

import pytest

import server


@pytest.fixture()
def api(tmp_path, monkeypatch):
    monkeypatch.setattr(server, "STAGING_DIR", tmp_path / "staging")
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{httpd.server_port}"
    httpd.shutdown()
    httpd.server_close()


def request_json(api, path, payload=None):
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = urllib.request.Request(api + path, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request) as response:
        return response.status, json.loads(response.read())


def test_health_and_kpis(api):
    status, health = request_json(api, "/api/health")
    assert status == 200
    assert health["status"] == "ok"
    status, kpis = request_json(api, "/api/kpis")
    assert status == 200
    assert set(kpis) == {
        "setores_mapeados", "obras_andamento", "fornecedores_ativos",
        "demandas_prioritarias", "zonas_zum", "zeis", "cobertura_creche",
        "cobertura_saude", "ico_medio",
    }


def test_audit_pagination_and_snapshots(api):
    _, audit = request_json(api, "/api/audit?limit=5&offset=1")
    assert audit["limit"] == 5
    assert audit["offset"] == 1
    assert len(audit["entries"]) <= 5
    _, snapshots = request_json(api, "/api/snapshots")
    assert "snapshots" in snapshots
    _, integrity = request_json(api, "/api/integrity")
    assert {"valid", "checked", "message"} <= integrity.keys()


def test_import_validates_and_writes_only_to_staging(api, tmp_path):
    status, result = request_json(api, "/api/import", {"origem": "test", "dados": [{"sigla": "Z01", "nome": "Teste"}]})
    assert status == 201
    assert result["success"] is True
    files = list((tmp_path / "staging").glob("import_test_*.json"))
    assert len(files) == 1
    assert len(result["sha256"]) == 64


def test_import_rejects_empty_records(api):
    with pytest.raises(urllib.error.HTTPError) as error:
        request_json(api, "/api/import", {"dados": []})
    assert error.value.code == 400


def test_frontend_files_and_geojson(api):
    frontend = Path(__file__).resolve().parents[1] / "frontend"
    for relative in ("index.html", "css/main.css", "js/main.js", "js/mapa.js", "js/kpis.js", "js/graficos.js", "js/tabela.js", "js/upload.js", "js/apmo.js", "vendor/leaflet/leaflet.js", "vendor/leaflet/leaflet.css"):
        assert (frontend / relative).stat().st_size > 0
    status, geojson = request_json(api, "/api/geojson/zonas")
    assert status == 200
    assert geojson["type"] == "FeatureCollection"
    assert all(feature["geometry"]["type"] in {"Polygon", "MultiPolygon"} for feature in geojson["features"])


def test_executive_header_and_demo_disclosure_are_present():
    html = (Path(__file__).resolve().parents[1] / "frontend" / "index.html").read_text(encoding="utf-8")
    assert all(marker in html for marker in ("header-zonas", "header-obras", "header-fornecedores"))
    assert "Dados demonstrativos" in html
