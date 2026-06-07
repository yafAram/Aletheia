from dataclasses import dataclass

import httpx

from app.domain.contracts import LlmGateway


@dataclass(slots=True)
class OllamaClient(LlmGateway):
    base_url: str
    model: str
    timeout_seconds: float = 120.0

    async def generate(self, message: str, system_prompt: str | None = None) -> str:
        payload = {
            "model": self.model,
            "stream": False,
            "messages": [],
        }
        if system_prompt:
            payload["messages"].append({"role": "system", "content": system_prompt})
        payload["messages"].append({"role": "user", "content": message})

        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            response = await client.post(f"{self.base_url}/api/chat", json=payload)
            response.raise_for_status()
            data = response.json()
            return data.get("message", {}).get("content", "")
