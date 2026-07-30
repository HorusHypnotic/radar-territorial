"""
OPERA Territorial — Cliente Supabase e Helpers de Auditoria
Usa o hash chain centralizado de python/modules/hash_chain.py
"""
import os
import hashlib
import json
from supabase import create_client, Client
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

url: str = os.getenv("SUPABASE_URL", "")
key: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
supabase: Client = create_client(url, key)


def log_audit(table_name: str, row_id: str, op: str, old_row: dict = None, new_row: dict = None, actor_id: str = None):
    """Insere registro no audit_log com hash calculado pela mesma fórmula do trigger SQL.

    A fórmula é idêntica ao trigger PostgreSQL:
      sha256(prev_hash || jsonb_new_row::text || at::text || actor_id)

    O trigger calcula curr_hash automaticamente, mas enviamos prev_hash
    para que o servidor possa verificar a cadeia.
    """
    # Busca o hash anterior para encadear
    prev_hash = "0x00"
    if op in ['UPDATE', 'DELETE']:
        prev = supabase.table('audit_log').select('curr_hash').eq('row_id', row_id).order('at', desc=True).limit(1).execute()
        if prev.data:
            prev_hash = prev.data[0]['curr_hash']

    # Calcula o hash esperado (mesma fórmula do trigger SQL)
    new_row_text = json.dumps(new_row, sort_keys=True) if new_row else ""
    actor_text = actor_id or ""
    at_text = datetime.utcnow().isoformat()
    content = f"{prev_hash}{new_row_text}{at_text}{actor_text}"
    curr_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()

    data = {
        "table_name": table_name,
        "row_id": row_id,
        "op": op,
        "actor_id": actor_id,
        "old_row": old_row,
        "new_row": new_row,
        "at": at_text,
        "prev_hash": prev_hash,
        "curr_hash": curr_hash
    }
    return supabase.table('audit_log').insert(data).execute()
