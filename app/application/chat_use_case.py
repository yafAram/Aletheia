import asyncio
import logging
from dataclasses import dataclass, field
from time import perf_counter

from app.domain.contracts import LlmGateway, MemoryRepository
from app.domain.cognitive_workspace import CognitiveWorkspace
from app.infrastructure.aletheia_self_store import AletheiaSelfStore
from app.infrastructure.initiative_store import InitiativeStore
from app.infrastructure.goal_store import GoalStore
from app.infrastructure.personality_store import PersonalityStore
from app.infrastructure.relationship_store import RelationshipStore
from app.modules.aletheia_self_engine import AletheiaSelfEngine
from app.modules.emotion_engine import EmotionEngine
from app.modules.initiative_engine import InitiativeEngine
from app.modules.goal_engine import GoalEngine
from app.modules.personality_engine import PersonalityEngine
from app.modules.relationship_engine import RelationshipEngine
from app.application.prompt_builder import PromptBuilder


logger = logging.getLogger(__name__)


@dataclass(slots=True)
class ChatResult:
    response: str
    latency_ms: int
    memory_items: int
    emotion_state: dict
    personality_state: dict
    self_state: dict
    relationship_state: dict
    significant_memory_count: int
    bond_state: dict
    bond_event_count: int
    initiative_state: dict
    initiative_action_count: int


