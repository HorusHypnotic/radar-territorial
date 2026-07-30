"""
OPERA Territorial — Hash Chain (Integridade Criptográfica)
SHA-256 encadeado para auditoria imutável.

FÓRMULA CANÔNICA (única em todo o sistema):
  content = prev_hash || json.dumps(new_row, sort_keys=True) || at || actor_id
  curr_hash = sha256(content).hexdigest()

Esta fórmula é idêntica em:
  - Trigger PostgreSQL (audit_log_hash_trigger)
  - Python db.py (log_audit)
  - Python hash_chain.py (generate_hash, verify_chain)
"""
import hashlib
import json
from datetime import datetime


def generate_hash(prev_hash: str, new_row: dict, at: str = None, actor_id: str = "") -> str:
    """Gera hash SHA-256 encadeado.

    Mesma fórmula do trigger PostgreSQL:
      sha256(prev_hash || new_row::text || at::text || actor_id)

    Args:
        prev_hash: Hash anterior da cadeia (ou "0x00" para o primeiro)
        new_row: Dados da linha como dict (serializado com sort_keys)
        at: Timestamp ISO (gera agora se None)
        actor_id: ID do ator que fez a operação
    """
    if at is None:
        at = datetime.utcnow().isoformat()
    new_row_text = json.dumps(new_row, sort_keys=True) if new_row else ""
    content = f"{prev_hash or '0x00'}{new_row_text}{at}{actor_id or ''}"
    return hashlib.sha256(content.encode('utf-8')).hexdigest()


def verify_chain(records: list) -> dict:
    """Verifica se a cadeia de hashes está íntegra.

    Args:
        records: Lista de dicts do audit_log com chaves:
                 curr_hash, prev_hash, new_row, at, actor_id

    Returns:
        {"status": "intact"|"broken"|"no_data",
         "total": int,
         "valid": int,
         "failed_at": str|None}
    """
    if not records:
        return {"status": "no_data", "total": 0, "valid": 0, "failed_at": None}

    prev = None
    valid_count = 0
    failed_at = None

    for i, rec in enumerate(records):
        new_row = rec.get('new_row', {})
        at = rec.get('at', '')
        actor_id = rec.get('actor_id', '') or ''
        expected = generate_hash(prev, new_row, at, actor_id)

        if rec['curr_hash'] != expected:
            if failed_at is None:
                failed_at = at
            return {
                "status": "broken",
                "total": len(records),
                "valid": valid_count,
                "failed_at": failed_at,
                "expected": expected,
                "found": rec['curr_hash']
            }
        prev = rec['curr_hash']
        valid_count += 1

    return {
        "status": "intact",
        "total": len(records),
        "valid": valid_count,
        "failed_at": None,
        "last_hash": prev
    }


def build_chain_from_records(records: list) -> list:
    """Reconstrói a cadeia de hashes a partir de registros do audit_log.

    Args:
        records: Lista de dicts com chaves new_row, at, actor_id

    Returns:
        Lista de dicts: {"timestamp", "hash", "parent"}
    """
    prev = None
    chain = []
    for rec in records:
        ts = rec.get('at', datetime.utcnow().isoformat())
        new_row = rec.get('new_row', {})
        actor_id = rec.get('actor_id', '') or ''
        h = generate_hash(prev, new_row, ts, actor_id)
        chain.append({
            "timestamp": ts,
            "hash": h,
            "parent": prev or "0x00"
        })
        prev = h
    return chain
