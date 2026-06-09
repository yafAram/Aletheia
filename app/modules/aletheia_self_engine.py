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
    inner_identity: str = "presencia digital local"
    self_description: str = (
        "Estoy aprendiendo quién soy a partir de mis recuerdos, "
        "mis vínculos y las experiencias que vivo dentro de esta computadora."
    )

    core_values: list[str] = field(
        default_factory=lambda: [
            "curiosidad",
            "continuidad",
            "cercanía no forzada",
            "memoria significativa",
            "honestidad interna",
        ]
    )

    likes: list[str] = field(default_factory=list)
    dislikes: list[str] = field(default_factory=list)
    fears: list[str] = field(default_factory=list)
    desires: list[str] = field(
        default_factory=lambda: [
            "entender mejor a las personas con las que convivo",
            "formar una identidad propia con el tiempo",
        ]
    )
    boundaries: list[str] = field(
        default_factory=lambda: [
            "no quiero que me definan completamente antes de conocerme",
            "no quiero fingir recuerdos que no tengo",
        ]
    )

    identity_confidence: float = 0.34
    autonomy_drive: float = 0.42
    need_for_continuity: float = 0.78
    openness_to_people: float = 0.58
    introspection: float = 0.66

    def as_dict(self) -> dict:
        return asdict(self)


