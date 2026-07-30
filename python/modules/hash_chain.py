"""
OPERA Territorial — Hash Chain (Integridade Criptográfica)
SHA-256 encadeado para auditoria imutável
"""
import hashlib
import json
from datetime import datetime


def generate_hash(prev_hash: str, payload: dict, timestamp: str = None) -> str:
    """Gera hash SHA-256 encadeado."""
    if timestamp is None:
        timestamp = datetime.utcnow().isoformat()
    content = f"{prev_hash or '0x00'}|{json.dumps(payload, sort_keys=True)}|{timestamp}"
    return hashlib.sha256(content.encode('utf-8')).hexdigest()


def verify_chain(records: list) -> bool:
    """Verifica se a cadeia de hashes está íntegra."""
    prev = None
    for rec in records:
        if prev is None:
            expected = generate_hash(None, rec['payload'])
        else:
            expected = generate_hash(prev, rec['payload'])
        if rec['curr_hash'] != expected:
            return False
        prev = rec['curr_hash']
    return True


def build_chain_from_records(records: list) -> list:
    """Reconstrói a cadeia de hashes a partir de registros."""
    prev = None
    chain = []
    for rec in records:
        ts = rec.get('at', datetime.utcnow().isoformat())
        h = generate_hash(prev, rec.get('new_row', {}), ts)
        chain.append({
            "timestamp": ts,
            "hash": h,
            "parent": prev or "0x00"
        })
        prev = h
    return chain
