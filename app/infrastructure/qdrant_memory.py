import hashlib
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4

from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models

from app.domain.contracts import MemoryRepository


@dataclass(slots=True)
class QdrantMemoryRepository(MemoryRepository):
    url: str
    collection_name: str
    vector_size: int = 64

    def __post_init__(self) -> None:
        self.client = AsyncQdrantClient(url=self.url)
        self._initialized = False

    async def initialize(self) -> None:
        if self._initialized:
            return

        exists = await self.client.collection_exists(
            collection_name=self.collection_name
        )

        if not exists:
            await self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(
                    size=self.vector_size,
                    distance=models.Distance.COSINE,
                ),
            )

        self._initialized = True

    async def save_text(self, text: str, metadata: dict | None = None) -> str:
        await self.initialize()

        item_id = str(uuid4())
        created_at = datetime.now(timezone.utc).isoformat()

        payload = {
            "id": item_id,
            "text": text,
            "metadata": metadata or {},
            "created_at": created_at,
        }

        await self.client.upsert(
            collection_name=self.collection_name,
            points=[
                models.PointStruct(
                    id=item_id,
                    vector=self._build_temporary_vector(text),
                    payload=payload,
                )
            ],
        )

        return item_id

    async def list_items(self, limit: int = 20) -> list[dict]:
        await self.initialize()

        if limit <= 0:
            limit = 20

        points, _ = await self.client.scroll(
            collection_name=self.collection_name,
            limit=limit,
            with_payload=True,
            with_vectors=False,
        )

        items = [point.payload for point in points if point.payload]

        return sorted(
            items,
            key=lambda item: item.get("created_at", ""),
            reverse=False,
        )

    async def count(self) -> int:
        await self.initialize()

        result = await self.client.count(
            collection_name=self.collection_name,
            exact=True,
        )

        return result.count

    async def clear(self) -> None:
        exists = await self.client.collection_exists(
            collection_name=self.collection_name
        )

        if exists:
            await self.client.delete_collection(
                collection_name=self.collection_name
            )

        self._initialized = False
        await self.initialize()

    def _build_temporary_vector(self, text: str) -> list[float]:
        """Vector temporal para poder persistir en Qdrant.

        Este NO es embedding semántico todavía.
        En el siguiente paso será reemplazado por embeddings reales.
        """

        clean_text = text.strip().lower().encode("utf-8")
        seed = hashlib.blake2b(clean_text, digest_size=64).digest()

        values: list[float] = []

        while len(values) < self.vector_size:
            for byte in seed:
                value = (byte / 255.0) * 2.0 - 1.0
                values.append(value)

                if len(values) == self.vector_size:
                    break

            seed = hashlib.blake2b(seed, digest_size=64).digest()

        norm = math.sqrt(sum(value * value for value in values))

        if norm == 0:
            return values

        return [value / norm for value in values]