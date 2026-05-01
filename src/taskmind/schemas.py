from datetime import datetime

from pydantic import BaseModel, Field


class TaskCreate(BaseModel):
    title: str
    description: str
    task_type: str = "analysis"
    risk_level: str = "medium"
    acceptance_criteria: list[str] = Field(default_factory=list)
    required_artifacts: list[str] = Field(default_factory=list)


class TaskRead(BaseModel):
    id: str
    title: str
    description: str
    task_type: str
    risk_level: str
    status: str
    acceptance_criteria: list[str]
    required_artifacts: list[str]
    route: list[str]
    assigned_agents: list[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class RunRead(BaseModel):
    id: str
    task_id: str
    status: str
    route: list[str]
    artifacts: dict
    evaluation: dict
    error: str | None
    started_at: datetime
    completed_at: datetime | None

    model_config = {"from_attributes": True}

