#!/usr/bin/env bash
set -euo pipefail

PORT="${1:-8090}"

cd "$(dirname "${BASH_SOURCE[0]}")/../python_server"
export PYTHONPATH="$(pwd)/.."

uvicorn main:app --host 0.0.0.0 --port "$PORT" --reload

