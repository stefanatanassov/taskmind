# Supervisor Mode

`taskmind` can expose its current execution state as files so an external master agent can supervise through a simple text interface instead of direct API integration.

This does not replace the task-driven runtime. It only changes the transport layer for supervision decisions.

## Directory layout

By default, `taskmind` writes to `./supervisor`:

```text
supervisor/
  state/
    current-task.yaml
    current-run.yaml
    feedback.yaml
    proposals.yaml
    checkpoints.yaml
    last-response-result.yaml
  inbox/
    supervisor-request.yaml
  outbox/
    supervisor-response.yaml
  history/
    events.jsonl
```

Override the base directory with `TASKMIND_SUPERVISOR_DIR`.

## Export current state

```bash
./scripts/supervisor.sh export-state
```

For a specific task:

```bash
./scripts/supervisor.sh export-state --task-id <task-id>
```

This writes the latest task state plus a combined request file at:

```text
supervisor/inbox/supervisor-request.yaml
```

## Write a supervisor response

Create `supervisor/outbox/supervisor-response.yaml` with a structured decision:

```yaml
task_id: 12345678-1234-1234-1234-123456789012
decision: retry_with_simpler_route
reasoning:
  - The last run failed on acceptance coverage.
  - A smaller route is more appropriate for this task shape.
actions:
  - action_type: requeue_task
    task_id: 12345678-1234-1234-1234-123456789012
    route_override:
      - implementer
      - critic
    reason: Retry without planner
status: ready_for_execution
```

Supported actions:

- `create_task`
- `requeue_task`
- `decide_proposal`
- `decide_checkpoint`

## Apply the response

```bash
./scripts/supervisor.sh apply-response
```

The apply step:

- validates the response schema
- applies the requested actions to the live database
- writes `state/last-response-result.yaml`
- appends an audit event to `history/events.jsonl`
- removes the consumed response file

## One-step cycle

```bash
./scripts/supervisor.sh cycle
```

The wrapper defaults to the host-exposed Docker Postgres address:

```text
postgresql+psycopg://taskmind:taskmind@127.0.0.1:5432/taskmind
```

Override `TASKMIND_DATABASE_URL` if you are using a different database.

This exports current state and, if a response file already exists, applies it in the same command.

## Intended use

This mode is useful when:

- a human or external master agent should supervise via files
- local or remote LLM workers should remain inside `taskmind`
- you want versionable, inspectable supervision decisions

This mode is not intended to turn `taskmind` into a prompt-driven agent chat. Tasks still drive execution.
