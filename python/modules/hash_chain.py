"""Cadeias SHA-256 determinísticas para auditoria, versões e evidências."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any, Iterable, Mapping, Optional


def canonical_json(value: Any) -> str:
    """Serializa dados de modo estável e independente de locale."""
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


class HashChain:
    """Calcula e verifica uma cadeia SHA-256 reproduzível."""

    def __init__(self, salt: Optional[str] = None) -> None:
        self.salt = salt if salt is not None else os.getenv("HASH_SALT", "opera_territorial_v2")

    def calculate_hash(
        self,
        data: Mapping[str, Any],
        previous_hash: Optional[str] = None,
        metadata: Optional[Mapping[str, Any]] = None,
    ) -> str:
        """Calcula o hash usando somente entradas persistíveis e reproduzíveis."""
        payload = "|".join(
            (
                self.salt,
                previous_hash or "",
                canonical_json(data),
                canonical_json(metadata or {}),
            )
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def build_entry(
        self,
        data: Mapping[str, Any],
        previous_hash: Optional[str] = None,
        metadata: Optional[Mapping[str, Any]] = None,
    ) -> dict[str, Any]:
        """Cria uma entrada autocontida pronta para persistência."""
        normalized_data = dict(data)
        normalized_metadata = dict(metadata or {})
        return {
            "data": normalized_data,
            "metadata": normalized_metadata,
            "prev_hash": previous_hash,
            "curr_hash": self.calculate_hash(normalized_data, previous_hash, normalized_metadata),
        }

    def verify_chain(
        self,
        entries: Iterable[Mapping[str, Any]],
        hash_field: str = "curr_hash",
        prev_hash_field: str = "prev_hash",
    ) -> dict[str, Any]:
        """Verifica o hash de cada entrada e o vínculo com sua predecessora."""
        result: dict[str, Any] = {
            "valid": True,
            "errors": [],
            "entries_checked": 0,
            "first_hash": None,
            "last_hash": None,
        }
        previous_hash: Optional[str] = None
        for index, entry in enumerate(entries):
            current_hash = entry.get(hash_field)
            stored_previous = entry.get(prev_hash_field)
            data = entry.get("data")
            if data is None:
                excluded = {hash_field, prev_hash_field, "metadata"}
                data = {key: value for key, value in entry.items() if key not in excluded}
            computed = self.calculate_hash(data, previous_hash, entry.get("metadata") or {})
            if stored_previous != previous_hash:
                result["valid"] = False
                result["errors"].append({"index": index, "field": prev_hash_field, "expected": previous_hash, "found": stored_previous})
            if current_hash != computed:
                result["valid"] = False
                result["errors"].append({"index": index, "field": hash_field, "stored": current_hash, "computed": computed})
            if index == 0:
                result["first_hash"] = current_hash
            previous_hash = current_hash
            result["entries_checked"] += 1
        result["last_hash"] = previous_hash
        return result

    @staticmethod
    def hash_file(file_path: Path, chunk_size: int = 8192) -> str:
        """Calcula SHA-256 do conteúdo de um arquivo."""
        digest = hashlib.sha256()
        with file_path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(chunk_size), b""):
                digest.update(chunk)
        return digest.hexdigest()

    @staticmethod
    def hash_file_content(content: bytes) -> str:
        """Calcula SHA-256 de conteúdo já carregado em memória."""
        return hashlib.sha256(content).hexdigest()

    def hash_evidence(self, content: bytes, metadata: Mapping[str, Any]) -> str:
        """Vincula o hash do arquivo aos metadados canônicos da evidência."""
        data = {"content_sha256": hashlib.sha256(content).hexdigest()}
        return self.calculate_hash(data, metadata=metadata)


def verify_obra_integrity(obra_id: str, supabase_client: Any, chain: Optional[HashChain] = None) -> dict[str, Any]:
    """Aciona os verificadores PostgreSQL que usam a serialização original."""
    del chain  # compatibilidade da assinatura; verificação autoritativa ocorre no banco
    checks = []
    checks_spec = (
        ("audit_chain", "verify_hash_chain", {"p_table_name": "obras", "p_row_id": obra_id}),
        ("snapshot_chain", "verify_snapshot_chain", {"p_obra_id": obra_id}),
        ("version_chain", "verify_version_chain", {"p_entity_type": "obras", "p_entity_id": obra_id}),
    )
    for name, function, params in checks_spec:
        rows = supabase_client.rpc(function, params).execute().data or []
        valid = all(row.get("is_valid", False) for row in rows)
        checks.append({"name": name, "valid": valid, "details": {"entries_checked": len(rows), "rows": rows}})
    return {"obra_id": obra_id, "valid": all(check["valid"] for check in checks), "checks": checks}
