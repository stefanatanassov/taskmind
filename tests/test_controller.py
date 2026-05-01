from __future__ import annotations

from taskmind.controller import select_route
from taskmind.models import Task


def test_select_route_for_feature_task():
    task = Task(
        title="Feature",
        description="Build feature",
        task_type="feature",
        risk_level="medium",
        acceptance_criteria=["one", "two"],
    )
    assert select_route(task) == ["planner", "implementer", "critic"]


def test_select_route_for_simple_task():
    task = Task(
        title="Simple",
        description="Small task",
        task_type="analysis",
        risk_level="low",
        acceptance_criteria=["one"],
    )
    assert select_route(task) == ["implementer", "critic"]

