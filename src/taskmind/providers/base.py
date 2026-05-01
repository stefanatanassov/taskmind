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


def build_execution_prompt(request: ModelRequest) -> str:
    references = "No reference materials."
    if request.reference_materials:
        references = "\n\n".join(
            (
                f"Reference name: {material.name}\n"
                f"Reference purpose: {material.purpose}\n"
                f"Reference content:\n{material.content}"
            )
            for material in request.reference_materials
        )

    return (
        f"Role: {request.role}\n"
        f"Purpose: {request.agent_purpose}\n"
        f"Expected outputs: {request.expected_outputs}\n"
        f"Task: {request.task_title}\n"
        f"Description: {request.task_description}\n"
        f"Acceptance criteria: {request.acceptance_criteria}\n"
        f"Reference materials:\n{references}\n"
        f"Context: {request.context}"
    )


class LLMProvider(Protocol):
    async def generate(self, request: ModelRequest) -> ModelResponse:
        ...
