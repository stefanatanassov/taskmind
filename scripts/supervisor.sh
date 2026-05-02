#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
export TASKMIND_DATABASE_URL="${TASKMIND_DATABASE_URL:-postgresql+psycopg://taskmind:taskmind@127.0.0.1:5432/taskmind}"

"$ROOT_DIR/.venv/bin/python" -m taskmind.supervisor "$@"
