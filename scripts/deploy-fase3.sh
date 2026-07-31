#!/usr/bin/env bash
set -euo pipefail

python -m pytest -q
python scripts/validate_deploy.py
git diff --check

echo "Validação concluída. O deploy ocorre pelo workflow após merge em master."
