"""Modelos validados das entidades centrais da Fase 3."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import date, datetime
from typing import Any, Optional


def _serialized(instance: Any) -> dict[str, Any]:
    values = asdict(instance)
    return {key: value.isoformat() if isinstance(value, (date, datetime)) else value for key, value in values.items() if value is not None}


def _required(value: Optional[str], field_name: str) -> str:
    normalized = str(value or "").strip()
    if not normalized:
        raise ValueError(f"{field_name} é obrigatório")
    return normalized


@dataclass
class Atividade:
    obra_id: str
    nome: str
    tipo: str
    id: Optional[str] = None
    responsavel_id: Optional[str] = None
    inicio_previsto: Optional[date] = None
    fim_previsto: Optional[date] = None
    inicio_real: Optional[date] = None
    fim_real: Optional[date] = None
    progresso_pct: float = 0.0
    custo_previsto: Optional[float] = None
    custo_real: Optional[float] = None
    descricao: Optional[str] = None
    status: str = "planejada"
    prioridade: int = 1
    version: int = 1

    def __post_init__(self) -> None:
        self.obra_id = _required(self.obra_id, "obra_id")
        self.nome = _required(self.nome, "nome")
        if self.tipo not in {"fundacao", "estrutura", "instalacao", "acabamento", "servico", "outro"}:
            raise ValueError("tipo de atividade inválido")
        if self.status not in {"planejada", "em_andamento", "concluida", "paralisada"}:
            raise ValueError("status de atividade inválido")
        if not 0 <= float(self.progresso_pct) <= 100:
            raise ValueError("progresso_pct deve estar entre 0 e 100")
        if not 1 <= int(self.prioridade) <= 5:
            raise ValueError("prioridade deve estar entre 1 e 5")
        if self.inicio_previsto and self.fim_previsto and self.fim_previsto < self.inicio_previsto:
            raise ValueError("fim_previsto não pode anteceder inicio_previsto")
        if self.inicio_real and self.fim_real and self.fim_real < self.inicio_real:
            raise ValueError("fim_real não pode anteceder inicio_real")

    def to_dict(self) -> dict[str, Any]:
        return _serialized(self)


@dataclass
class ICORegistro:
    obra_id: str
    data_referencia: date
    componentes: dict[str, float]
    id: Optional[str] = None
    atividade_id: Optional[str] = None
    ico_valor: Optional[float] = None
    calculado_por: Optional[str] = None
    metodo: str = "ponderado"
    peso_qualidade: float = 0.25
    peso_prazo: float = 0.25
    peso_custo: float = 0.25
    peso_seguranca: float = 0.25
    observacao: Optional[str] = None

    def __post_init__(self) -> None:
        self.obra_id = _required(self.obra_id, "obra_id")
        if not isinstance(self.data_referencia, date):
            raise ValueError("data_referencia deve ser uma data")
        if self.metodo not in {"ponderado", "manual"}:
            raise ValueError("método de ICO inválido")
        if not isinstance(self.componentes, dict):
            raise ValueError("componentes deve ser um objeto")
        for key, value in self.componentes.items():
            if key not in {"qualidade", "prazo", "custo", "seguranca", "sustentabilidade"} or not 0 <= float(value) <= 100:
                raise ValueError("componente de ICO inválido")
        weights = self.peso_qualidade + self.peso_prazo + self.peso_custo + self.peso_seguranca
        if abs(weights - 1) >= 0.001:
            raise ValueError("a soma dos pesos deve ser 1")
        if self.ico_valor is None:
            self.ico_valor = self.calcular_ico()
        if not 0 <= float(self.ico_valor) <= 100:
            raise ValueError("ico_valor deve estar entre 0 e 100")

    def calcular_ico(self) -> float:
        weights = {"qualidade": self.peso_qualidade, "prazo": self.peso_prazo, "custo": self.peso_custo, "seguranca": self.peso_seguranca}
        return round(sum(float(self.componentes.get(key, 0)) * weight for key, weight in weights.items()), 2)

    def to_dict(self) -> dict[str, Any]:
        return _serialized(self)


@dataclass
class Evidencia:
    tipo: str
    storage_path: str
    hash_sha256: str
    tamanho_bytes: int
    mime_type: str
    id: Optional[str] = None
    obra_id: Optional[str] = None
    atividade_id: Optional[str] = None
    exif: Optional[dict[str, Any]] = None
    gps_lat: Optional[float] = None
    gps_lng: Optional[float] = None
    captured_at: Optional[datetime] = None
    device: Optional[str] = None
    uploaded_by: Optional[str] = None
    descricao: Optional[str] = None
    tags: list[str] = field(default_factory=list)
    aprovado: bool = False

    def __post_init__(self) -> None:
        if self.tipo not in {"foto", "video", "audio", "pdf", "checklist", "reo", "eco", "documento"}:
            raise ValueError("tipo de evidência inválido")
        self.storage_path = _required(self.storage_path, "storage_path")
        if len(self.hash_sha256) != 64 or any(char not in "0123456789abcdef" for char in self.hash_sha256.lower()):
            raise ValueError("hash_sha256 inválido")
        if not self.obra_id and not self.atividade_id:
            raise ValueError("obra_id ou atividade_id é obrigatório")
        if self.tamanho_bytes < 0:
            raise ValueError("tamanho_bytes inválido")
        if self.gps_lat is not None and not -90 <= self.gps_lat <= 90:
            raise ValueError("gps_lat inválida")
        if self.gps_lng is not None and not -180 <= self.gps_lng <= 180:
            raise ValueError("gps_lng inválida")

    def to_dict(self) -> dict[str, Any]:
        return _serialized(self)


@dataclass
class ECO:
    obra_id: str
    tipo: str
    descricao: str
    id: Optional[str] = None
    impacto_prazo_dias: Optional[int] = None
    impacto_custo: Optional[float] = None
    evidencias_ids: list[str] = field(default_factory=list)
    status: str = "pendente"
    criado_por: Optional[str] = None
    aprovado_por: Optional[str] = None
    motivo: Optional[str] = None
    valor_original: Optional[float] = None
    valor_novo: Optional[float] = None
    version: int = 1

    def __post_init__(self) -> None:
        self.obra_id = _required(self.obra_id, "obra_id")
        self.descricao = _required(self.descricao, "descricao")
        if self.tipo not in {"aditivo", "distrato", "ocorrencia", "medicao", "revisao", "outro"}:
            raise ValueError("tipo de ECO inválido")
        if self.status not in {"pendente", "aprovado", "rejeitado", "cancelado"}:
            raise ValueError("status de ECO inválido")

    def to_dict(self) -> dict[str, Any]:
        return _serialized(self)
