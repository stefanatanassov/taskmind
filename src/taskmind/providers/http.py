from __future__ import annotations

import httpx

from taskmind.providers.base import ModelRequest, ModelResponse


def _format_reference_materials(request: ModelRequest) -> str:
    if not request.reference_materials:
        return "No reference materials."
    sections: list[str] = []
    for material in request.reference_materials:
        sections.append(
            f"Reference name: {material.name}\n"
            f"Reference purpose: {material.purpose}\n"
            f"Reference content:\n{material.content}"
        )
    return "\n\n".join(sections)


class OpenAICompatibleProvider:
    def __init__(self, base_url: str, model: str, api_key: str | None = None) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_key = api_key

    async def generate(self, request: ModelRequest) -> ModelResponse:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        f"You are the {request.role} agent.\n"
                        f"Purpose: {request.agent_purpose}\n"
                        f"Expected outputs: {request.expected_outputs}\n"
                        f"Use the provided reference materials when relevant."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Task: {request.task_title}\n"
                        f"Description: {request.task_description}\n"
                        f"Acceptance criteria: {request.acceptance_criteria}\n"
                        f"Reference materials:\n{_format_reference_materials(request)}\n"
                        f"Context: {request.context}"
                    ),
                },
            ],
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(f"{self.base_url}/chat/completions", headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
        content = data["choices"][0]["message"]["content"]
        return ModelResponse(content=content, metadata={"provider": "openai_compatible", "raw": data})


class OllamaProvider:
    def __init__(self, base_url: str, model: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model

    async def generate(self, request: ModelRequest) -> ModelResponse:
        payload = {
            "model": self.model,
            "prompt": (
                f"Role: {request.role}\n"
                f"Purpose: {request.agent_purpose}\n"
                f"Expected outputs: {request.expected_outputs}\n"
                f"Task: {request.task_title}\n"
                f"Description: {request.task_description}\n"
                f"Acceptance criteria: {request.acceptance_criteria}\n"
                f"Reference materials:\n{_format_reference_materials(request)}\n"
                f"Context: {request.context}\n"
            ),
            "stream": False,
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(f"{self.base_url}/api/generate", json=payload)
            response.raise_for_status()
            data = response.json()
        return ModelResponse(content=data["response"], metadata={"provider": "ollama", "raw": data})
