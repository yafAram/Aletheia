from fastapi import APIRouter, Depends, Query

from app.api.schemas import (
    AletheiaSelfResetResponse,
    AletheiaSelfResponse,
    BondEventsResponse,
    BondResetResponse,
    BondStateResponse,
    ChatRequest,
    ChatResponse,
    EmotionStateResponse,
    MemoryClearResponse,
    MemoryListResponse,
    PersonalityResetResponse,
    PersonalityStateResponse,
    RelationshipListResponse,
    SignificantMemoryListResponse,
)
from app.application.chat_use_case import ChatUseCase
from app.core.config import Settings, get_settings
from app.domain.contracts import MemoryRepository
from app.infrastructure.aletheia_self_store import AletheiaSelfStore
from app.infrastructure.ollama_client import OllamaClient
from app.infrastructure.ollama_embedding_client import OllamaEmbeddingClient
from app.infrastructure.personality_store import PersonalityStore
from app.infrastructure.qdrant_memory import QdrantMemoryRepository
from app.infrastructure.relationship_store import RelationshipStore
from app.modules.aletheia_self_engine import AletheiaSelfEngine
from app.modules.emotion_engine import EmotionEngine
from app.modules.personality_engine import PersonalityEngine
from app.modules.relationship_engine import RelationshipEngine

router = APIRouter(prefix="/api", tags=["Aletheia"])

_memory_repository: QdrantMemoryRepository | None = None

_emotion_engine = EmotionEngine()

_personality_store = PersonalityStore()
_personality_engine = PersonalityEngine(profile=_personality_store.load())

_aletheia_self_store = AletheiaSelfStore()
_aletheia_self_engine = _aletheia_self_store.load_engine()

_relationship_store = RelationshipStore()
_relationship_engine = _relationship_store.load_engine()


def get_memory_repository(
    settings: Settings = Depends(get_settings),
) -> MemoryRepository:
    global _memory_repository

    if _memory_repository is None:
        embedding_gateway = OllamaEmbeddingClient(
            base_url=settings.ollama_base_url,
            model=settings.ollama_embedding_model,
        )

        _memory_repository = QdrantMemoryRepository(
            url=settings.qdrant_url,
            collection_name=settings.qdrant_collection,
            embedding_gateway=embedding_gateway,
            vector_size=settings.qdrant_vector_size,
        )

    return _memory_repository


def get_emotion_engine() -> EmotionEngine:
    return _emotion_engine


def get_personality_store() -> PersonalityStore:
    return _personality_store


def get_personality_engine() -> PersonalityEngine:
    return _personality_engine


def get_aletheia_self_store() -> AletheiaSelfStore:
    return _aletheia_self_store


def get_aletheia_self_engine() -> AletheiaSelfEngine:
    return _aletheia_self_engine


def get_relationship_store() -> RelationshipStore:
    return _relationship_store


def get_relationship_engine() -> RelationshipEngine:
    return _relationship_engine


def get_chat_use_case(
    settings: Settings = Depends(get_settings),
    memory: MemoryRepository = Depends(get_memory_repository),
    emotion_engine: EmotionEngine = Depends(get_emotion_engine),
    personality_engine: PersonalityEngine = Depends(get_personality_engine),
    personality_store: PersonalityStore = Depends(get_personality_store),
    aletheia_self_engine: AletheiaSelfEngine = Depends(get_aletheia_self_engine),
    aletheia_self_store: AletheiaSelfStore = Depends(get_aletheia_self_store),
    relationship_engine: RelationshipEngine = Depends(get_relationship_engine),
    relationship_store: RelationshipStore = Depends(get_relationship_store),
) -> ChatUseCase:
    llm = OllamaClient(
        base_url=settings.ollama_base_url,
        model=settings.ollama_model,
    )

    return ChatUseCase(
        llm=llm,
        memory=memory,
        emotion_engine=emotion_engine,
        personality_engine=personality_engine,
        personality_store=personality_store,
        aletheia_self_engine=aletheia_self_engine,
        aletheia_self_store=aletheia_self_store,
        relationship_engine=relationship_engine,
        relationship_store=relationship_store,
    )


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    settings: Settings = Depends(get_settings),
    use_case: ChatUseCase = Depends(get_chat_use_case),
) -> ChatResponse:
    result = await use_case.execute(
        message=request.message,
        use_memory=request.use_memory,
    )

    return ChatResponse(
        response=result.response,
        model=settings.ollama_model,
        latency_ms=result.latency_ms,
        memory_items=result.memory_items,
        emotion_state=result.emotion_state,
        personality_state=result.personality_state,
        self_state=result.self_state,
        relationship_state=result.relationship_state,
        significant_memory_count=result.significant_memory_count,
        bond_state=result.bond_state,
        bond_event_count=result.bond_event_count,
    )


