# System Overview

`taskmind` is a modular monolith built around a task queue and isolated runs.

## Runtime components

- API: accepts tasks and exposes system state
- Worker: polls queued tasks and executes routes
- Postgres: source of truth for tasks, runs, and feedback
- Redis: reserved for coordination and future queue/event use

## Flow

1. A task is created through the API.
2. The controller selects a route.
3. The worker claims the task and executes planner, implementer, and critic steps.
4. Evaluation records a structured result.
5. Feedback persists whether the route added value.

## Design constraints

- task-driven, not prompt-driven
- isolated execution runs
- explicit evaluation
- local-first provider abstraction
- modular code boundaries for future extraction

