from __future__ import annotations

from sqlalchemy import create_engine, inspect, text

from taskmind.schema import ensure_runtime_schema


def test_runtime_schema_adds_missing_adaptation_columns(tmp_path):
    db_path = tmp_path / "schema.db"
    engine = create_engine(f"sqlite+pysqlite:///{db_path}", future=True)

    with engine.begin() as connection:
        connection.execute(
            text(
                """
                CREATE TABLE adaptation_proposals (
                    id VARCHAR(36) PRIMARY KEY,
                    proposal_type VARCHAR(50) NOT NULL,
                    target_kind VARCHAR(50) NOT NULL,
                    target_id VARCHAR(100) NOT NULL,
                    status VARCHAR(20) NOT NULL,
                    priority VARCHAR(20) NOT NULL,
                    title VARCHAR(255) NOT NULL,
                    rationale TEXT NOT NULL,
                    evidence JSON,
                    recommendation JSON,
                    dedupe_key VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP,
                    updated_at TIMESTAMP
                )
                """
            )
        )

    ensure_runtime_schema(engine)

    columns = {column["name"] for column in inspect(engine).get_columns("adaptation_proposals")}
    assert "review_notes" in columns
    assert "decided_at" in columns
