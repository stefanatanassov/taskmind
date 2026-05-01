from __future__ import annotations

from taskmind.providers.base import ModelRequest, ModelResponse


class MockProvider:
    async def generate(self, request: ModelRequest) -> ModelResponse:
        criteria = ", ".join(request.acceptance_criteria) if request.acceptance_criteria else "no explicit criteria"
        content = f"{request.role} handled '{request.task_title}' with focus on {criteria}."
        return ModelResponse(content=content, metadata={"provider": "mock"})

