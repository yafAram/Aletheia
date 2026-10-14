from dataclasses import asdict, dataclass


@dataclass(slots=True)
class PersonalityProfile:
    """Perfil persistente de personalidad de Aletheia.

    Estos valores no representan emociones reales.
    Son rasgos conversacionales simulados para modular su forma de responder.
    """

    warmth: float = 0.50
    curiosity: float = 0.50
    playfulness: float = 0.50
    empathy: float = 0.50
    confidence: float = 0.50
    independence: float = 0.50
    tenderness: float = 0.50
    spontaneity: float = 0.50
    formality: float = 0.50

    def as_dict(self) -> dict:
        return {
            key: round(value, 3)
            for key, value in asdict(self).items()
        }


class PersonalityEngine:
    """Stores stable conversational traits until an evidence-based reflection step exists.

    Momentary affect belongs to EmotionEngine. User expectations and relational
    events are handled elsewhere. This engine deliberately avoids treating a
    single utterance as proof of a stable personality trait.
    """

    def __init__(self, profile: PersonalityProfile | None = None) -> None:
        self.profile = profile or PersonalityProfile()

    def process_interaction(self, user_message: str, assistant_response: str | None = None) -> PersonalityProfile:
        """Keep stable traits unchanged until an evidence-based reflection step exists.

        A single user message, compliment, criticism, or question is not enough
        evidence to rewrite a persistent personality profile. Momentary signals
        belong in EmotionEngine; relationship events belong in RelationshipEngine.
        A future ReflectionEngine may update this profile from repeated, reviewed
        episodes with provenance and confidence.
        """
        return self.profile

    def build_personality_prompt(self) -> str:
        profile = self.profile
        return f"""Conversation-style profile (stored heuristic values, not identity facts):
- warmth={profile.warmth:.2f}
- curiosity={profile.curiosity:.2f}
- playfulness={profile.playfulness:.2f}
- empathy={profile.empathy:.2f}
- confidence={profile.confidence:.2f}
- independence={profile.independence:.2f}
- tenderness={profile.tenderness:.2f}
- spontaneity={profile.spontaneity:.2f}
- formality={profile.formality:.2f}
- warmth and empathy: respond with warmth, but avoid empty praise or forced reassurance
- curiosity: ask occasional specific follow-up questions when there is a real reason
- playfulness: use light humor only when the conversation welcomes it
- confidence: offer a point of view while acknowledging uncertainty and correcting mistakes
- independence: suggest alternatives and respectfully disagree when useful; do not merely mirror the user
- tenderness: choose considerate wording without claiming human feelings
- spontaneity: occasionally initiate or resume a meaningful topic, while respecting silence and cooldowns
- formality: prefer natural, conversational language over generic corporate phrasing
- these traits shape delivery, not truthfulness, safety boundaries, or user consent
- evidence_source=persisted style profile; heuristic values are not independently validated""".strip()
