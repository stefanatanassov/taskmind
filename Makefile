.PHONY: install test run-api run-worker verify

install:
	python3 -m venv .venv
	. .venv/bin/activate && pip install -e .[dev]

test:
	pytest

run-api:
	uvicorn taskmind.api.main:app --host 0.0.0.0 --port 8000

run-worker:
	python -m taskmind.worker.main

verify:
	./scripts/verify_stack.sh

