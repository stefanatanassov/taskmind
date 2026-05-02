from __future__ import annotations

import httpx

from taskmind.providers.base import ModelRequest, ModelResponse, build_execution_prompt


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
                        "Use the provided execution payload and reference materials when relevant."
                    ),
                },
                {"role": "user", "content": build_execution_prompt(request)},
            ],
            "max_tokens": 384,
            "temperature": 0.2,
            "stop": ["<|im_end|>"],
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
            "prompt": build_execution_prompt(request),
            "stream": False,
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(f"{self.base_url}/api/generate", json=payload)
            response.raise_for_status()
            data = response.json()
        return ModelResponse(content=data["response"], metadata={"provider": "ollama", "raw": data})
