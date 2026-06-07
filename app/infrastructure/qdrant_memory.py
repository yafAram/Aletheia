from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4

from app.domain.contracts import MemoryRepository


@dataclass(slots=True)
class InMemoryFallbackRepository(MemoryRepository):
    """Memoria temporal para arrancar el MVP antes de meter embeddings reales.
    
    Esta memoria no sobrevive si reiniciar el contenedor.
    Luego sera reemplazada o complementada con Qdrant o similar.
    """

    items: list[dict] = field(default_factory=list)

    async def save_text(self, text: str, metadata: dict | None = None) -> str:
        item_id = str(uuid4())

        self.items.append({
            "id": item_id,
            "text": text,
            "metadata": metadata or {},
            "created_at": datetime.now(timezone.utc).isoformat(),
        })

        return item_id

    async def list_items(self, limit: int = 20) -> list[dict]:
        if limit <=0:
            limit = 20
        
        return self.items[-limit:]

    async def count(self) -> int:
        return len(self.items)

    async def clear(self) -> None:
        self.items.clear()



       
