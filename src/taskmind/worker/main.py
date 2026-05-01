from __future__ import annotations

import argparse
import asyncio
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import select, text

from taskmind.agents.registry import AgentRegistry
from taskmind.config import get_settings
from taskmind.db import Base, SessionLocal, engine
from taskmind.evaluation import evaluate_run
from taskmind.models import Run, Task
from taskmind.providers.base import ModelRequest, ReferenceMaterial
from taskmind.providers.router import get_provider


def utcnow() -> datetime:
    return datetime.now(UTC)


def load_reference_materials(contract) -> list[ReferenceMaterial]:
    materials: list[ReferenceMaterial] = []
    for material_ref in contract.material_refs:
        path = Path(material_ref.path)
        with path.open("r", encoding="utf-8") as handle:
            materials.append(
                ReferenceMaterial(
                    name=material_ref.name,
                    purpose=material_ref.purpose,
                    content=handle.read(),
                )
            )
    return materials


async def process_next_task() -> bool:
    provider = get_provider()
    registry = AgentRegistry()
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
                contract = registry.get_agent_for_role(role)
                if contract is None:
                    raise ValueError(f"No active agent contract found for role '{role}'")
                response = await provider.generate(
                    ModelRequest(
                        role=role,
                        task_title=task.title,
                        task_description=task.description,
                        acceptance_criteria=task.acceptance_criteria,
                        agent_purpose=contract.purpose,
                        expected_outputs=contract.expected_outputs,
                        reference_materials=load_reference_materials(contract),
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
            run.error = str(exc)
            run.status = "failed"
            run.completed_at = utcnow()
            task.status = "failed"

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
    while True:
        processed = await process_next_task()
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
