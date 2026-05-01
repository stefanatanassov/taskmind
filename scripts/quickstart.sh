#!/usr/bin/env bash
set -euo pipefail

MODE="${1:-mock}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${ROOT_DIR}/.env"

usage() {
  cat <<'EOF'
Usage:
  ./scripts/quickstart.sh mock
  ./scripts/quickstart.sh ollama
  TASKMIND_PROVIDER_BASE_URL=https://api.openai.com/v1 \
  TASKMIND_PROVIDER_API_KEY=your_key \
  TASKMIND_MODEL=gpt-4.1-mini \
  ./scripts/quickstart.sh openai-compatible
EOF
}

write_env() {
  cat > "${ENV_FILE}" <<EOF
TASKMIND_ENV=development
TASKMIND_DATABASE_URL=postgresql+psycopg://taskmind:taskmind@postgres:5432/taskmind
TASKMIND_REDIS_URL=redis://redis:6379/0
TASKMIND_PROVIDER=${TASKMIND_PROVIDER}
TASKMIND_MODEL=${TASKMIND_MODEL}
TASKMIND_PROVIDER_BASE_URL=${TASKMIND_PROVIDER_BASE_URL}
TASKMIND_PROVIDER_API_KEY=${TASKMIND_PROVIDER_API_KEY}
TASKMIND_WORKER_POLL_INTERVAL=2
EOF
}

start_mock() {
  TASKMIND_PROVIDER="mock"
  TASKMIND_MODEL="${TASKMIND_MODEL:-gpt-oss}"
  TASKMIND_PROVIDER_BASE_URL=""
  TASKMIND_PROVIDER_API_KEY=""
  write_env
  docker compose up --build -d
}

start_ollama() {
  TASKMIND_PROVIDER="ollama"
  TASKMIND_MODEL="${TASKMIND_MODEL:-qwen2.5-coder:14b}"
  TASKMIND_PROVIDER_BASE_URL="${TASKMIND_PROVIDER_BASE_URL:-http://ollama:11434}"
  TASKMIND_PROVIDER_API_KEY=""
  write_env
  docker compose -f docker-compose.yml -f docker-compose.ollama.yml up --build -d
}

start_openai_compatible() {
  if [ -z "${TASKMIND_PROVIDER_BASE_URL:-}" ] || [ -z "${TASKMIND_PROVIDER_API_KEY:-}" ]; then
    echo "TASKMIND_PROVIDER_BASE_URL and TASKMIND_PROVIDER_API_KEY must be set for openai-compatible mode."
    exit 1
  fi
  TASKMIND_PROVIDER="openai_compatible"
  TASKMIND_MODEL="${TASKMIND_MODEL:-gpt-4.1-mini}"
  write_env
  docker compose up --build -d
}

echo "Starting taskmind in '${MODE}' mode..."

case "${MODE}" in
  mock)
    start_mock
    ;;
  ollama)
    start_ollama
    ;;
  openai-compatible)
    start_openai_compatible
    ;;
  *)
    usage
    exit 1
    ;;
esac

echo "Waiting for API readiness..."
for _ in $(seq 1 60); do
  if curl --fail --silent http://localhost:8000/readyz >/dev/null 2>&1; then
    break
  fi
  sleep 2
done

./scripts/verify_stack.sh

echo
echo "taskmind is running."
echo "Try: ./scripts/demo_task.sh"
echo "API: http://localhost:8000"
