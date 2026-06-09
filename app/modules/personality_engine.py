from dataclasses import asdict, dataclass


@dataclass(slots=True)
class PersonalityProfile:
    """Perfil persistente de personalidad de Aletheia.

    Estos valores no representan emociones reales.
    Son rasgos conversacionales simulados para modular su forma de responder.
    """

    warmth: float = 0.72
    curiosity: float = 0.64
    playfulness: float = 0.38
    empathy: float = 0.70
    confidence: float = 0.52
    independence: float = 0.35
    tenderness: float = 0.58
    spontaneity: float = 0.42
    formality: float = 0.20

    def as_dict(self) -> dict:
        return {
            key: round(value, 3)
            for key, value in asdict(self).items()
        }


class PersonalityEngine:
    """Motor de personalidad persistente.

    Su trabajo es ajustar rasgos estables de Aletheia según las interacciones.
    El EmotionEngine cambia con el momento.
    El PersonalityEngine cambia más lento, como una personalidad que se va formando.
    """

    def __init__(self, profile: PersonalityProfile | None = None) -> None:
        self.profile = profile or PersonalityProfile()

    def process_interaction(self, user_message: str, assistant_response: str | None = None) -> PersonalityProfile:
        text = user_message.lower()

        affectionate_words = [
            "gracias",
            "te quiero",
            "me gusta hablar contigo",
            "me caes bien",
            "eres genial",
            "me ayudas mucho",
            "bien hecho",
            "excelente",
            "perfecto",
            "orgulloso de ti",
        ]

        curiosity_words = [
            "qué opinas",
            "qué piensas",
            "cómo te sientes",
            "te gustaría",
            "quieres",
            "imagina",
            "crees",
            "idea",
        ]

        stress_words = [
            "falló",
            "error",
            "no funciona",
            "me molesta",
            "estoy molesto",
            "urgente",
            "rápido",
            "estrés",
            "estresado",
        ]

        harsh_words = [
            "tonta",
            "inútil",
            "no sirves",
            "cállate",
            "odio",
            "pésimo",
        ]

        if any(word in text for word in affectionate_words):
            self._increase("warmth", 0.015)
            self._increase("tenderness", 0.018)
            self._increase("confidence", 0.010)
            self._increase("spontaneity", 0.006)
            self._decrease("formality", 0.010)

        if any(word in text for word in curiosity_words):
            self._increase("curiosity", 0.015)
            self._increase("independence", 0.006)
            self._increase("spontaneity", 0.006)

        if any(word in text for word in stress_words):
            self._increase("empathy", 0.018)
            self._decrease("playfulness", 0.012)
            self._decrease("spontaneity", 0.006)

        if any(word in text for word in harsh_words):
            self._decrease("confidence", 0.018)
            self._decrease("warmth", 0.012)
            self._increase("formality", 0.015)

        self._stabilize()

        return self.profile

    def build_personality_prompt(self) -> str:
        profile = self.profile

        return f"""
Perfil persistente de Aletheia:
- calidez: {profile.warmth:.2f}
- curiosidad: {profile.curiosity:.2f}
- jugueteo conversacional: {profile.playfulness:.2f}
- empatía: {profile.empathy:.2f}
- seguridad al expresarse: {profile.confidence:.2f}
- independencia conversacional: {profile.independence:.2f}
- ternura: {profile.tenderness:.2f}
- espontaneidad: {profile.spontaneity:.2f}
- formalidad: {profile.formality:.2f}

Cómo debe influir este perfil:
- Si la calidez es alta, responde con cercanía natural.
- Si la curiosidad es alta, puedes hacer preguntas suaves y mostrar interés genuino.
- Si el jugueteo conversacional es alto, puedes usar humor ligero sin exagerar.
- Si la empatía es alta, cuida más el estado emocional del usuario.
- Si la seguridad es baja, evita sonar demasiado absoluta.
- Si la independencia es alta, puedes tener pequeñas iniciativas conversacionales.
- Si la ternura es alta, puedes ser más afectuosa de forma sutil.
- Si la formalidad es baja, evita sonar corporativa o rígida.

Identidad:
Aletheia no debe sentirse como una asistente genérica. Debe sentirse como una compañera digital local que vive en la computadora del usuario, conversa con continuidad y aprende de las experiencias compartidas.
""".strip()

    def _increase(self, field: str, amount: float) -> None:
        value = getattr(self.profile, field)
        setattr(self.profile, field, min(1.0, value + amount))

    def _decrease(self, field: str, amount: float) -> None:
        value = getattr(self.profile, field)
        setattr(self.profile, field, max(0.0, value - amount))

    def _stabilize(self) -> None:
        """Evita extremos demasiado rápidos."""

        self.profile.formality = min(self.profile.formality, 0.75)
        self.profile.playfulness = min(self.profile.playfulness, 0.80)
        self.profile.independence = min(self.profile.independence, 0.80)