#!/usr/bin/env bash
set -euo pipefail

echo "Submitting demo task..."

curl --fail --silent -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "title": "CSV import validator",
    "description": "Build an import validator with duplicate detection and a structured error report.",
    "task_type": "feature",
    "risk_level": "medium",
    "acceptance_criteria": [
      "parse CSV rows",
      "detect duplicate entries",
      "return structured error report"
    ],
    "required_artifacts": [
      "plan",
      "implementation",
      "critique"
    ]
  }' > /tmp/taskmind_demo_task.json

cat /tmp/taskmind_demo_task.json
echo

TASK_ID=$(python3 -c 'import json; print(json.load(open("/tmp/taskmind_demo_task.json"))["id"])')

echo "Waiting for task ${TASK_ID} to complete..."
STATUS=""
for _ in $(seq 1 20); do
  STATUS=$(curl --fail --silent "http://localhost:8000/tasks/${TASK_ID}" | python3 -c 'import json,sys; print(json.load(sys.stdin)["status"])')
  if [ "${STATUS}" = "completed" ] || [ "${STATUS}" = "failed" ]; then
    break
  fi
  sleep 1
done

if [ "${STATUS}" != "completed" ]; then
  echo "Demo task did not complete successfully. Final status: ${STATUS}"
  exit 1
fi

echo
echo "Current tasks:"
curl --fail --silent http://localhost:8000/tasks
echo
echo "Current runs:"
curl --fail --silent http://localhost:8000/runs
echo
