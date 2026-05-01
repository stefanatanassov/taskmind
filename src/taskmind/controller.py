from __future__ import annotations

from taskmind.models import Task


def select_route(task: Task) -> list[str]:
    criteria_count = len(task.acceptance_criteria or [])
    route = ["implementer", "critic"]
    if criteria_count >= 2 or task.task_type in {"feature", "refactor"}:
        route = ["planner", "implementer", "critic"]
    if task.risk_level == "high" and "critic" not in route:
        route.append("critic")
    return route

