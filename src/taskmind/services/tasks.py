from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from taskmind.models import Task
from taskmind.orchestration import derive_route_for_task
from taskmind.schemas import TaskCreate


def create_task(session: Session, payload: TaskCreate) -> Task:
    task = Task(
        title=payload.title,
        description=payload.description,
        task_type=payload.task_type,
        risk_level=payload.risk_level,
        acceptance_criteria=payload.acceptance_criteria,
        required_artifacts=payload.required_artifacts,
    )
    task.route = derive_route_for_task(task)
    task.assigned_agents = task.route
    session.add(task)
    session.commit()
    session.refresh(task)
    return task


def list_tasks(session: Session) -> list[Task]:
    return list(session.scalars(select(Task).order_by(Task.created_at.desc())))


def get_task(session: Session, task_id: str) -> Task | None:
    return session.get(Task, task_id)
