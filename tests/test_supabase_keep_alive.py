import json

from scripts import supabase_keep_alive


class Response:
    status = 200

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return json.dumps({"ok": True, "schema_ready": True}).encode()


def test_ping_calls_read_only_rpc(monkeypatch):
    captured = {}

    def open_request(request, timeout):
        captured["request"] = request
        captured["timeout"] = timeout
        return Response()

    monkeypatch.setattr(supabase_keep_alive.urllib.request, "urlopen", open_request)
    result = supabase_keep_alive.ping("https://abc.supabase.co", "public-key")
    assert result["schema_ready"] is True
    assert captured["request"].full_url.endswith("/rest/v1/rpc/opera_keep_alive")
    assert captured["request"].method == "POST"


def test_configuration_requires_public_key(monkeypatch, tmp_path):
    monkeypatch.setattr(supabase_keep_alive, "ROOT", tmp_path)
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_ANON_KEY", raising=False)
    try:
        supabase_keep_alive.load_configuration()
    except RuntimeError as exc:
        assert "obrigatórios" in str(exc)
    else:
        raise AssertionError("configuração ausente deveria falhar")
