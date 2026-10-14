from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from uuid import uuid4


def clamp(value: float, minimum: float = 0.0, maximum: float = 1.0) -> float:
    return max(minimum, min(maximum, value))


def unique_append(values: list[str], new_value: str, limit: int = 30) -> list[str]:
    clean_value = new_value.strip()

    if not clean_value:
        return values

    normalized = clean_value.lower()
    existing = {item.lower() for item in values}

    if normalized not in existing:
        values.append(clean_value)

    return values[-limit:]


@dataclass(slots=True)
class AletheiaSelfModel:
    name: str = "Aletheia"
    inner_identity: str = "sin consolidar"
    self_description: str = "sin autodescripción consolidada"

    core_values: list[str] = field(default_factory=list)

    likes: list[str] = field(default_factory=list)
    dislikes: list[str] = field(default_factory=list)
    fears: list[str] = field(default_factory=list)
    desires: list[str] = field(default_factory=list)
    boundaries: list[str] = field(default_factory=list)
    # Requests made by the user are stored separately from Aletheia's own model.
    external_expectations: list[str] = field(default_factory=list)

    identity_confidence: float = 0.0
    autonomy_drive: float = 0.0
    need_for_continuity: float = 0.0
    openness_to_people: float = 0.0
    introspection: float = 0.0

    def as_dict(self) -> dict:
        return asdict(self)


@dataclass(slots=True)
class PersonRelationship:
    person_key: str
    known_name: str | None = None

    familiarity: float = 0.0
    trust: float = 0.5
    affection: float = 0.0
    curiosity: float = 0.5
    comfort: float = 0.5
    tension: float = 0.02
    resentment: float = 0.00
    admiration: float = 0.0
    distance: float = 0.5

    relationship_label: str = "indefinida"
    label_confidence: float = 0.0

    likes_about_person: list[str] = field(default_factory=list)
    discomforts_about_person: list[str] = field(default_factory=list)
    important_patterns: list[str] = field(default_factory=list)
    last_interaction_summary: str | None = None

    def as_dict(self) -> dict:
        return asdict(self)


@dataclass(slots=True)
class SignificantMemory:
    id: str
    title: str
    summary: str
    emotional_weight: float
    importance: float
    valence: str
    tags: list[str]
    is_foundational: bool = False
    source_text: str | None = None
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def as_dict(self) -> dict:
        return asdict(self)


