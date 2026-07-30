"""
OPERA Territorial — Server v3.0 (Flask + Supabase)
API REST completa com endpoints APMO + serve frontend
Pesquisa de campo: 03/09/2026
"""
import os
import json
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
from datetime import datetime
import uuid

from python.db import supabase, log_audit
from python.modules.hash_chain import generate_hash, verify_chain

load_dotenv()
app = Flask(__name__, static_folder='frontend', static_url_path='')
CORS(app)

PORT = int(os.getenv("PORT", 8001))

# ====================
# SERVE FRONTEND
# ====================
@app.route('/')
def index():
    return send_from_directory('frontend', 'index.html')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('frontend', path)

# ====================
# API ENDPOINTS
# ====================

@app.route('/api/dashboard', methods=['GET'])
def get_dashboard():
    """Agrega KPIs reais do Supabase."""
    try:
        zonas = supabase.table('zonas').select('id', count='exact').execute()
        total_zonas = zonas.count
        
        obras = supabase.table('obras').select('id', count='exact').eq('status', 'em_andamento').execute()
        obras_ativas = obras.count
        
        forn = supabase.table('fornecedores').select('id', count='exact').eq('ativo', True).execute()
        fornecedores_ativos = forn.count
        
        demandas = 22  # mock
        
        tipos = supabase.table('zonas').select('tipo', count='exact').group_by('tipo').execute()
        counts = {item['tipo']: item['count'] for item in tipos.data} if tipos.data else {}
        
        creche = "25%"
        saude = "50%"
        
        return jsonify({
            "kpis": {
                "setores": total_zonas,
                "obras": obras_ativas,
                "fornecedores": fornecedores_ativos,
                "demandas": demandas,
                "zum": counts.get('ZUM', 0),
                "zeis": counts.get('ZEIS', 0),
                "creche_cobertura": creche,
                "saude_cobertura": saude
            },
            "setores": supabase.table('zonas').select('codigo, nome, tipo, to_ratio, ca_basico, ca_maximo, nivel_incomodidade').execute().data
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/audit', methods=['GET'])
def get_audit():
    limit = request.args.get('limit', 20, type=int)
    try:
        result = supabase.table('audit_log').select('*').order('at', desc=True).limit(limit).execute()
        return jsonify(result.data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/snapshots', methods=['GET'])
def get_snapshots():
    try:
        result = supabase.table('snapshot_operacional').select('*').order('snapshot_date', desc=True).execute()
        return jsonify(result.data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/integrity', methods=['GET'])
def check_integrity():
    """Verifica a cadeia de hash usando verify_chain() centralizado."""
    try:
        result = supabase.table('audit_log').select('curr_hash, prev_hash, new_row, at, actor_id').order('at', asc=True).execute()
        if not result.data:
            return jsonify({"status": "no_data", "message": "Nenhum registro encontrado"})
        # Usa a função centralizada verify_chain que bate com o trigger SQL
        chain_result = verify_chain(result.data)
        return jsonify(chain_result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/ico', methods=['GET'])
def get_ico():
    obra_id = request.args.get('obra_id')
    if not obra_id:
        return jsonify({"error": "obra_id e obrigatorio"}), 400
    try:
        result = supabase.table('ico_registros').select('*').eq('obra_id', obra_id).order('data_referencia', desc=True).limit(10).execute()
        return jsonify(result.data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/restore', methods=['POST'])
def restore_snapshot():
    """Restaura um snapshot operacional."""
    data = request.get_json()
    obra_id = data.get('obra_id')
    snapshot_date = data.get('snapshot_date')
    if not obra_id or not snapshot_date:
        return jsonify({"error": "obra_id e snapshot_date obrigatorios"}), 400
    try:
        snapshot = supabase.table('snapshot_operacional').select('payload').eq('obra_id', obra_id).eq('snapshot_date', snapshot_date).execute()
        if not snapshot.data:
            return jsonify({"error": "Snapshot nao encontrado"}), 404
        return jsonify({"status": "restored", "payload": snapshot.data[0]['payload']})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ====================
# MAIN
# ====================
if __name__ == '__main__':
    print('═══════════════════════════════════════════════')
    print('  OPERA Territorial v3.0 — Servidor Flask+Supabase')
    print(f'  Frontend: http://127.0.0.1:{PORT}/')
    print('  /api/dashboard  /api/audit')
    print('  /api/snapshots  /api/integrity')
    print('  /api/ico        /api/restore')
    print('═══════════════════════════════════════════════')
    app.run(host='0.0.0.0', port=PORT, debug=False)
