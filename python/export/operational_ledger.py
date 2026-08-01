"""Livro-razão operacional encadeado e verificável em JSON."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

from python.modules.hash_chain import canonical_json


SCHEMA_VERSION = "opera-ledger/1.0"


def _record_hash(sequence: int, kind: str, timestamp: str, payload: Mapping[str, Any], previous: str | None) -> str:
    material = {"sequence": sequence, "kind": kind, "timestamp": timestamp, "payload": payload, "prev_hash": previous}
    return hashlib.sha256(canonical_json(material).encode("utf-8")).hexdigest()


def build_ledger(records: Iterable[Mapping[str, Any]], generated_at: str | None = None) -> dict[str, Any]:
    entries = []
    previous = None
    for sequence, source in enumerate(records, start=1):
        kind = str(source.get("kind") or "event")
        timestamp = str(source.get("timestamp") or "")
        payload = dict(source.get("payload") or {})
        current = _record_hash(sequence, kind, timestamp, payload, previous)
        entries.append({"sequence": sequence, "kind": kind, "timestamp": timestamp, "payload": payload, "prev_hash": previous, "curr_hash": current})
        previous = current
    generated_at = generated_at or datetime.now(timezone.utc).isoformat()
    entries_hash = hashlib.sha256(canonical_json(entries).encode("utf-8")).hexdigest()
    return {"manifest": {"schema": SCHEMA_VERSION, "generated_at": generated_at, "algorithm": "SHA-256", "entries": len(entries), "first_hash": entries[0]["curr_hash"] if entries else None, "root_hash": previous, "entries_hash": entries_hash, "external_timestamp": None, "signature": None}, "entries": entries}


def verify_ledger(document: Mapping[str, Any]) -> dict[str, Any]:
    errors = []
    previous = None
    entries = document.get("entries") if isinstance(document.get("entries"), list) else []
    for index, entry in enumerate(entries, start=1):
        expected = _record_hash(index, str(entry.get("kind") or "event"), str(entry.get("timestamp") or ""), entry.get("payload") or {}, previous)
        if entry.get("sequence") != index: errors.append({"sequence": index, "error": "sequence"})
        if entry.get("prev_hash") != previous: errors.append({"sequence": index, "error": "prev_hash"})
        if entry.get("curr_hash") != expected: errors.append({"sequence": index, "error": "curr_hash"})
        previous = entry.get("curr_hash")
    manifest = document.get("manifest") or {}
    if manifest.get("root_hash") != previous: errors.append({"error": "root_hash"})
    expected_entries_hash = hashlib.sha256(canonical_json(entries).encode("utf-8")).hexdigest()
    if manifest.get("entries_hash") != expected_entries_hash: errors.append({"error": "entries_hash"})
    return {"valid": not errors, "entries_checked": len(entries), "root_hash": previous, "errors": errors}


def repository_records(base_dir: Path, obra_id: str | None = None) -> list[dict[str, Any]]:
    records = []
    audit_path = base_dir / "data" / "output" / "auditoria.json"
    try: audit = json.loads(audit_path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError): audit = []
    for event in audit if isinstance(audit, list) else []:
        if obra_id and str(event.get("row_id") or event.get("detalhes", {}).get("obra_id") or "") != obra_id: continue
        records.append({"kind": "audit", "timestamp": event.get("at") or event.get("timestamp") or "", "payload": event})
    snapshot_dir = base_dir / "data" / "snapshots"
    for path in sorted(snapshot_dir.glob("*_metadata.json")):
        try: metadata = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError: continue
        if obra_id and str(metadata.get("obra_id") or "") not in ("", obra_id): continue
        records.append({"kind": "snapshot", "timestamp": metadata.get("timestamp") or path.stem, "payload": metadata})
    return sorted(records, key=lambda item: (str(item["timestamp"]), item["kind"], canonical_json(item["payload"])))
