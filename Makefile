.PHONY: install test run-api run-worker verify quickstart-mock quickstart-ollama quickstart-openai-compatible demo-task

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

quickstart-mock:
	./scripts/quickstart.sh mock

quickstart-ollama:
	./scripts/quickstart.sh ollama

quickstart-openai-compatible:
	./scripts/quickstart.sh openai-compatible

demo-task:
	./scripts/demo_task.sh
