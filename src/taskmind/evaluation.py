from __future__ import annotations

from taskmind.models import Task


def evaluate_run(task: Task, artifacts: dict) -> dict:
    implemented = artifacts.get("implementer", "")
    criteria = task.acceptance_criteria or []
    criteria_hits = sum(1 for criterion in criteria if criterion.lower() in implemented.lower())
    coverage = criteria_hits / len(criteria) if criteria else 1.0
    accepted = coverage >= 0.5
    return {
        "accepted": accepted,
        "requirements_covered": coverage,
        "agent_was_necessary": len(task.route or []) > 1,
        "notes": artifacts.get("critic", ""),
    }

