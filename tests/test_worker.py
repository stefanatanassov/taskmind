from __future__ import annotations

import asyncio

from taskmind.db import SessionLocal
from taskmind.models import Run
from taskmind.schemas import TaskCreate
from taskmind.services.tasks import create_task
from taskmind.worker.main import process_next_task


def test_worker_processes_queued_task():
    with SessionLocal() as session:
        create_task(
            session,
            TaskCreate(
                title="Worker task",
                description="Test queue processing.",
                task_type="analysis",
                risk_level="low",
                acceptance_criteria=["queue processing"],
            ),
        )

    processed = asyncio.run(process_next_task())
    assert processed is True

    with SessionLocal() as session:
        run = session.query(Run).first()
        assert run is not None
        assert run.status in {"completed", "failed"}
        assert "implementer" in run.artifacts
