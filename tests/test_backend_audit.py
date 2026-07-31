import json
import threading
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

import pytest

import server
from python.modules.hash_chain import HashChain


OBRA_ID = "11111111-1111-4111-8111-111111111111"
ENTITY_ID = "22222222-2222-4222-8222-222222222222"
USER_ID = "33333333-3333-4333-8333-333333333333"


class RpcResult:
    def __init__(self, data):
        self.data = data


class RpcCall:
    def __init__(self, data):
        self.data = data

    def execute(self):
        return RpcResult(self.data)


class SupabaseMock:
    def __init__(self):
        self.calls = []

    def rpc(self, name, params=None):
        self.calls.append((name, params or {}))
        if name.startswith("verify_"):
            return RpcCall([{"position": 1, "is_valid": True}])
        if name == "generate_daily_snapshots":
            return RpcCall(2)
        return RpcCall("44444444-4444-4444-8444-444444444444")


@pytest.fixture()
def api():
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{httpd.server_port}"
    httpd.shutdown()
    httpd.server_close()


def post_json(api, path, payload=None):
    body = json.dumps(payload).encode("utf-8") if payload is not None else b""
    request = urllib.request.Request(api + path, data=body, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(request) as response:
        return response.status, json.loads(response.read())


@pytest.fixture()
def audited_api(api, monkeypatch):
    client = SupabaseMock()
    monkeypatch.setattr(server, "create_supabase_client", lambda: client)
    return api, client


def test_hash_chain_valid_and_tampered():
    chain = HashChain(salt="test")
    first = chain.build_entry({"id": 1}, metadata={"at": "2026-07-31T12:00:00Z"})
    second = chain.build_entry({"id": 2}, first["curr_hash"], {"at": "2026-07-31T12:01:00Z"})
    result = chain.verify_chain([first, second])
    assert result["valid"] is True
    assert result["entries_checked"] == 2
    second["data"]["id"] = 99
    assert chain.verify_chain([first, second])["valid"] is False


def test_hash_file_and_evidence(tmp_path):
    path = tmp_path / "evidence.bin"
    path.write_bytes(b"evidencia")
    chain = HashChain(salt="test")
    assert len(chain.hash_file(path)) == 64
    assert chain.hash_evidence(b"evidencia", {"gps": [-8, -50]}) == chain.hash_evidence(b"evidencia", {"gps": [-8, -50]})


def test_integrity_uses_database_verifiers(audited_api):
    api, client = audited_api
    with urllib.request.urlopen(f"{api}/api/integrity/{OBRA_ID}") as response:
        result = json.loads(response.read())
    assert result["valid"] is True
    assert len(result["checks"]) == 3
    assert [call[0] for call in client.calls] == ["verify_hash_chain", "verify_snapshot_chain", "verify_version_chain"]


def test_retify_entity_requires_long_reason(audited_api):
    api, _ = audited_api
    with pytest.raises(urllib.error.HTTPError) as error:
        post_json(api, f"/api/retify/obras/{ENTITY_ID}", {"updates": {"status": "revisao"}, "reason": "Curto", "expected_version": 1})
    assert error.value.code == 400


def test_retify_entity_requires_expected_version(audited_api):
    api, _ = audited_api
    with pytest.raises(urllib.error.HTTPError) as error:
        post_json(api, f"/api/retify/obras/{ENTITY_ID}", {"updates": {"status": "revisao"}, "reason": "Motivo formal suficientemente longo para a retificação."})
    assert error.value.code == 400


def test_retify_entity_calls_rpc(audited_api):
    api, client = audited_api
    status, result = post_json(api, f"/api/retify/obras/{ENTITY_ID}", {"updates": {"status": "revisao"}, "reason": "Retificação motivada pela revisão formal do cronograma.", "edited_by": USER_ID, "expected_version": 1})
    assert status == 200
    assert result["success"] is True
    assert client.calls[-1][0] == "retify_entity"


def test_generate_one_and_all_snapshots(audited_api):
    api, client = audited_api
    _, generated = post_json(api, f"/api/generate-snapshot/{OBRA_ID}?snapshot_date=2026-07-29")
    assert generated["date"] == "2026-07-29"
    _, all_generated = post_json(api, "/api/snapshot/generate-all")
    assert all_generated["generated"] == 2
    assert client.calls[-1][0] == "generate_daily_snapshots"


def test_restore_snapshot_requires_reason_and_calls_rpc(audited_api):
    api, client = audited_api
    payload = {"snapshot_id": ENTITY_ID, "restored_by": USER_ID, "reason": "Restauração autorizada após conferência formal do estado anterior."}
    _, result = post_json(api, "/api/snapshot/restore", payload)
    assert result["success"] is True
    assert client.calls[-1][0] == "restore_snapshot"


def test_migrations_exist_and_do_not_contain_plain_sha256_calls():
    migrations = Path(__file__).resolve().parents[1] / "data" / "schemas" / "migrations"
    for name in ("002_audit_trigger.sql", "003_versioning.sql", "004_snapshot_eov.sql"):
        content = (migrations / name).read_text(encoding="utf-8")
        assert "digest(" in content
        assert "sha256(" not in content


def test_eov_job_calls_rpc(monkeypatch):
    from python.modules import eov_job

    client = SupabaseMock()
    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setenv("SUPABASE_SERVICE_KEY", "test-service-key")
    monkeypatch.setattr(eov_job, "create_client", lambda _url, _key: client)
    assert eov_job.generate_daily_snapshots() == 2
    assert client.calls[-1][0] == "generate_daily_snapshots"


def test_static_builder_excludes_backend_and_sensitive_snapshot_paths(tmp_path):
    from python.modules.build_static_site import build

    target = tmp_path.resolve()
    # O builder exige destino interno para tornar a remoção recursiva segura.
    internal_target = Path(__file__).resolve().parents[1] / "_site_test"
    try:
        result = build(internal_target)
        assert (result / "frontend" / "index.html").exists()
        assert not (result / "server.py").exists()
        assert not list(result.rglob("*.parquet"))
        index = (result / "data" / "snapshots" / "index.json").read_text(encoding="utf-8")
        assert "D:\\Radar Territorial" not in index
    finally:
        if internal_target.exists():
            import shutil
            shutil.rmtree(internal_target)
