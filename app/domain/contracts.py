from abc import ABC, abstractmethod


class LlmGateway(ABC):
    @abstractmethod
    async def generate(self, message: str, system_prompt: str | None = None) -> str:
        raise NotImplementedError


class MemoryRepository(ABC):
    @abstractmethod
    async def save_text(self, text: str, metadata: dict | None = None) -> str:
        raise NotImplementedError
