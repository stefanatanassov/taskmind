# FAQ

## What is `taskmind`?

`taskmind` is a task-driven agent orchestration MVP. A task enters the system, the controller chooses a route, the worker executes isolated steps, evaluation scores the output, and feedback records whether the route was useful.

## How is this different from a prompt-driven agent app?

The primary input is a `Task`, not a chat prompt. Users submit work with acceptance criteria. The system decides whether to use planner, implementer, critic, or a simpler route.

## What happens when I add a task?

1. The API stores the task in Postgres.
2. The controller selects a route.
3. The worker polls queued tasks.
4. The worker runs the selected agent roles.
5. Artifacts and evaluation are stored as a `Run`.
6. The task ends in `completed` or `failed`.

## How do I add a task?

Use the API directly:

```bash
curl -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Validate CSV imports",
    "description": "Build an import validator with duplicate detection.",
    "task_type": "feature",
    "risk_level": "medium",
    "acceptance_criteria": [
      "parse CSV rows",
      "detect duplicates",
      "return structured error report"
    ]
  }'
```

Or use:

```bash
./scripts/demo_task.sh
```

## How do I register a new agent?

Add a YAML file under `config/agents/`, then make sure the controller knows when to select that role. The worker already knows how to execute role-based steps through the provider interface.

Start with:

- [docs/contributors/how-to-register-agent.md](/Users/stefanatanassov/Documents/New%20project/docs/contributors/how-to-register-agent.md)

## Where is routing logic defined?

The current MVP route selection is in [src/taskmind/controller.py](/Users/stefanatanassov/Documents/New%20project/src/taskmind/controller.py).

## Where are tasks and runs stored?

The SQL models live in:

- [src/taskmind/models.py](/Users/stefanatanassov/Documents/New%20project/src/taskmind/models.py)

## How do I switch models?

Set the provider through `.env` or the quickstart script:

- `mock`
- `ollama`
- `openai_compatible`

See:

- [README.md](/Users/stefanatanassov/Documents/New%20project/README.md)
- [scripts/quickstart.sh](/Users/stefanatanassov/Documents/New%20project/scripts/quickstart.sh)

## How do I tweak behavior?

There are three main levers:

1. Change routing logic in [src/taskmind/controller.py](/Users/stefanatanassov/Documents/New%20project/src/taskmind/controller.py)
2. Change provider/model selection in `.env` or [scripts/quickstart.sh](/Users/stefanatanassov/Documents/New%20project/scripts/quickstart.sh)
3. Change evaluation heuristics in [src/taskmind/evaluation.py](/Users/stefanatanassov/Documents/New%20project/src/taskmind/evaluation.py)

## Should the help assistant be part of runtime orchestration?

No. Keep explanation and onboarding separate from the task execution loop. A guide assistant is useful for documentation and contributor help, but it should not become part of the control plane.

