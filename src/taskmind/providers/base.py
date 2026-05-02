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
                f"{material.name} ({material.purpose})\n{material.content}"
            )
            for material in request.reference_materials
        )

    criteria = "\n".join(f"- {criterion}" for criterion in request.acceptance_criteria) or "- No explicit criteria"
    expected_outputs = "\n".join(f"- {item}" for item in request.expected_outputs) or "- Provide the requested artifact"

    return (
        f"You are the {request.role} for this task.\n\n"
        f"Goal:\n{request.agent_purpose}\n\n"
        f"Return a work product that satisfies these expected outputs:\n{expected_outputs}\n\n"
        f"Task title:\n{request.task_title}\n\n"
        f"Task description:\n{request.task_description}\n\n"
        f"Acceptance criteria:\n{criteria}\n\n"
        f"Reference materials:\n{references}\n\n"
        f"Execution context:\n{request.context}\n\n"
        "Instructions:\n"
        "- Return only substantive work product.\n"
        "- Do not repeat or restate the headings above.\n"
        "- Do not echo the prompt structure.\n"
        "- Keep the answer concrete, concise, and directly tied to the task."
    )


class LLMProvider(Protocol):
    async def generate(self, request: ModelRequest) -> ModelResponse:
        ...
