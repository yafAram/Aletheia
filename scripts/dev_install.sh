#!/usr/bin/env bash
set -euo pipefail

python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements-dev.txt

cp -n .env.example .env || true

echo "Entorno listo. Activa con: source .venv/bin/activate"
