"""Exporta e verifica o livro-razão operacional local."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from python.export.operational_ledger import build_ledger, repository_records, verify_ledger


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "data" / "output" / "livro_razao.json")
    parser.add_argument("--obra-id")
    args = parser.parse_args()
    document = build_ledger(repository_records(ROOT, args.obra_id))
    verification = verify_ledger(document)
    if not verification["valid"]: raise RuntimeError(f"livro-razão inválido: {verification['errors']}")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(document, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{args.output.resolve()} · {verification['entries_checked']} entradas · {verification['root_hash']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
