from fastapi import APIRouter, Depends, Query

from app.api.schemas import (
    ChatRequest,
    ChatResponse,
    MemoryClearResponse,
    MemoryListResponse,
)
from app.application.chat_use_case import ChatUseCase
from app.core.config import Settings, get_settings
from app.infrastructure.ollama_client import OllamaClient
from app.infrastructure.qdrant_memory import InMemoryFallbackRepository

router = APIRouter(prefix="/api", tags=["Aletheia"])

_memory = InMemoryFallbackRepository()


def get_memory_repository() -> InMemoryFallbackRepository:
    return _memory


def get_chat_use_case(settings: Settings = Depends(get_settings)) -> ChatUseCase:
    llm = OllamaClient(
        base_url=settings.ollama_base_url,
        model=settings.ollama_model,
    )

    return ChatUseCase(llm=llm, memory=_memory)


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
    )


@router.get("/memory", response_model=MemoryListResponse)
async def list_memory(
    limit: int = Query(default=20, ge=1, le=100),
    memory: InMemoryFallbackRepository = Depends(get_memory_repository),
) -> MemoryListResponse:
    items = await memory.list_items(limit=limit)
    total = await memory.count()

    return MemoryListResponse(items=items, total=total)


@router.delete("/memory", response_model=MemoryClearResponse)
async def clear_memory(
    memory: InMemoryFallbackRepository = Depends(get_memory_repository),
) -> MemoryClearResponse:
    deleted_items = await memory.count()
    await memory.clear()

    return MemoryClearResponse(
        status="memory_cleared",
        deleted_items=deleted_items,
    )