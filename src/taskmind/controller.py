from __future__ import annotations

from taskmind.models import Task


def select_route(task: Task) -> list[str]:
    criteria_count = len(task.acceptance_criteria or [])
    if task.risk_level == "high":
        return ["planner", "implementer", "critic"]
    if criteria_count >= 3 or task.task_type == "refactor":
        return ["planner", "implementer", "critic"]
    if criteria_count <= 1 and task.risk_level == "low" and task.task_type == "analysis":
        return ["implementer"]
    return ["implementer", "critic"]
