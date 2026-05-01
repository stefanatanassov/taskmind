# Contributor Guide

## First contribution paths

- add a provider adapter
- improve routing policy
- improve evaluation scoring
- add UI or API endpoints
- improve Docker or CI verification

## Local setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
pytest
```

## Stack verification

```bash
cp .env.example .env
docker compose up --build -d
./scripts/verify_stack.sh
```

## Contribution expectations

- preserve task-driven architecture
- keep interfaces explicit
- add tests for controller, execution, or API changes
- prefer configuration over hidden behavior

