import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4

from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models

from app.domain.contracts import EmbeddingGateway, MemoryRepository


@dataclass(slots=True)
class QdrantMemoryRepository(MemoryRepository):
    url: str
    collection_name: str
    embedding_gateway: EmbeddingGateway
    vector_size: int = 768
    client: AsyncQdrantClient = field(init=False, repr=False)
    _initialized: bool = field(default=False, init=False, repr=False)
    _initialize_lock: asyncio.Lock = field(init=False, repr=False)

    def __post_init__(self) -> None:
        # All mutable attributes must be declared because this dataclass uses slots.
        self.client = AsyncQdrantClient(url=self.url)
        self._initialize_lock = asyncio.Lock()

    async def initialize(self) -> None:
        if self._initialized:
            return

        # Avoid two concurrent requests both attempting to create the collection.
        async with self._initialize_lock:
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
        vector = await self.embedding_gateway.embed(text)

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
                    vector=vector,
                    payload=payload,
                )
            ],
        )

        return item_id

    async def search_similar(self, query: str, limit: int = 8) -> list[dict]:
        await self.initialize()

        if limit <= 0:
            limit = 8

        vector = await self.embedding_gateway.embed(query)

        results = await self.client.search(
            collection_name=self.collection_name,
            query_vector=vector,
            limit=limit,
            with_payload=True,
        )

        items: list[dict] = []

        for result in results:
            if not result.payload:
                continue

            payload = dict(result.payload)
            payload["score"] = float(result.score)
            items.append(payload)

        return items

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
        await self.initialize()
        async with self._initialize_lock:
            exists = await self.client.collection_exists(
                collection_name=self.collection_name
            )

            if exists:
                await self.client.delete_collection(
                    collection_name=self.collection_name
                )

            self._initialized = False
            exists_after_delete = await self.client.collection_exists(
                collection_name=self.collection_name
            )
            if not exists_after_delete:
                await self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=models.VectorParams(
                        size=self.vector_size,
                        distance=models.Distance.COSINE,
                    ),
                )
            self._initialized = True

    async def close(self) -> None:
        """Close the underlying async client during application shutdown."""
        await self.client.close()