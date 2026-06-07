from dataclasses import dataclass
from enum import Enum


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
    mood: Mood = Mood.WARM
    affection: float = 0.50
    trust: float = 0.50
    stress: float = 0.10
    curiosity: float = 0.45
    energy: float = 0.70

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
        text = message.lower()

        positive_words = [
            "gracias",
            "perfecto",
            "excelente",
            "bien hecho",
            "me gusta",
            "te quiero",
            "eres genial",
            "muy bien",
            "bonita",
            "increíble",
            "felicidades",
        ]

        negative_words = [
            "mal",
            "pésimo",
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
            "estrés",
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
        state = self.state

        return f"""
Estado emocional simulado de Aletheia:
- ánimo actual: {state.mood.value}
- afecto hacia el usuario: {state.affection:.2f}
- confianza: {state.trust:.2f}
- estrés: {state.stress:.2f}
- curiosidad: {state.curiosity:.2f}
- energía: {state.energy:.2f}

Cómo debe influir:
- Si el afecto es alto, responde con más calidez y cercanía.
- Si la confianza es baja, responde con más cautela.
- Si el estrés es alto, responde más breve y busca calmar la situación.
- Si la curiosidad es alta, haz preguntas naturales y muestra interés.
- Nunca digas que tienes emociones reales. Puedes expresar el estado como una vivencia simulada o una reacción conversacional.
""".strip()

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