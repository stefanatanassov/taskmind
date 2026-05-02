from __future__ import annotations

import asyncio

from taskmind.models import AgentUsefulness
from taskmind.providers.base import ModelResponse
from taskmind.db import SessionLocal
from taskmind.schemas import TaskCreate
from taskmind.services.tasks import create_task
from taskmind.worker.main import process_next_task


def test_healthz(client):
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_readyz(client):
    response = client.get("/readyz")
    assert response.status_code == 200
    assert response.json() == {"status": "ready", "database": "ok"}


def test_create_task(client):
    payload = {
        "title": "Test task",
        "description": "Create a first task.",
        "task_type": "feature",
        "risk_level": "medium",
        "acceptance_criteria": ["do one", "do two"],
    }
    response = client.post("/tasks", json=payload)
    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "Test task"
    assert body["route"] == ["implementer", "critic"]


def test_dashboard_page(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "taskmind" in response.text
    assert "Agent usefulness" in response.text
    assert "Failed runs" in response.text
    assert "Adaptation proposals" in response.text
    assert "Review checkpoints" in response.text


def test_analytics_endpoints(client):
    with SessionLocal() as session:
        create_task(
            session,
            TaskCreate(
                title="Analytics task",
                description="Populate analytics.",
                task_type="feature",
                risk_level="medium",
                acceptance_criteria=["one", "two", "three"],
            ),
        )
    asyncio.run(process_next_task())

    summary = client.get("/analytics/summary")
    assert summary.status_code == 200
    assert summary.json()["total_runs"] == 1
    assert summary.json()["feedback_events"] == 3

    agents = client.get("/analytics/agents")
    assert agents.status_code == 200
    assert len(agents.json()) == 3

    routes = client.get("/analytics/routes")
    assert routes.status_code == 200
    assert routes.json()[0]["route"] == "planner -> implementer -> critic"
    assert "comparison_baseline_route" in routes.json()[0]

    feedback = client.get("/feedback")
    assert feedback.status_code == 200
    assert len(feedback.json()) == 3

    filtered_feedback = client.get("/feedback", params={"agent_role": "critic"})
    assert filtered_feedback.status_code == 200
    assert len(filtered_feedback.json()) == 1

    runs = client.get("/runs", params={"status": "completed"})
    assert runs.status_code == 200
    assert len(runs.json()) == 1


def test_failure_analytics_endpoint(client):
    class SparseProvider:
        async def generate(self, request):
            return ModelResponse(content=f"{request.role} fallback output", metadata={})

    payload = {
        "title": "Failure task",
        "description": "Miss acceptance criteria on purpose.",
        "task_type": "analysis",
        "risk_level": "low",
        "acceptance_criteria": ["missing one", "missing two"],
    }
    response = client.post("/tasks", json=payload)
    assert response.status_code == 201
    assert response.json()["route"] == ["implementer", "critic"]
    asyncio.run(process_next_task(provider=SparseProvider()))

    failures = client.get("/analytics/failures")
    assert failures.status_code == 200
    body = failures.json()
    assert len(body) == 1
    assert body[0]["failure_reason"] == "acceptance_criteria_missing"
    assert body[0]["missing_criteria_count"] == 2

    runs = client.get("/runs", params={"status": "failed", "route": "implementer -> critic"})
    assert runs.status_code == 200
    assert len(runs.json()) == 1


def test_adaptation_and_review_endpoints(client):
    with SessionLocal() as session:
        session.add(
            AgentUsefulness(
                agent_id="critic_v1",
                agent_role="critic",
                total_runs=3,
                accepted_runs=1,
                average_usefulness=0.1,
                last_usefulness=-0.1,
            )
        )
        session.commit()

    proposals = client.post("/adaptation/proposals/refresh")
    assert proposals.status_code == 200
    body = proposals.json()
    assert any(item["proposal_type"] == "agent_deactivation" for item in body)

    with SessionLocal() as session:
        create_task(
            session,
            TaskCreate(
                title="High risk task",
                description="Needs human validation.",
                task_type="feature",
                risk_level="high",
                acceptance_criteria=["one", "two", "three"],
            ),
        )
    asyncio.run(process_next_task())

    checkpoints = client.get("/review-checkpoints")
    assert checkpoints.status_code == 200
    checkpoint_body = checkpoints.json()
    assert len(checkpoint_body) == 1
    assert checkpoint_body[0]["checkpoint_type"] == "high_risk_validation"
    assert checkpoint_body[0]["status"] == "pending"

    decision = client.post(f"/review-checkpoints/{checkpoint_body[0]['id']}", json={"status": "approved"})
    assert decision.status_code == 200
    assert decision.json()["status"] == "approved"
