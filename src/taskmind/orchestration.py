from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from taskmind.config import get_settings
from taskmind.controller import select_route
from taskmind.models import Run, Task


TERMINAL_TASK_STATUSES = {"completed", "failed"}
PROMPT_ECHO_REASONS = {"prompt_echo", "low_signal_output"}


@dataclass(frozen=True)
class OrchestrationDirective:
    action: str
    task_id: str


def infer_model_tier() -> str:
    settings = get_settings()
    model_name = (settings.model or "").lower()
    provider = settings.provider.lower()
    if provider == "mock":
        return "synthetic"
    if provider == "openai_compatible" and any(token in model_name for token in ("llama-2-7b", "7b", "8b")):
        return "small_local"
    if provider == "ollama" and any(token in model_name for token in ("7b", "8b")):
        return "small_local"
    if provider in {"ollama", "openai_compatible"}:
        return "local_or_self_hosted"
    return "remote"


def should_decompose_task(task: Task) -> bool:
    if task.orchestration_kind != "primary" or task.parent_task_id is not None:
        return False
    if infer_model_tier() != "small_local":
        return False
    criteria = task.acceptance_criteria or []
    if len(criteria) < 3:
        return False
    if task.risk_level == "low" and task.task_type == "analysis":
        return False
    return True


def _build_delegated_subtasks(session: Session, task: Task) -> list[Task]:
    created: list[Task] = []
    criteria = task.acceptance_criteria or []
    for index, criterion in enumerate(criteria, start=1):
        child = Task(
            parent_task_id=task.id,
            title=f"{task.title} :: slice {index}",
            description=(
                f"Parent task: {task.title}\n"
                f"Parent description:\n{task.description}\n\n"
                f"Focus only on this acceptance slice:\n- {criterion}\n\n"
                "Produce a concrete contribution for this slice only. "
                "Do not restate the whole task or rewrite the prompt."
            ),
            task_type=task.task_type,
            risk_level="low" if task.risk_level == "low" else "medium",
            status="queued",
            orchestration_kind="delegated",
            orchestration_depth=task.orchestration_depth + 1,
            orchestration_metadata={
                "parent_id": task.id,
                "criterion_index": index - 1,
                "criterion": criterion,
                "source_route": task.route,
            },
            acceptance_criteria=[criterion],
            required_artifacts=["implementation"],
            route=["implementer", "critic"],
            assigned_agents=["implementer", "critic"],
        )
        session.add(child)
        created.append(child)
    task.status = "waiting_on_subtasks"
    task.orchestration_metadata = {
        **(task.orchestration_metadata or {}),
        "delegated_children_created": len(created),
        "delegated_due_to_model_tier": infer_model_tier(),
    }
    return created


def _has_synthesis_child(session: Session, task: Task) -> bool:
    statement = select(Task.id).where(
        Task.parent_task_id == task.id,
        Task.orchestration_kind == "synthesis",
    )
    return session.execute(statement).first() is not None


def _create_synthesis_task(session: Session, task: Task, children: list[Task]) -> Task:
    synthesis_notes: list[str] = []
    for child in children:
        latest_run = session.scalars(
            select(Run).where(Run.task_id == child.id).order_by(Run.started_at.desc())
        ).first()
        child_output = ""
        if latest_run is not None:
            child_output = latest_run.artifacts.get("implementer", "")
        synthesis_notes.append(
            f"Child slice: {child.acceptance_criteria[0] if child.acceptance_criteria else child.title}\n"
            f"Output:\n{child_output.strip() or '[no output]'}"
        )

    child_summary = "\n\n".join(synthesis_notes)
    synthesis = Task(
        parent_task_id=task.id,
        title=f"{task.title} :: synthesis",
        description=(
            f"Parent task: {task.title}\n"
            f"Parent description:\n{task.description}\n\n"
            "Below are delegated slice outputs. Synthesize them into one coherent final answer that "
            "covers the original acceptance criteria without repeating prompt labels.\n\n"
            f"{child_summary}"
        ),
        task_type=task.task_type,
        risk_level=task.risk_level,
        status="queued",
        orchestration_kind="synthesis",
        orchestration_depth=task.orchestration_depth + 1,
        orchestration_metadata={
            "parent_id": task.id,
            "child_task_ids": [child.id for child in children],
        },
        acceptance_criteria=list(task.acceptance_criteria or []),
        required_artifacts=list(task.required_artifacts or ["implementation", "critique"]),
        route=["implementer", "critic"],
        assigned_agents=["implementer", "critic"],
    )
    session.add(synthesis)
    task.status = "synthesizing"
    task.orchestration_metadata = {
        **(task.orchestration_metadata or {}),
        "synthesis_task_title": synthesis.title,
    }
    return synthesis


