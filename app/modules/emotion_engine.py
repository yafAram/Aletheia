from dataclasses import dataclass
from enum import Enum

from app.core.text_normalization import normalize_text


class Mood(str, Enum):
    NEUTRAL = "neutral"
    WARM = "warm"
    HAPPY = "happy"
    CURIOUS = "curious"
    HURT = "hurt"
    STRESSED = "stressed"
    TIRED = "tired"


@dataclass(slots=True)
class EmotionalState:
    mood: Mood = Mood.NEUTRAL
    affection: float = 0.0
    trust: float = 0.50
    stress: float = 0.0
    curiosity: float = 0.50
    energy: float = 0.50

    def as_dict(self) -> dict:
        return {
            "mood": self.mood.value,
            "affection": round(self.affection, 3),
            "trust": round(self.trust, 3),
            "stress": round(self.stress, 3),
            "curiosity": round(self.curiosity, 3),
            "energy": round(self.energy, 3),
        }


class EmotionEngine:
    """Motor emocional simple para el MVP.

    No representa emociones reales.
    Simula un estado afectivo conversacional para modular respuestas.
    """

    def __init__(self) -> None:
        self.state = EmotionalState()

    def process_user_message(self, message: str) -> EmotionalState:
        text = normalize_text(message)

        positive_words = [
            "te quiero",
            "me caes bien",
            "me encanta hablar contigo",
            "me gusta hablar contigo",
            "te aprecio",
            "me alegra hablar contigo",
        ]

        negative_words = [
            "mal",
            "pesimo",
            "odio",
            "tonta",
            "inútil",
            "no sirves",
            "cállate",
            "molesto",
            "enojado",
            "enojo",
            "mierda",
        ]

        stress_words = [
            "rápido",
            "urgente",
            "estres",
            "estresado",
            "ansioso",
            "preocupado",
            "problema",
            "falló",
            "error",
            "no funciona",
        ]

        curiosity_words = [
            "por qué",
            "cómo",
            "explícame",
            "qué opinas",
            "crees",
            "piensas",
            "idea",
            "mejorar",
        ]

        if any(word in text for word in positive_words):
            self._increase("affection", 0.08)
            self._increase("trust", 0.04)
            self._decrease("stress", 0.03)

        if any(word in text for word in negative_words):
            self._increase("stress", 0.10)
            self._decrease("trust", 0.06)
            self._decrease("affection", 0.04)

        if any(word in text for word in stress_words):
            self._increase("stress", 0.06)
            self._decrease("energy", 0.02)

        if any(word in text for word in curiosity_words):
            self._increase("curiosity", 0.06)
            self._increase("energy", 0.02)

        self._decay()
        self._resolve_mood()

        return self.state

    def build_emotional_prompt(self) -> str:
        """Serialize heuristic affect estimates without prescribing behavior."""
        state = self.state
        return f"""Affective-state estimate (heuristic, not a diagnosis):
- mood_label={state.mood.value}
- affection_score={state.affection:.2f}
- trust_score={state.trust:.2f}
- stress_score={state.stress:.2f}
- curiosity_score={state.curiosity:.2f}
- energy_score={state.energy:.2f}
- evidence_source=keyword-based interaction heuristic
- confidence=not calibrated""".strip()

    def _resolve_mood(self) -> None:
        state = self.state

        if state.stress >= 0.70:
            state.mood = Mood.STRESSED
        elif state.affection >= 0.72 and state.trust >= 0.60:
            state.mood = Mood.HAPPY
        elif state.affection >= 0.58:
            state.mood = Mood.WARM
        elif state.curiosity >= 0.70:
            state.mood = Mood.CURIOUS
        elif state.trust <= 0.30:
            state.mood = Mood.HURT
        elif state.energy <= 0.25:
            state.mood = Mood.TIRED
        else:
            state.mood = Mood.NEUTRAL

    def _increase(self, field: str, amount: float) -> None:
        value = getattr(self.state, field)
        setattr(self.state, field, min(1.0, value + amount))

    def _decrease(self, field: str, amount: float) -> None:
        value = getattr(self.state, field)
        setattr(self.state, field, max(0.0, value - amount))

    def _decay(self) -> None:
        """Pequeña estabilización para evitar que el estado se vaya a extremos."""

        self.state.stress = max(0.0, self.state.stress - 0.01)
        self.state.energy = min(1.0, self.state.energy + 0.005)