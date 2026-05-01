# How To Add A Task

## Task shape

The API accepts:

- `title`
- `description`
- `task_type`
- `risk_level`
- `acceptance_criteria`
- `required_artifacts`

The request schema is defined in:

- [src/taskmind/schemas.py](/Users/stefanatanassov/Documents/New%20project/src/taskmind/schemas.py)

## Example

```bash
curl -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Build import validator",
    "description": "Create a validator for CSV imports.",
    "task_type": "feature",
    "risk_level": "medium",
    "acceptance_criteria": [
      "parse CSV rows",
      "detect duplicates",
      "return structured error report"
    ],
    "required_artifacts": [
      "plan",
      "implementation",
      "critique"
    ]
  }'
```

## What happens next

- the API persists the task
- the controller assigns a route
- the worker claims the task
- the worker stores a run record with artifacts and evaluation

## Inspecting results

```bash
curl http://localhost:8000/tasks
curl http://localhost:8000/runs
```

