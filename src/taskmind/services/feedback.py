from __future__ import annotations

from sqlalchemy.orm import Session

from taskmind.agents.schemas import AgentRuntimeProfile
from taskmind.models import AgentUsefulness, FeedbackEvent, Run, Task


def _clamp_score(value: float) -> float:
    return max(-1.0, min(1.0, value))


def _usefulness_score(task: Task, role: str, evaluation: dict) -> tuple[float, str]:
    coverage = float(evaluation.get("requirements_covered", 0.0))
    accepted = bool(evaluation.get("accepted", False))
    criteria_total = int(evaluation.get("criteria_total", len(task.acceptance_criteria or [])))
    route_length = len(task.route or [])

    score = (0.7 * coverage) + (0.3 if accepted else -0.3)
    note = "Route outcome baseline."

    if role == "implementer":
        score += 0.10
        note = "Primary output role."
    elif role == "critic":
        score += 0.05 if route_length > 1 else -0.10
        note = "Review role in multi-step route." if route_length > 1 else "Review role used on direct route."
    elif role == "planner":
        if route_length >= 3 and criteria_total >= 3:
            score += 0.10
            note = "Planner used on higher-ambiguity task."
        else:
            score -= 0.15
            note = "Planner may have added avoidable overhead."

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
        usefulness_score, note = _usefulness_score(task, role, evaluation)
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
