import copy
import json
import threading
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

import server
from python.export.operational_ledger import build_ledger, verify_ledger


def test_operational_ledger_detects_tampering():
    ledger = build_ledger([
        {"kind": "audit", "timestamp": "2026-08-01T00:00:00Z", "payload": {"op": "INSERT"}},
        {"kind": "snapshot", "timestamp": "2026-08-02T00:00:00Z", "payload": {"rows": 4}},
    ], generated_at="2026-08-02T01:00:00Z")
    assert verify_ledger(ledger) == {"valid": True, "entries_checked": 2, "root_hash": ledger["manifest"]["root_hash"], "errors": []}
    tampered = copy.deepcopy(ledger); tampered["entries"][0]["payload"]["op"] = "DELETE"
    result = verify_ledger(tampered)
    assert result["valid"] is False
    assert {error["error"] for error in result["errors"]} >= {"curr_hash", "entries_hash"}


def test_pwa_manifest_and_offline_core_are_scoped():
    frontend = Path(__file__).resolve().parents[1] / "frontend"
    manifest = json.loads((frontend / "manifest.webmanifest").read_text(encoding="utf-8"))
    assert manifest["start_url"] == manifest["scope"] == "./"
    assert {icon["sizes"] for icon in manifest["icons"]} == {"192x192", "512x512"}
    worker = (frontend / "sw.js").read_text(encoding="utf-8")
    assert "opera-territorial-v6" in worker
    assert "livro_razao.json" in worker
    assert "event.request.mode === \"navigate\"" in worker
    for size in (192, 512):
        content = (frontend / "icons" / f"icon-{size}.png").read_bytes()
        assert content.startswith(b"\x89PNG\r\n\x1a\n")
        assert int.from_bytes(content[16:20], "big") == int.from_bytes(content[20:24], "big") == size


def test_ledger_api_is_verifiable(tmp_path, monkeypatch):
    output = tmp_path / "data" / "output"; output.mkdir(parents=True)
    (output / "auditoria.json").write_text(json.dumps([{"timestamp": "2026-08-01", "evento": "teste"}]), encoding="utf-8")
    monkeypatch.setattr(server, "BASE_DIR", tmp_path)
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{httpd.server_port}/api/ledger") as response:
            ledger = json.loads(response.read())
        assert verify_ledger(ledger)["valid"] is True
        assert ledger["manifest"]["entries"] == 1
    finally:
        httpd.shutdown(); httpd.server_close()


def test_preservation_migration_is_append_only_and_does_not_fake_timestamp():
    sql = (server.BASE_DIR / "data" / "schemas" / "migrations" / "007_preservacao_verificavel.sql").read_text(encoding="utf-8")
    assert "opera_append_only" in sql
    assert "timestamp_rfc3161 jsonb" in sql
    assert "external_timestamp_verified',false" in sql
    assert "insert into storage.buckets" in sql
