#!/usr/bin/env bash
set -euo pipefail

echo "Waiting for API readiness..."
READY=0
for _ in $(seq 1 60); do
  if curl --fail --silent http://localhost:8000/readyz > /tmp/taskmind_readyz.json 2>/dev/null; then
    READY=1
    break
  fi
  sleep 2
done

if [ "${READY}" -ne 1 ]; then
  echo "API did not become ready in time."
  exit 1
fi

echo "Checking API readiness..."
cat /tmp/taskmind_readyz.json
echo

echo "Creating smoke task..."
TASK_PAYLOAD='{"title":"Smoke task","description":"Verify stack boots and worker processes queued task.","task_type":"analysis","risk_level":"low","acceptance_criteria":["worker claims task","run is persisted"]}'
curl --fail --silent -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d "${TASK_PAYLOAD}" > /tmp/taskmind_task.json
cat /tmp/taskmind_task.json
echo

TASK_ID=$(python3 -c 'import json; print(json.load(open("/tmp/taskmind_task.json"))["id"])')

echo "Waiting for worker to process task ${TASK_ID}..."
STATUS=""
for _ in $(seq 1 20); do
  STATUS=$(curl --fail --silent http://localhost:8000/tasks/${TASK_ID} | python3 -c 'import json,sys; print(json.load(sys.stdin)["status"])')
  if [ "${STATUS}" = "completed" ] || [ "${STATUS}" = "failed" ]; then
    break
  fi
  sleep 1
done

if [ "${STATUS}" != "completed" ]; then
  echo "Task did not complete successfully. Final status: ${STATUS}"
  exit 1
fi

echo "Final task state:"
curl --fail --silent http://localhost:8000/tasks/${TASK_ID}
echo

echo "Recent runs:"
curl --fail --silent http://localhost:8000/runs
echo

echo "Verification complete."
