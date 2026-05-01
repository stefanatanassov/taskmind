from __future__ import annotations

from collections import Counter

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from taskmind.models import AgentUsefulness, FeedbackEvent, Run, Task


def build_summary(session: Session) -> dict:
    tasks = list(session.scalars(select(Task)))
    runs = list(session.scalars(select(Run)))
    feedback_events = list(session.scalars(select(FeedbackEvent)))

    total_tasks = len(tasks)
    total_runs = len(runs)
    completed_runs = [run for run in runs if run.status == "completed"]
    failed_runs = [run for run in runs if run.status == "failed"]
    average_coverage = (
        sum(float(run.evaluation.get("requirements_covered", 0.0)) for run in runs) / total_runs if total_runs else 0.0
    )
    route_distribution = Counter(" -> ".join(run.route) for run in runs if run.route)

    return {
        "total_tasks": total_tasks,
        "total_runs": total_runs,
        "completed_runs": len(completed_runs),
        "failed_runs": len(failed_runs),
        "run_success_rate": (len(completed_runs) / total_runs) if total_runs else 0.0,
        "average_requirements_covered": average_coverage,
        "feedback_events": len(feedback_events),
        "top_routes": [{"route": route, "count": count} for route, count in route_distribution.most_common(5)],
    }


def list_agent_usefulness(session: Session) -> list[AgentUsefulness]:
    return list(session.scalars(select(AgentUsefulness).order_by(AgentUsefulness.average_usefulness.desc())))


def build_route_analytics(session: Session) -> list[dict]:
    runs = list(session.scalars(select(Run)))
    grouped: dict[str, dict] = {}
    for run in runs:
        route_key = " -> ".join(run.route) if run.route else "unrouted"
        bucket = grouped.setdefault(route_key, {"route": route_key, "runs": 0, "completed": 0, "average_coverage": 0.0})
        bucket["runs"] += 1
        if run.status == "completed":
            bucket["completed"] += 1
        bucket["average_coverage"] += float(run.evaluation.get("requirements_covered", 0.0))

    results: list[dict] = []
    for bucket in grouped.values():
        average_coverage = bucket["average_coverage"] / bucket["runs"] if bucket["runs"] else 0.0
        results.append(
            {
                "route": bucket["route"],
                "runs": bucket["runs"],
                "completed": bucket["completed"],
                "success_rate": (bucket["completed"] / bucket["runs"]) if bucket["runs"] else 0.0,
                "average_requirements_covered": average_coverage,
            }
        )
    return sorted(results, key=lambda item: item["runs"], reverse=True)


def list_recent_feedback(session: Session, limit: int = 20) -> list[FeedbackEvent]:
    return list(session.scalars(select(FeedbackEvent).order_by(FeedbackEvent.created_at.desc()).limit(limit)))
