"""
OPERA Territorial — Cliente Supabase e Helpers de Auditoria
"""
import os
from supabase import create_client, Client
from dotenv import load_dotenv
import hashlib
import json
from datetime import datetime

load_dotenv()

url: str = os.getenv("SUPABASE_URL", "")
key: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
supabase: Client = create_client(url, key)


def compute_hash(prev_hash: str, data: dict, actor_id: str = None) -> str:
    """Calcula SHA-256 encadeado."""
    timestamp = datetime.utcnow().isoformat()
    base = f"{prev_hash or '0x00'}|{json.dumps(data, sort_keys=True)}|{timestamp}|{actor_id or 'system'}"
    return hashlib.sha256(base.encode('utf-8')).hexdigest()


def log_audit(table_name: str, row_id: str, op: str, old_row: dict = None, new_row: dict = None, actor_id: str = None):
    """Insere registro no audit_log com hash automático (trigger no banco)."""
    data = {
        "table_name": table_name,
        "row_id": row_id,
        "op": op,
        "actor_id": actor_id,
        "old_row": old_row,
        "new_row": new_row,
        "at": datetime.utcnow().isoformat()
    }
    if op in ['UPDATE', 'DELETE']:
        prev = supabase.table('audit_log').select('curr_hash').eq('row_id', row_id).order('at', desc=True).limit(1).execute()
        if prev.data:
            data['prev_hash'] = prev.data[0]['curr_hash']
    return supabase.table('audit_log').insert(data).execute()
