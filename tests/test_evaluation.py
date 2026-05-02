from __future__ import annotations

from taskmind.evaluation import evaluate_run
from taskmind.models import Task


def test_evaluation_rejects_prompt_echo_output():
    task = Task(
        title="Echo task",
        description="Reject prompt echo.",
        task_type="feature",
        risk_level="medium",
        acceptance_criteria=[
            "public package presentation is defined",
            "reservation flow is described",
            "deposit and full payment paths are described",
        ],
        route=["implementer", "critic"],
    )

    result = evaluate_run(
        task,
        {
            "implementer": (
                "Role: implementer\nPurpose: do the task\nExpected outputs: implementation\n"
                "Acceptance criteria: public package presentation is defined, reservation flow is described, "
                "deposit and full payment paths are described\nReference materials: none\nContext: {}"
            )
        },
    )

    assert result["accepted"] is False
    assert result["failure_reason"] == "prompt_echo"
