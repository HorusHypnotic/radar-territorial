"""Gera um SQL único, ordenado e transacional para o SQL Editor do Supabase."""

from __future__ import annotations

import argparse
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MIGRATIONS = ROOT / "data" / "schemas" / "migrations"


def migration_paths() -> list[Path]:
    return sorted(MIGRATIONS.glob("[0-9][0-9][0-9]_*.sql"))


def build_bundle() -> str:
    sections = ["-- Gerado por scripts/build_migration_bundle.py", "begin;"]
    for path in migration_paths():
        sections.extend((f"\n-- >>> {path.name}", path.read_text(encoding="utf-8").strip()))
    sections.extend(("\ncommit;", ""))
    return "\n".join(sections)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="arquivo de saída; sem ele, imprime no terminal")
    args = parser.parse_args()
    bundle = build_bundle()
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(bundle, encoding="utf-8")
        print(args.output.resolve())
    else:
        print(bundle, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
