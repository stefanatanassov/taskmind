# How To Register An Agent

## Step 1: add an agent config

Create a YAML file in `config/agents/`.

Example:

```yaml
id: reviewer_v1
name: Reviewer
role: reviewer
status: active
model_profile: default
allowed_task_types:
  - feature
  - bugfix
```

Existing examples:

- [config/agents/planner_v1.yaml](/Users/stefanatanassov/Documents/New%20project/config/agents/planner_v1.yaml)
- [config/agents/implementer_v1.yaml](/Users/stefanatanassov/Documents/New%20project/config/agents/implementer_v1.yaml)
- [config/agents/critic_v1.yaml](/Users/stefanatanassov/Documents/New%20project/config/agents/critic_v1.yaml)

## Step 2: teach the controller when to use it

The current routing policy is explicit and lives in:

- [src/taskmind/controller.py](/Users/stefanatanassov/Documents/New%20project/src/taskmind/controller.py)

If you add a new role, update route selection so tasks can actually choose it.

## Step 3: make sure the role is meaningful

Do not add roles that duplicate `planner`, `implementer`, or `critic` without a narrow reason.

A useful new agent should:

- solve a repeated failure pattern
- improve outcomes for a clear task type
- justify added latency and cost

## Step 4: validate it

At minimum:

```bash
pytest
./scripts/quickstart.sh mock
./scripts/demo_task.sh
```

## Important design rule

Help agents and guide agents are fine, but keep them outside the runtime control plane unless they provide measurable execution value.

