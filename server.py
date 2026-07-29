"""
OPERA Territorial — Server v2.0
Servidor HTTP com endpoints APMO: /api/audit, /api/snapshots, /api/integrity, /api/ico, /api/dashboard
Compatível com frontend/index.html (offline-first + API real)
"""

import json
import hashlib
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs
from pathlib import Path
from datetime import datetime, timezone

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = DATA_DIR / "output"
SNAPSHOTS_DIR = DATA_DIR / "snapshots"
FRONTEND_DIR = BASE_DIR / "frontend"

def get_audit_log():
    audit_file = OUTPUT_DIR / "auditoria.json"
    if audit_file.exists():
        with open(audit_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"events": [], "hash_chain": []}

def add_audit_event(event_type, details, data=None):
    log = get_audit_log()
    parent_hash = log["hash_chain"][-1]["hash"] if log["hash_chain"] else "0x0000000000000000"
    timestamp = datetime.now(timezone.utc).isoformat()
    event = {
        "timestamp": timestamp,
        "type": event_type,
        "details": details,
        "parent_hash": parent_hash,
        "data_hash": hashlib.sha256(
            json.dumps({"ts": timestamp, "type": event_type, "data": data}).encode()
        ).hexdigest()
    }
    log["events"].append(event)
    log["hash_chain"].append({
        "timestamp": timestamp,
        "hash": f"0x{event['data_hash'][:32]}",
        "parent": parent_hash
    })
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_DIR / "auditoria.json", 'w', encoding='utf-8') as f:
        json.dump(log, f, indent=2, ensure_ascii=False)
    return event

def list_snapshots():
    if not SNAPSHOTS_DIR.exists():
        return {"snapshots": []}
    snapshots = []
    for meta_file in SNAPSHOTS_DIR.glob("*_metadata.json"):
        try:
            with open(meta_file, 'r', encoding='utf-8') as f:
                meta = json.load(f)
            snapshots.append(meta)
        except (json.JSONDecodeError, IOError):
            continue
    snapshots.sort(key=lambda x: x.get("timestamp", ""))
    return {"snapshots": snapshots}

def verify_integrity():
    log = get_audit_log()
    chain = log.get("hash_chain", [])
    checks = []
    if len(chain) == 0:
        return {"status": "no_data", "checks": []}
    valid = True
    for i, entry in enumerate(chain):
        if i == 0:
            if entry["parent"] != "0x0000000000000000":
                valid = False
                checks.append({"index": i, "status": "invalid_root"})
            else:
                checks.append({"index": i, "status": "ok"})
        else:
            expected_parent = chain[i - 1]["hash"]
            if entry["parent"] != expected_parent:
                valid = False
                checks.append({"index": i, "status": "broken_chain"})
            else:
                checks.append({"index": i, "status": "ok"})
    return {
        "status": "valid" if valid else "corrupted",
        "total": len(chain),
        "valid": sum(1 for c in checks if c["status"] == "ok"),
        "checks": checks
    }

def calculate_ico():
    geojson_path = OUTPUT_DIR / "radar_geojson.geojson"
    if not geojson_path.exists():
        return {"ico": 0, "zones": [], "error": "GeoJSON não encontrado"}
    with open(geojson_path, 'r', encoding='utf-8') as f:
        geojson = json.load(f)
    features = geojson.get("features", [])
    if not features:
        return {"ico": 0, "zones": []}
    icos = []
    zones = []
    for feat in features:
        props = feat.get("properties", {})
        nome = props.get("nome", "Desconhecido")
        indicador = float(props.get("indicador_ajustado", 0))
        ico = min(100, max(0, indicador))
        icos.append(ico)
        zones.append({"nome": nome, "ico": round(ico, 1)})
    avg_ico = sum(icos) / len(icos) if icos else 0
    return {"ico": round(avg_ico, 1), "zones": zones}

