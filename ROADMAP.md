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

The next priority is not more infrastructure. It is learning and observability:

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

## v0.2 Next: Feedback and usefulness

Goal: make the system measurably self-informing.

- add explicit feedback records beyond embedded run evaluation
- add agent usefulness score history
- add route analytics
- add richer evaluation rubric fields
- add failed-run inspection and error summaries
- add a lightweight dashboard for tasks, runs, and agent performance

Success criteria:

- you can see which routes are being used
- you can see which agents contribute to successful outcomes
- you can see repeated failure patterns
- you can compare simple routes against multi-agent routes

## v0.3 After that: Guided adaptation

Goal: recommend improvements without handing control to autonomous self-rewrite.

- add adaptation proposals
- suggest route changes based on historical outcomes
- suggest prompt or material improvements
- suggest agent deactivation for consistently low-value roles
- add explicit human review checkpoints for adaptation decisions

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

1. feedback table or model
2. usefulness scoring per agent
3. run analytics endpoint
4. minimal dashboard page
5. documented rubric expansion

That is the shortest path from “working orchestration MVP” to “adaptive system with visible value”.
