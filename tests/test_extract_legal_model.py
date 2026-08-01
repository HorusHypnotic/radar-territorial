import pytest

from scripts.extract_legal_model import build_model, extract_activities


def test_extracts_scoped_cnae_and_continuation():
    text = """ANEXO VI: QUADRO DE ATIVIDADES
    COMÉRCIO PARA NÍVEL 1
    47.12-1. Comércio varejista de mercadorias
    em geral
    SERVIÇOS PARA NÍVEL 2
    85.1. Educação infantil
    ANEXO VII"""
    activities = extract_activities(text)
    assert activities[0]["escopo"] == "ZUM-N1"
    assert "em geral" in activities[0]["nome"]
    assert activities[1]["escopo"] == "ZUM-N2"


def test_extracts_multiple_codes_from_ocr_joined_line_without_zone_label():
    text = """ANEXO VI: QUADRO DE ATIVIDADES
    COMÉRCIO PARA NÍVEL 3
    47.42-3. Material elétrico ZONA DE USO 47.52-1. Equipamentos de telefonia
    ANEXO VII"""
    activities = extract_activities(text)
    assert [(item["cnae"], item["nome"]) for item in activities] == [
        ("47.42-3", "Material elétrico"), ("47.52-1", "Equipamentos de telefonia")
    ]


def test_model_rejects_implausibly_small_annex():
    text = "ANEXO VI: QUADRO DE ATIVIDADES\nCOMÉRCIO PARA NÍVEL 1\n47.12-1. Mercado\nANEXO VII"
    with pytest.raises(ValueError, match="extração suspeita"):
        build_model(text)
