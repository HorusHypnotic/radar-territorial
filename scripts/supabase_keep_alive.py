"""Executa uma consulta mínima e somente leitura no Supabase."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from pathlib import Path

from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parents[1]


def load_configuration() -> tuple[str, str]:
    for name in (".env.local", ".env"):
        path = ROOT / name
        if path.is_file():
            load_dotenv(path, override=False)
    url = (os.getenv("SUPABASE_URL") or "").rstrip("/")
    key = os.getenv("SUPABASE_ANON_KEY") or ""
    if not url or not key:
        raise RuntimeError("SUPABASE_URL e SUPABASE_ANON_KEY são obrigatórios")
    return url, key


def ping(url: str, key: str, timeout: float = 20) -> dict[str, object]:
    request = urllib.request.Request(
        f"{url.rstrip('/')}/rest/v1/rpc/opera_keep_alive",
        data=b"{}",
        method="POST",
        headers={
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "User-Agent": "OPERA-keep-alive/1.0",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read())
            if response.status != 200 or payload.get("ok") is not True:
                raise RuntimeError("resposta inesperada do keep-alive")
            return payload
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:300]
        raise RuntimeError(f"Supabase respondeu HTTP {exc.code}: {detail}") from exc


def main() -> int:
    url, key = load_configuration()
    result = ping(url, key)
    print(f"Keep-alive confirmado; schema_ready={result.get('schema_ready')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
