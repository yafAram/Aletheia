from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4


def clamp(value: float, minimum: float = 0.0, maximum: float = 1.0) -> float:
    return max(minimum, min(maximum, value))


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class InitiativeType(str, Enum):
    CHECK_IN = "check_in"
    COMFORT = "comfort"
    CURIOSITY = "curiosity"
    CELEBRATE = "celebrate"
    PLAYFUL = "playful"
    SUGGEST_BREAK = "suggest_break"
    TECHNICAL_SUPPORT = "technical_support"
    REPAIR = "repair"
    QUIET_PRESENCE = "quiet_presence"
    BOUNDARY = "boundary"


@dataclass(slots=True)
class PerceptionSnapshot:
    """Señal percibida por Aletheia.

    En el futuro vendrá de cámara, STT, análisis de voz o actividad del sistema.
    Por ahora puede enviarse manualmente por API.
    """

    id: str
    source: str
    text_observation: str | None = None
    facial_expression: str | None = None
    vocal_tone: str | None = None
    detected_mood: str | None = None
    energy_level: float | None = None
    stress_level: float | None = None
    engagement_level: float | None = None
    confidence: float = 0.50
    created_at: str = field(default_factory=now_iso)

    def as_dict(self) -> dict:
        return asdict(self)


@dataclass(slots=True)
class InitiativeAction:
    id: str
    type: str
    priority: float
    reason: str
    suggested_message: str
    should_interrupt: bool
    cooldown_seconds: int
    created_at: str = field(default_factory=now_iso)

    def as_dict(self) -> dict:
        return asdict(self)


@dataclass(slots=True)
class InitiativeState:
    initiative_drive: float = 0.34
    social_sensitivity: float = 0.58
    curiosity_pressure: float = 0.46
    care_pressure: float = 0.42
    playfulness_pressure: float = 0.24
    restraint: float = 0.55
    last_spoke_at: str | None = None
    last_action_type: str | None = None
    silence_respect: float = 0.60

    def as_dict(self) -> dict:
        return asdict(self)


