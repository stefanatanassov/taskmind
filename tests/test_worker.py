from __future__ import annotations

import asyncio
from dataclasses import dataclass

from taskmind.db import SessionLocal
from taskmind.models import Run
from taskmind.providers.base import ModelResponse
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
        assert "Materials:" in run.artifacts["implementer"]


@dataclass
class CapturedRequest:
    role: str
    agent_purpose: str
    expected_outputs: list[str]
    reference_material_names: list[str]
    reference_material_contents: list[str]


class CapturingProvider:
    def __init__(self) -> None:
        self.requests: list[CapturedRequest] = []

    async def generate(self, request):
        self.requests.append(
            CapturedRequest(
                role=request.role,
                agent_purpose=request.agent_purpose,
                expected_outputs=request.expected_outputs,
                reference_material_names=[material.name for material in request.reference_materials],
                reference_material_contents=[material.content for material in request.reference_materials],
            )
        )
        return ModelResponse(content=f"{request.role} ok", metadata={})


def test_worker_injects_agent_purpose_and_reference_materials(monkeypatch):
    provider = CapturingProvider()
    monkeypatch.setattr("taskmind.worker.main.get_provider", lambda: provider)

    with SessionLocal() as session:
        create_task(
            session,
            TaskCreate(
                title="Grounded task",
                description="Verify references are injected.",
                task_type="feature",
                risk_level="medium",
                acceptance_criteria=["use reference materials", "produce grounded output"],
            ),
        )

    processed = asyncio.run(process_next_task())
    assert processed is True

    assert [request.role for request in provider.requests] == ["planner", "implementer", "critic"]

    planner_request = provider.requests[0]
    assert "decomposition" in planner_request.agent_purpose.lower() or "decompose" in planner_request.agent_purpose.lower()
    assert planner_request.reference_material_names == ["planning principles"]
    assert any("Prefer the smallest plan" in content for content in planner_request.reference_material_contents)

    critic_request = provider.requests[-1]
    assert critic_request.reference_material_names == ["critique rubric"]
    assert any("Check each acceptance criterion directly" in content for content in critic_request.reference_material_contents)
