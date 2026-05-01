# taskmind

`taskmind` is a task-driven agent orchestration MVP. Tasks enter a queue, the controller selects an execution route, isolated runs produce outputs, evaluation scores the result, and feedback records whether each agent added value.

This first iteration is intentionally narrow:

- one API
- one worker
- one Postgres database
- one Redis instance
- three built-in agents: planner, implementer, critic
- one provider abstraction with `mock`, `ollama`, and OpenAI-compatible support

## Why this exists

Most agent systems are prompt-first. `taskmind` is work-first.

It answers three concrete questions:

1. Can this task be automated?
2. Did agents improve the result?
3. Which agents are worth keeping?

## MVP capabilities

- Create tasks over HTTP
- Persist tasks and runs in Postgres
- Poll queued tasks from a worker
- Route tasks through planner, implementer, and critic
- Score outputs with a simple evaluation loop
- Expose health and readiness endpoints
- Run locally in Docker Compose
- Support local or remote model providers through configuration

## One-command quickstart

Mock provider, no external credentials:

```bash
./scripts/quickstart.sh mock
```

Local Ollama:

```bash
./scripts/quickstart.sh ollama
```

Remote OpenAI-compatible provider:

```bash
TASKMIND_PROVIDER_BASE_URL=https://api.openai.com/v1 \
TASKMIND_PROVIDER_API_KEY=your_key \
TASKMIND_MODEL=gpt-4.1-mini \
./scripts/quickstart.sh openai-compatible
```

Submit a demo task after startup:

```bash
./scripts/demo_task.sh
```

Useful endpoints:

- [http://localhost:8000/healthz](http://localhost:8000/healthz)
- [http://localhost:8000/tasks](http://localhost:8000/tasks)
- [http://localhost:8000/runs](http://localhost:8000/runs)

## Quickstart

1. Copy the environment file:

```bash
cp .env.example .env
```

2. Start the stack:

```bash
docker compose up --build
```

3. Verify the stack:

```bash
./scripts/verify_stack.sh
```

4. Create a task:

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

5. Inspect tasks and runs:

```bash
curl http://localhost:8000/tasks
curl http://localhost:8000/runs
```

## Demo flows

### Demo 1: mock mode

```bash
./scripts/quickstart.sh mock
./scripts/demo_task.sh
```

### Demo 2: local Ollama

```bash
./scripts/quickstart.sh ollama
./scripts/demo_task.sh
```

### Demo 3: remote provider

```bash
TASKMIND_PROVIDER_BASE_URL=https://api.openai.com/v1 \
TASKMIND_PROVIDER_API_KEY=your_key \
TASKMIND_MODEL=gpt-4.1-mini \
./scripts/quickstart.sh openai-compatible
./scripts/demo_task.sh
```

## Model providers

The default provider is `mock` so the stack works without external credentials.

Supported provider modes in this version:

- `mock`
- `ollama`
- `openai_compatible`

Set them through `.env`:

```env
TASKMIND_PROVIDER=mock
TASKMIND_MODEL=gpt-oss
TASKMIND_PROVIDER_BASE_URL=http://ollama:11434
TASKMIND_PROVIDER_API_KEY=
```

For Ollama, set:

```env
TASKMIND_PROVIDER=ollama
TASKMIND_MODEL=qwen2.5-coder:14b
TASKMIND_PROVIDER_BASE_URL=http://ollama:11434
```

For OpenAI-compatible APIs, set:

```env
TASKMIND_PROVIDER=openai_compatible
TASKMIND_MODEL=gpt-4.1-mini
TASKMIND_PROVIDER_BASE_URL=https://api.openai.com/v1
TASKMIND_PROVIDER_API_KEY=your_key
```

## Docker modes

- `docker compose up --build`: API, worker, Postgres, Redis
- `docker compose -f docker-compose.yml -f docker-compose.ollama.yml up --build`: core stack plus Ollama

The quickstart script chooses the correct mode automatically.

## Core concepts

- `Task`: the unit of work and control plane object
- `Run`: one isolated execution instance for a task
- `Agent profile`: a versioned agent definition
- `Evaluation`: structured judgment of output quality and route value
- `Feedback event`: the evidence layer for adaptation

## Repository map

- [src/taskmind](/Users/stefanatanassov/Documents/New%20project/src/taskmind)
- [config/agents](/Users/stefanatanassov/Documents/New%20project/config/agents)
- [tests](/Users/stefanatanassov/Documents/New%20project/tests)
- [docs/architecture/system-overview.md](/Users/stefanatanassov/Documents/New%20project/docs/architecture/system-overview.md)
- [docs/contributors/getting-started.md](/Users/stefanatanassov/Documents/New%20project/docs/contributors/getting-started.md)

## Development

Local Python workflow:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
pytest
```

Shutdown:

```bash
docker compose down -v
docker compose -f docker-compose.yml -f docker-compose.ollama.yml down -v
```

## Next milestones

- add a web dashboard
- add richer evaluation rubrics
- add adaptation proposals and agent usefulness scoring history
- add benchmark tasks
- add GitHub workflows for CI and smoke verification
