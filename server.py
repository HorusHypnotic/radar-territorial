"""Servidor HTTP local do OPERA Territorial, sem dependências de framework."""

from __future__ import annotations

import hashlib
import base64
import binascii
import json
import mimetypes
import os
import re
from datetime import date, datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, unquote, urlparse
from uuid import UUID

from python.restore import restaurar_snapshot

BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR / "frontend"
OUTPUT_DIR = BASE_DIR / "data" / "output"
STAGING_DIR = BASE_DIR / "data" / "staging"
SNAPSHOTS_DIR = BASE_DIR / "data" / "snapshots"
SERVER_VERSION = "2.1.0"
MAX_IMPORT_BYTES = 5 * 1024 * 1024
MAX_EVIDENCE_BYTES = 10 * 1024 * 1024
EVIDENCE_DIR = BASE_DIR / "data" / "evidencias"
SAFE_TIMESTAMP = re.compile(r"^[0-9]{8}_[0-9]{6}$")
mimetypes.add_type("application/geo+json", ".geojson")
MUTABLE_ENTITIES = {"zonas", "obras", "fornecedores", "atividades", "cronograma", "materiais", "equipes", "ocorrencias", "ecos"}


def create_supabase_client() -> Any:
    """Cria cliente privilegiado apenas no backend e somente quando configurado."""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY")
    if not url or not key:
        raise RuntimeError("Supabase não configurado no backend")
    from supabase import create_client

    return create_client(url, key)


def valid_uuid(value: Any, field: str) -> str:
    """Valida e normaliza UUIDs recebidos pela API."""
    try:
        return str(UUID(str(value)))
    except (ValueError, TypeError, AttributeError) as exc:
        raise ValueError(f"{field} deve ser um UUID válido") from exc


def rpc_data(client: Any, function: str, params: dict[str, Any] | None = None) -> Any:
    """Executa uma RPC Supabase preservando compatibilidade entre versões do SDK."""
    call = client.rpc(function, params or {})
    return call.execute().data


