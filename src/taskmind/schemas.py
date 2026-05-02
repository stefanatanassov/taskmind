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
    parent_task_id: str | None
    title: str
    description: str
    task_type: str
    risk_level: str
    status: str
    orchestration_kind: str
    orchestration_depth: int
    orchestration_metadata: dict | None
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


class FeedbackEventRead(BaseModel):
    id: str
    task_id: str
    run_id: str
    agent_id: str
    agent_role: str
    task_status: str
    accepted: bool
    usefulness_score: float
    requirements_covered: float
    criteria_total: int
    route_length: int
    reference_material_count: int
    notes: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class AgentUsefulnessRead(BaseModel):
    agent_id: str
    agent_role: str
    total_runs: int
    accepted_runs: int
    average_usefulness: float
    last_usefulness: float
    last_updated: datetime

    model_config = {"from_attributes": True}


class AdaptationProposalRead(BaseModel):
    id: str
    proposal_type: str
    target_kind: str
    target_id: str
    status: str
    priority: str
    title: str
    rationale: str
    evidence: dict
    recommendation: dict
    review_notes: str | None
    decided_at: datetime | None
    dedupe_key: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AdaptationProposalDecision(BaseModel):
    status: str
    review_notes: str | None = None


class ReviewCheckpointRead(BaseModel):
    id: str
    task_id: str | None
    run_id: str | None
    checkpoint_type: str
    status: str
    rationale: str
    payload: dict
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ReviewCheckpointDecision(BaseModel):
    status: str


class SupervisorTaskPayload(BaseModel):
    title: str
    description: str
    task_type: str = "analysis"
    risk_level: str = "medium"
    acceptance_criteria: list[str] = Field(default_factory=list)
    required_artifacts: list[str] = Field(default_factory=list)


class SupervisorAction(BaseModel):
    action_type: str
    task_id: str | None = None
    route_override: list[str] | None = None
    proposal_id: str | None = None
    checkpoint_id: str | None = None
    status: str | None = None
    review_notes: str | None = None
    task: SupervisorTaskPayload | None = None
    reason: str | None = None


class SupervisorResponse(BaseModel):
    task_id: str | None = None
    decision: str | None = None
    reasoning: list[str] = Field(default_factory=list)
    actions: list[SupervisorAction] = Field(default_factory=list)
    status: str = "ready_for_execution"