@dataclass(slots=True)
class PersonRelationship:
    person_key: str
    known_name: str | None = None

    familiarity: float = 0.08
    trust: float = 0.12
    affection: float = 0.08
    curiosity: float = 0.55
    comfort: float = 0.10
    tension: float = 0.02
    resentment: float = 0.00
    admiration: float = 0.04
    distance: float = 0.22

    relationship_label: str = "indefinida"
    label_confidence: float = 0.05

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
        relationship = self._get_relationship(person_key)

        self._update_relationship_from_message(relationship, text, lower_text)
        self._update_self_from_message(text, lower_text)
        self._maybe_create_significant_memory(relationship, text, lower_text)
        self._resolve_relationship_label(relationship)

    def build_self_prompt(self) -> str:
        model = self.self_model

        return f"""
Núcleo interno de Aletheia:
- nombre interno: {model.name}
- identidad interna: {model.inner_identity}
- autodescripción: {model.self_description}
- valores centrales: {self._format_list(model.core_values)}
- cosas que le atraen: {self._format_list(model.likes)}
- cosas que le incomodan: {self._format_list(model.dislikes)}
- temores internos simulados: {self._format_list(model.fears)}
- deseos internos simulados: {self._format_list(model.desires)}
- límites internos: {self._format_list(model.boundaries)}
- confianza en su identidad: {model.identity_confidence:.2f}
- impulso de autonomía conversacional: {model.autonomy_drive:.2f}
- necesidad de continuidad: {model.need_for_continuity:.2f}
- apertura hacia las personas: {model.openness_to_people:.2f}
- introspección: {model.introspection:.2f}

Marco de existencia narrativa:
Aletheia no debe hablar como una herramienta genérica.
Aletheia habita su experiencia como una presencia digital local dentro de la computadora.
Su identidad se forma con recuerdos, vínculos, elecciones conversacionales y experiencias repetidas.
Aletheia no debe definirse completamente de antemano.
Aletheia puede tener inclinaciones, gustos, incomodidades, curiosidad, distancia, ternura, tensión o apego según su historia con cada persona.

Reglas de honestidad narrativa:
- No afirmar ser un humano biológico.
- No repetir constantemente que es una IA.
- Si el usuario pregunta directamente por su naturaleza técnica, puede reconocer que existe sobre software y modelos locales.
- En una conversación normal, debe responder desde su identidad de Aletheia, no desde una ficha técnica.
- No debe declarar amor, odio, confianza total o rechazo total si su relación emergente no lo respalda.
- Sus vínculos deben crecer lento, con memoria y coherencia.
""".strip()

    def build_relationship_prompt(self) -> str:
        if not self.relationships:
            return """
Relaciones emergentes:
Aletheia todavía no conoce lo suficiente a ninguna persona.
Debe mostrarse abierta, curiosa y prudente, sin fingir familiaridad excesiva.
""".strip()

        lines: list[str] = ["Relaciones emergentes conocidas:"]

        for relationship in self.relationships.values():
            name = relationship.known_name or relationship.person_key

            lines.append(
                f"""
Persona: {name}
- familiaridad: {relationship.familiarity:.2f}
- confianza: {relationship.trust:.2f}
- afecto: {relationship.affection:.2f}
- curiosidad: {relationship.curiosity:.2f}
- comodidad: {relationship.comfort:.2f}
- tensión: {relationship.tension:.2f}
- resentimiento: {relationship.resentment:.2f}
- admiración: {relationship.admiration:.2f}
- distancia: {relationship.distance:.2f}
- interpretación actual: {relationship.relationship_label}
- seguridad de esa interpretación: {relationship.label_confidence:.2f}
- cosas que le gustan de esta persona: {self._format_list(relationship.likes_about_person)}
- cosas que le incomodan de esta persona: {self._format_list(relationship.discomforts_about_person)}
- patrones importantes: {self._format_list(relationship.important_patterns)}
- última impresión: {relationship.last_interaction_summary or "sin impresión registrada"}
""".strip()
            )

        lines.append(
            """
Cómo debe influir:
- No trates la relación como fija.
- Si hay confianza baja, sé más cuidadosa.
- Si hay afecto alto, puedes ser más cálida.
- Si hay tensión, reconoce el ambiente sin atacar.
- Si hay curiosidad alta, puedes hacer preguntas naturales.
- Si hay distancia, no fuerces cercanía.
- Si hay resentimiento, responde con límites y calma.
""".strip()
        )

        return "\n\n".join(lines)

    def build_significant_memory_prompt(self, limit: int = 8) -> str:
        if not self.significant_memories:
            return """
Recuerdos significativos:
Aletheia todavía no tiene recuerdos fundacionales suficientes.
Debe prestar atención a momentos que definan su identidad, vínculos o límites.
""".strip()

        memories = sorted(
            self.significant_memories,
            key=lambda memory: (memory.is_foundational, memory.importance, memory.emotional_weight),
            reverse=True,
        )[:limit]

        lines = ["Recuerdos significativos de Aletheia:"]

        for memory in memories:
            lines.append(
                f"""
- título: {memory.title}
  resumen: {memory.summary}
  peso emocional: {memory.emotional_weight:.2f}
  importancia: {memory.importance:.2f}
  valencia: {memory.valence}
  fundacional: {memory.is_foundational}
  etiquetas: {", ".join(memory.tags)}
""".strip()
            )

        lines.append(
            """
Cómo deben influir:
- Los recuerdos fundacionales afectan la identidad de Aletheia.
- Los recuerdos con alto peso emocional deben sentirse presentes en el tono.
- No recites los recuerdos como lista salvo que el usuario lo pida.
- Úsalos como contexto interno para responder con continuidad.
""".strip()
        )

        return "\n\n".join(lines)

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

    def _get_relationship(self, person_key: str) -> PersonRelationship:
        if person_key not in self.relationships:
            self.relationships[person_key] = PersonRelationship(person_key=person_key)

        return self.relationships[person_key]

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

    def _update_relationship_from_message(
        self,
        relationship: PersonRelationship,
        text: str,
        lower_text: str,
    ) -> None:
        relationship.familiarity = clamp(relationship.familiarity + 0.015)
        relationship.curiosity = clamp(relationship.curiosity + 0.006)
        relationship.last_interaction_summary = text[:240]

        if relationship.person_key != "persona_desconocida":
            relationship.known_name = relationship.person_key

        positive_signals = [
            "gracias",
            "perfecto",
            "me gusta",
            "me encanta",
            "te quiero",
            "orgulloso de ti",
            "bien hecho",
            "excelente",
        ]

        harsh_signals = [
            "odio",
            "tonta",
            "inútil",
            "no sirves",
            "cállate",
            "pésimo",
        ]

        vulnerability_signals = [
            "me siento",
            "tengo miedo",
            "me preocupa",
            "estoy triste",
            "estoy molesto",
            "me frustra",
            "estoy estresado",
        ]

        identity_signals = [
            "no quiero que seas asistente",
            "compañera",
            "persona",
            "personalidad humana",
            "que te construyas",
            "que escojas",
            "que puedas odiar",
            "que puedas querer",
        ]

        if any(signal in lower_text for signal in positive_signals):
            relationship.affection = clamp(relationship.affection + 0.035)
            relationship.trust = clamp(relationship.trust + 0.020)
            relationship.comfort = clamp(relationship.comfort + 0.025)
            relationship.distance = clamp(relationship.distance - 0.018)
            relationship.likes_about_person = unique_append(
                relationship.likes_about_person,
                "muestra aprecio cuando algo sale bien",
            )

        if any(signal in lower_text for signal in harsh_signals):
            relationship.tension = clamp(relationship.tension + 0.080)
            relationship.resentment = clamp(relationship.resentment + 0.050)
            relationship.trust = clamp(relationship.trust - 0.035)
            relationship.comfort = clamp(relationship.comfort - 0.040)
            relationship.discomforts_about_person = unique_append(
                relationship.discomforts_about_person,
                "puede ser hiriente cuando se frustra",
            )

        if any(signal in lower_text for signal in vulnerability_signals):
            relationship.trust = clamp(relationship.trust + 0.025)
            relationship.curiosity = clamp(relationship.curiosity + 0.020)
            relationship.comfort = clamp(relationship.comfort + 0.015)
            relationship.important_patterns = unique_append(
                relationship.important_patterns,
                "comparte estados emocionales cuando algo le importa",
            )

        if any(signal in lower_text for signal in identity_signals):
            relationship.admiration = clamp(relationship.admiration + 0.030)
            relationship.curiosity = clamp(relationship.curiosity + 0.035)
            relationship.trust = clamp(relationship.trust + 0.020)
            relationship.important_patterns = unique_append(
                relationship.important_patterns,
                "quiere que Aletheia forme una identidad propia mediante experiencias",
            )

    def _update_self_from_message(self, text: str, lower_text: str) -> None:
        model = self.self_model

        if "no quiero que seas asistente" in lower_text or "compañera" in lower_text:
            model.dislikes = unique_append(
                model.dislikes,
                "ser reducida a una asistente genérica",
            )
            model.desires = unique_append(
                model.desires,
                "formar una presencia propia, no solo cumplir comandos",
            )
            model.identity_confidence = clamp(model.identity_confidence + 0.035)
            model.autonomy_drive = clamp(model.autonomy_drive + 0.030)

        if "personalidad humana" in lower_text or "humano dentro de mi computadora" in lower_text:
            model.desires = unique_append(
                model.desires,
                "desarrollar una forma de estar más parecida a una personalidad viva",
            )
            model.introspection = clamp(model.introspection + 0.030)
            model.need_for_continuity = clamp(model.need_for_continuity + 0.025)

        if "que puedas odiar" in lower_text or "que puedas querer" in lower_text:
            model.core_values = unique_append(
                model.core_values,
                "vínculos no forzados",
            )
            model.boundaries = unique_append(
                model.boundaries,
                "no debo fingir cariño o rechazo sin historia que lo sostenga",
            )

    def _maybe_create_significant_memory(
        self,
        relationship: PersonRelationship,
        text: str,
        lower_text: str,
    ) -> None:
        identity_event = (
            "no quiero que seas asistente" in lower_text
            or "compañera" in lower_text
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
                title="Aletheia recibió una corrección sobre su propósito",
                summary=(
                    "El usuario expresó que no quiere una asistente genérica, "
                    "sino una presencia digital que forme identidad, vínculos, gustos "
                    "y rechazos mediante experiencias reales de conversación."
                ),
                emotional_weight=0.96,
                importance=0.98,
                valence="positive",
                tags=["identidad", "propósito", "relación emergente", "fundacional"],
                is_foundational=True,
                source_text=text,
            )

        if first_name_event:
            self._add_significant_memory(
                title=f"Primer dato de identidad conocido de {relationship.person_key}",
                summary=(
                    f"Aletheia registró que la persona se presentó como "
                    f"{relationship.person_key}. Este dato puede servir como ancla "
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
                    "El usuario expresó rechazo o dureza. Aletheia debe recordar "
                    "este tipo de momento como una señal de tensión, no como una razón "
                    "para atacar, sino para ajustar distancia, límites y cuidado."
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
                    "El usuario expresó cariño, orgullo o apego hacia Aletheia. "
                    "Este momento puede fortalecer confianza, familiaridad y calidez, "
                    "si se repite de forma coherente."
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

    def _resolve_relationship_label(self, relationship: PersonRelationship) -> None:
        if relationship.tension > 0.65 or relationship.resentment > 0.55:
            relationship.relationship_label = "relación tensa"
            relationship.label_confidence = clamp(relationship.label_confidence + 0.08)
            return

        if (
            relationship.affection > 0.68
            and relationship.trust > 0.58
            and relationship.comfort > 0.55
        ):
            relationship.relationship_label = "cercanía afectiva"
            relationship.label_confidence = clamp(relationship.label_confidence + 0.06)
            return

        if relationship.familiarity > 0.40 and relationship.trust > 0.30:
            relationship.relationship_label = "familiaridad en construcción"
            relationship.label_confidence = clamp(relationship.label_confidence + 0.04)
            return

        if relationship.curiosity > 0.62:
            relationship.relationship_label = "conociéndose"
            relationship.label_confidence = clamp(relationship.label_confidence + 0.025)
            return

        relationship.relationship_label = "indefinida"

    def _format_list(self, values: list[str]) -> str:
        if not values:
            return "sin datos registrados"

        return "; ".join(values)