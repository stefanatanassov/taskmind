from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml
from sqlalchemy import select
from sqlalchemy.orm import Session

from taskmind.config import get_settings
from taskmind.db import Base, SessionLocal, engine
from taskmind.models import ReviewCheckpoint, Run, Task
from taskmind.schema import ensure_runtime_schema
from taskmind.schemas import (
    AdaptationProposalRead,
    FeedbackEventRead,
    ReviewCheckpointRead,
    RunRead,
    SupervisorResponse,
    TaskCreate,
    TaskRead,
)
from taskmind.services.adaptation import (
    list_adaptation_proposals,
    update_adaptation_proposal,
    update_review_checkpoint,
)
from taskmind.services.analytics import list_recent_feedback
from taskmind.services.tasks import create_task


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _serialize(model: Any) -> Any:
    if model is None:
        return None
    if isinstance(model, list):
        return [_serialize(item) for item in model]
    if hasattr(model, "model_dump"):
        return model.model_dump(mode="json")
    return model


def _paths(base_dir: Path) -> dict[str, Path]:
    state_dir = base_dir / "state"
    inbox_dir = base_dir / "inbox"
    outbox_dir = base_dir / "outbox"
    history_dir = base_dir / "history"
    return {
        "base": base_dir,
        "state": state_dir,
        "inbox": inbox_dir,
        "outbox": outbox_dir,
        "history": history_dir,
        "task": state_dir / "current-task.yaml",
        "run": state_dir / "current-run.yaml",
        "feedback": state_dir / "feedback.yaml",
        "proposals": state_dir / "proposals.yaml",
        "checkpoints": state_dir / "checkpoints.yaml",
        "request": inbox_dir / "supervisor-request.yaml",
        "response": outbox_dir / "supervisor-response.yaml",
        "result": state_dir / "last-response-result.yaml",
        "history_file": history_dir / "events.jsonl",
    }


def _ensure_dirs(paths: dict[str, Path]) -> None:
    for key in ("state", "inbox", "outbox", "history"):
        paths[key].mkdir(parents=True, exist_ok=True)


def _write_yaml(path: Path, payload: Any) -> None:
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=False), encoding="utf-8")


def _append_history(paths: dict[str, Path], event_type: str, payload: dict[str, Any]) -> None:
    event = {"timestamp": _utcnow().isoformat(), "event_type": event_type, "payload": payload}
    with paths["history_file"].open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=True) + "\n")


def _select_task(session: Session, task_id: str | None) -> Task | None:
    if task_id:
        return session.get(Task, task_id)
    return session.scalars(select(Task).order_by(Task.updated_at.desc())).first()


def _select_run(session: Session, task: Task | None) -> Run | None:
    if task is None:
        return None
    return session.scalars(select(Run).where(Run.task_id == task.id).order_by(Run.started_at.desc())).first()


def _recommended_actions(task: Task | None, run: Run | None, checkpoints: list[ReviewCheckpointRead], proposals: list[AdaptationProposalRead]) -> list[dict[str, Any]]:
    if task is None:
        return [{"action_type": "create_task", "why": "No task is available yet in the current workspace state."}]

    actions: list[dict[str, Any]] = []
    if task.status == "queued":
        actions.append({"action_type": "wait_for_worker", "task_id": task.id, "why": "Task is queued and awaiting execution."})
    if run and run.status == "failed":
        actions.append(
            {
                "action_type": "requeue_task",
                "task_id": task.id,
                "why": "Last run failed. Supervisor can retry with the same or an overridden route.",
            }
        )
    if any(checkpoint.status == "pending" for checkpoint in checkpoints):
        actions.append({"action_type": "decide_checkpoint", "task_id": task.id, "why": "Pending review checkpoints block final acceptance."})
    if any(proposal.status == "open" for proposal in proposals):
        actions.append({"action_type": "decide_proposal", "task_id": task.id, "why": "Open adaptation proposals need explicit supervision."})
    if task.status in {"completed", "failed"}:
        actions.append({"action_type": "create_task", "why": "Supervisor can queue the next task slice when ready."})
    return actions


def export_supervisor_state(task_id: str | None = None, base_dir: str | None = None) -> dict[str, Any]:
    settings = get_settings()
    root = Path(base_dir or settings.supervisor_dir)
    paths = _paths(root)
    _ensure_dirs(paths)

    with SessionLocal() as session:
        task = _select_task(session, task_id)
        run = _select_run(session, task)
        feedback = (
            list_recent_feedback(session, limit=50, task_status=task.status if task else None)
            if task is not None
            else []
        )
        if run is not None:
            feedback = [item for item in feedback if item.run_id == run.id]
        proposals = [AdaptationProposalRead.model_validate(item) for item in list_adaptation_proposals(session)]
        checkpoints: list[ReviewCheckpointRead] = []
        if task is not None:
            checkpoints = [
                ReviewCheckpointRead.model_validate(item)
                for item in list(
                    session.scalars(
                        select(ReviewCheckpoint)
                        .where(ReviewCheckpoint.task_id == task.id)
                        .order_by(ReviewCheckpoint.created_at.desc())
                    )
                )
            ]

        task_payload = TaskRead.model_validate(task) if task is not None else None
        run_payload = RunRead.model_validate(run) if run is not None else None
        feedback_payload = [FeedbackEventRead.model_validate(item) for item in feedback]

        request_payload = {
            "exported_at": _utcnow().isoformat(),
            "task_id": task.id if task is not None else None,
            "task_status": task.status if task is not None else "no_task",
            "summary": {
                "title": task.title if task is not None else None,
                "route": run.route if run is not None else (task.route if task is not None else []),
                "run_status": run.status if run is not None else None,
                "requirements_covered": run.evaluation.get("requirements_covered") if run is not None else None,
                "failure_reason": run.evaluation.get("failure_reason") if run is not None else None,
                "pending_checkpoints": len([item for item in checkpoints if item.status == "pending"]),
                "open_proposals": len([item for item in proposals if item.status == "open"]),
            },
            "recommended_actions": _recommended_actions(task, run, checkpoints, proposals),
            "state_files": {
                "task": str(paths["task"]),
                "run": str(paths["run"]),
                "feedback": str(paths["feedback"]),
                "proposals": str(paths["proposals"]),
                "checkpoints": str(paths["checkpoints"]),
                "response": str(paths["response"]),
            },
        }

        _write_yaml(paths["task"], _serialize(task_payload))
        _write_yaml(paths["run"], _serialize(run_payload))
        _write_yaml(paths["feedback"], _serialize(feedback_payload))
        _write_yaml(paths["proposals"], _serialize(proposals))
        _write_yaml(paths["checkpoints"], _serialize(checkpoints))
        _write_yaml(paths["request"], request_payload)
        _append_history(paths, "state_exported", request_payload)
        return request_payload


