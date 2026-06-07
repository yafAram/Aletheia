from abc import ABC, abstractmethod


class LlmGateway(ABC):
    @abstractmethod
    async def generate(self, message: str, system_prompt: str | None = None) -> str:
        raise NotImplementedError


class MemoryRepository(ABC):
    @abstractmethod
    async def save_text(self, text: str, metadata: dict | None = None) -> str:
        raise NotImplementedError

    @abstractmethod
    async def list_items(self, text: str, metadata: dict | None = None) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    async def count(self, limit: int = 20) -> int:
        raise NotImplementedError

    @abstractmethod
    async def clear(self) -> None:
        raise NotImplementedError
