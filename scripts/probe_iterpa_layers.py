"""Sonda somente-leitura de metadados ArcGIS. Executar manualmente via PETECO/Termux.
Não baixa feições, não usa credenciais, não imprime atributos de pessoas.
"""
import json
import sys
from urllib.request import urlopen

BASE = "https://arcgisportal.iterpa.pa.gov.br/server/rest/services/SICARF/acervoFundiarioMapserver/MapServer"
LAYERS = (87, 72, 73, 63, 64, 93, 98)


def fetch_metadata(layer_id: int) -> dict:
    with urlopen(f"{BASE}/{layer_id}?f=pjson", timeout=15) as response:
        data = json.load(response)
    if "error" in data:
        raise RuntimeError(f"ArcGIS error on layer {layer_id}: {data['error'].get('code')}")
    return {
        "id": layer_id,
        "name": data.get("name"),
        "geometryType": data.get("geometryType"),
        "maxRecordCount": data.get("maxRecordCount"),
        "supportsQuery": "Query" in data.get("capabilities", ""),
        "field_names": [f.get("name") for f in data.get("fields", [])],
        "has_personal_data_risk": any(
            any(word in (f.get("name") or "").lower() for word in ("cpf", "nome", "requerente", "proprietario", "titular"))
            for f in data.get("fields", [])
        ),
    }


def main() -> int:
    for layer in LAYERS:
        try:
            print(json.dumps(fetch_metadata(layer), ensure_ascii=False))
        except Exception as exc:
            print(json.dumps({"id": layer, "status": "BLOCKED", "error_type": type(exc).__name__}))
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
