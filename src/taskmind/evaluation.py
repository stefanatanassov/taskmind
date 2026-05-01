from __future__ import annotations

from taskmind.models import Task


def evaluate_run(task: Task, artifacts: dict) -> dict:
    implemented = artifacts.get("implementer", "")
    criteria = task.acceptance_criteria or []
    matched_criteria = [criterion for criterion in criteria if criterion.lower() in implemented.lower()]
    missing_criteria = [criterion for criterion in criteria if criterion.lower() not in implemented.lower()]
    criteria_hits = len(matched_criteria)
    coverage = criteria_hits / len(criteria) if criteria else 1.0
    accepted = coverage >= 0.5
    return {
        "accepted": accepted,
        "requirements_covered": coverage,
        "criteria_total": len(criteria),
        "criteria_hits": criteria_hits,
        "matched_criteria": matched_criteria,
        "missing_criteria": missing_criteria,
        "artifact_roles_present": sorted(artifacts.keys()),
        "route_length": len(task.route or []),
        "review_recommended": (task.risk_level == "high") or not accepted,
        "agent_was_necessary": len(task.route or []) > 1,
        "notes": artifacts.get("critic", ""),
    }
