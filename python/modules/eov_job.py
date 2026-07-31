"""Entrada de cron para gerar os Estados Operacionais Verificáveis diários."""

from __future__ import annotations

import logging
import os

from dotenv import load_dotenv
from supabase import create_client

logger = logging.getLogger(__name__)


def generate_daily_snapshots() -> int:
    """Executa a RPC transacional de snapshots usando credenciais do backend."""
    load_dotenv()
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY")
    if not url or not key:
        raise RuntimeError("SUPABASE_URL e SUPABASE_SERVICE_KEY são obrigatórios")
    response = create_client(url, key).rpc("generate_daily_snapshots", {}).execute()
    generated = int(response.data or 0)
    logger.info("Snapshots EOV processados", extra={"generated": generated})
    return generated


def main() -> int:
    """Executa o job e devolve código apropriado ao agendador."""
    logging.basicConfig(level=os.getenv("PIPELINE_LOG_LEVEL", "INFO"))
    try:
        generated = generate_daily_snapshots()
    except Exception:
        logger.exception("Falha ao gerar snapshots EOV")
        return 1
    print(f"Snapshots EOV gerados: {generated}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
