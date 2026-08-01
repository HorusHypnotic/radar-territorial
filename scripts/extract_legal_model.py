"""Extrai o catálogo CNAE do Anexo VI e publica o modelo legal territorial.

O texto de entrada deve ser OCR da LC 128/2022. O script não infere permissões
entre níveis: cada atividade fica vinculada exatamente ao grupo onde foi listada.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

SOURCE_URL = "https://redencao.pa.gov.br/publicacoes/legislacoes/lei/4165/lei-complementar-no-1282022"
CODE_VALUE = r"(?:\d{1,2}(?:[.\-]\d{1,2}){1,2}|\d{4}-\d)(?:/\d{2})?"
CODE = re.compile(rf"^\s*({CODE_VALUE})\s*[.\-–—]?\s+(.+)")
INLINE_CODE = re.compile(rf"(?<![\d.])({CODE_VALUE})\s*[.\-–—]?\s+")
HEADINGS = {
    "COMERCIO PARA NÍVEL 1": "ZUM-N1", "SERVIÇOS PARA NÍVEL 1": "ZUM-N1",
    "COMÉRCIO PARA NÍVEL 1": "ZUM-N1", "SERVICOS PARA NÍVEL 1": "ZUM-N1",
    "SERVIÇOS PARA NÍVEL 2": "ZUM-N2", "SERVICOS PARA NÍVEL 2": "ZUM-N2",
    "COMÉRCIO PARA NÍVEL 3": "ZUM-N3", "COMERCIO PARA NÍVEL 3": "ZUM-N3",
    "SERVIÇOS PARA NÍVEL 3": "ZUM-N3", "SERVICOS PARA NÍVEL 3": "ZUM-N3",
    "SERVIÇOS PARA NÍVEL 4": "ZUM-N4", "SERVICOS PARA NÍVEL 4": "ZUM-N4",
    "COMÉRCIO PARA NÍVEL 5": "ZUM-N5", "COMERCIO PARA NÍVEL 5": "ZUM-N5",
    "SERVIÇOS PARA NÍVEL 5": "ZUM-N5", "SERVICOS PARA NÍVEL 5": "ZUM-N5",
    "INDÚSTRIAS PARA NÍVEL 6": "ZUM-N6", "INDUSTRIAS PARA NÍVEL 6": "ZUM-N6",
    "COMERCIO E SERVIÇOS PARA A ZOR": "ZOR", "COMÉRCIO E SERVIÇOS PARA A ZOR": "ZOR",
}

INDICES = {
    "ZUM-N1": {"to_max": 70, "ca_basico": 1.0, "ca_maximo": 2.5, "permeabilidade": 20, "artigo": 51},
    "ZUM-N2": {"to_max": 70, "ca_basico": 1.0, "ca_maximo": 2.5, "permeabilidade": 20, "artigo": 51},
    "ZUM-N3": {"to_max": 65, "ca_basico": 1.0, "ca_maximo": 5.0, "permeabilidade": 20, "artigo": 52},
    "ZUM-N4": {"to_max": 65, "ca_basico": 1.0, "ca_maximo": 5.0, "permeabilidade": 20, "artigo": 53},
    "ZUM-N5": {"to_max": 70, "ca_basico": 1.0, "ca_maximo": 2.5, "permeabilidade": 20, "artigo": 54},
    "ZUM-N6": {"to_max": 60, "ca_basico": 1.0, "ca_maximo": 2.0, "permeabilidade": 30, "artigo": 55},
    "ZOR": {"to_max": 20, "ca_basico": 0.4, "ca_maximo": None, "permeabilidade": 50, "artigo": 57},
    "ZIR": {"to_max": 60, "ca_basico": 1.0, "ca_maximo": 2.0, "permeabilidade": 30, "artigo": 58},
}


def repair_mojibake(value: str) -> str:
    replacements = {"Ă‡": "Ç", "Ă§": "ç", "Ă‰": "É", "Ă©": "é", "Ă": "Í", "Ăş": "ú", "Ă£": "ã", "Ăµ": "õ"}
    for broken, repaired in replacements.items():
        value = value.replace(broken, repaired)
    for _ in range(2):
        if "Ã" not in value and "Â" not in value:
            break
        repaired = None
        for encoding in ("cp1252", "latin1"):
            try:
                repaired = value.encode(encoding).decode("utf-8")
                break
            except (UnicodeEncodeError, UnicodeDecodeError):
                continue
        if repaired is None:
            break
        value = repaired
    return value


def normalize(value: str) -> str:
    value = repair_mojibake(value)
    return re.sub(r"\s+", " ", value).strip(" -*.;")


def clean_activity_name(value: str) -> str:
    value = normalize(value)
    value = re.split(r"\s+(?:ZONA DE\b|PROTE\S{0,8} DO|RESIDENCIAL\b|UNIFAMILIAR\b|MISTO\b|N[ÍIĂ]\S{0,5}VEL\s*[1-6]|MICRO INDUSTRIAL|PARQUE LOG[ÍI]|IND[ÚUĂ]\S{0,8}STRIA COM|ESSES\b)", value, maxsplit=1, flags=re.I)[0]
    value = re.split(r"\s+\[\|?\s*ZONA", value, maxsplit=1, flags=re.I)[0]
    return normalize(value).lstrip("—–â€ ")


def extract_activities(text: str) -> list[dict[str, Any]]:
    upper_text = text.upper()
    start = upper_text.rfind("ANEXO VI: QUADRO DE ATIVIDADES")
    remainder = upper_text[start + 1:] if start >= 0 else ""
    end_match = re.search(r"ANEXO\s+VI(?:I|L)\b", remainder)
    end = start + 1 + end_match.start() if end_match else -1
    if start < 0 or end < 0:
        raise ValueError("limites do Anexo VI não encontrados")
    scope: str | None = None
    activities: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    for raw in text[start:end].splitlines():
        line = normalize(raw)
        upper = line.upper()
        level_heading = re.search(r"PARA\s+N\S{0,8}VEL\s*([1-6])", upper)
        matched_heading = f"ZUM-N{level_heading.group(1)}" if level_heading else next((value for key, value in HEADINGS.items() if key in upper), None)
        if "PARA A ZOR" in upper:
            matched_heading = "ZOR"
        if matched_heading:
            scope, current = matched_heading, None
            continue
        matches = list(INLINE_CODE.finditer(line))
        if scope and matches:
            prefix = clean_activity_name(line[:matches[0].start()])
            if current and prefix:
                current["nome"] = clean_activity_name(current["nome"] + " " + prefix)
            for index, match in enumerate(matches):
                finish = matches[index + 1].start() if index + 1 < len(matches) else len(line)
                name = clean_activity_name(line[match.end():finish])
                if not name:
                    continue
                current = {"cnae": match.group(1), "nome": name, "escopo": scope, "status": "permitido", "referencia": "LC 128/2022, Anexo VI"}
                activities.append(current)
        elif current and line and not any(token in upper for token in ("ZONAS USOS", "RUA GUARANT", "ESTADO DO", "PREFEITURA", "GABINETE")):
            if not re.fullmatch(r"\d{1,3}", line):
                continuation = clean_activity_name(line)
                if continuation:
                    current["nome"] = clean_activity_name(current["nome"] + " " + continuation)
    unique: dict[tuple[str, str], dict[str, Any]] = {}
    for activity in activities:
        unique[(activity["cnae"], activity["escopo"])] = activity
    return list(unique.values())


def build_model(text: str) -> dict[str, Any]:
    activities = extract_activities(text)
    if len(activities) < 80:
        raise ValueError(f"extração suspeita: apenas {len(activities)} atividades")
    return {
        "metadata": {
            "status": "derivado_validado", "source": "Lei Complementar nº 128/2022",
            "source_url": SOURCE_URL, "architecture": "DIM/FATO",
            "activity_count": len(activities),
            "notice": "Consulta informativa. CNAE listado no Anexo VI não substitui certidão municipal, análise de impacto ou licenciamento.",
        },
        "dim_zoneamento": INDICES,
        "dim_atividades": activities,
        "fato_permissoes": [{"escopo": a["escopo"], "cnae": a["cnae"], "status": a["status"], "referencia": a["referencia"]} for a in activities],
        "dim_territorio": {
            "municipio": "Redenção-PA", "levels": ["município", "região de planejamento", "setor", "zona", "quadra", "lote"],
            "available_geometry": ["município", "zona"],
            "notice": "A LC 128/2022 não fornece geometrias cadastrais de quadras e lotes; esses níveis exigem base municipal própria.",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    model = build_model(args.source.read_text(encoding="utf-8-sig"))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(model, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Atividades extraídas: {model['metadata']['activity_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