def build_dashboard():
    ico_data = calculate_ico()
    audit = get_audit_log()
    snapshots = list_snapshots()
    integrity = verify_integrity()
    geojson_path = OUTPUT_DIR / "radar_geojson.geojson"
    setores = 0
    obras = 0
    fornecedores = set()
    if geojson_path.exists():
        with open(geojson_path, 'r', encoding='utf-8') as f:
            geojson = json.load(f)
        features = geojson.get("features", [])
        setores = len(features)
        for feat in features:
            props = feat.get("properties", {})
            if props.get("categoria") == "Alto":
                obras += 1
            if props.get("nome"):
                fornecedores.add(props["nome"])
    return {
        "kpis": {
            "setores": setores,
            "obras": obras,
            "fornecedores": len(fornecedores),
            "demandas": sum(1 for _ in features) * 2 if geojson_path.exists() else 0,
            "zum": 1, "zeis": 1,
            "creche_cobertura": "25%",
            "saude_cobertura": "50%"
        },
        "ico": ico_data,
        "audit": {"events": len(audit.get("events", [])), "hash_chain": len(audit.get("hash_chain", []))},
        "snapshots": len(snapshots.get("snapshots", [])),
        "integrity": integrity.get("status", "unknown")
    }

class OPERAHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        params = parse_qs(parsed.query)

        if path == '/api/audit':
            self._json_response(get_audit_log())
            return
        if path == '/api/snapshots':
            self._json_response(list_snapshots())
            return
        if path == '/api/integrity':
            self._json_response(verify_integrity())
            return
        if path == '/api/ico':
            self._json_response(calculate_ico())
            return
        if path == '/api/dashboard':
            self._json_response(build_dashboard())
            return
        if path == '/api/restore':
            timestamp = params.get('timestamp', [''])[0]
            try:
                from python.restore import restaurar_snapshot
                result = restaurar_snapshot(timestamp)
                self._json_response(result)
            except Exception as exc:
                self._json_response({"error": str(exc)}, status=500)
            return

        # Serve frontend
        if path == '/' or path == '/index.html':
            self._serve_file(FRONTEND_DIR / "index.html", "text/html; charset=utf-8")
            return
        static_path = FRONTEND_DIR / path.lstrip('/')
        if static_path.exists() and static_path.is_file():
            self._serve_file(static_path, self._guess_mime(static_path.suffix))
            return
        docs_path = BASE_DIR / "docs" / path.lstrip('/')
        if docs_path.exists() and docs_path.is_file():
            self._serve_file(docs_path, self._guess_mime(docs_path.suffix))
            return

        self._json_response({"error": "Not found"}, status=404)

    def _json_response(self, data, status=200):
        body = json.dumps(data, indent=2, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(body)

    def _serve_file(self, path, content_type):
        with open(path, 'rb') as f:
            body = f.read()
        self.send_response(200)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _guess_mime(self, ext):
        mimes = {
            '.html': 'text/html; charset=utf-8',
            '.css': 'text/css; charset=utf-8',
            '.js': 'application/javascript; charset=utf-8',
            '.json': 'application/json; charset=utf-8',
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.svg': 'image/svg+xml',
        }
        return mimes.get(ext, 'application/octet-stream')

    def log_message(self, format, *args):
        print(f"[OPERA] {datetime.now():%H:%M:%S} — {format % args}")

if __name__ == '__main__':
    host = os.environ.get('OPERA_HOST', '127.0.0.1')
    port = int(os.environ.get('OPERA_PORT', '8001'))
    server = ThreadingHTTPServer((host, port), OPERAHandler)
    print('═══════════════════════════════════════════════')
    print('  OPERA Territorial v2.0 — Servidor ativo')
    print(f'  Frontend: http://{host}:{port}/')
    print('  /api/audit    /api/snapshots')
    print('  /api/integrity /api/ico')
    print('  /api/dashboard /api/restore')
    print('═══════════════════════════════════════════════')
    server.serve_forever()