@router.get("/memory", response_model=MemoryListResponse)
async def list_memory(
    limit: int = Query(default=20, ge=1, le=100),
    memory: MemoryRepository = Depends(get_memory_repository),
) -> MemoryListResponse:
    items = await memory.list_items(limit=limit)
    total = await memory.count()

    return MemoryListResponse(items=items, total=total)


@router.delete("/memory", response_model=MemoryClearResponse)
async def clear_memory(
    memory: MemoryRepository = Depends(get_memory_repository),
) -> MemoryClearResponse:
    deleted_items = await memory.count()
    await memory.clear()

    return MemoryClearResponse(
        status="memory_cleared",
        deleted_items=deleted_items,
    )


@router.get("/emotion", response_model=EmotionStateResponse)
async def get_emotion_state(
    emotion_engine: EmotionEngine = Depends(get_emotion_engine),
) -> EmotionStateResponse:
    return EmotionStateResponse(**emotion_engine.state.as_dict())


@router.get("/personality", response_model=PersonalityStateResponse)
async def get_personality_state(
    personality_engine: PersonalityEngine = Depends(get_personality_engine),
) -> PersonalityStateResponse:
    return PersonalityStateResponse(**personality_engine.profile.as_dict())


@router.post("/personality/reset", response_model=PersonalityResetResponse)
async def reset_personality(
    personality_store: PersonalityStore = Depends(get_personality_store),
) -> PersonalityResetResponse:
    global _personality_engine

    profile = personality_store.reset()
    _personality_engine = PersonalityEngine(profile=profile)

    return PersonalityResetResponse(
        status="personality_reset",
        personality=PersonalityStateResponse(**profile.as_dict()),
    )


@router.get("/self", response_model=AletheiaSelfResponse)
async def get_aletheia_self(
    aletheia_self_engine: AletheiaSelfEngine = Depends(get_aletheia_self_engine),
) -> AletheiaSelfResponse:
    return AletheiaSelfResponse(**aletheia_self_engine.as_dict())


@router.get("/relationships", response_model=RelationshipListResponse)
async def get_relationships(
    aletheia_self_engine: AletheiaSelfEngine = Depends(get_aletheia_self_engine),
) -> RelationshipListResponse:
    relationships = {
        key: relationship.as_dict()
        for key, relationship in aletheia_self_engine.relationships.items()
    }

    return RelationshipListResponse(
        relationships=relationships,
        total=len(relationships),
    )


@router.get("/significant-memories", response_model=SignificantMemoryListResponse)
async def get_significant_memories(
    aletheia_self_engine: AletheiaSelfEngine = Depends(get_aletheia_self_engine),
) -> SignificantMemoryListResponse:
    items = [
        memory.as_dict()
        for memory in aletheia_self_engine.significant_memories
    ]

    return SignificantMemoryListResponse(
        items=items,
        total=len(items),
    )


@router.post("/self/reset", response_model=AletheiaSelfResetResponse)
async def reset_aletheia_self(
    aletheia_self_store: AletheiaSelfStore = Depends(get_aletheia_self_store),
) -> AletheiaSelfResetResponse:
    global _aletheia_self_engine

    _aletheia_self_engine = aletheia_self_store.reset()

    return AletheiaSelfResetResponse(
        status="self_reset",
        state=AletheiaSelfResponse(**_aletheia_self_engine.as_dict()),
    )


@router.get("/bond", response_model=BondStateResponse)
async def get_bond_state(
    relationship_engine: RelationshipEngine = Depends(get_relationship_engine),
) -> BondStateResponse:
    return BondStateResponse(**relationship_engine.as_dict())


@router.get("/bond/events", response_model=BondEventsResponse)
async def get_bond_events(
    relationship_engine: RelationshipEngine = Depends(get_relationship_engine),
) -> BondEventsResponse:
    items = [
        event.as_dict()
        for event in relationship_engine.events
    ]

    return BondEventsResponse(
        items=items,
        total=len(items),
    )


@router.post("/bond/reset", response_model=BondResetResponse)
async def reset_bond_state(
    relationship_store: RelationshipStore = Depends(get_relationship_store),
) -> BondResetResponse:
    global _relationship_engine

    _relationship_engine = relationship_store.reset()

    return BondResetResponse(
        status="bond_reset",
        state=BondStateResponse(**_relationship_engine.as_dict()),
    )