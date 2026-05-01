# Contributing

## Ground rules

- keep the system task-driven
- prefer explicit interfaces over implicit behavior
- avoid adding agent roles unless they prove unique value
- include tests for behavior changes
- document operational changes in `README.md` or `docs/`

## Local development

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
pytest
```

## Stack validation

```bash
cp .env.example .env
docker compose up --build -d
./scripts/verify_stack.sh
docker compose down -v
```

## Good first contributions

- add provider adapters
- improve route selection heuristics
- improve evaluation scoring
- add agent usefulness history
- improve the UI
- improve CI and smoke tests

