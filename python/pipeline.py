"""
OPERA Territorial — Pipeline ETL
Lê CSV de zonas e popula o Supabase com auditoria e versionamento
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from datetime import datetime
from python.db import supabase, log_audit
from python.modules.hash_chain import generate_hash
import uuid


def ingest_zonas(csv_path: str):
    """Lê CSV de zonas e insere no Supabase com versionamento."""
    df = pd.read_csv(csv_path, sep=';', encoding='utf-8')
    
    for _, row in df.iterrows():
        data = {
            "codigo": row['codigo'],
            "nome": row['nome'],
            "macrozona": row.get('macrozona'),
            "tipo": row.get('tipo'),
            "to_ratio": float(row.get('to_ratio', 0)),
            "ca_basico": float(row.get('ca_basico', 0)),
            "ca_maximo": float(row.get('ca_maximo', 0)),
            "permeabilidade_min": float(row.get('permeabilidade_min', 0)),
            "altura_maxima": float(row.get('altura_maxima', 0)),
            "nivel_incomodidade": row.get('nivel_incomodidade'),
            "version": 1,
            "created_reason": "Importação inicial via pipeline"
        }
        
        result = supabase.table('zonas').insert(data).execute()
        if result.data:
            new_id = result.data[0]['id']
            log_audit('zonas', new_id, 'INSERT', new_row=data, actor_id='system')
            version_data = {
                "entity_id": new_id,
                "version": 1,
                "snapshot": data,
                "reason": "Versão inicial da importação",
                "edited_by": None,
                "valid_from": datetime.utcnow().isoformat()
            }
            supabase.table('zonas_versions').insert(version_data).execute()
            print(f"Zona {row['codigo']} inserida com ID {new_id}")
        else:
            print(f"Erro ao inserir {row['codigo']}: {result}")


def create_snapshot(obra_id: str, snapshot_date: str = None):
    """Cria snapshot operacional de uma obra."""
    if snapshot_date is None:
        snapshot_date = datetime.utcnow().date().isoformat()
    
    # Coleta dados da obra
    obra = supabase.table('obras').select('*').eq('id', obra_id).execute()
    if not obra.data:
        return {"error": f"Obra {obra_id} não encontrada"}
    
    # Busca hash anterior
    prev = supabase.table('snapshot_operacional').select('curr_hash').eq('obra_id', obra_id).order('snapshot_date', desc=True).limit(1).execute()
    prev_hash = prev.data[0]['curr_hash'] if prev.data else None
    
    payload = {
        "obra": obra.data[0],
        "date": snapshot_date,
        "generated_by": "pipeline",
        "timestamp": datetime.utcnow().isoformat()
    }
    
    curr_hash = generate_hash(prev_hash, payload)
    
    snapshot = {
        "obra_id": obra_id,
        "snapshot_date": snapshot_date,
        "payload": payload,
        "prev_hash": prev_hash,
        "curr_hash": curr_hash
    }
    
    result = supabase.table('snapshot_operacional').insert(snapshot).execute()
    return result.data


if __name__ == "__main__":
    # Exemplo de uso:
    # python3 python/pipeline.py ingest zonas.csv
    # python3 python/pipeline.py snapshot <obra_id>
    if len(sys.argv) < 2:
        print("Uso: python3 python/pipeline.py <ingest|snapshot> [arquivo|obra_id]")
        sys.exit(1)
    
    cmd = sys.argv[1]
    if cmd == "ingest":
        ingest_zonas(sys.argv[2])
    elif cmd == "snapshot":
        create_snapshot(sys.argv[2])
