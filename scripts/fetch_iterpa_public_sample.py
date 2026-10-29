"""Coleta controlada de amostra pública ArcGIS para QA local.
Não envia credenciais, não consulta pessoas e não exporta atributos.
Execução manual via PETECO; exige rede e confirmação de licença/termos.
"""
import json
import sys
from urllib.parse import urlencode
from urllib.request import urlopen

BASE = "https://arcgisportal.iterpa.pa.gov.br/server/rest/services/SICARF/acervoFundiarioMapserver/MapServer"
ALLOWED_LAYERS = {87, 72, 73, 63, 64}
MAX_FEATURES = 5


def fetch_sample(layer_id: int) -> dict:
    if layer_id not in ALLOWED_LAYERS:
        raise ValueError("Camada não autorizada para amostra")
    query = urlencode({
        "where": "1=1",
        "outFields": "OBJECTID",
        "returnGeometry": "true",
        "outSR": "4326",
        "resultRecordCount": str(MAX_FEATURES),
        "f": "geojson",
    })
    with urlopen(f"{BASE}/{layer_id}/query?{query}", timeout=20) as response:
        payload = json.load(response)
    if payload.get("type") != "FeatureCollection" or not isinstance(payload.get("features"), list):
        raise RuntimeError("Resposta não é GeoJSON FeatureCollection")
    geometries = []
    for feature in payload["features"][:MAX_FEATURES]:
        geometry = feature.get("geometry") if isinstance(feature, dict) else None
        if geometry and geometry.get("type") in {"Polygon", "MultiPolygon", "Point", "MultiPoint", "LineString", "MultiLineString"}:
            geometries.append({"type": "Feature", "properties": {}, "geometry": geometry})
    return {
        "type": "FeatureCollection",
        "features": geometries,
        "metadata": {
            "source": f"{BASE}/{layer_id}",
            "layer_id": layer_id,
            "crs_requested": "EPSG:4326",
            "limit": MAX_FEATURES,
            "sample_only": True,
            "not_evidence_of_ownership": True,
            "not_a_redencao_geographic_clip": True,
        },
    }


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Uso: python scripts/fetch_iterpa_public_sample.py 87")
    print(json.dumps(fetch_sample(int(sys.argv[1])), ensure_ascii=False))
