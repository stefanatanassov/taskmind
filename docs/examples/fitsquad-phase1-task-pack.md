# FitSquad Phase 1 Task Pack

This task pack translates the FitSquad brief into bounded `taskmind` tasks that match the current system well.

Important:

- the current live stack is running with `TASKMIND_PROVIDER=mock`
- these tasks are useful once the provider is switched to a real local or remote model
- do not submit the entire FitSquad project as one task
- keep the work phased and aligned to the original Phase 1 scope

## Recommended order

1. `01-phase1-blueprint.json`
2. `02-data-model-and-api.json`
3. `03-reservation-payment-flow.json`
4. `04-admin-mvp-ops.json`

## Why this split works

- Task 1 produces the product and delivery frame.
- Task 2 defines the persistence and API contract.
- Task 3 locks the critical booking and payment behavior.
- Task 4 keeps internal operations minimal and aligned to Phase 1.

## How to use

Switch to a real provider first, then submit one task at a time:

```bash
curl -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d @examples/tasks/fitsquad-phase1/01-phase1-blueprint.json
```

Inspect results:

```bash
curl http://localhost:8000/tasks
curl http://localhost:8000/runs
curl http://localhost:8000/feedback
curl http://localhost:8000/adaptation/proposals
curl http://localhost:8000/review-checkpoints
```

## What not to do

- do not ask for contracts, invoices, CRM, or advanced financial tracking in Phase 1
- do not mix architecture, UX, backend, and reporting into one task
- do not treat unresolved business questions as a reason to expand scope

## Expected route behavior

With the current controller:

- tasks with 3 or more acceptance criteria route to `planner -> implementer -> critic`
- simple Phase 1 refinement tasks may route to `implementer -> critic`
- high-risk tasks always route through the full chain and create review checkpoints
