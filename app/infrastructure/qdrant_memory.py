from dataclasses import dataclass
from uuid import uuid4

from app.domain.contracts import MemoryRepository


@dataclass(slots=True)
class InMemoryFallbackRepository(MemoryRepository):
    """Memoria temporal para arrancar el MVP antes de meter embeddings reales."""

    items: list[dict]

    async def save_text(self, text: str, metadata: dict | None = None) -> str:
        item_id = str(uuid4())
        self.items.append({"id": item_id, "text": text, "metadata": metadata or {}})
        return item_id
