from dataclasses import dataclass

import httpx


@dataclass(slots=True)
class OllamaEmbeddingClient:
    base_url: str
    model: str
    timeout_seconds: float = 60.0

    async def embed(self, text: str) -> list[float]:
        clean_text = text.strip()

        if not clean_text:
            raise ValueError("Cannot generate embedding for empty text.")

        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            response = await client.post(
                f"{self.base_url}/api/embeddings",
                json={
                    "model": self.model,
                    "prompt": clean_text,
                },
            )

            response.raise_for_status()
            data = response.json()

        embedding = data.get("embedding")

        if not embedding:
            raise RuntimeError("Ollama did not return an embedding.")

        return [float(value) for value in embedding]