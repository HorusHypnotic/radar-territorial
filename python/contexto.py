import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from python.audit import registrar_evento


class ContextoOperacional:
    """Mantém relacionamentos semânticos entre entidades do projeto."""

    def __init__(self, output_dir: Optional[Path] = None):
        self.output_dir = output_dir or Path(__file__).resolve().parent.parent / "data" / "output"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.relacionamentos_path = self.output_dir / "contexto.json"

    def _carregar(self) -> List[Dict[str, Any]]:
        if not self.relacionamentos_path.exists():
            return []
        try:
            data = json.loads(self.relacionamentos_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return []
        return data if isinstance(data, list) else []

    def _salvar(self, relacionamentos: List[Dict[str, Any]]) -> None:
        self.relacionamentos_path.write_text(json.dumps(relacionamentos, indent=2, ensure_ascii=False), encoding="utf-8")

    def vincular(self, origem: str, destino: str, tipo: str = "relaciona_com", detalhe: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        relacionamento = {
            "id": f"{origem}-{destino}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "origem": origem,
            "destino": destino,
            "tipo": tipo,
            "detalhe": detalhe or {},
            "timestamp": datetime.now().isoformat(timespec="seconds"),
        }
        relacionamentos = self._carregar()
        relacionamentos.append(relacionamento)
        self._salvar(relacionamentos)
        registrar_evento("contexto_vinculo", detalhes=relacionamento, output_dir=self.output_dir)
        return relacionamento

    def listar(self) -> List[Dict[str, Any]]:
        return self._carregar()

    def por_origem(self, origem: str) -> List[Dict[str, Any]]:
        return [item for item in self._carregar() if item.get("origem") == origem]

    def por_destino(self, destino: str) -> List[Dict[str, Any]]:
        return [item for item in self._carregar() if item.get("destino") == destino]
