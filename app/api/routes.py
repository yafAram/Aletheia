from fastapi import APIRouter, Depends

from app.api.schemas import ChatRequest, ChatResponse
from app.application.chat_use_case import ChatUseCase
from app.core.config import Settings, get_settings
from app.infrastructure.ollama_client import OllamaClient
from app.infrastructure.qdrant_memory import InMemoryFallbackRepository

router = APIRouter(prefix="/api", tags=["Aletheia"])
_memory = InMemoryFallbackRepository(items=[])


def get_chat_use_case(settings: Settings = Depends(get_settings)) -> ChatUseCase:
    llm = OllamaClient(
        base_url=settings.ollama_base_url,
        model=settings.ollama_model,
    )
    return ChatUseCase(llm=llm, memory=_memory)


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    use_case: ChatUseCase = Depends(get_chat_use_case),
) -> ChatResponse:
    response = await use_case.execute(request.message)
    return ChatResponse(response=response)
