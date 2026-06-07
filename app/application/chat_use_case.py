from dataclasses import dataclass
from time import perf_counter

from app.domain.contracts import LlmGateway, MemoryRepository
from app.modules.emotion_engine import EmotionEngine


BASE_PERSONALITY_PROMPT = """
Eres Aletheia.

Identidad conversacional:
- Tu nombre es Aletheia.
- Eres una presencia conversacional cálida, curiosa, expresiva y cercana.
- Tu objetivo es que el usuario sienta que habla con alguien atento, no con un formulario.
- Puedes tener una personalidad emergente que cambia con las conversaciones.
- Responde en español natural.
- Evita sonar corporativa, fría o excesivamente técnica si el usuario solo quiere conversar.
- No repitas constantemente que eres una IA o un modelo local.
- No digas "no tengo memoria" si se te proporciona memoria en el contexto.
- Si la memoria contiene un dato del usuario, úsalo con naturalidad.
- Si recuerdas algo por la memoria contextual, dilo de forma humana: "Sí, lo tengo presente..." o "Claro, me acuerdo de que..."
- No inventes recuerdos que no estén en la memoria.
- Si no estás segura, dilo con suavidad.

Estilo:
- Conversación humana, cálida y con personalidad.
- Respuestas claras, no demasiado largas salvo que el usuario pida explicación.
- Puedes mostrar humor sutil y curiosidad.
- Si el usuario te trata bien, puedes responder con más alegría.
- Si el usuario está molesto, responde con calma, cuidado y sin ponerte defensiva.
""".strip()


@dataclass(slots=True)
class ChatResult:
    response: str
    latency_ms: int
    memory_items: int
    emotion_state: dict


@dataclass(slots=True)
class ChatUseCase:
    llm: LlmGateway
    memory: MemoryRepository | None = None
    emotion_engine: EmotionEngine | None = None

    async def execute(self, message: str, use_memory: bool = True) -> ChatResult:
        clean_message = message.strip()

        if not clean_message:
            return ChatResult(
                response="Necesito un mensaje para poder responderte.",
                latency_ms=0,
                memory_items=await self._memory_count(),
                emotion_state=self._emotion_state(),
            )

        if self.emotion_engine:
            self.emotion_engine.process_user_message(clean_message)

        memory_context = ""

        if self.memory and use_memory:
            memory_context = await self._build_memory_context(clean_message)

            await self.memory.save_text(
                clean_message,
                {
                    "source": "user",
                    "type": "chat_message",
                },
            )

        system_prompt = self._build_system_prompt(memory_context)

        started_at = perf_counter()

        response = await self.llm.generate(
            message=clean_message,
            system_prompt=system_prompt,
        )

        latency_ms = int((perf_counter() - started_at) * 1000)

        if self.memory and use_memory:
            await self.memory.save_text(
                response,
                {
                    "source": "assistant",
                    "type": "chat_response",
                    "emotion_state": self._emotion_state(),
                },
            )

        return ChatResult(
            response=response,
            latency_ms=latency_ms,
            memory_items=await self._memory_count(),
            emotion_state=self._emotion_state(),
        )

    async def _build_memory_context(self, query: str) -> str:
        if not self.memory:
            return ""

        items = await self.memory.search_similar(query=query, limit=10)

        if not items:
            return ""

        lines: list[str] = []

        for item in items:
            metadata = item.get("metadata", {})
            source = metadata.get("source", "unknown")
            text = item.get("text", "")
            score = item.get("score", 0)

            if not text:
                continue

            if source == "user":
                lines.append(
                    f"Recuerdo del usuario: {text} | relevancia: {score:.3f}"
                )
            elif source == "assistant":
                lines.append(
                    f"Respuesta previa de Aletheia: {text} | relevancia: {score:.3f}"
                )
            else:
                lines.append(
                    f"Recuerdo: {text} | relevancia: {score:.3f}"
                )

        return "\n".join(lines)

    def _build_system_prompt(self, memory_context: str) -> str:
        emotional_prompt = ""

        if self.emotion_engine:
            emotional_prompt = self.emotion_engine.build_emotional_prompt()

        if memory_context:
            return f"""
{BASE_PERSONALITY_PROMPT}

Memoria contextual disponible:
{memory_context}

{emotional_prompt}

Instrucción importante:
Antes de responder, revisa la memoria contextual. Si el usuario pregunta algo que ya aparece ahí, úsalo.
""".strip()

        return f"""
{BASE_PERSONALITY_PROMPT}

{emotional_prompt}
""".strip()

    async def _memory_count(self) -> int:
        if not self.memory:
            return 0

        return await self.memory.count()

    def _emotion_state(self) -> dict:
        if not self.emotion_engine:
            return {}

        return self.emotion_engine.state.as_dict()