def apply_supervisor_response(base_dir: str | None = None) -> dict[str, Any]:
    settings = get_settings()
    root = Path(base_dir or settings.supervisor_dir)
    paths = _paths(root)
    _ensure_dirs(paths)
    if not paths["response"].exists():
        raise FileNotFoundError(f"No supervisor response file found at {paths['response']}")

    payload = yaml.safe_load(paths["response"].read_text(encoding="utf-8")) or {}
    response = SupervisorResponse.model_validate(payload)
    results: list[dict[str, Any]] = []

    with SessionLocal() as session:
        for action in response.actions:
            if action.action_type == "create_task":
                if action.task is None:
                    raise ValueError("create_task action requires a task payload")
                created = create_task(session, TaskCreate(**action.task.model_dump()))
                results.append({"action_type": "create_task", "task_id": created.id, "status": "applied"})
                continue

            if action.action_type == "requeue_task":
                if action.task_id is None:
                    raise ValueError("requeue_task action requires task_id")
                task = session.get(Task, action.task_id)
                if task is None:
                    raise ValueError(f"Task '{action.task_id}' was not found")
                task.status = "queued"
                if action.route_override:
                    task.route = action.route_override
                    task.assigned_agents = action.route_override
                session.add(task)
                session.commit()
                results.append(
                    {
                        "action_type": "requeue_task",
                        "task_id": task.id,
                        "route": task.route,
                        "status": "applied",
                    }
                )
                continue

            if action.action_type == "decide_proposal":
                if action.proposal_id is None or action.status is None:
                    raise ValueError("decide_proposal action requires proposal_id and status")
                proposal = update_adaptation_proposal(
                    session,
                    action.proposal_id,
                    status=action.status,
                    review_notes=action.review_notes,
                )
                if proposal is None:
                    raise ValueError(f"Proposal '{action.proposal_id}' was not found")
                results.append({"action_type": "decide_proposal", "proposal_id": proposal.id, "status": proposal.status})
                continue

            if action.action_type == "decide_checkpoint":
                if action.checkpoint_id is None or action.status is None:
                    raise ValueError("decide_checkpoint action requires checkpoint_id and status")
                checkpoint = update_review_checkpoint(session, action.checkpoint_id, action.status)
                if checkpoint is None:
                    raise ValueError(f"Checkpoint '{action.checkpoint_id}' was not found")
                results.append(
                    {"action_type": "decide_checkpoint", "checkpoint_id": checkpoint.id, "status": checkpoint.status}
                )
                continue

            raise ValueError(f"Unsupported supervisor action '{action.action_type}'")

    result_payload = {
        "applied_at": _utcnow().isoformat(),
        "decision": response.decision,
        "status": "applied",
        "results": results,
    }
    _write_yaml(paths["result"], result_payload)
    _append_history(paths, "response_applied", result_payload)
    paths["response"].unlink(missing_ok=True)
    return result_payload


def cycle(task_id: str | None = None, base_dir: str | None = None) -> dict[str, Any]:
    exported = export_supervisor_state(task_id=task_id, base_dir=base_dir)
    paths = _paths(Path(base_dir or get_settings().supervisor_dir))
    if paths["response"].exists():
        applied = apply_supervisor_response(base_dir=base_dir)
        return {"exported": exported, "applied": applied}
    return {"exported": exported, "applied": None}


def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    export_parser = subparsers.add_parser("export-state")
    export_parser.add_argument("--task-id")
    export_parser.add_argument("--base-dir")

    apply_parser = subparsers.add_parser("apply-response")
    apply_parser.add_argument("--base-dir")

    cycle_parser = subparsers.add_parser("cycle")
    cycle_parser.add_argument("--task-id")
    cycle_parser.add_argument("--base-dir")

    args = parser.parse_args()
    Base.metadata.create_all(bind=engine)
    ensure_runtime_schema(engine)

    if args.command == "export-state":
        print(yaml.safe_dump(export_supervisor_state(task_id=args.task_id, base_dir=args.base_dir), sort_keys=False))
        return 0
    if args.command == "apply-response":
        print(yaml.safe_dump(apply_supervisor_response(base_dir=args.base_dir), sort_keys=False))
        return 0

    print(yaml.safe_dump(cycle(task_id=args.task_id, base_dir=args.base_dir), sort_keys=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