def load_json(path: Path, fallback: Any) -> Any:
    """Carrega JSON local ou devolve um valor seguro quando ausente/inválido."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return fallback


def dashboard_data() -> dict[str, Any]:
    """Normaliza o contrato do dashboard para zonas, obras e fornecedores."""
    payload = load_json(OUTPUT_DIR / "dashboard_data.json", {})
    if isinstance(payload, list):
        return {"zonas": payload, "obras": [], "fornecedores": []}
    if not isinstance(payload, dict):
        return {"zonas": [], "obras": [], "fornecedores": []}
    payload.setdefault("zonas", [])
    payload.setdefault("obras", [])
    payload.setdefault("fornecedores", [])
    return payload


def coverage(zones: list[dict[str, Any]], fields: tuple[str, ...]) -> int:
    """Calcula percentual de registros prioritários entre os que têm o indicador."""
    values = []
    for zone in zones:
        value = next((zone[field] for field in fields if field in zone), None)
        if value is not None:
            values.append(value)
    if not values:
        return 0
    priorities = {"prioritário", "prioritario", "alta", "crítica", "critica"}
    return round(sum(str(value).lower() in priorities for value in values) / len(values) * 100)


def calculate_kpis(data: dict[str, Any]) -> dict[str, int]:
    """Calcula os indicadores do frontend a partir do contrato consolidado."""
    zones = data.get("zonas", [])
    works = data.get("obras", [])
    suppliers = data.get("fornecedores", [])

    def zone_type(zone: dict[str, Any]) -> str:
        return str(zone.get("tipo") or zone.get("sigla") or "").upper()

    priority_values = {"alta", "prioritário", "prioritario", "crítica", "critica"}
    priority_count = sum(
        any(str(value).lower() in priority_values for value in (zone.get("demandas") or zone.get("prioridades") or zone.values()))
        for zone in zones
    )
    ico_values = [float(work["ico"]) for work in works if work.get("ico") is not None]
    return {
        "setores_mapeados": len(zones),
        "obras_andamento": sum(str(work.get("status", "")).lower() in {"andamento", "ativa", "ativo"} for work in works),
        "fornecedores_ativos": sum(supplier.get("ativo", True) is not False for supplier in suppliers),
        "demandas_prioritarias": priority_count,
        "zonas_zum": sum(zone_type(zone) == "ZUM" for zone in zones),
        "zeis": sum(zone_type(zone) == "ZEIS" for zone in zones),
        "cobertura_creche": coverage(zones, ("educacao_infantil", "EducacaoInfantil")),
        "cobertura_saude": coverage(zones, ("saude", "Saude")),
        "ico_medio": round(sum(ico_values) / len(ico_values)) if ico_values else 0,
    }


def list_snapshots() -> list[dict[str, Any]]:
    """Lista metadados de snapshots, do mais recente para o mais antigo."""
    index = load_json(SNAPSHOTS_DIR / "index.json", [])
    if isinstance(index, dict):
        index = index.get("snapshots", [])
    snapshots = index if isinstance(index, list) else []
    for item in snapshots:
        timestamp = item.get("timestamp")
        metadata = load_json(SNAPSHOTS_DIR / f"radar_{timestamp}_metadata.json", {}) if timestamp else {}
        if isinstance(metadata, dict):
            item.update({key: value for key, value in metadata.items() if key not in item or key == "hashes"})
    return sorted(snapshots, key=lambda item: str(item.get("timestamp", "")), reverse=True)


class Handler(BaseHTTPRequestHandler):
    """Rotas REST e arquivos estáticos do produto."""

    def send_json(self, payload: Any, status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def send_file(self, path: Path) -> None:
        resolved = path.resolve()
        if not resolved.is_relative_to(BASE_DIR) or not resolved.is_file():
            self.send_error(404)
            return
        body = resolved.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", mimetypes.guess_type(resolved.name)[0] or "application/octet-stream")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def query_int(self, params: dict[str, list[str]], name: str, default: int, minimum: int, maximum: int) -> int:
        try:
            return min(max(int(params.get(name, [str(default)])[0]), minimum), maximum)
        except ValueError:
            return default

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        data = dashboard_data()
        file_routes = {
            "/api/data": OUTPUT_DIR / "dashboard_data.json",
            "/api/geojson/zonas": OUTPUT_DIR / "zonas_poligonos.geojson",
            "/api/geojson/pontos": OUTPUT_DIR / "radar_geojson.geojson",
        }
        if parsed.path == "/api/health":
            self.send_json({"status": "ok", "version": SERVER_VERSION})
        elif parsed.path == "/api/data":
            self.send_json(data)
        elif parsed.path in file_routes:
            self.send_file(file_routes[parsed.path])
        elif parsed.path == "/api/kpis":
            self.send_json(calculate_kpis(data))
        elif parsed.path.startswith("/api/obras/") and parsed.path.endswith("/atividades"):
            try:
                obra_id = valid_uuid(unquote(parsed.path.split("/")[3]), "obra_id")
                query = create_supabase_client().table("atividades").select("*").eq("obra_id", obra_id).is_("deleted_at", "null")
                status = params.get("status", [""])[0]
                if status:
                    if status not in {"planejada", "em_andamento", "concluida", "paralisada"}:
                        raise ValueError("status de atividade inválido")
                    query = query.eq("status", status)
                response = query.order("prioridade", desc=True).execute()
                self.send_json({"atividades": response.data or [], "total": len(response.data or [])})
            except ValueError as exc:
                self.send_json({"error": str(exc)}, 400)
            except RuntimeError as exc:
                self.send_json({"error": str(exc)}, 503)
            except Exception:
                self.send_json({"error": "falha ao consultar atividades"}, 502)
        elif parsed.path.startswith("/api/obras/") and parsed.path.endswith("/ico"):
            try:
                obra_id = valid_uuid(unquote(parsed.path.split("/")[3]), "obra_id")
                query = create_supabase_client().table("ico_registros").select("*").eq("obra_id", obra_id).order("data_referencia", desc=True)
                start_date, end_date = params.get("start_date", [""])[0], params.get("end_date", [""])[0]
                if start_date:
                    date.fromisoformat(start_date)
                    query = query.gte("data_referencia", start_date)
                if end_date:
                    date.fromisoformat(end_date)
                    query = query.lte("data_referencia", end_date)
                response = query.limit(100).execute()
                self.send_json({"registros": response.data or [], "total": len(response.data or [])})
            except ValueError as exc:
                self.send_json({"error": str(exc)}, 400)
            except RuntimeError as exc:
                self.send_json({"error": str(exc)}, 503)
            except Exception:
                self.send_json({"error": "falha ao consultar ICO"}, 502)
        elif parsed.path.startswith("/api/obras/") and parsed.path.endswith("/ecos"):
            try:
                obra_id = valid_uuid(unquote(parsed.path.split("/")[3]), "obra_id")
                query = create_supabase_client().table("ecos").select("*").eq("obra_id", obra_id)
                status = params.get("status", [""])[0]
                if status:
                    if status not in {"pendente", "aprovado", "rejeitado", "cancelado"}:
                        raise ValueError("status de ECO inválido")
                    query = query.eq("status", status)
                response = query.order("criado_at", desc=True).execute()
                self.send_json({"ecos": response.data or [], "total": len(response.data or [])})
            except ValueError as exc:
                self.send_json({"error": str(exc)}, 400)
            except RuntimeError as exc:
                self.send_json({"error": str(exc)}, 503)
            except Exception:
                self.send_json({"error": "falha ao consultar ECOs"}, 502)
        elif parsed.path == "/api/zonas":
            self.send_json({"zonas": data["zonas"], "total": len(data["zonas"])})
        elif parsed.path.startswith("/api/zonas/"):
            zone_id = unquote(parsed.path.removeprefix("/api/zonas/"))
            zone = next((item for item in data["zonas"] if str(item.get("id") or item.get("sigla")) == zone_id), None)
            self.send_json(zone or {"error": "zona não encontrada"}, 200 if zone else 404)
        elif parsed.path == "/api/audit":
            entries = load_json(OUTPUT_DIR / "audit_log.json", load_json(OUTPUT_DIR / "auditoria.json", []))
            entries = entries if isinstance(entries, list) else []
            table_name = params.get("table_name", [""])[0]
            if table_name:
                entries = [entry for entry in entries if entry.get("table_name") == table_name]
            limit = self.query_int(params, "limit", 20, 1, 100)
            offset = self.query_int(params, "offset", 0, 0, 1_000_000)
            self.send_json({"entries": entries[offset : offset + limit], "total": len(entries), "limit": limit, "offset": offset})
        elif parsed.path == "/api/snapshots":
            snapshots = list_snapshots()
            self.send_json({"snapshots": snapshots, "total": len(snapshots)})
        elif parsed.path == "/api/snapshot":
            timestamp = params.get("timestamp", params.get("date", [""]))[0]
            snapshot = next((item for item in list_snapshots() if str(item.get("timestamp", "")).startswith(timestamp)), None)
            self.send_json(snapshot or {"error": "snapshot não encontrado"}, 200 if snapshot else 404)
        elif parsed.path.startswith("/api/integrity/"):
            obra_id = unquote(parsed.path.removeprefix("/api/integrity/"))
            try:
                obra_id = valid_uuid(obra_id, "obra_id")
                from python.modules.hash_chain import verify_obra_integrity

                self.send_json(verify_obra_integrity(obra_id, create_supabase_client()))
            except ValueError as exc:
                self.send_json({"error": str(exc)}, 400)
            except RuntimeError as exc:
                self.send_json({"error": str(exc)}, 503)
            except Exception:
                self.send_json({"error": "falha ao verificar integridade no banco"}, 502)
        elif parsed.path == "/api/integrity":
            snapshots = list_snapshots()
            valid = all(item.get("hashes") for item in snapshots)
            self.send_json({"valid": valid, "checked": len(snapshots), "message": "Cadeia íntegra" if valid else "Snapshots sem hash detectados"})
        elif parsed.path == "/api/ledger":
            from python.export.operational_ledger import build_ledger, repository_records
            obra_id = params.get("obra_id", [""])[0] or None
            try:
                if obra_id: obra_id = valid_uuid(obra_id, "obra_id")
                self.send_json(build_ledger(repository_records(BASE_DIR, obra_id)))
            except ValueError as exc:
                self.send_json({"error": str(exc)}, 400)
        elif parsed.path == "/api/ico":
            works = data["obras"]
            work_id = params.get("obra_id", [""])[0]
            if work_id:
                works = [work for work in works if str(work.get("id")) == work_id]
            values = [float(work["ico"]) for work in works if work.get("ico") is not None]
            self.send_json({"ico": round(sum(values) / len(values)) if values else 0, "obras": len(works)})
        elif parsed.path == "/":
            self.send_response(302)
            self.send_header("Location", "/frontend/")
            self.end_headers()
        elif parsed.path in {"/frontend", "/frontend/"}:
            self.send_file(FRONTEND_DIR / "index.html")
        elif parsed.path.startswith("/frontend/"):
            self.send_file(FRONTEND_DIR / parsed.path.removeprefix("/frontend/"))
        elif parsed.path.startswith("/data/output/"):
            self.send_file(OUTPUT_DIR / parsed.path.removeprefix("/data/output/"))
        else:
            self.send_error(404)

    def read_json_body(self, max_bytes: int = MAX_IMPORT_BYTES) -> Any:
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0 or length > max_bytes:
            raise ValueError(f"corpo vazio ou acima do limite de {max_bytes // (1024 * 1024)} MB")
        return json.loads(self.rfile.read(length).decode("utf-8"))

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        if parsed.path == "/api/restore":
            timestamp = parse_qs(parsed.query).get("timestamp", [""])[0]
            if not SAFE_TIMESTAMP.fullmatch(timestamp):
                self.send_json({"error": "timestamp inválido"}, 400)
                return
            try:
                self.send_json(restaurar_snapshot(timestamp))
            except (FileNotFoundError, ValueError) as exc:
                self.send_json({"error": str(exc)}, 400)
            except Exception:
                self.send_json({"error": "falha interna ao restaurar snapshot"}, 500)
            return
        if parsed.path == "/api/import":
            try:
                payload = self.read_json_body()
                records = payload.get("dados") if isinstance(payload, dict) else None
                if not isinstance(records, list) or not records or not all(isinstance(item, dict) for item in records):
                    raise ValueError("dados deve ser uma lista não vazia de objetos")
                if len(records) > 10_000:
                    raise ValueError("limite de 10.000 registros excedido")
                origin = re.sub(r"[^a-zA-Z0-9_-]", "_", str(payload.get("origem", "upload")))[:40]
                timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
                STAGING_DIR.mkdir(parents=True, exist_ok=True)
                path = STAGING_DIR / f"import_{origin}_{timestamp}.json"
                document = {"metadata": {"origem": origin, "timestamp": timestamp, "total": len(records)}, "dados": records}
                path.write_text(json.dumps(document, ensure_ascii=False, indent=2), encoding="utf-8")
                digest = hashlib.sha256(path.read_bytes()).hexdigest()
                self.send_json({"success": True, "message": f"{len(records)} registros recebidos", "import_id": timestamp, "sha256": digest}, 201)
            except (ValueError, json.JSONDecodeError, UnicodeDecodeError) as exc:
                self.send_json({"success": False, "error": str(exc)}, 400)
            return
        if parsed.path.startswith("/api/obras/") and parsed.path.endswith("/atividades"):
            try:
                from python.models.apmo_entities import Atividade

                obra_id = valid_uuid(unquote(parsed.path.split("/")[3]), "obra_id")
                payload = self.read_json_body()
                if not isinstance(payload, dict):
                    raise ValueError("atividade deve ser um objeto")
                payload = {**payload, "obra_id": obra_id}
                payload.pop("id", None)
                for field in ("inicio_previsto", "fim_previsto", "inicio_real", "fim_real"):
                    if payload.get(field):
                        payload[field] = date.fromisoformat(str(payload[field]))
                record = Atividade(**payload).to_dict()
                response = create_supabase_client().table("atividades").insert(record).execute()
                self.send_json({"atividade": (response.data or [None])[0]}, 201)
            except (ValueError, TypeError, json.JSONDecodeError, UnicodeDecodeError) as exc:
                self.send_json({"error": str(exc)}, 400)
            except RuntimeError as exc:
                self.send_json({"error": str(exc)}, 503)
            except Exception:
                self.send_json({"error": "falha ao criar atividade"}, 502)
            return
        if parsed.path.startswith("/api/obras/") and parsed.path.endswith("/ico"):
            try:
                from python.models.apmo_entities import ICORegistro

                obra_id = valid_uuid(unquote(parsed.path.split("/")[3]), "obra_id")
                payload = self.read_json_body()
                if not isinstance(payload, dict):
                    raise ValueError("registro ICO deve ser um objeto")
                payload = {**payload, "obra_id": obra_id}
                payload.pop("id", None)
                payload["data_referencia"] = date.fromisoformat(str(payload.get("data_referencia") or date.today().isoformat()))
                record = ICORegistro(**payload).to_dict()
                response = create_supabase_client().table("ico_registros").insert(record).execute()
                self.send_json({"registro": (response.data or [None])[0]}, 201)
            except (ValueError, TypeError, json.JSONDecodeError, UnicodeDecodeError) as exc:
                self.send_json({"error": str(exc)}, 400)
            except RuntimeError as exc:
                self.send_json({"error": str(exc)}, 503)
            except Exception:
                self.send_json({"error": "falha ao registrar ICO"}, 502)
            return
        if parsed.path.startswith("/api/obras/") and parsed.path.endswith("/ecos"):
            try:
                from python.models.apmo_entities import ECO

                obra_id = valid_uuid(unquote(parsed.path.split("/")[3]), "obra_id")
                payload = self.read_json_body()
                if not isinstance(payload, dict):
                    raise ValueError("ECO deve ser um objeto")
                payload = {**payload, "obra_id": obra_id}
                payload.pop("id", None)
                response = create_supabase_client().table("ecos").insert(ECO(**payload).to_dict()).execute()
                self.send_json({"eco": (response.data or [None])[0]}, 201)
            except (ValueError, TypeError, json.JSONDecodeError, UnicodeDecodeError) as exc:
                self.send_json({"error": str(exc)}, 400)
            except RuntimeError as exc:
                self.send_json({"error": str(exc)}, 503)
            except Exception:
                self.send_json({"error": "falha ao criar ECO"}, 502)
            return
        if parsed.path == "/api/evidencias/upload":
            local_path = None
            storage_path = None
            storage_bucket = None
            try:
                from python.models.apmo_entities import Evidencia
                from python.modules.hash_chain import HashChain

                payload = self.read_json_body(max_bytes=MAX_EVIDENCE_BYTES * 2)
                if not isinstance(payload, dict):
                    raise ValueError("evidência deve ser um objeto")
                obra_id = valid_uuid(payload.get("obra_id"), "obra_id") if payload.get("obra_id") else None
                atividade_id = valid_uuid(payload.get("atividade_id"), "atividade_id") if payload.get("atividade_id") else None
                try:
                    content = base64.b64decode(str(payload.get("content_base64", "")), validate=True)
                except (binascii.Error, ValueError) as exc:
                    raise ValueError("content_base64 inválido") from exc
                if not content or len(content) > MAX_EVIDENCE_BYTES:
                    raise ValueError("evidência vazia ou acima do limite de 10 MB")
                filename = re.sub(r"[^a-zA-Z0-9._-]", "_", Path(str(payload.get("filename", "evidencia.bin"))).name)[:120]
                if not filename:
                    raise ValueError("filename inválido")
                owner = obra_id or atividade_id
                relative_path = Path(str(owner)) / f"{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S_%f')}_{filename}"
                local_path = EVIDENCE_DIR / str(owner) / relative_path.name
                local_path.parent.mkdir(parents=True, exist_ok=True)
                local_path.write_bytes(content)
                record = Evidencia(tipo=str(payload.get("tipo", "")), storage_path=relative_path.as_posix(), hash_sha256=HashChain.hash_file_content(content), tamanho_bytes=len(content), mime_type=str(payload.get("mime_type") or "application/octet-stream"), obra_id=obra_id, atividade_id=atividade_id, descricao=payload.get("descricao"), tags=payload.get("tags") or [], gps_lat=payload.get("gps_lat"), gps_lng=payload.get("gps_lng"), device=payload.get("device")).to_dict()
                client = create_supabase_client()
                storage_bucket = client.storage.from_("evidencias")
                storage_path = relative_path.as_posix()
                storage_bucket.upload(storage_path, content, {"content-type": record["mime_type"], "upsert": "false"})
                response = client.table("evidencias").insert(record).execute()
                self.send_json({"success": True, "evidencia": (response.data or [None])[0], "hash_sha256": record["hash_sha256"]}, 201)
            except (ValueError, TypeError, json.JSONDecodeError, UnicodeDecodeError) as exc:
                if local_path and local_path.is_file():
                    local_path.unlink()
                if storage_bucket and storage_path:
                    try: storage_bucket.remove([storage_path])
                    except Exception: pass
                self.send_json({"error": str(exc)}, 400)
            except RuntimeError as exc:
                if local_path and local_path.is_file():
                    local_path.unlink()
                if storage_bucket and storage_path:
                    try: storage_bucket.remove([storage_path])
                    except Exception: pass
                self.send_json({"error": str(exc)}, 503)
            except Exception:
                if local_path and local_path.is_file():
                    local_path.unlink()
                if storage_bucket and storage_path:
                    try: storage_bucket.remove([storage_path])
                    except Exception: pass
                self.send_json({"error": "falha ao armazenar evidência"}, 502)
            return
        if parsed.path.startswith("/api/retify/"):
            parts = [unquote(part) for part in parsed.path.removeprefix("/api/retify/").split("/")]
            try:
                if len(parts) != 2 or parts[0] not in MUTABLE_ENTITIES:
                    raise ValueError("tipo de entidade não permitido")
                entity_type, entity_id = parts[0], valid_uuid(parts[1], "entity_id")
                payload = self.read_json_body()
                updates = payload.get("updates") if isinstance(payload, dict) else None
                reason = str(payload.get("reason", "")).strip() if isinstance(payload, dict) else ""
                edited_by = payload.get("edited_by") if isinstance(payload, dict) else None
                expected_version = payload.get("expected_version") if isinstance(payload, dict) else None
                if not isinstance(updates, dict) or not updates:
                    raise ValueError("updates deve ser um objeto não vazio")
                if {"id", "created_at", "created_by", "version"} & updates.keys():
                    raise ValueError("updates contém campos protegidos")
                if len(reason) < 20:
                    raise ValueError("motivo deve ter pelo menos 20 caracteres")
                if not isinstance(expected_version, int) or isinstance(expected_version, bool) or expected_version < 1:
                    raise ValueError("expected_version deve ser um inteiro positivo")
                edited_by = valid_uuid(edited_by, "edited_by") if edited_by else None
                version_id = rpc_data(create_supabase_client(), "retify_entity", {"p_entity_type": entity_type, "p_entity_id": entity_id, "p_updates": updates, "p_reason": reason, "p_edited_by": edited_by, "p_expected_version": expected_version})
                self.send_json({"success": True, "version_id": version_id, "message": "Entidade retificada com sucesso"})
            except (ValueError, json.JSONDecodeError, UnicodeDecodeError) as exc:
                self.send_json({"error": str(exc)}, 400)
            except RuntimeError as exc:
                self.send_json({"error": str(exc)}, 503)
            except Exception:
                self.send_json({"error": "falha ao retificar entidade no banco"}, 502)
            return
        if parsed.path.startswith("/api/generate-snapshot/"):
            try:
                obra_id = valid_uuid(unquote(parsed.path.removeprefix("/api/generate-snapshot/")), "obra_id")
                snapshot_date = params.get("snapshot_date", [date.today().isoformat()])[0]
                date.fromisoformat(snapshot_date)
                snapshot_id = rpc_data(create_supabase_client(), "generate_obra_snapshot", {"p_obra_id": obra_id, "p_snapshot_date": snapshot_date, "p_gerado_por": None})
                self.send_json({"success": True, "snapshot_id": snapshot_id, "obra_id": obra_id, "date": snapshot_date})
            except (ValueError, json.JSONDecodeError) as exc:
                self.send_json({"error": str(exc)}, 400)
            except RuntimeError as exc:
                self.send_json({"error": str(exc)}, 503)
            except Exception:
                self.send_json({"error": "falha ao gerar snapshot no banco"}, 502)
            return
        if parsed.path == "/api/snapshot/generate-all":
            try:
                generated = rpc_data(create_supabase_client(), "generate_daily_snapshots")
                self.send_json({"success": True, "generated": generated, "message": "Snapshots diários processados"})
            except RuntimeError as exc:
                self.send_json({"error": str(exc)}, 503)
            except Exception:
                self.send_json({"error": "falha ao gerar snapshots no banco"}, 502)
            return
        if parsed.path == "/api/snapshot/restore":
            try:
                payload = self.read_json_body()
                snapshot_id = valid_uuid(payload.get("snapshot_id"), "snapshot_id")
                reason = str(payload.get("reason", "")).strip()
                restored_by = payload.get("restored_by")
                if len(reason) < 20:
                    raise ValueError("motivo deve ter pelo menos 20 caracteres")
                restored_by = valid_uuid(restored_by, "restored_by") if restored_by else None
                version_id = rpc_data(create_supabase_client(), "restore_snapshot", {"p_snapshot_id": snapshot_id, "p_reason": reason, "p_restored_by": restored_by})
                self.send_json({"success": True, "version_id": version_id, "snapshot_id": snapshot_id})
            except (ValueError, json.JSONDecodeError, UnicodeDecodeError, AttributeError) as exc:
                self.send_json({"error": str(exc)}, 400)
            except RuntimeError as exc:
                self.send_json({"error": str(exc)}, 503)
            except Exception:
                self.send_json({"error": "falha ao restaurar snapshot no banco"}, 502)
            return
        self.send_error(404)

    def do_PUT(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if not parsed.path.startswith("/api/atividades/"):
            self.send_error(404)
            return
        try:
            atividade_id = valid_uuid(unquote(parsed.path.removeprefix("/api/atividades/")), "atividade_id")
            payload = self.read_json_body()
            updates = payload.get("updates") if isinstance(payload, dict) else None
            reason = str(payload.get("reason", "")).strip() if isinstance(payload, dict) else ""
            expected_version = payload.get("expected_version") if isinstance(payload, dict) else None
            edited_by = payload.get("edited_by") if isinstance(payload, dict) else None
            if not isinstance(updates, dict) or not updates:
                raise ValueError("updates deve ser um objeto não vazio")
            if len(reason) < 20:
                raise ValueError("motivo deve ter pelo menos 20 caracteres")
            if not isinstance(expected_version, int) or isinstance(expected_version, bool) or expected_version < 1:
                raise ValueError("expected_version deve ser um inteiro positivo")
            edited_by = valid_uuid(edited_by, "edited_by") if edited_by else None
            version_id = rpc_data(create_supabase_client(), "retify_entity", {"p_entity_type": "atividades", "p_entity_id": atividade_id, "p_updates": updates, "p_reason": reason, "p_edited_by": edited_by, "p_expected_version": expected_version})
            self.send_json({"success": True, "version_id": version_id})
        except (ValueError, json.JSONDecodeError, UnicodeDecodeError) as exc:
            self.send_json({"error": str(exc)}, 400)
        except RuntimeError as exc:
            self.send_json({"error": str(exc)}, 503)
        except Exception:
            self.send_json({"error": "falha ao retificar atividade"}, 502)

    def log_message(self, format: str, *args: Any) -> None:
        return


if __name__ == "__main__":
    host = os.getenv("SERVER_HOST", "127.0.0.1")
    port = int(os.getenv("SERVER_PORT", "8001"))
    server = ThreadingHTTPServer((host, port), Handler)
    print(f"OPERA Territorial ativo em http://{host}:{port}")
    server.serve_forever()
