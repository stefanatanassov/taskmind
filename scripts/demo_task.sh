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
  }'

echo
echo "Current tasks:"
curl --fail --silent http://localhost:8000/tasks
echo
echo "Current runs:"
curl --fail --silent http://localhost:8000/runs
echo
