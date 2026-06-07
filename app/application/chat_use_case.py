from dataclasses import dataclass

from app.domain.contracts import LlmGateway, MemoryRepository


DEFAULT_SYSTEM_PROMPT = """
Eres Aletheia, un agente IA local. Responde en español, de forma clara,
consciente de que estás ejecutándote en una máquina local. No inventes acciones
que no ejecutaste. Si falta contexto, dilo.
""".strip()


@dataclass(slots=True)
class ChatUseCase:
    llm: LlmGateway
    memory: MemoryRepository | None = None

    async def execute(self, message: str) -> str:
        clean_message = message.strip()
        if not clean_message:
            return "Necesito un mensaje para responder."

        if self.memory:
            await self.memory.save_text(clean_message, {"source": "user"})

        response = await self.llm.generate(
            message=clean_message,
            system_prompt=DEFAULT_SYSTEM_PROMPT,
        )

        if self.memory:
            await self.memory.save_text(response, {"source": "assistant"})

        return response
