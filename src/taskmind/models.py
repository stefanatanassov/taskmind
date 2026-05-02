from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from taskmind.db import Base


def _uuid() -> str:
    return str(uuid4())


def _utcnow() -> datetime:
    return datetime.now(UTC)


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    task_type: Mapped[str] = mapped_column(String(50), nullable=False)
    risk_level: Mapped[str] = mapped_column(String(20), nullable=False, default="medium")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="queued")
    acceptance_criteria: Mapped[list[str]] = mapped_column(JSON, default=list)
    required_artifacts: Mapped[list[str]] = mapped_column(JSON, default=list)
    route: Mapped[list[str]] = mapped_column(JSON, default=list)
    assigned_agents: Mapped[list[str]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    runs: Mapped[list["Run"]] = relationship(back_populates="task")
    feedback_events: Mapped[list["FeedbackEvent"]] = relationship(back_populates="task")
    review_checkpoints: Mapped[list["ReviewCheckpoint"]] = relationship(back_populates="task")


class Run(Base):
    __tablename__ = "runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    task_id: Mapped[str] = mapped_column(String(36), ForeignKey("tasks.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="running")
    route: Mapped[list[str]] = mapped_column(JSON, default=list)
    artifacts: Mapped[dict] = mapped_column(JSON, default=dict)
    evaluation: Mapped[dict] = mapped_column(JSON, default=dict)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    task: Mapped[Task] = relationship(back_populates="runs")
    feedback_events: Mapped[list["FeedbackEvent"]] = relationship(back_populates="run")
    review_checkpoints: Mapped[list["ReviewCheckpoint"]] = relationship(back_populates="run")


class FeedbackEvent(Base):
    __tablename__ = "feedback_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    task_id: Mapped[str] = mapped_column(String(36), ForeignKey("tasks.id"), nullable=False)
    run_id: Mapped[str] = mapped_column(String(36), ForeignKey("runs.id"), nullable=False)
    agent_id: Mapped[str] = mapped_column(String(100), nullable=False)
    agent_role: Mapped[str] = mapped_column(String(50), nullable=False)
    task_status: Mapped[str] = mapped_column(String(20), nullable=False)
    accepted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    usefulness_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    requirements_covered: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    criteria_total: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    route_length: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    reference_material_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    task: Mapped[Task] = relationship(back_populates="feedback_events")
    run: Mapped[Run] = relationship(back_populates="feedback_events")


class AgentUsefulness(Base):
    __tablename__ = "agent_usefulness"

    agent_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    agent_role: Mapped[str] = mapped_column(String(50), nullable=False)
    total_runs: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    accepted_runs: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    average_usefulness: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    last_usefulness: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    last_updated: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


class AdaptationProposal(Base):
    __tablename__ = "adaptation_proposals"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    proposal_type: Mapped[str] = mapped_column(String(50), nullable=False)
    target_kind: Mapped[str] = mapped_column(String(50), nullable=False)
    target_id: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="open")
    priority: Mapped[str] = mapped_column(String(20), nullable=False, default="medium")
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    evidence: Mapped[dict] = mapped_column(JSON, default=dict)
    recommendation: Mapped[dict] = mapped_column(JSON, default=dict)
    review_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    dedupe_key: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


class ReviewCheckpoint(Base):
    __tablename__ = "review_checkpoints"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    task_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("tasks.id"), nullable=True)
    run_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("runs.id"), nullable=True)
    checkpoint_type: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    task: Mapped[Task | None] = relationship(back_populates="review_checkpoints")
    run: Mapped[Run | None] = relationship(back_populates="review_checkpoints")
