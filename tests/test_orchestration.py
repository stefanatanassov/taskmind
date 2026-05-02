from __future__ import annotations

import asyncio

from taskmind.db import SessionLocal
from taskmind.models import Run, Task
from taskmind.providers.base import ModelResponse
from taskmind.schemas import TaskCreate
from taskmind.services.tasks import create_task
from taskmind.worker.main import process_next_task


class CohesiveProvider:
    async def generate(self, request):
        body = (
            f"For the task {request.task_title}, this slice covers {', '.join(request.acceptance_criteria)}. "
            "The response gives concrete deliverables, explains implementation intent, names the key entities, "
            "and keeps the wording direct so the result can be synthesized into a stronger final artifact. "
            "It includes enough detail to satisfy the criterion without repeating raw prompt labels or boilerplate."
        )
        return ModelResponse(content=body, metadata={"provider": "cohesive"})


def test_small_local_model_triggers_dynamic_decomposition(monkeypatch):
    monkeypatch.setattr("taskmind.orchestration.infer_model_tier", lambda: "small_local")

    with SessionLocal() as session:
        parent = create_task(
            session,
            TaskCreate(
                title="FitSquad blueprint",
                description="Create a phase 1 product blueprint.",
                task_type="feature",
                risk_level="medium",
                acceptance_criteria=[
                    "public package presentation is defined",
                    "reservation flow is described",
                    "deposit and full payment paths are described",
                ],
                required_artifacts=["plan", "implementation", "critique"],
            ),
        )

    assert asyncio.run(process_next_task(provider=CohesiveProvider())) is True

    with SessionLocal() as session:
        refreshed_parent = session.get(Task, parent.id)
        assert refreshed_parent is not None
        assert refreshed_parent.status == "waiting_on_subtasks"

        children = (
            session.query(Task)
            .filter(Task.parent_task_id == parent.id, Task.orchestration_kind == "delegated")
            .order_by(Task.created_at.asc())
            .all()
        )
        assert len(children) == 3
        assert all(child.route == ["implementer", "critic"] for child in children)


def test_dynamic_decomposition_finishes_parent_via_synthesis(monkeypatch):
    monkeypatch.setattr("taskmind.orchestration.infer_model_tier", lambda: "small_local")

    with SessionLocal() as session:
        parent = create_task(
            session,
            TaskCreate(
                title="FitSquad blueprint synthesis",
                description="Build a bounded blueprint with synthesis.",
                task_type="feature",
                risk_level="medium",
                acceptance_criteria=[
                    "public package presentation is defined",
                    "reservation flow is described",
                    "deposit and full payment paths are described",
                ],
            ),
        )

    provider = CohesiveProvider()
    for _ in range(10):
        processed = asyncio.run(process_next_task(provider=provider))
        if not processed:
            break

    with SessionLocal() as session:
        refreshed_parent = session.get(Task, parent.id)
        assert refreshed_parent is not None
        assert refreshed_parent.status == "completed"
        assert refreshed_parent.orchestration_metadata["finalized_by_synthesis"]

        synthesis = (
            session.query(Task)
            .filter(Task.parent_task_id == parent.id, Task.orchestration_kind == "synthesis")
            .one()
        )
        assert synthesis.status == "completed"

        synthesis_run = (
            session.query(Run)
            .filter(Run.task_id == synthesis.id)
            .order_by(Run.started_at.desc())
            .first()
        )
        assert synthesis_run is not None
        assert synthesis_run.status == "completed"
