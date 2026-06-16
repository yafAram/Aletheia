from dataclasses import dataclass

import httpx

from app.domain.contracts import LlmGateway


@dataclass(slots=True)
class OllamaClient(LlmGateway):
    base_url: str
    model: str
    timeout_seconds: float = 180.0

    num_predict: int = 220
    temperature: float = 0.7
    top_p: float = 0.9
    num_ctx: int = 3072
    keep_alive: str = "30m"

    async def generate(self, message: str, system_prompt: str | None = None) -> str:
        clean_message = message.strip()

        if not clean_message:
            return "Necesito que me digas algo para poder responderte."

        messages: list[dict] = []

        if system_prompt:
            messages.append(
                {
                    "role": "system",
                    "content": system_prompt,
                }
            )

        messages.append(
            {
                "role": "user",
                "content": clean_message,
            }
        )

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "keep_alive": self.keep_alive,
            "options": {
                "num_predict": self.num_predict,
                "temperature": self.temperature,
                "top_p": self.top_p,
                "num_ctx": self.num_ctx,
            },
        }

        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            response = await client.post(
                f"{self.base_url}/api/chat",
                json=payload,
            )

            response.raise_for_status()
            data = response.json()

        content = data.get("message", {}).get("content", "").strip()

        if not content:
            return "Me quedé sin una respuesta clara. ¿Puedes repetirlo de otra forma?"

        return content