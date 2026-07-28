import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional


def _default_output_dir() -> Path:
    return Path(__file__).resolve().parent.parent / "data" / "output"


def registrar_evento(
    evento: str,
    detalhes: Optional[Dict[str, Any]] = None,
    output_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    """Registra um evento de auditoria em um arquivo JSON local."""
    output_path = output_dir or _default_output_dir()
    output_path.mkdir(parents=True, exist_ok=True)

    entry = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "evento": evento,
        "detalhes": detalhes or {},
    }

    history_path = output_path / "auditoria.json"
    if history_path.exists():
        try:
            history = json.loads(history_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            history = []
        if not isinstance(history, list):
            history = []
    else:
        history = []

    history.append(entry)
    history_path.write_text(json.dumps(history, indent=2, ensure_ascii=False), encoding="utf-8")
    return entry


def carregar_auditoria(output_dir: Optional[Path] = None) -> list[Dict[str, Any]]:
    """Carrega a trilha de auditoria local."""
    history_path = (output_dir or _default_output_dir()) / "auditoria.json"
    if not history_path.exists():
        return []

    try:
        data = json.loads(history_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []

    return data if isinstance(data, list) else []
