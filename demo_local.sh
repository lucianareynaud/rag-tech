#!/usr/bin/env bash
set -euo pipefail

PY=${PYTHON:-python3}
PORT=${PORT:-8000}
HOST=${HOST:-0.0.0.0}

echo "[1/4] Criando venv (.venv)…"
$PY -m venv .venv
source .venv/bin/activate

echo "[2/4] Instalando dependências…"
pip install -U pip wheel
pip install -r requirements.txt

echo "[3/4] Ingestão do corpus…"
python -m scripts.ingest

echo "[4/4] Subindo API em http://$HOST:$PORT …"
exec uvicorn app.main:app --host "$HOST" --port "$PORT"
