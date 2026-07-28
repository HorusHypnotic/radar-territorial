import json
from pathlib import Path

from python.audit import carregar_auditoria
from python.contexto import ContextoOperacional
from python.snapshots import carregar_snapshots, verificar_integridade
from python.compare import comparar_snapshots


def carregar_dados_para_dashboard():
    """Carrega dados do pipeline e gera JSON para o dashboard."""
    base_dir = Path(__file__).resolve().parent.parent.parent
    output_dir = base_dir / "data" / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    dados = {
        "setores": 0,
        "obras": 0,
        "fornecedores": 0,
        "prioridade": 0,
        "zonas": [],
        "auditoria": carregar_auditoria(output_dir),
        "snapshots": carregar_snapshots(),
        "comparacao": {},
        "integridade": [],
        "contexto": [],
    }

    geojson_path = output_dir / "radar_geojson.geojson"
    if geojson_path.exists():
        with geojson_path.open("r", encoding="utf-8") as handle:
            geojson = json.load(handle)
        features = geojson.get("features", [])
        if features:
            dados["setores"] = len(features)
            dados["obras"] = sum(1 for feature in features if (feature.get("properties", {}).get("categoria") == "Alto"))
            dados["fornecedores"] = len({feature.get("properties", {}).get("nome") for feature in features if feature.get("properties", {}).get("nome")})
            valores = [float(feature.get("properties", {}).get("indicador_ajustado", 0)) for feature in features]
            dados["prioridade"] = sum(valores) / len(valores) if valores else 0
            dados["zonas"] = [
                {
                    "nome": feature.get("properties", {}).get("nome", f"Zona {index}"),
                    "indicador": float(feature.get("properties", {}).get("indicador_ajustado", 0)),
                    "categoria": feature.get("properties", {}).get("categoria", "Médio"),
                }
                for index, feature in enumerate(features)
            ]
    else:
        print("⚠️ Arquivo de dados não encontrado. Execute o pipeline primeiro.")

    snapshots = carregar_snapshots()
    dados["integridade"] = [verificar_integridade(item["timestamp"]) for item in snapshots]

    contexto = ContextoOperacional(output_dir=output_dir)
    dados["contexto"] = contexto.listar()

    if len(snapshots) >= 2:
        ultimo = snapshots[-1]["timestamp"]
        anterior = snapshots[-2]["timestamp"]
        try:
            dados["comparacao"] = comparar_snapshots(anterior, ultimo)
        except Exception as exc:
            dados["comparacao"] = {"erro": str(exc)}

    json_path = output_dir / "dashboard_data.json"
    with json_path.open("w", encoding="utf-8") as handle:
        json.dump(dados, handle, indent=2, ensure_ascii=False)

    return dados

    print(f"✅ Dados salvos em: {json_path}")
    return dados


if __name__ == "__main__":
    carregar_dados_para_dashboard()
