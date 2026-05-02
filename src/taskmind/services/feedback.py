from __future__ import annotations

from statistics import mean

from sqlalchemy import select
from sqlalchemy.orm import Session

from taskmind.agents.schemas import AgentRuntimeProfile
from taskmind.models import AgentUsefulness, FeedbackEvent, Run, Task


def _clamp_score(value: float) -> float:
    return max(-1.0, min(1.0, value))


def _observed_simpler_route_baseline(session: Session, task: Task, route_length: int) -> dict | None:
    runs = list(
        session.scalars(
            select(Run)
            .join(Task)
            .where(Task.task_type == task.task_type, Task.risk_level == task.risk_level, Run.task_id != task.id)
        )
    )
    grouped: dict[str, list[Run]] = {}
    for candidate in runs:
        candidate_route_length = len(candidate.route or [])
        if candidate_route_length >= route_length or candidate_route_length == 0:
            continue
        grouped.setdefault(" -> ".join(candidate.route), []).append(candidate)

    if not grouped:
        return None

    route_key, route_runs = sorted(grouped.items(), key=lambda item: (len(item[0].split(" -> ")), item[0]))[0]
    success_rate = mean(1.0 if run.status == "completed" else 0.0 for run in route_runs)
    coverage = mean(float(run.evaluation.get("requirements_covered", 0.0)) for run in route_runs)
    return {"route": route_key, "success_rate": success_rate, "coverage": coverage}


def _usefulness_score(session: Session, task: Task, role: str, evaluation: dict) -> tuple[float, str]:
    coverage = float(evaluation.get("requirements_covered", 0.0))
    accepted = bool(evaluation.get("accepted", False))
    criteria_total = int(evaluation.get("criteria_total", len(task.acceptance_criteria or [])))
    route_length = len(task.route or [])
    failure_reason = evaluation.get("failure_reason")
    baseline = _observed_simpler_route_baseline(session, task, route_length)

    score = (0.45 * coverage) + (0.25 if accepted else -0.35)
    note = "Route outcome baseline."

    if failure_reason == "execution_error":
        score -= 0.15
        note = "Execution failure penalized."

    if role == "implementer":
        score += 0.12
        note = "Primary output role."
    elif role == "critic":
        score += 0.08 if route_length > 1 else -0.15
        note = "Review role in multi-step route." if route_length > 1 else "Review role used on direct route."
    elif role == "planner":
        if route_length >= 3 and criteria_total >= 3:
            score += 0.12
            note = "Planner used on higher-ambiguity task."
        else:
            score -= 0.20
            note = "Planner may have added avoidable overhead."

    if role != "implementer" and route_length > 1:
        score -= 0.06 * (route_length - 1)

    if baseline is not None:
        delta_success = (1.0 if accepted else 0.0) - baseline["success_rate"]
        delta_coverage = coverage - baseline["coverage"]
        route_delta = (0.25 * delta_success) + (0.20 * delta_coverage)
        if role == "implementer":
            score += route_delta * 0.6
        else:
            score += route_delta
        if delta_success <= 0 and delta_coverage <= 0 and role in {"planner", "critic"}:
            score -= 0.10
        note = f"{note} Compared against simpler route '{baseline['route']}'."

    return _clamp_score(score), note


def record_feedback_events(
    session: Session,
    task: Task,
    run: Run,
    runtime_profiles: dict[str, AgentRuntimeProfile],
    evaluation: dict,
) -> list[FeedbackEvent]:
    events: list[FeedbackEvent] = []
    criteria_total = int(evaluation.get("criteria_total", len(task.acceptance_criteria or [])))

    for role in task.route:
        profile = runtime_profiles[role]
        usefulness_score, note = _usefulness_score(session, task, role, evaluation)
        event = FeedbackEvent(
            task_id=task.id,
            run_id=run.id,
            agent_id=profile.id,
            agent_role=profile.role,
            task_status=run.status,
            accepted=bool(evaluation.get("accepted", False)),
            usefulness_score=usefulness_score,
            requirements_covered=float(evaluation.get("requirements_covered", 0.0)),
            criteria_total=criteria_total,
            route_length=len(task.route or []),
            reference_material_count=len(profile.reference_materials),
            notes=note,
        )
        session.add(event)
        events.append(event)
        _update_agent_usefulness(session, event)

    return events


def _update_agent_usefulness(session: Session, event: FeedbackEvent) -> None:
    aggregate = session.get(AgentUsefulness, event.agent_id)
    if aggregate is None:
        aggregate = AgentUsefulness(
            agent_id=event.agent_id,
            agent_role=event.agent_role,
            total_runs=0,
            accepted_runs=0,
            average_usefulness=0.0,
            last_usefulness=0.0,
        )
        session.add(aggregate)

    previous_total = aggregate.total_runs
    aggregate.total_runs += 1
    if event.accepted:
        aggregate.accepted_runs += 1
    aggregate.last_usefulness = event.usefulness_score
    aggregate.average_usefulness = (
        ((aggregate.average_usefulness * previous_total) + event.usefulness_score) / aggregate.total_runs
    )
