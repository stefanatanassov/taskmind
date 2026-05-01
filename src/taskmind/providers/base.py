from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass
class ModelRequest:
    role: str
    task_title: str
    task_description: str
    acceptance_criteria: list[str]
    context: dict


@dataclass
class ModelResponse:
    content: str
    metadata: dict


class LLMProvider(Protocol):
    async def generate(self, request: ModelRequest) -> ModelResponse:
        ...

