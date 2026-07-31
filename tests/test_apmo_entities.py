import base64
import json
import threading
import urllib.request
from datetime import date, datetime
from http.server import ThreadingHTTPServer

import pytest

import server
from python.models.apmo_entities import Atividade, ECO, Evidencia, ICORegistro
from python.modules.hash_chain import HashChain


OBRA_ID = "11111111-1111-4111-8111-111111111111"
ATIVIDADE_ID = "22222222-2222-4222-8222-222222222222"


class Result:
    def __init__(self, data):
        self.data = data


class QueryMock:
    def __init__(self, table, calls):
        self.table = table
        self.calls = calls
        self.operation = "select"
        self.payload = None

    def select(self, *_args): self.operation = "select"; return self
    def eq(self, *_args): return self
    def is_(self, *_args): return self
    def order(self, *_args, **_kwargs): return self
    def gte(self, *_args): return self
    def lte(self, *_args): return self
    def limit(self, *_args): return self
    def insert(self, payload): self.operation = "insert"; self.payload = payload; return self

    def execute(self):
        self.calls.append((self.table, self.operation, self.payload))
        if self.operation == "insert":
            return Result([{"id": ATIVIDADE_ID, **self.payload}])
        return Result([])


class ClientMock:
    def __init__(self): self.calls = []
    def table(self, name): return QueryMock(name, self.calls)
    def rpc(self, name, params): self.calls.append(("rpc", name, params)); return RpcMock()


class RpcMock:
    def execute(self): return Result("33333333-3333-4333-8333-333333333333")


@pytest.fixture()
def apmo_api(tmp_path, monkeypatch):
    client = ClientMock()
    monkeypatch.setattr(server, "create_supabase_client", lambda: client)
    monkeypatch.setattr(server, "EVIDENCE_DIR", tmp_path / "evidencias")
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{httpd.server_port}", client, tmp_path
    httpd.shutdown()
    httpd.server_close()


def request_json(api, path, method="GET", payload=None):
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = urllib.request.Request(api + path, data=body, method=method, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request) as response:
        return response.status, json.loads(response.read())


def test_atividade_creation_and_validation():
    atividade = Atividade(obra_id=OBRA_ID, nome="Fundação", tipo="fundacao", inicio_previsto=date(2026, 1, 1), fim_previsto=date(2026, 2, 1), progresso_pct=50)
    assert atividade.to_dict()["inicio_previsto"] == "2026-01-01"
    with pytest.raises(ValueError):
        Atividade(obra_id=OBRA_ID, nome="Inválida", tipo="fundacao", progresso_pct=101)


def test_ico_calculation():
    ico = ICORegistro(obra_id=OBRA_ID, data_referencia=date(2026, 7, 31), componentes={"qualidade": 85, "prazo": 70, "custo": 90, "seguranca": 75})
    assert ico.calcular_ico() == 80
    assert ico.ico_valor == 80


def test_evidencia_and_eco_models():
    content = b"Teste de evidencia"
    evidence = Evidencia(obra_id=OBRA_ID, tipo="foto", storage_path="evidencias/teste.jpg", hash_sha256=HashChain.hash_file_content(content), tamanho_bytes=len(content), mime_type="image/jpeg", tags=["qualidade"])
    assert len(evidence.hash_sha256) == 64
    eco = ECO(obra_id=OBRA_ID, tipo="aditivo", descricao="Aditivo de prazo", impacto_prazo_dias=15)
    assert eco.status == "pendente"


def test_activity_endpoints_and_versioned_update(apmo_api):
    api, client, _ = apmo_api
    status, listed = request_json(api, f"/api/obras/{OBRA_ID}/atividades")
    assert status == 200 and listed["total"] == 0
    status, created = request_json(api, f"/api/obras/{OBRA_ID}/atividades", "POST", {"nome": "Fundação", "tipo": "fundacao"})
    assert status == 201 and created["atividade"]["nome"] == "Fundação"
    status, updated = request_json(api, f"/api/atividades/{ATIVIDADE_ID}", "PUT", {"updates": {"progresso_pct": 30}, "reason": "Avanço confirmado pela medição técnica semanal.", "expected_version": 1})
    assert status == 200 and updated["success"] is True
    assert client.calls[-1][1] == "retify_entity"


def test_ico_and_eco_endpoints(apmo_api):
    api, client, _ = apmo_api
    _, ico = request_json(api, f"/api/obras/{OBRA_ID}/ico", "POST", {"data_referencia": "2026-07-31", "componentes": {"qualidade": 80, "prazo": 80, "custo": 80, "seguranca": 80}})
    assert ico["registro"]["ico_valor"] == 80
    _, eco = request_json(api, f"/api/obras/{OBRA_ID}/ecos", "POST", {"tipo": "aditivo", "descricao": "Revisão contratual demonstrativa"})
    assert eco["eco"]["status"] == "pendente"
    assert any(call[0] == "ico_registros" for call in client.calls)


def test_evidence_upload_hashes_and_uses_isolated_storage(apmo_api):
    api, client, tmp_path = apmo_api
    content = b"evidencia-binaria"
    status, result = request_json(api, "/api/evidencias/upload", "POST", {"obra_id": OBRA_ID, "tipo": "documento", "filename": "../laudo.pdf", "mime_type": "application/pdf", "content_base64": base64.b64encode(content).decode("ascii")})
    assert status == 201
    assert result["hash_sha256"] == HashChain.hash_file_content(content)
    stored = list((tmp_path / "evidencias" / OBRA_ID).glob("*_laudo.pdf"))
    assert len(stored) == 1 and stored[0].read_bytes() == content
    assert any(call[0] == "evidencias" for call in client.calls)


def test_migration_005_uses_current_audit_trigger():
    migration = (server.BASE_DIR / "data" / "schemas" / "migrations" / "005_entidades_apmo.sql").read_text(encoding="utf-8")
    assert "opera_audit_row" in migration
    assert "audit_trigger_function" not in migration
    assert "create index if not exists" in migration.lower()
