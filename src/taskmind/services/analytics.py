from __future__ import annotations

from collections import Counter
from statistics import mean

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from taskmind.models import AgentUsefulness, FeedbackEvent, Run, Task


def _route_key(route: list[str] | None) -> str:
    return " -> ".join(route) if route else "unrouted"


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
    route_distribution = Counter(_route_key(run.route) for run in runs if run.route)
    most_recent_failure = max(failed_runs, key=lambda run: run.completed_at or run.started_at, default=None)

    return {
        "total_tasks": total_tasks,
        "total_runs": total_runs,
        "completed_runs": len(completed_runs),
        "failed_runs": len(failed_runs),
        "run_success_rate": (len(completed_runs) / total_runs) if total_runs else 0.0,
        "average_requirements_covered": average_coverage,
        "feedback_events": len(feedback_events),
        "top_routes": [{"route": route, "count": count} for route, count in route_distribution.most_common(5)],
        "most_recent_failure": (
            {
                "run_id": most_recent_failure.id,
                "route": _route_key(most_recent_failure.route),
                "failure_reason": most_recent_failure.evaluation.get("failure_reason") or "unknown",
            }
            if most_recent_failure
            else None
        ),
    }


def list_agent_usefulness(session: Session) -> list[AgentUsefulness]:
    return list(session.scalars(select(AgentUsefulness).order_by(AgentUsefulness.average_usefulness.desc())))


def build_route_analytics(session: Session) -> list[dict]:
    runs = list(session.scalars(select(Run)))
    grouped: dict[str, dict] = {}
    cohort_buckets: dict[tuple[str, str], dict[str, list[Run]]] = {}
    for run in runs:
        route_key = _route_key(run.route)
        task = run.task
        cohort = (task.task_type, task.risk_level) if task else ("unknown", "unknown")
        bucket = grouped.setdefault(
            route_key,
            {
                "route": route_key,
                "runs": 0,
                "completed": 0,
                "failed": 0,
                "average_coverage": 0.0,
                "route_length": len(run.route or []),
                "task_type_distribution": Counter(),
                "risk_distribution": Counter(),
                "cohort_examples": Counter(),
            },
        )
        bucket["runs"] += 1
        if run.status == "completed":
            bucket["completed"] += 1
        elif run.status == "failed":
            bucket["failed"] += 1
        bucket["average_coverage"] += float(run.evaluation.get("requirements_covered", 0.0))
        if task:
            bucket["task_type_distribution"][task.task_type] += 1
            bucket["risk_distribution"][task.risk_level] += 1
            bucket["cohort_examples"][f"{task.task_type}/{task.risk_level}"] += 1
            cohort_buckets.setdefault(cohort, {}).setdefault(route_key, []).append(run)

    results: list[dict] = []
    for bucket in grouped.values():
        average_coverage = bucket["average_coverage"] / bucket["runs"] if bucket["runs"] else 0.0
        dominant_task_type = bucket["task_type_distribution"].most_common(1)[0][0] if bucket["task_type_distribution"] else None
        dominant_risk = bucket["risk_distribution"].most_common(1)[0][0] if bucket["risk_distribution"] else None
        dominant_cohort = bucket["cohort_examples"].most_common(1)[0][0] if bucket["cohort_examples"] else None

        simpler_candidates: list[tuple[str, int, float, float]] = []
        for (task_type, risk_level), routes in cohort_buckets.items():
            if dominant_task_type and dominant_risk and (task_type, risk_level) != (dominant_task_type, dominant_risk):
                continue
            for candidate_route, route_runs in routes.items():
                route_length = len(candidate_route.split(" -> ")) if candidate_route != "unrouted" else 0
                if route_length >= bucket["route_length"]:
                    continue
                success_rate = mean(1.0 if candidate.status == "completed" else 0.0 for candidate in route_runs)
                coverage = mean(float(candidate.evaluation.get("requirements_covered", 0.0)) for candidate in route_runs)
                simpler_candidates.append((candidate_route, route_length, success_rate, coverage))

        simpler_route = None
        marginal_success = None
        marginal_coverage = None
        if simpler_candidates:
            simpler_route, _, baseline_success, baseline_coverage = sorted(
                simpler_candidates, key=lambda item: (item[1], item[0])
            )[0]
            success_rate = (bucket["completed"] / bucket["runs"]) if bucket["runs"] else 0.0
            marginal_success = success_rate - baseline_success
            marginal_coverage = average_coverage - baseline_coverage
        results.append(
            {
                "route": bucket["route"],
                "runs": bucket["runs"],
                "completed": bucket["completed"],
                "failed": bucket["failed"],
                "success_rate": (bucket["completed"] / bucket["runs"]) if bucket["runs"] else 0.0,
                "average_requirements_covered": average_coverage,
                "route_length": bucket["route_length"],
                "dominant_task_type": dominant_task_type,
                "dominant_risk_level": dominant_risk,
                "dominant_cohort": dominant_cohort,
                "comparison_baseline_route": simpler_route,
                "marginal_success_vs_simpler_route": marginal_success,
                "marginal_coverage_vs_simpler_route": marginal_coverage,
            }
        )
    return sorted(results, key=lambda item: item["runs"], reverse=True)


def build_failed_run_analytics(session: Session, limit: int = 20, route: str | None = None) -> list[dict]:
    runs = list(session.scalars(select(Run).where(Run.status == "failed").order_by(Run.started_at.desc())))
    results: list[dict] = []
    for run in runs:
        route_key = _route_key(run.route)
        if route and route_key != route:
            continue
        task = run.task
        results.append(
            {
                "run_id": run.id,
                "task_id": run.task_id,
                "task_title": task.title if task else None,
                "task_type": task.task_type if task else None,
                "risk_level": task.risk_level if task else None,
                "route": route_key,
                "failure_reason": run.evaluation.get("failure_reason") or "unknown",
                "missing_criteria_count": int(run.evaluation.get("missing_criteria_count", 0)),
                "missing_criteria": run.evaluation.get("missing_criteria", []),
                "error_summary": run.error or run.evaluation.get("notes"),
                "started_at": run.started_at,
                "completed_at": run.completed_at,
            }
        )
        if len(results) >= limit:
            break
    return results


def list_recent_feedback(
    session: Session,
    limit: int = 20,
    agent_role: str | None = None,
    task_status: str | None = None,
    accepted: bool | None = None,
) -> list[FeedbackEvent]:
    stmt = select(FeedbackEvent).order_by(FeedbackEvent.created_at.desc()).limit(limit)
    if agent_role:
        stmt = stmt.where(FeedbackEvent.agent_role == agent_role)
    if task_status:
        stmt = stmt.where(FeedbackEvent.task_status == task_status)
    if accepted is not None:
        stmt = stmt.where(FeedbackEvent.accepted == accepted)
    return list(session.scalars(stmt))