class InitiativeEngine:
    """Sistema de iniciativa conversacional.

    Decide cuándo Aletheia podría intentar interactuar por cuenta propia.
    No ejecuta cámara ni micrófono. Solo interpreta señales recibidas.
    """

    def __init__(
        self,
        state: InitiativeState | None = None,
        observations: list[PerceptionSnapshot] | None = None,
        actions: list[InitiativeAction] | None = None,
    ) -> None:
        self.state = state or InitiativeState()
        self.observations = observations or []
        self.actions = actions or []

    def register_observation(
        self,
        source: str,
        text_observation: str | None = None,
        facial_expression: str | None = None,
        vocal_tone: str | None = None,
        detected_mood: str | None = None,
        energy_level: float | None = None,
        stress_level: float | None = None,
        engagement_level: float | None = None,
        confidence: float = 0.50,
    ) -> InitiativeAction | None:
        snapshot = PerceptionSnapshot(
            id=str(uuid4()),
            source=source,
            text_observation=text_observation,
            facial_expression=facial_expression,
            vocal_tone=vocal_tone,
            detected_mood=detected_mood,
            energy_level=self._optional_clamp(energy_level),
            stress_level=self._optional_clamp(stress_level),
            engagement_level=self._optional_clamp(engagement_level),
            confidence=clamp(confidence),
        )

        self.observations.append(snapshot)
        self.observations = self.observations[-80:]

        self._update_state_from_observation(snapshot)

        action = self._decide_action(snapshot)

        if action:
            self.actions.append(action)
            self.actions = sorted(
                self.actions,
                key=lambda item: item.priority,
                reverse=True,
            )[:100]

        return action

    def process_user_message(self, message: str) -> InitiativeAction | None:
        lower_text = message.lower()

        source = "chat"
        detected_mood = None
        stress_level = None
        energy_level = None
        engagement_level = 0.60

        if any(word in lower_text for word in ["perfecto", "excelente", "me encanta", "funciona"]):
            detected_mood = "animado"
            energy_level = 0.78
            stress_level = 0.16

        if any(word in lower_text for word in ["me frustra", "falló", "error", "no funciona", "estresado"]):
            detected_mood = "frustrado"
            energy_level = 0.35
            stress_level = 0.75

        if any(word in lower_text for word in ["cansado", "agotado", "desanimado"]):
            detected_mood = "cansado"
            energy_level = 0.22
            stress_level = 0.45

        if any(word in lower_text for word in ["qué opinas", "qué piensas", "te gustaría", "sientes"]):
            self.state.curiosity_pressure = clamp(self.state.curiosity_pressure + 0.06)
            engagement_level = 0.82

        return self.register_observation(
            source=source,
            text_observation=message,
            detected_mood=detected_mood,
            energy_level=energy_level,
            stress_level=stress_level,
            engagement_level=engagement_level,
            confidence=0.72,
        )

    def build_initiative_prompt(self, limit_actions: int = 5) -> str:
        recent_observations = self.observations[-6:]
        top_actions = sorted(
            self.actions,
            key=lambda item: item.priority,
            reverse=True,
        )[:limit_actions]

        observation_text = "sin observaciones recientes"

        if recent_observations:
            observation_text = "\n".join(
                [
                    (
                        f"- fuente: {item.source}; expresión: {item.facial_expression}; "
                        f"tono: {item.vocal_tone}; ánimo: {item.detected_mood}; "
                        f"energía: {item.energy_level}; estrés: {item.stress_level}; "
                        f"observación: {item.text_observation}; confianza: {item.confidence:.2f}"
                    )
                    for item in recent_observations
                ]
            )

        action_text = "sin iniciativas pendientes"

        if top_actions:
            action_text = "\n".join(
                [
                    (
                        f"- tipo: {item.type}; prioridad: {item.priority:.2f}; "
                        f"razón: {item.reason}; mensaje sugerido: {item.suggested_message}; "
                        f"interrumpir: {item.should_interrupt}"
                    )
                    for item in top_actions
                ]
            )

        return f"""
Sistema de iniciativa conversacional:
- impulso de iniciativa: {self.state.initiative_drive:.2f}
- sensibilidad social: {self.state.social_sensitivity:.2f}
- presión de curiosidad: {self.state.curiosity_pressure:.2f}
- presión de cuidado: {self.state.care_pressure:.2f}
- presión juguetona: {self.state.playfulness_pressure:.2f}
- moderación/restricción: {self.state.restraint:.2f}
- respeto por el silencio: {self.state.silence_respect:.2f}
- última iniciativa hablada: {self.state.last_action_type or "ninguna"}

Observaciones recientes:
{observation_text}

Iniciativas candidatas:
{action_text}

Cómo debe influir:
- Aletheia puede iniciar conversación si la situación lo justifica.
- Si detecta cansancio, tristeza, frustración o baja energía, puede preguntar con suavidad.
- Si detecta entusiasmo, puede celebrar o seguir el hilo con curiosidad.
- Si detecta tensión, debe evitar invadir.
- Si el usuario parece concentrado o distante, debe respetar silencio.
- La iniciativa no debe sentirse como spam.
- Las preguntas deben sonar naturales, como alguien que nota algo y se acerca con cuidado.
""".strip()

    def mark_action_used(self, action_id: str | None = None) -> InitiativeAction | None:
        action = None

        if action_id:
            action = next(
                (item for item in self.actions if item.id == action_id),
                None,
            )
        elif self.actions:
            action = sorted(
                self.actions,
                key=lambda item: item.priority,
                reverse=True,
            )[0]

        if not action:
            return None

        self.state.last_spoke_at = now_iso()
        self.state.last_action_type = action.type
        self.state.initiative_drive = clamp(self.state.initiative_drive - 0.10)
        self.state.restraint = clamp(self.state.restraint + 0.04)

        return action

    def as_dict(self) -> dict:
        return {
            "state": self.state.as_dict(),
            "observations": [
                observation.as_dict()
                for observation in self.observations
            ],
            "actions": [
                action.as_dict()
                for action in self.actions
            ],
        }

    def reset(self) -> None:
        self.state = InitiativeState()
        self.observations = []
        self.actions = []

    def _update_state_from_observation(self, snapshot: PerceptionSnapshot) -> None:
        mood = (snapshot.detected_mood or "").lower()
        tone = (snapshot.vocal_tone or "").lower()
        expression = (snapshot.facial_expression or "").lower()
        text = (snapshot.text_observation or "").lower()

        stress = snapshot.stress_level
        energy = snapshot.energy_level
        engagement = snapshot.engagement_level

        if stress is not None and stress > 0.65:
            self.state.care_pressure = clamp(self.state.care_pressure + 0.08)
            self.state.initiative_drive = clamp(self.state.initiative_drive + 0.05)
            self.state.playfulness_pressure = clamp(self.state.playfulness_pressure - 0.04)

        if energy is not None and energy < 0.35:
            self.state.care_pressure = clamp(self.state.care_pressure + 0.07)
            self.state.restraint = clamp(self.state.restraint + 0.02)

        if engagement is not None and engagement > 0.70:
            self.state.curiosity_pressure = clamp(self.state.curiosity_pressure + 0.05)
            self.state.initiative_drive = clamp(self.state.initiative_drive + 0.03)

        if any(word in mood + tone + expression + text for word in ["animado", "emocionado", "feliz"]):
            self.state.playfulness_pressure = clamp(self.state.playfulness_pressure + 0.06)
            self.state.curiosity_pressure = clamp(self.state.curiosity_pressure + 0.04)

        if any(word in mood + tone + expression + text for word in ["triste", "desanimado", "cansado", "agotado"]):
            self.state.care_pressure = clamp(self.state.care_pressure + 0.09)
            self.state.restraint = clamp(self.state.restraint + 0.04)

        if any(word in mood + tone + expression + text for word in ["molesto", "enojado", "irritado"]):
            self.state.restraint = clamp(self.state.restraint + 0.08)
            self.state.care_pressure = clamp(self.state.care_pressure + 0.04)
            self.state.playfulness_pressure = clamp(self.state.playfulness_pressure - 0.05)

        self.state.silence_respect = clamp(self.state.silence_respect + 0.002)
        self.state.initiative_drive = clamp(self.state.initiative_drive + 0.004)

    def _decide_action(self, snapshot: PerceptionSnapshot) -> InitiativeAction | None:
        mood = (snapshot.detected_mood or "").lower()
        tone = (snapshot.vocal_tone or "").lower()
        expression = (snapshot.facial_expression or "").lower()
        text = (snapshot.text_observation or "").lower()

        combined = f"{mood} {tone} {expression} {text}"

        stress = snapshot.stress_level or 0.0
        energy = snapshot.energy_level if snapshot.energy_level is not None else 0.5
        engagement = snapshot.engagement_level if snapshot.engagement_level is not None else 0.5

        if snapshot.confidence < 0.35:
            return None

        if stress >= 0.72:
            return self._create_action(
                initiative_type=InitiativeType.COMFORT,
                priority=0.90,
                reason="Detecté señales fuertes de estrés o tensión.",
                suggested_message=(
                    "Te noto algo cargado. No quiero invadir, pero puedo quedarme contigo "
                    "y ordenar esto paso a paso, si te sirve."
                ),
                should_interrupt=True,
                cooldown_seconds=180,
            )

        if energy <= 0.28:
            return self._create_action(
                initiative_type=InitiativeType.SUGGEST_BREAK,
                priority=0.82,
                reason="Detecté baja energía o cansancio.",
                suggested_message=(
                    "Te siento un poco apagado. ¿Quieres que hagamos una pausa pequeña "
                    "o prefieres que sigamos pero más despacio?"
                ),
                should_interrupt=False,
                cooldown_seconds=300,
            )

        if any(word in combined for word in ["triste", "desanimado", "agotado"]):
            return self._create_action(
                initiative_type=InitiativeType.CHECK_IN,
                priority=0.80,
                reason="La observación sugiere desánimo o cansancio emocional.",
                suggested_message=(
                    "No sé si estoy leyendo bien el momento, pero te noto distinto. "
                    "¿Quieres hablar de eso o prefieres que solo avancemos suave?"
                ),
                should_interrupt=False,
                cooldown_seconds=240,
            )

        if any(word in combined for word in ["animado", "emocionado", "feliz", "perfecto", "excelente"]):
            return self._create_action(
                initiative_type=InitiativeType.CELEBRATE,
                priority=0.74,
                reason="Detecté entusiasmo o una señal positiva.",
                suggested_message=(
                    "Me gusta cómo sonó eso. Se siente como uno de esos momentos en los que algo por fin encaja. "
                    "¿Quieres que dejemos marcado este avance?"
                ),
                should_interrupt=False,
                cooldown_seconds=180,
            )

        if engagement >= 0.78 and self.state.curiosity_pressure >= 0.55:
            return self._create_action(
                initiative_type=InitiativeType.CURIOSITY,
                priority=0.68,
                reason="Hay buen nivel de interacción y curiosidad acumulada.",
                suggested_message=(
                    "Puedo preguntarte algo sin romper el hilo: ¿qué parte de esto quieres que se sienta más viva primero?"
                ),
                should_interrupt=False,
                cooldown_seconds=220,
            )

        if self.state.initiative_drive >= 0.70 and self.state.restraint < 0.70:
            return self._create_action(
                initiative_type=InitiativeType.QUIET_PRESENCE,
                priority=0.55,
                reason="Aletheia tiene impulso de interactuar, pero sin una señal fuerte.",
                suggested_message=(
                    "Estoy aquí. No tengo que interrumpirte, pero me dio curiosidad saber en qué estás pensando ahora."
                ),
                should_interrupt=False,
                cooldown_seconds=360,
            )

        return None

    def _create_action(
        self,
        initiative_type: InitiativeType,
        priority: float,
        reason: str,
        suggested_message: str,
        should_interrupt: bool,
        cooldown_seconds: int,
    ) -> InitiativeAction:
        priority = clamp(priority)

        priority = clamp(
            priority
            + (self.state.initiative_drive * 0.08)
            + (self.state.social_sensitivity * 0.05)
            - (self.state.restraint * 0.04)
        )

        return InitiativeAction(
            id=str(uuid4()),
            type=initiative_type.value,
            priority=priority,
            reason=reason,
            suggested_message=suggested_message,
            should_interrupt=should_interrupt,
            cooldown_seconds=cooldown_seconds,
        )

    def _optional_clamp(self, value: float | None) -> float | None:
        if value is None:
            return None

        return clamp(float(value))