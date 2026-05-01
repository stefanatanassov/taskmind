# How To Register An Agent

## Step 1: add an agent config

Create a YAML file in `config/agents/`.

Example:

```yaml
id: reviewer_v1
name: Reviewer
role: reviewer
status: active
description: Reviews implementation outputs for a narrow class of tasks.
purpose: Catch a repeated failure pattern that the default critic misses.
model_profile: default
allowed_task_types:
  - feature
  - bugfix
when_to_use:
  - Tasks involving API compatibility
when_not_to_use:
  - Generic low-risk tasks
expected_inputs:
  - task description
  - implementer output
expected_outputs:
  - critique summary
tool_policy:
  allowed_tools: []
budget_policy:
  max_cost_usd: 0.15
  max_latency_sec: 20
material_refs:
  - name: api review checklist
    path: docs/materials/api-review-checklist.md
    purpose: Checklist material the agent can use during evaluation.
```

Existing examples:

- [config/agents/planner_v1.yaml](../../config/agents/planner_v1.yaml)
- [config/agents/implementer_v1.yaml](../../config/agents/implementer_v1.yaml)
- [config/agents/critic_v1.yaml](../../config/agents/critic_v1.yaml)

## Step 2: teach the controller when to use it

The current routing policy is explicit and lives in:

- [src/taskmind/controller.py](../../src/taskmind/controller.py)

If you add a new role, update route selection so tasks can actually choose it.

## Step 2.5: attach material, not just instructions

The contract should describe:

- what the agent is for
- when it should or should not be used
- what it expects in
- what it must return

Detailed domain knowledge should usually live in referenced material, not in a giant persona prompt.

That keeps the role stable while letting the knowledge evolve.

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
