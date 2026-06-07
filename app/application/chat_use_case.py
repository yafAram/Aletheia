from dataclasses import dataclass
from time import perf_counter

from app.domain.contracts import LlmGateway, MemoryRepository


DEFAULT_SYSTEM_PROMPT = """
Eres Aletheia, un agente IA local ejecutándose en la máquina del usuario.

Reglas:
- Responde siempre en español.
- Sé clara, útil y directa.
- No inventes acciones que no ejecutaste.
- Si no tienes suficiente contexto, dilo.
- Recuerda que estás en una etapa MVP local.
""".strip()


@dataclass(slots=True)
class ChatResult:
    response: str
    latency_ms: int
    memory_items: int


@dataclass(slots=True)
class ChatUseCase:
    llm: LlmGateway
    memory: MemoryRepository | None = None

    async def execute(self, message: str, use_memory: bool = True) -> ChatResult:
        clean_message = message.strip()
        if not clean_message:
            return ChatResult(
                response="Necesito un mensaje para responder.", 
                latency_ms=0, 
                memory_items=await self._memory_count(),
                )

        if self.memory and use_memory:
            await self.memory.save_text(
                clean_message, {
                    "source": "user",
                    "type": "chat_message",
                    }
                )
        
        started_at = perf_counter()

        response = await self.llm.generate(
            message=clean_message,
            system_prompt=DEFAULT_SYSTEM_PROMPT,
        )

        latency_ms = int ((perf_counter() - started_at) * 1000)

        if self.memory and use_memory:
            await self.memory.save_text(
                response, {
                "source": "assistant",
                "type": "chat_response"
                },
            )

        return ChatResult(
            response=response,
            latency_ms=latency_ms,
            memory_items=await self._memory_count(),
        )

    async def _memory_count(self) -> int:
        if not self.memory:
            return 0

        return await self.memory.count()
