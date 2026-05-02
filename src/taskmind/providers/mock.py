from __future__ import annotations

from taskmind.providers.base import ModelRequest, ModelResponse


class MockProvider:
    async def generate(self, request: ModelRequest) -> ModelResponse:
        criteria = ", ".join(request.acceptance_criteria) if request.acceptance_criteria else "no explicit criteria"
        material_names = ", ".join(material.name for material in request.reference_materials) or "no materials"
        content = (
            f"{request.role} handled '{request.task_title}' with concrete coverage for {criteria}. "
            f"This response stays focused on execution detail, expected outcomes, and direct requirement coverage. "
            f"It explains the work in plain language, names the relevant package or task concepts, and avoids simply "
            f"repeating the request structure. Purpose: {request.agent_purpose}. Materials: {material_names}. "
            f"Each acceptance point is addressed with a useful implementation note so the evaluator can confirm "
            f"substantive completion rather than short filler text."
        )
        return ModelResponse(content=content, metadata={"provider": "mock"})
