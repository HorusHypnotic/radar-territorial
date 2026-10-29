"""Validador offline de respostas ArcGIS previamente salvas.
Não imprime atributos de feições nem comprova domínio fundiário.
"""
import json
import sys
from pathlib import Path


def validate(payload):
    if not isinstance(payload, dict) or payload.get("error"):
        return {"status": "BLOCKED", "reason": "arcgis_error_or_invalid"}
    if not isinstance(payload.get("features"), list):
        return {"status": "BLOCKED", "reason": "missing_features"}
    features = payload["features"]
    geometry_count = sum(
        isinstance(feature.get("geometry"), dict)
        for feature in features if isinstance(feature, dict)
    )
    reference = payload.get("spatialReference") or {}
    return {
        "status": "PARSED",
        "features": len(features),
        "geometries": geometry_count,
        "spatial_reference": reference.get("wkid") if isinstance(reference, dict) else None,
        "exceededTransferLimit": payload.get("exceededTransferLimit", False),
        "note": "No property or title inference",
    }


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Uso: python scripts/validate_iterpa_response.py resposta-publica.json")
    print(json.dumps(validate(json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))), ensure_ascii=False))
