from abc import ABC, abstractmethod


class LlmGateway(ABC):
    @abstractmethod
    async def generate(self, message: str, system_prompt: str | None = None) -> str:
        raise NotImplementedError


class EmbeddingGateway(ABC):
    @abstractmethod
    async def embed(self, text: str) -> list[float]:
        raise NotImplementedError


class MemoryRepository(ABC):
    @abstractmethod
    async def save_text(self, text: str, metadata: dict | None = None) -> str:
        raise NotImplementedError

    @abstractmethod
    async def search_similar(self, query: str, limit: int = 8) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    async def list_items(self, limit: int = 20) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    async def count(self) -> int:
        raise NotImplementedError

    @abstractmethod
    async def clear(self) -> None:
        raise NotImplementedError