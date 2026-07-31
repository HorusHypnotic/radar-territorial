"""Verifica, sem alterar dados, credenciais e acesso ao schema Supabase."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parents[1]
PLACEHOLDER_PARTS = ("seu-projeto", "sua-service-key", "sua-anon-key", "seu-project-id", "...")


def credentials_error(url: str | None, key: str | None) -> str | None:
    if not url or not key:
        return "SUPABASE_URL e SUPABASE_SERVICE_KEY são obrigatórios"
    if any(part in url.lower() or part in key.lower() for part in PLACEHOLDER_PARTS):
        return "as credenciais ainda contêm placeholders"
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.hostname or not parsed.hostname.endswith(".supabase.co"):
        return "SUPABASE_URL deve ser uma URL HTTPS do domínio supabase.co"
    return None


def select_env_file(explicit: str | None) -> Path | None:
    if explicit:
        return Path(explicit).resolve()
    for name in (".env.local", ".env", ".env.codex"):
        candidate = ROOT / name
        if candidate.is_file():
            return candidate
    return None


def check(env_file: str | None = None, table: str | None = None) -> dict[str, object]:
    selected = select_env_file(env_file)
    if selected:
        load_dotenv(selected, override=False)
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY")
    target_table = table or os.getenv("SUPABASE_TABLE", "zonas")
    error = credentials_error(url, key)
    result: dict[str, object] = {
        "ok": False,
        "env_file": str(selected) if selected else None,
        "table": target_table,
    }
    if error:
        result["error"] = error
        return result

    try:
        from supabase import create_client

        response = create_client(url, key).table(target_table).select("id", count="exact").limit(1).execute()
        result.update(ok=True, reachable=True, row_count=response.count)
    except Exception as exc:
        result.update(reachable=False, error=f"{type(exc).__name__}: {exc}")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-file", help="arquivo de ambiente fora do Git")
    parser.add_argument("--table", help="tabela usada na consulta somente leitura")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = check(args.env_file, args.table)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif result["ok"]:
        print(f"Supabase acessível; tabela {result['table']} consultada com sucesso.")
    else:
        print(f"Supabase não validado: {result['error']}")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
