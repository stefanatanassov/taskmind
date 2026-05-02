# Roadmap

This roadmap reflects the actual current state of `taskmind`, not just the original plan.

## Current position

`taskmind` has completed its first credible MVP phase:

- task-driven API
- worker-based execution loop
- Postgres-backed persistence
- provider abstraction
- Docker quickstart
- grounded agent execution through reference materials
- onboarding docs and guide-agent example
- local tests and CI smoke validation

The next priority is guided adaptation on top of the completed feedback layer:

- can the system show which routes add value?
- can it show which agents are worth keeping?
- can it explain failures clearly enough to improve routing and agents over time?

## v0.1 Complete

- task-driven API
- worker-based execution loop
- built-in planner, implementer, critic roles
- compact runtime routing
- Postgres persistence for tasks and runs
- provider abstraction for `mock`, `ollama`, and OpenAI-compatible APIs
- Docker Compose deployment
- one-command quickstart flows
- runtime grounding with agent purpose and reference materials
- onboarding FAQ and contributor docs
- pytest coverage for core behavior
- GitHub Actions smoke validation

## v0.2 Complete: Feedback and usefulness

Goal: make the system measurably self-informing.

Completed in this slice:

- explicit feedback records beyond embedded run evaluation
- agent usefulness aggregates and score history through feedback events
- route analytics
- richer evaluation rubric fields
- stronger usefulness heuristics with simpler-route comparison
- clearer failed-run inspection views and error summaries
- richer dashboard filtering and drill-down support
- a lightweight dashboard for tasks, runs, feedback, and agent performance

Success criteria:

- you can see which routes are being used
- you can see which agents contribute to successful outcomes
- you can see repeated failure patterns
- you can compare simple routes against multi-agent routes

## v0.3 In Progress: Guided adaptation

Goal: recommend improvements without handing control to autonomous self-rewrite.

Completed in this slice:

- adaptation proposal storage and API
- route-change proposals from historical outcomes
- low-value agent review proposals
- material review proposals from repeated criteria misses
- explicit human review checkpoints for high-risk or review-recommended runs
- checkpoint decision endpoint for approve/reject/pending flow

Still remaining in v0.3:

- richer proposal types for prompt and material tuning
- proposal acceptance workflow with audit notes
- review checkpoints attached to more policy classes
- dashboard controls for checkpoint decisions and proposal lifecycle

Success criteria:

- the system can recommend how to improve itself
- changes remain reviewable and auditable
- humans stay in control of structural changes

## v0.4 Later: Benchmarking and expansion

Goal: make performance more portable and comparable across environments.

- add provider benchmark packs
- add optional local model bundles
- add benchmark task suites
- add queue backend abstraction if scaling pressure justifies it
- add optional review and policy packs

Success criteria:

- users can compare providers and routes on repeatable tasks
- contributors can validate changes against shared benchmark scenarios

## Non-goals for now

- autonomous orchestration self-rewrite
- distributed multi-node agent mesh
- large plugin ecosystem
- too many agent roles without evidence
- infrastructure expansion before feedback analytics exist

## Immediate next build slice

The next concrete iteration should implement:

1. provider and route benchmark task packs
2. richer proposal rules for prompt and material tuning
3. proposal acceptance workflow and audit notes
4. checkpoint controls in the dashboard
5. docs for reading analytics and acting on feedback

That is the shortest path from “visible learning MVP” to “guided adaptive system”.
