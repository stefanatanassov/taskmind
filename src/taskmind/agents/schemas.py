from __future__ import annotations

from pydantic import BaseModel, Field

from taskmind.providers.base import ReferenceMaterial


class MaterialReference(BaseModel):
    name: str
    path: str
    purpose: str


class ToolPolicy(BaseModel):
    allowed_tools: list[str] = Field(default_factory=list)
    notes: str | None = None


class BudgetPolicy(BaseModel):
    max_cost_usd: float | None = None
    max_latency_sec: int | None = None


class QualityBar(BaseModel):
    must_check: list[str] = Field(default_factory=list)
    notes: str | None = None


class RoutingHints(BaseModel):
    min_acceptance_criteria: int | None = None
    preferred_task_types: list[str] = Field(default_factory=list)
    avoid_risk_levels: list[str] = Field(default_factory=list)


class AgentContract(BaseModel):
    id: str
    name: str
    role: str
    status: str
    description: str
    purpose: str
    model_profile: str
    allowed_task_types: list[str] = Field(default_factory=list)
    when_to_use: list[str] = Field(default_factory=list)
    when_not_to_use: list[str] = Field(default_factory=list)
    expected_inputs: list[str] = Field(default_factory=list)
    expected_outputs: list[str] = Field(default_factory=list)
    routing_hints: RoutingHints = Field(default_factory=RoutingHints)
    tool_policy: ToolPolicy = Field(default_factory=ToolPolicy)
    budget_policy: BudgetPolicy = Field(default_factory=BudgetPolicy)
    quality_bar: QualityBar = Field(default_factory=QualityBar)
    failure_modes: list[str] = Field(default_factory=list)
    handoff_rules: list[str] = Field(default_factory=list)
    evaluation_metrics: list[str] = Field(default_factory=list)
    example_tasks: list[str] = Field(default_factory=list)
    material_refs: list[MaterialReference] = Field(default_factory=list)


class AgentRuntimeProfile(BaseModel):
    id: str
    role: str
    purpose: str
    expected_outputs: list[str] = Field(default_factory=list)
    reference_materials: list[ReferenceMaterial] = Field(default_factory=list)
