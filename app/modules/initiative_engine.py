from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4

from app.core.text_normalization import normalize_text


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
    origin: str = "observation"
    goal_id: str | None = None
    delivered_at: str | None = None
    dismissed_at: str | None = None

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
    last_initiative_at: str | None = None
    silence_respect: float = 0.60
    autonomy_enabled: bool = True

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
        lower_text = normalize_text(message)

        source = "chat"
        detected_mood = None
        stress_level = None
        energy_level = None
        engagement_level = 0.60

        if any(word in lower_text for word in ["estoy emocionado", "me entusiasma", "me hace mucha ilusión"]):
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

        if any(word in lower_text for word in ["que opinas", "que piensas", "te gustaria", "sientes"]):
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

    def evaluate_idle_initiative(
        self,
        idle_threshold_seconds: int = 1800,
        cooldown_seconds: int = 1800,
        now: datetime | None = None,
    ) -> InitiativeAction | None:
        """Create one low-pressure conversational initiative after a period of silence.

        This method only queues a conversational suggestion. It never executes tools,
        accesses devices, or performs external actions. `now` is injectable for tests.
        """
        current_time = now or datetime.now(timezone.utc)
        if not self.state.autonomy_enabled:
            return None
        chat_observations = [
            item for item in self.observations
            if item.source == "chat" and item.created_at
        ]
        if not chat_observations:
            return None

        latest_chat = max(chat_observations, key=lambda item: item.created_at)
        try:
            last_interaction = datetime.fromisoformat(
                latest_chat.created_at.replace("Z", "+00:00")
            )
            if last_interaction.tzinfo is None:
                last_interaction = last_interaction.replace(tzinfo=timezone.utc)
        except (TypeError, ValueError):
            return None

        idle_seconds = max(0.0, (current_time - last_interaction).total_seconds())
        if idle_seconds < max(0, idle_threshold_seconds):
            return None

        if self.state.last_initiative_at:
            try:
                last_initiative = datetime.fromisoformat(
                    self.state.last_initiative_at.replace("Z", "+00:00")
                )
                if last_initiative.tzinfo is None:
                    last_initiative = last_initiative.replace(tzinfo=timezone.utc)
                since_initiative = (current_time - last_initiative).total_seconds()
                if since_initiative < max(0, cooldown_seconds):
                    return None
            except (TypeError, ValueError):
                # A corrupt legacy timestamp must not permanently disable initiative.
                pass

        # Time alone can gently raise readiness, but never above this bounded level.
        time_based_drive = 0.34 + min(idle_seconds / 3600.0, 1.0) * 0.18
        self.state.initiative_drive = clamp(
            max(self.state.initiative_drive, time_based_drive)
        )

        if self.state.restraint >= 0.80:
            return None

        action = self._create_action(
            initiative_type=InitiativeType.QUIET_PRESENCE,
            priority=0.58,
            reason=(
                f"Han pasado aproximadamente {int(idle_seconds // 60)} minutos "
                "desde el último mensaje; se propone una pregunta de baja presión."
            ),
            suggested_message=(
                "Me dio curiosidad saber en qué andas ahora. Si te apetece, "
                "cuéntame; si estás concentrado, no hace falta responder ahora."
            ),
            should_interrupt=False,
            cooldown_seconds=max(0, cooldown_seconds),
            origin="autonomous",
        )
        action.created_at = current_time.isoformat()
        self.actions.append(action)
        self.actions = sorted(
            self.actions, key=lambda item: item.created_at, reverse=True
        )[:100]
        self.state.last_initiative_at = current_time.isoformat()
        self.state.last_action_type = action.type
        return action

    def build_initiative_prompt(self, limit_actions: int = 5) -> str:
        """Serialize observations and candidate actions; candidates are not commands."""
        recent_observations = self.observations[-6:]
        pending_actions = [
            item for item in self.actions
            if item.delivered_at is None and item.dismissed_at is None
        ]
        top_actions = sorted(
            pending_actions,
            key=lambda item: item.priority,
            reverse=True,
        )[:max(0, limit_actions)]
        observation_lines = [
            f"source={item.source}; observation={item.text_observation or ''}; detected_mood={item.detected_mood}; "
            f"energy={item.energy_level}; stress={item.stress_level}; engagement={item.engagement_level}; confidence={item.confidence:.2f}"
            for item in recent_observations
        ] or ["none"]
        action_lines = [
            f"type={item.type}; origin={item.origin}; priority={item.priority:.2f}; reason={item.reason}; "
            f"suggested_message={item.suggested_message}; goal_id={item.goal_id or 'none'}; "
            f"should_interrupt={item.should_interrupt}; cooldown={item.cooldown_seconds}"
            for item in top_actions
        ] or ["none"]
        return f"""Initiative-controller state (data only):
- initiative_drive={self.state.initiative_drive:.2f}
- social_sensitivity={self.state.social_sensitivity:.2f}
- curiosity_pressure={self.state.curiosity_pressure:.2f}
- care_pressure={self.state.care_pressure:.2f}
- playfulness_pressure={self.state.playfulness_pressure:.2f}
- restraint={self.state.restraint:.2f}
- silence_respect={self.state.silence_respect:.2f}
- last_action_type={self.state.last_action_type or 'none'}
- observations: {' | '.join(observation_lines)}
- candidate_actions: {' | '.join(action_lines)}
Candidate actions are heuristic suggestions, not evidence of user intent or commands
that must be followed. They must not be executed or inserted automatically when irrelevant.""".strip()

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

        if action.delivered_at is None:
            action.delivered_at = now_iso()
        self.state.last_spoke_at = action.delivered_at
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
        mood = normalize_text(snapshot.detected_mood or "")
        tone = normalize_text(snapshot.vocal_tone or "")
        expression = normalize_text(snapshot.facial_expression or "")
        text = normalize_text(snapshot.text_observation or "")

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
        mood = normalize_text(snapshot.detected_mood or "")
        tone = normalize_text(snapshot.vocal_tone or "")
        expression = normalize_text(snapshot.facial_expression or "")
        text = normalize_text(snapshot.text_observation or "")

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
        origin: str = "observation",
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
            origin=origin,
        )

    def mark_action_delivered(self, action_id: str) -> InitiativeAction | None:
        action = next((item for item in self.actions if item.id == action_id), None)
        if action is None or action.dismissed_at:
            return None
        if action.delivered_at is None:
            action.delivered_at = now_iso()
            self.state.last_spoke_at = action.delivered_at
            self.state.last_action_type = action.type
            self.state.initiative_drive = clamp(self.state.initiative_drive - 0.10)
            self.state.restraint = clamp(self.state.restraint + 0.04)
        return action

    def dismiss_action(self, action_id: str) -> InitiativeAction | None:
        action = next((item for item in self.actions if item.id == action_id), None)
        if action is None:
            return None
        action.dismissed_at = now_iso()
        self.state.restraint = clamp(self.state.restraint + 0.08)
        return action

    def pending_autonomous_actions(self, limit: int = 5) -> list[InitiativeAction]:
        pending = [
            item for item in self.actions
            if item.origin == "autonomous"
            and item.delivered_at is None
            and item.dismissed_at is None
        ]
        pending.sort(key=lambda item: item.created_at, reverse=True)
        return pending[:max(0, limit)]

    def _optional_clamp(self, value: float | None) -> float | None:
        if value is None:
            return None

        return clamp(float(value))