def _finalize_parent_from_synthesis(session: Session, task: Task, synthesis: Task) -> None:
    latest_run = session.scalars(
        select(Run).where(Run.task_id == synthesis.id).order_by(Run.started_at.desc())
    ).first()
    task.status = synthesis.status
    task.route = synthesis.route
    task.assigned_agents = synthesis.assigned_agents
    task.orchestration_metadata = {
        **(task.orchestration_metadata or {}),
        "finalized_by_synthesis": synthesis.id,
        "final_run_id": latest_run.id if latest_run is not None else None,
        "final_evaluation": latest_run.evaluation if latest_run is not None else None,
    }


def advance_orchestration(session: Session) -> OrchestrationDirective | None:
    synthesizing_parent = session.scalars(
        select(Task)
        .where(Task.status == "synthesizing", Task.orchestration_kind == "primary")
        .order_by(Task.created_at.asc())
    ).first()
    if synthesizing_parent is not None:
        synthesis_child = session.scalars(
            select(Task)
            .where(
                Task.parent_task_id == synthesizing_parent.id,
                Task.orchestration_kind == "synthesis",
                Task.status.in_(TERMINAL_TASK_STATUSES),
            )
            .order_by(Task.created_at.desc())
        ).first()
        if synthesis_child is not None:
            _finalize_parent_from_synthesis(session, synthesizing_parent, synthesis_child)
            session.add(synthesizing_parent)
            session.commit()
            return OrchestrationDirective(action="finalized_parent", task_id=synthesizing_parent.id)

    waiting_parent = session.scalars(
        select(Task)
        .where(Task.status == "waiting_on_subtasks", Task.orchestration_kind == "primary")
        .order_by(Task.created_at.asc())
    ).first()
    if waiting_parent is not None:
        children = list(
            session.scalars(
                select(Task).where(Task.parent_task_id == waiting_parent.id, Task.orchestration_kind == "delegated")
            )
        )
        if children and all(child.status in TERMINAL_TASK_STATUSES for child in children):
            if any(child.status == "failed" for child in children):
                waiting_parent.status = "failed"
                waiting_parent.orchestration_metadata = {
                    **(waiting_parent.orchestration_metadata or {}),
                    "child_failure_ids": [child.id for child in children if child.status == "failed"],
                }
                session.add(waiting_parent)
                session.commit()
                return OrchestrationDirective(action="failed_parent", task_id=waiting_parent.id)
            if not _has_synthesis_child(session, waiting_parent):
                synthesis = _create_synthesis_task(session, waiting_parent, children)
                session.commit()
                return OrchestrationDirective(action="spawned_synthesis", task_id=synthesis.id)

    queued_primary = session.scalars(
        select(Task)
        .where(Task.status == "queued", Task.orchestration_kind == "primary")
        .order_by(Task.created_at.asc())
    ).first()
    queued_non_primary_exists = session.execute(
        select(Task.id).where(Task.status == "queued", Task.orchestration_kind != "primary")
    ).first()
    if queued_primary is not None and should_decompose_task(queued_primary) and queued_non_primary_exists is None:
        _build_delegated_subtasks(session, queued_primary)
        session.add(queued_primary)
        session.commit()
        return OrchestrationDirective(action="spawned_subtasks", task_id=queued_primary.id)

    return None


def pick_next_executable_task(session: Session) -> Task | None:
    queued = session.scalars(
        select(Task)
        .where(Task.status == "queued")
        .order_by(Task.created_at.asc())
    )
    for task in queued:
        if task.orchestration_kind == "primary" and should_decompose_task(task):
            continue
        return task
    return None


def derive_route_for_task(task: Task) -> list[str]:
    if task.orchestration_kind in {"delegated", "synthesis"}:
        return ["implementer", "critic"]
    return select_route(task)