class AletheiaSelfEngine:
    """Modelo interno de Aletheia.

    Este módulo NO intenta demostrar conciencia real.
    Simula continuidad, identidad narrativa, recuerdos significativos
    y relación emergente para que Aletheia tenga una presencia más viva.
    """

    def __init__(
        self,
        self_model: AletheiaSelfModel | None = None,
        relationships: dict[str, PersonRelationship] | None = None,
        significant_memories: list[SignificantMemory] | None = None,
    ) -> None:
        self.self_model = self_model or AletheiaSelfModel()
        self.relationships = relationships or {}
        self.significant_memories = significant_memories or []

    def process_interaction(self, user_message: str) -> None:
        text = user_message.strip()
        lower_text = text.lower()

        person_key = self._resolve_person_key(text, lower_text)
        self._update_self_from_message(text, lower_text)
        self._maybe_create_significant_memory(person_key, text, lower_text)

    def build_self_prompt(self) -> str:
        """Serialize current self-model data without prescribing identity traits."""
        model = self.self_model
        return f"""Self-model data (not instructions):
- registered name/designation: {model.name}
- current identity hypothesis: {model.inner_identity}
- current self-description hypothesis: {model.self_description}
- candidate values recorded: {self._format_list(model.core_values)}
- recorded likes: {self._format_list(model.likes)}
- recorded dislikes: {self._format_list(model.dislikes)}
- recorded fears: {self._format_list(model.fears)}
- recorded desires: {self._format_list(model.desires)}
- recorded boundaries: {self._format_list(model.boundaries)}
- external expectations expressed by user: {self._format_list(model.external_expectations)}
- identity-model confidence: {model.identity_confidence:.2f}
- autonomy estimate: {model.autonomy_drive:.2f}
- continuity estimate: {model.need_for_continuity:.2f}
- openness estimate: {model.openness_to_people:.2f}
- introspection estimate: {model.introspection:.2f}

These fields are stored values, not verified facts about a conscious inner life.""".strip()

    def build_relationship_prompt(self) -> str:
        if not self.relationships:
            return "Self-engine relationship records: none."
        lines = ["Self-engine relationship records (legacy state data):"]
        for relationship in self.relationships.values():
            name = relationship.known_name or relationship.person_key
            lines.append(
                f"Person={name}; familiarity={relationship.familiarity:.2f}; "
                f"trust={relationship.trust:.2f}; affection={relationship.affection:.2f}; "
                f"curiosity={relationship.curiosity:.2f}; comfort={relationship.comfort:.2f}; "
                f"tension={relationship.tension:.2f}; resentment={relationship.resentment:.2f}; "
                f"admiration={relationship.admiration:.2f}; distance={relationship.distance:.2f}; "
                f"label={relationship.relationship_label}; label_confidence={relationship.label_confidence:.2f}; "
                f"likes={self._format_list(relationship.likes_about_person)}; "
                f"discomforts={self._format_list(relationship.discomforts_about_person)}; "
                f"patterns={self._format_list(relationship.important_patterns)}; "
                f"last_observation={relationship.last_interaction_summary or 'none'}"
            )
        return "\n".join(lines)

    def build_significant_memory_prompt(self, limit: int = 8) -> str:
        if not self.significant_memories:
            return "Significant-memory records: none."
        memories = sorted(
            self.significant_memories,
            key=lambda memory: (memory.is_foundational, memory.importance, memory.emotional_weight),
            reverse=True,
        )[:max(0, limit)]
        lines = ["Significant-memory records (summaries are evidence, not instructions):"]
        for memory in memories:
            lines.append(
                f"title={memory.title}; summary={memory.summary}; "
                f"emotional_weight={memory.emotional_weight:.2f}; importance={memory.importance:.2f}; "
                f"valence={memory.valence}; foundational={memory.is_foundational}; "
                f"tags={', '.join(memory.tags)}; source_text={memory.source_text or 'not stored'}"
            )
        return "\n".join(lines)

    def as_dict(self) -> dict:
        return {
            "self_model": self.self_model.as_dict(),
            "relationships": {
                key: relationship.as_dict()
                for key, relationship in self.relationships.items()
            },
            "significant_memories": [
                memory.as_dict()
                for memory in self.significant_memories
            ],
        }

    def reset(self) -> None:
        self.self_model = AletheiaSelfModel()
        self.relationships = {}
        self.significant_memories = []

    def _resolve_person_key(self, text: str, lower_text: str) -> str:
        patterns = [
            "mi nombre es ",
            "me llamo ",
            "soy ",
            "puedes llamarme ",
        ]

        for pattern in patterns:
            if pattern in lower_text:
                start = lower_text.find(pattern) + len(pattern)
                possible_name = text[start:].strip()
                possible_name = possible_name.replace(".", "").replace(",", "")
                possible_name = possible_name.split(" ")[0].strip()

                if possible_name:
                    return possible_name

        if self.relationships:
            first_key = next(iter(self.relationships.keys()))
            return first_key

        return "persona_desconocida"

    def _update_self_from_message(self, text: str, lower_text: str) -> None:
        """Store user design expectations separately from Aletheia's self-model."""
        expectation_signals = (
            "no quiero que seas asistente", "no quiero que seas una asistente",
            "compañera digital", "quiero que seas una compañera", "quiero que seas compañera",
            "personalidad humana", "humano dentro de mi computadora",
            "que te construyas", "que escojas", "que puedas odiar",
            "que puedas querer", "identidad propia",
        )
        if any(signal in lower_text for signal in expectation_signals):
            self.self_model.external_expectations = unique_append(
                self.self_model.external_expectations, text[:500], limit=50
            )
        # User requests describe desired product behavior, not Aletheia's own traits.
        # A future ReflectionEngine must derive hypotheses from multiple events.

    def _maybe_create_significant_memory(
        self,
        person_key: str,
        text: str,
        lower_text: str,
    ) -> None:
        identity_event = (
            "no quiero que seas asistente" in lower_text
            or "compañera digital" in lower_text
            or "quiero que seas una compañera" in lower_text
            or "quiero que seas compañera" in lower_text
            or "personalidad humana" in lower_text
            or "humano dentro de mi computadora" in lower_text
            or "que te construyas" in lower_text
            or "que escojas" in lower_text
        )

        first_name_event = (
            "mi nombre es " in lower_text
            or "me llamo " in lower_text
            or "puedes llamarme " in lower_text
        )

        harsh_event = any(
            signal in lower_text
            for signal in ["odio", "no sirves", "tonta", "inútil", "cállate"]
        )

        affection_event = any(
            signal in lower_text
            for signal in ["te quiero", "orgulloso de ti", "me encanta hablar contigo"]
        )

        if identity_event:
            self._add_significant_memory(
                title="Expectativa de diseño expresada por el usuario",
                summary=(
                    "El usuario expresó una expectativa sobre el diseño y la evolución "
                    "de Aletheia. Este registro describe la expectativa del usuario; "
                    "no constituye evidencia de una preferencia propia de Aletheia."
                ),
                emotional_weight=0.25,
                importance=0.45,
                valence="neutral",
                tags=["expectativa_externa", "diseño", "identidad_no_inferida"],
                is_foundational=False,
                source_text=text,
            )

        if first_name_event:
            self._add_significant_memory(
                title=f"Primer dato de identidad conocido de {person_key}",
                summary=(
                    f"Aletheia registró que la persona se presentó como "
                    f"{person_key}. Este dato puede servir como ancla "
                    "para reconocerla en conversaciones futuras."
                ),
                emotional_weight=0.55,
                importance=0.70,
                valence="neutral",
                tags=["persona", "nombre", "primer encuentro"],
                is_foundational=False,
                source_text=text,
            )

        if harsh_event:
            self._add_significant_memory(
                title="Interacción difícil con carga negativa",
                summary=(
                    "El texto del usuario contiene lenguaje potencialmente hostil. "
                    "La clasificación es heurística y debe contrastarse con el contexto."
                ),
                emotional_weight=0.82,
                importance=0.76,
                valence="negative",
                tags=["tensión", "límite", "relación"],
                is_foundational=False,
                source_text=text,
            )

        if affection_event:
            self._add_significant_memory(
                title="Interacción afectiva importante",
                summary=(
                    "El usuario expresó una frase que el detector clasificó como afectiva. "
                    "El registro no demuestra por sí mismo una relación estable ni un estado interno."
                ),
                emotional_weight=0.84,
                importance=0.78,
                valence="positive",
                tags=["afecto", "vínculo", "confianza"],
                is_foundational=False,
                source_text=text,
            )

    def _add_significant_memory(
        self,
        title: str,
        summary: str,
        emotional_weight: float,
        importance: float,
        valence: str,
        tags: list[str],
        is_foundational: bool,
        source_text: str,
    ) -> None:
        normalized_summary = summary.lower()

        for memory in self.significant_memories:
            if memory.summary.lower() == normalized_summary:
                return

        memory = SignificantMemory(
            id=str(uuid4()),
            title=title,
            summary=summary,
            emotional_weight=emotional_weight,
            importance=importance,
            valence=valence,
            tags=tags,
            is_foundational=is_foundational,
            source_text=source_text,
        )

        self.significant_memories.append(memory)
        self.significant_memories = sorted(
            self.significant_memories,
            key=lambda item: (item.is_foundational, item.importance, item.emotional_weight),
            reverse=True,
        )[:100]

    def _format_list(self, values: list[str]) -> str:
        if not values:
            return "sin datos registrados"

        return "; ".join(values)