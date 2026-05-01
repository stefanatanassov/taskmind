from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass
class ReferenceMaterial:
    name: str
    purpose: str
    content: str


@dataclass
class ModelRequest:
    role: str
    task_title: str
    task_description: str
    acceptance_criteria: list[str]
    agent_purpose: str
    expected_outputs: list[str]
    reference_materials: list[ReferenceMaterial]
    context: dict


@dataclass
class ModelResponse:
    content: str
    metadata: dict


class LLMProvider(Protocol):
    async def generate(self, request: ModelRequest) -> ModelResponse:
        ...
