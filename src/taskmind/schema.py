from __future__ import annotations

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine


def ensure_runtime_schema(engine: Engine) -> None:
    inspector = inspect(engine)

    if "adaptation_proposals" in inspector.get_table_names():
        columns = {column["name"] for column in inspector.get_columns("adaptation_proposals")}
        statements: list[str] = []
        if "review_notes" not in columns:
            statements.append("ALTER TABLE adaptation_proposals ADD COLUMN review_notes TEXT")
        if "decided_at" not in columns:
            statements.append("ALTER TABLE adaptation_proposals ADD COLUMN decided_at TIMESTAMP WITH TIME ZONE")

        if statements:
            with engine.begin() as connection:
                for statement in statements:
                    connection.execute(text(statement))
