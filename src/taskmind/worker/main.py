from __future__ import annotations

import argparse
import asyncio
from datetime import UTC, datetime

from sqlalchemy import select, text

from taskmind.agents.registry import AgentRegistry
from taskmind.config import get_settings
from taskmind.db import Base, SessionLocal, engine
from taskmind.evaluation import evaluate_run
from taskmind.models import Run, Task
from taskmind.providers.base import ModelRequest
from taskmind.providers.router import get_provider
from taskmind.services.feedback import record_feedback_events


def utcnow() -> datetime:
    return datetime.now(UTC)


async def process_next_task(provider=None, registry=None) -> bool:
    provider = provider or get_provider()
    registry = registry or AgentRegistry()
    with SessionLocal() as session:
        task = session.scalars(select(Task).where(Task.status == "queued").order_by(Task.created_at.asc())).first()
        if not task:
            return False

        task.status = "running"
        run = Run(task_id=task.id, route=task.route, status="running", artifacts={}, evaluation={})
        session.add(run)
        session.commit()
        session.refresh(run)

        artifacts: dict[str, str] = {}
        try:
            for role in task.route:
                runtime_profile = registry.get_runtime_profile_for_role(role)
                if runtime_profile is None:
                    raise ValueError(f"No active agent runtime profile found for role '{role}'")
                response = await provider.generate(
                    ModelRequest(
                        role=role,
                        task_title=task.title,
                        task_description=task.description,
                        acceptance_criteria=task.acceptance_criteria,
                        agent_purpose=runtime_profile.purpose,
                        expected_outputs=runtime_profile.expected_outputs,
                        reference_materials=runtime_profile.reference_materials,
                        context={"task_id": task.id, "prior_artifacts": artifacts},
                    )
                )
                artifacts[role] = response.content

            evaluation = evaluate_run(task, artifacts)
            run.artifacts = artifacts
            run.evaluation = evaluation
            run.status = "completed" if evaluation["accepted"] else "failed"
            run.completed_at = utcnow()
            task.status = "completed" if evaluation["accepted"] else "failed"
        except Exception as exc:  # pragma: no cover
            evaluation = {
                "accepted": False,
                "requirements_covered": 0.0,
                "criteria_total": len(task.acceptance_criteria or []),
                "criteria_hits": 0,
                "matched_criteria": [],
                "missing_criteria": task.acceptance_criteria or [],
                "artifact_roles_present": sorted(artifacts.keys()),
                "route_length": len(task.route or []),
                "review_recommended": True,
                "agent_was_necessary": len(task.route or []) > 1,
                "notes": str(exc),
            }
            run.artifacts = artifacts
            run.evaluation = evaluation
            run.error = str(exc)
            run.status = "failed"
            run.completed_at = utcnow()
            task.status = "failed"

        runtime_profiles = {
            role: registry.get_runtime_profile_for_role(role)
            for role in task.route
            if registry.get_runtime_profile_for_role(role) is not None
        }
        if runtime_profiles:
            record_feedback_events(session, task, run, runtime_profiles, run.evaluation)

        session.add(task)
        session.add(run)
        session.commit()
        return True


def healthcheck() -> int:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as session:
        session.execute(text("SELECT 1"))
    return 0


async def run_forever() -> None:
    settings = get_settings()
    Base.metadata.create_all(bind=engine)
    provider = get_provider()
    registry = AgentRegistry()
    while True:
        processed = await process_next_task(provider=provider, registry=registry)
        await asyncio.sleep(settings.worker_poll_interval if not processed else 1)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--healthcheck", action="store_true")
    args = parser.parse_args()
    if args.healthcheck:
        return healthcheck()
    asyncio.run(run_forever())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