@dataclass(slots=True)
class ChatUseCase:
    llm: LlmGateway
    memory: MemoryRepository | None = None
    emotion_engine: EmotionEngine | None = None
    personality_engine: PersonalityEngine | None = None
    personality_store: PersonalityStore | None = None
    aletheia_self_engine: AletheiaSelfEngine | None = None
    aletheia_self_store: AletheiaSelfStore | None = None
    relationship_engine: RelationshipEngine | None = None
    relationship_store: RelationshipStore | None = None
    initiative_engine: InitiativeEngine | None = None
    initiative_store: InitiativeStore | None = None
    goal_engine: GoalEngine | None = None
    goal_store: GoalStore | None = None

    memory_search_limit: int = 4
    significant_memory_prompt_limit: int = 4
    bond_event_prompt_limit: int = 4
    initiative_action_prompt_limit: int = 3
    goal_prompt_limit: int = 8
    async_memory_persistence: bool = True
    _memory_tasks: set[asyncio.Task[None]] = field(default_factory=set, init=False, repr=False)

    async def execute(self, message: str, use_memory: bool = True) -> ChatResult:
        clean_message = message.strip()

        if not clean_message:
            return ChatResult(
                response="Necesito que me digas algo para poder responderte.",
                latency_ms=0,
                memory_items=await self._memory_count(),
                emotion_state=self._emotion_state(),
                personality_state=self._personality_state(),
                self_state=self._self_state(),
                relationship_state=self._relationship_state(),
                significant_memory_count=self._significant_memory_count(),
                bond_state=self._bond_state(),
                bond_event_count=self._bond_event_count(),
                initiative_state=self._initiative_state(),
                initiative_action_count=self._initiative_action_count(),
            )

        if self.emotion_engine:
            self.emotion_engine.process_user_message(clean_message)

        if self.personality_engine:
            self.personality_engine.process_interaction(clean_message)
            self._save_personality()

        if self.aletheia_self_engine:
            self.aletheia_self_engine.process_interaction(clean_message)
            self._save_aletheia_self()

        if self.relationship_engine:
            self.relationship_engine.process_user_message(clean_message)
            self._save_relationship()

        if self.initiative_engine:
            self.initiative_engine.process_user_message(clean_message)
            self._save_initiative()

        if self.goal_engine:
            self.goal_engine.observe_user_message(clean_message)
            self._save_goals()

        memory_context = ""

        if self.memory and use_memory:
            memory_context = await self._build_memory_context(clean_message)

            await self._persist_memory(
                clean_message,
                {
                    "source": "user",
                    "type": "chat_message",
                    "emotion_state": self._emotion_state(),
                    "personality_state": self._personality_state(),
                    "self_state": self._self_state(),
                    "relationship_state": self._relationship_state(),
                    "significant_memory_count": self._significant_memory_count(),
                    "bond_state": self._bond_state(),
                    "bond_event_count": self._bond_event_count(),
                    "initiative_state": self._initiative_state(),
                    "initiative_action_count": self._initiative_action_count(),
                },
            )

        system_prompt = self._build_system_prompt(memory_context)

        started_at = perf_counter()

        try:
            response = await self.llm.generate(
                message=clean_message,
                system_prompt=system_prompt,
            )
        finally:
            # Flush user-message persistence even if Ollama fails.
            await self._flush_memory_tasks()

        latency_ms = int((perf_counter() - started_at) * 1000)

        if self.memory and use_memory:
            await self._persist_memory(
                response,
                {
                    "source": "assistant",
                    "type": "chat_response",
                    "emotion_state": self._emotion_state(),
                    "personality_state": self._personality_state(),
                    "self_state": self._self_state(),
                    "relationship_state": self._relationship_state(),
                    "significant_memory_count": self._significant_memory_count(),
                    "bond_state": self._bond_state(),
                    "bond_event_count": self._bond_event_count(),
                    "initiative_state": self._initiative_state(),
                    "initiative_action_count": self._initiative_action_count(),
                },
            )
            await self._flush_memory_tasks()

        return ChatResult(
            response=response,
            latency_ms=latency_ms,
            memory_items=await self._memory_count(),
            emotion_state=self._emotion_state(),
            personality_state=self._personality_state(),
            self_state=self._self_state(),
            relationship_state=self._relationship_state(),
            significant_memory_count=self._significant_memory_count(),
            bond_state=self._bond_state(),
            bond_event_count=self._bond_event_count(),
            initiative_state=self._initiative_state(),
            initiative_action_count=self._initiative_action_count(),
        )

    async def _build_memory_context(self, query: str) -> str:
        if not self.memory:
            return ""

        items = await self.memory.search_similar(
            query=query,
            limit=self.memory_search_limit,
        )

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

    def _build_cognitive_workspace(self, memory_context: str) -> CognitiveWorkspace:
        """Snapshot the available engine state without transferring engine ownership."""
        emotional_prompt = (
            self.emotion_engine.build_emotional_prompt()
            if self.emotion_engine else ""
        )
        personality_prompt = (
            self.personality_engine.build_personality_prompt()
            if self.personality_engine else ""
        )

        self_prompt = ""
        self_relationship_prompt = ""
        significant_memory_prompt = ""
        if self.aletheia_self_engine:
            self_prompt = self.aletheia_self_engine.build_self_prompt()
            # RelationshipEngine is the authoritative relationship model. The
            # self-engine's legacy relationship store remains for compatibility,
            # but feeding both models to the LLM would duplicate/conflict evidence.
            self_relationship_prompt = ""
            significant_memory_prompt = (
                self.aletheia_self_engine.build_significant_memory_prompt(
                    limit=self.significant_memory_prompt_limit
                )
            )

        bond_prompt = (
            self.relationship_engine.build_relationship_prompt(
                limit_events=self.bond_event_prompt_limit
            )
            if self.relationship_engine else ""
        )
        initiative_prompt = (
            self.initiative_engine.build_initiative_prompt(
                limit_actions=self.initiative_action_prompt_limit
            )
            if self.initiative_engine else ""
        )
        goals_prompt = (
            self.goal_engine.build_prompt(limit=self.goal_prompt_limit)
            if self.goal_engine else ""
        )

        return CognitiveWorkspace(
            memory_context=memory_context,
            emotional_prompt=emotional_prompt,
            personality_prompt=personality_prompt,
            self_prompt=self_prompt,
            self_relationship_prompt=self_relationship_prompt,
            significant_memory_prompt=significant_memory_prompt,
            bond_prompt=bond_prompt,
            initiative_prompt=initiative_prompt,
            goals_prompt=goals_prompt,
            emotion_state=self._emotion_state(),
            personality_state=self._personality_state(),
            self_state=self._self_state(),
            relationship_state=self._relationship_state(),
            bond_state=self._bond_state(),
            initiative_state=self._initiative_state(),
        )

    def _build_system_prompt(self, memory_context: str) -> str:
        """Compatibility entry point delegating prompt composition to PromptBuilder."""
        workspace = self._build_cognitive_workspace(memory_context)
        return PromptBuilder().build(workspace)

    async def _memory_count(self) -> int:
        if not self.memory:
            return 0

        return await self.memory.count()

    async def _persist_memory(self, text: str, metadata: dict) -> None:
        if not self.memory:
            return

        if self.async_memory_persistence:
            task = asyncio.create_task(
                self._safe_save_memory(text=text, metadata=metadata)
            )
            self._memory_tasks.add(task)
            task.add_done_callback(self._on_memory_task_done)
            return

        await self._safe_save_memory(text=text, metadata=metadata)

    def _on_memory_task_done(self, task: asyncio.Task[None]) -> None:
        self._memory_tasks.discard(task)
        # Retrieve any unexpected exception so it is never silently discarded.
        if task.cancelled():
            return
        error = task.exception()
        if error is not None:
            logger.error(
                "Unexpected background memory task failure: %s",
                error,
                exc_info=(type(error), error, error.__traceback__),
            )

    async def _flush_memory_tasks(self) -> None:
        """Wait for scheduled writes before returning a result or propagating errors."""
        while self._memory_tasks:
            pending = tuple(self._memory_tasks)
            await asyncio.gather(*pending, return_exceptions=True)

    async def _safe_save_memory(self, text: str, metadata: dict) -> None:
        if not self.memory:
            return
        try:
            await self.memory.save_text(text, metadata)
        except Exception:
            logger.exception("Could not persist a chat memory item")

    def _emotion_state(self) -> dict:
        if not self.emotion_engine:
            return {}

        return self.emotion_engine.state.as_dict()

    def _personality_state(self) -> dict:
        if not self.personality_engine:
            return {}

        return self.personality_engine.profile.as_dict()

    def _self_state(self) -> dict:
        if not self.aletheia_self_engine:
            return {}

        return self.aletheia_self_engine.self_model.as_dict()

    def _relationship_state(self) -> dict:
        """Return the single authoritative relationship model."""
        if not self.relationship_engine:
            return {}

        return {
            key: bond.as_dict()
            for key, bond in self.relationship_engine.bonds.items()
        }

    def _significant_memory_count(self) -> int:
        if not self.aletheia_self_engine:
            return 0

        return len(self.aletheia_self_engine.significant_memories)

    def _bond_state(self) -> dict:
        if not self.relationship_engine:
            return {}

        return {
            "bonds": {
                key: bond.as_dict()
                for key, bond in self.relationship_engine.bonds.items()
            }
        }

    def _bond_event_count(self) -> int:
        if not self.relationship_engine:
            return 0

        return len(self.relationship_engine.events)

    def _initiative_state(self) -> dict:
        if not self.initiative_engine:
            return {}

        return self.initiative_engine.as_dict()

    def _initiative_action_count(self) -> int:
        if not self.initiative_engine:
            return 0

        return len(self.initiative_engine.actions)

    def _save_personality(self) -> None:
        if not self.personality_engine or not self.personality_store:
            return

        self.personality_store.save(self.personality_engine.profile)

    def _save_aletheia_self(self) -> None:
        if not self.aletheia_self_engine or not self.aletheia_self_store:
            return

        self.aletheia_self_store.save_engine(self.aletheia_self_engine)

    def _save_relationship(self) -> None:
        if not self.relationship_engine or not self.relationship_store:
            return

        self.relationship_store.save_engine(self.relationship_engine)

    def _save_initiative(self) -> None:
        if not self.initiative_engine or not self.initiative_store:
            return

        self.initiative_store.save_engine(self.initiative_engine)

    def _save_goals(self) -> None:
        if not self.goal_engine or not self.goal_store:
            return

        self.goal_store.save_engine(self.goal_engine)
