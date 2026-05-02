from __future__ import annotations

import asyncio
from pathlib import Path

import yaml

from taskmind.db import SessionLocal
from taskmind.models import ReviewCheckpoint, Task
from taskmind.schemas import TaskCreate
from taskmind.services.tasks import create_task
from taskmind.supervisor import apply_supervisor_response, export_supervisor_state
from taskmind.worker.main import process_next_task


def test_supervisor_export_writes_state_files(tmp_path: Path):
    with SessionLocal() as session:
        task = create_task(
            session,
            TaskCreate(
                title="Supervisor export task",
                description="Create a state snapshot for supervision.",
                task_type="feature",
                risk_level="high",
                acceptance_criteria=["one", "two", "three"],
            ),
        )

    asyncio.run(process_next_task())

    payload = export_supervisor_state(task_id=task.id, base_dir=str(tmp_path))

    assert payload["task_id"] == task.id
    assert payload["summary"]["pending_checkpoints"] == 1
    assert any(item["action_type"] == "decide_checkpoint" for item in payload["recommended_actions"])

    request_path = tmp_path / "inbox" / "supervisor-request.yaml"
    task_path = tmp_path / "state" / "current-task.yaml"
    run_path = tmp_path / "state" / "current-run.yaml"
    history_path = tmp_path / "history" / "events.jsonl"

    assert request_path.exists()
    assert task_path.exists()
    assert run_path.exists()
    assert history_path.exists()

    task_doc = yaml.safe_load(task_path.read_text(encoding="utf-8"))
    run_doc = yaml.safe_load(run_path.read_text(encoding="utf-8"))
    assert task_doc["id"] == task.id
    assert run_doc["task_id"] == task.id


def test_supervisor_apply_response_updates_checkpoint_and_creates_task(tmp_path: Path):
    with SessionLocal() as session:
        task = create_task(
            session,
            TaskCreate(
                title="Supervisor apply task",
                description="Needs approval and follow-up work.",
                task_type="feature",
                risk_level="high",
                acceptance_criteria=["one", "two", "three"],
            ),
        )

    asyncio.run(process_next_task())
    export_supervisor_state(task_id=task.id, base_dir=str(tmp_path))

    with SessionLocal() as session:
        checkpoint = session.query(ReviewCheckpoint).filter(ReviewCheckpoint.task_id == task.id).one()

    response_path = tmp_path / "outbox" / "supervisor-response.yaml"
    response_path.write_text(
        yaml.safe_dump(
            {
                "task_id": task.id,
                "decision": "approve_and_queue_next_slice",
                "reasoning": ["High-risk output has been reviewed.", "Queue the next bounded task."],
                "actions": [
                    {
                        "action_type": "decide_checkpoint",
                        "checkpoint_id": checkpoint.id,
                        "status": "approved",
                    },
                    {
                        "action_type": "create_task",
                        "task": {
                            "title": "Follow-up slice",
                            "description": "Queue the next bounded task.",
                            "task_type": "analysis",
                            "risk_level": "low",
                            "acceptance_criteria": ["next step is visible"],
                            "required_artifacts": ["implementation"],
                        },
                    },
                ],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    result = apply_supervisor_response(base_dir=str(tmp_path))
    assert result["status"] == "applied"
    assert len(result["results"]) == 2
    assert not response_path.exists()
    assert (tmp_path / "state" / "last-response-result.yaml").exists()

    with SessionLocal() as session:
        refreshed_checkpoint = session.get(ReviewCheckpoint, checkpoint.id)
        assert refreshed_checkpoint is not None
        assert refreshed_checkpoint.status == "approved"
        follow_up_task = session.query(Task).filter(Task.title == "Follow-up slice").one()
        assert follow_up_task.status == "queued"
