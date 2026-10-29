"""Checks offline for the public-source catalog, not a geospatial integration test."""
import json
from pathlib import Path

CATALOG = Path(__file__).resolve().parents[1] / "data" / "sources" / "fundiario-v1.json"


def test_fundiario_catalog_is_only_a_catalog():
    data = json.loads(CATALOG.read_text(encoding="utf-8"))
    assert data["status"] == "CATALOG_ONLY_NOT_INGESTED"
    assert {s["id"] for s in data["sources"]} == {"incra-acervo", "iterpa-sicarf", "ibge-malhas"}
    assert all(s["access"] == "NOT_TESTED" for s in data["sources"])
    assert all(s["licence"] == "TO_VERIFY" for s in data["sources"])
    assert all(s["url"].startswith("https://") for s in data["sources"])
    assert "do not prove ownership" in data["warning"]
