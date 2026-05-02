from __future__ import annotations

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine


def ensure_runtime_schema(engine: Engine) -> None:
    inspector = inspect(engine)
    statements: list[str] = []

    if "tasks" in inspector.get_table_names():
        task_columns = {column["name"] for column in inspector.get_columns("tasks")}
        if "parent_task_id" not in task_columns:
            statements.append("ALTER TABLE tasks ADD COLUMN parent_task_id VARCHAR(36)")
        if "orchestration_kind" not in task_columns:
            statements.append("ALTER TABLE tasks ADD COLUMN orchestration_kind VARCHAR(20) NOT NULL DEFAULT 'primary'")
        if "orchestration_depth" not in task_columns:
            statements.append("ALTER TABLE tasks ADD COLUMN orchestration_depth INTEGER NOT NULL DEFAULT 0")
        if "orchestration_metadata" not in task_columns:
            statements.append("ALTER TABLE tasks ADD COLUMN orchestration_metadata JSON")

    if "adaptation_proposals" in inspector.get_table_names():
        columns = {column["name"] for column in inspector.get_columns("adaptation_proposals")}
        if "review_notes" not in columns:
            statements.append("ALTER TABLE adaptation_proposals ADD COLUMN review_notes TEXT")
        if "decided_at" not in columns:
            statements.append("ALTER TABLE adaptation_proposals ADD COLUMN decided_at TIMESTAMP WITH TIME ZONE")

    if statements:
        with engine.begin() as connection:
            for statement in statements:
                connection.execute(text(statement))
