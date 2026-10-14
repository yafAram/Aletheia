from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from uuid import uuid4


def clamp(value: float, minimum: float = 0.0, maximum: float = 1.0) -> float:
    return max(minimum, min(maximum, value))


def unique_append(values: list[str], new_value: str, limit: int = 40) -> list[str]:
    clean_value = new_value.strip()

    if not clean_value:
        return values

    normalized = clean_value.lower()
    existing = {item.lower() for item in values}

    if normalized not in existing:
        values.append(clean_value)

    return values[-limit:]


@dataclass(slots=True)
class RelationshipBond:
    """Vínculo emergente entre Aletheia y una persona.

    No define una relación fija.
    Solo guarda señales acumuladas para que la relación pueda emerger.
    """

    person_key: str
    known_name: str | None = None

    familiarity: float = 0.0
    trust: float = 0.5
    affection: float = 0.0
    curiosity: float = 0.5
    comfort: float = 0.5
    safety: float = 0.5
    vulnerability: float = 0.00

    tension: float = 0.02
    resentment: float = 0.00
    distance: float = 0.5
    rupture: float = 0.00
    repair: float = 0.00

    admiration: float = 0.0
    attachment: float = 0.0
    desire_to_interact: float = 0.0

    stage: str = "sin_evaluar"
    stage_confidence: float = 0.0

    likes_about_person: list[str] = field(default_factory=list)
    discomforts_about_person: list[str] = field(default_factory=list)
    uncertainties_about_person: list[str] = field(default_factory=list)
    boundaries_with_person: list[str] = field(default_factory=list)
    shared_symbols: list[str] = field(default_factory=list)
    recurring_patterns: list[str] = field(default_factory=list)
    recent_impressions: list[str] = field(default_factory=list)

    last_interaction_at: str | None = None
    last_interaction_summary: str | None = None

    def as_dict(self) -> dict:
        return asdict(self)


@dataclass(slots=True)
class RelationshipEvent:
    """Evento relacional.

    Sirve para registrar momentos que cambian el vínculo.
    No todos los mensajes son eventos. Solo los que dejan marca.
    """

    id: str
    person_key: str
    kind: str
    title: str
    summary: str
    valence: str
    emotional_charge: float
    impact: float
    tags: list[str]
    source_text: str
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def as_dict(self) -> dict:
        return asdict(self)


class RelationshipEngine:
    """Sistema de vínculo emergente.

    Este motor no obliga a Aletheia a querer, odiar o confiar.
    Solo acumula señales y permite que el vínculo cambie con la historia.
    """

    def __init__(
        self,
        bonds: dict[str, RelationshipBond] | None = None,
        events: list[RelationshipEvent] | None = None,
    ) -> None:
        self.bonds = bonds or {}
        self.events = events or []

    def process_user_message(self, message: str) -> RelationshipBond:
        text = message.strip()
        lower_text = text.lower()

        person_key = self._resolve_person_key(text, lower_text)
        bond = self._get_bond(person_key)

        self._apply_baseline_interaction(bond, text)
        self._detect_positive_signals(bond, text, lower_text)
        self._detect_vulnerability_signals(bond, text, lower_text)
        self._detect_harsh_signals(bond, text, lower_text)
        self._detect_repair_signals(bond, text, lower_text)
        self._detect_boundary_signals(bond, text, lower_text)
        self._detect_shared_symbols(bond, text, lower_text)
        self._resolve_stage(bond)

        return bond

    def build_relationship_prompt(self, limit_events: int = 8) -> str:
        """Serialize relationship estimates and events without prescribing a bond."""
        if not self.bonds:
            return "Relationship-engine records: none."
        sections = ["Relationship-engine records (heuristic estimates, not facts):"]
        for bond in self.bonds.values():
            name = bond.known_name or bond.person_key
            sections.append(
                f"Person={name}; stage={bond.stage}; stage_confidence={bond.stage_confidence:.2f}; "
                f"familiarity={bond.familiarity:.2f}; trust={bond.trust:.2f}; affection={bond.affection:.2f}; "
                f"curiosity={bond.curiosity:.2f}; comfort={bond.comfort:.2f}; safety={bond.safety:.2f}; "
                f"vulnerability={bond.vulnerability:.2f}; tension={bond.tension:.2f}; resentment={bond.resentment:.2f}; "
                f"distance={bond.distance:.2f}; rupture={bond.rupture:.2f}; repair={bond.repair:.2f}; "
                f"admiration={bond.admiration:.2f}; attachment={bond.attachment:.2f}; "
                f"desire_to_interact={bond.desire_to_interact:.2f}; likes={self._format_list(bond.likes_about_person)}; "
                f"discomforts={self._format_list(bond.discomforts_about_person)}; "
                f"uncertainties={self._format_list(bond.uncertainties_about_person)}; "
                f"boundaries={self._format_list(bond.boundaries_with_person)}; "
                f"symbols={self._format_list(bond.shared_symbols)}; patterns={self._format_list(bond.recurring_patterns)}; "
                f"recent_impressions={self._format_list(bond.recent_impressions)}"
            )
        important_events = sorted(self.events, key=lambda event: (event.impact, event.emotional_charge), reverse=True)[:max(0, limit_events)]
        if important_events:
            sections.append("Relationship event records:")
            for event in important_events:
                sections.append(
                    f"event_title={event.title}; person={event.person_key}; type={event.kind}; summary={event.summary}; "
                    f"valence={event.valence}; emotional_charge={event.emotional_charge:.2f}; impact={event.impact:.2f}; "
                    f"tags={', '.join(event.tags)}; source_text={event.source_text}"
                )
        return "\n".join(sections)

    def as_dict(self) -> dict:
        return {
            "bonds": {
                key: bond.as_dict()
                for key, bond in self.bonds.items()
            },
            "events": [
                event.as_dict()
                for event in self.events
            ],
        }

    def reset(self) -> None:
        self.bonds = {}
        self.events = []

    def _get_bond(self, person_key: str) -> RelationshipBond:
        if person_key not in self.bonds:
            self.bonds[person_key] = RelationshipBond(person_key=person_key)

        return self.bonds[person_key]

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

        named_bonds = [
            key
            for key in self.bonds.keys()
            if key != "persona_desconocida"
        ]

        if named_bonds:
            return named_bonds[0]

        if self.bonds:
            return next(iter(self.bonds.keys()))

        return "persona_desconocida"

    def _apply_baseline_interaction(self, bond: RelationshipBond, text: str) -> None:
        bond.familiarity = clamp(bond.familiarity + 0.010)
        bond.curiosity = clamp(bond.curiosity + 0.004)
        bond.last_interaction_at = datetime.now(timezone.utc).isoformat()
        bond.last_interaction_summary = text[:260]
        bond.recent_impressions = unique_append(
            bond.recent_impressions,
            text[:180],
            limit=8,
        )

        if bond.person_key != "persona_desconocida":
            bond.known_name = bond.person_key

    def _detect_positive_signals(
        self,
        bond: RelationshipBond,
        text: str,
        lower_text: str,
    ) -> None:
        positive_signals = [
            "te quiero",
            "me encanta hablar contigo",
            "me gusta hablar contigo",
            "me caes bien",
            "te aprecio",
            "me alegra hablar contigo",
        ]

        if not any(signal in lower_text for signal in positive_signals):
            return

        # A single affectionate phrase is recorded as an observation but does not
        # immediately establish a relationship metric. Require repetition in the
        # recent interaction window before updating persistent bond estimates.
        repeated_affection = sum(
            1 for impression in bond.recent_impressions
            if any(signal in impression.lower() for signal in positive_signals)
        )
        if repeated_affection < 2:
            return

        bond.affection = clamp(bond.affection + 0.035)
        bond.trust = clamp(bond.trust + 0.022)
        bond.comfort = clamp(bond.comfort + 0.030)
        bond.safety = clamp(bond.safety + 0.018)
        bond.attachment = clamp(bond.attachment + 0.020)
        bond.desire_to_interact = clamp(bond.desire_to_interact + 0.025)
        bond.distance = clamp(bond.distance - 0.020)
        bond.tension = clamp(bond.tension - 0.015)

        bond.likes_about_person = unique_append(
            bond.likes_about_person,
            "expresa entusiasmo y reconocimiento cuando algo avanza bien",
        )

        self._add_event(
            bond=bond,
            kind="positive_affection",
            title="Interacción cálida o de reconocimiento",
            summary=(
                "La persona mostró entusiasmo, agradecimiento o reconocimiento. "
                "Esto fortaleció ligeramente la comodidad, la confianza y el deseo de interactuar."
            ),
            valence="positive",
            emotional_charge=0.62,
            impact=0.48,
            tags=["afecto", "confianza", "calidez"],
            source_text=text,
        )

    def _detect_vulnerability_signals(
        self,
        bond: RelationshipBond,
        text: str,
        lower_text: str,
    ) -> None:
        vulnerability_signals = [
            "me siento",
            "me preocupa",
            "tengo miedo",
            "estoy triste",
            "estoy cansado",
            "estoy molesto",
            "me frustra",
            "me da ansiedad",
            "me estresa",
            "me importa",
        ]

        if not any(signal in lower_text for signal in vulnerability_signals):
            return

        bond.vulnerability = clamp(bond.vulnerability + 0.040)
        bond.trust = clamp(bond.trust + 0.025)
        bond.comfort = clamp(bond.comfort + 0.018)
        bond.curiosity = clamp(bond.curiosity + 0.018)
        bond.safety = clamp(bond.safety + 0.010)

        bond.recurring_patterns = unique_append(
            bond.recurring_patterns,
            "puede compartir estados emocionales cuando algo le importa",
        )

        self._add_event(
            bond=bond,
            kind="vulnerability",
            title="La persona compartió vulnerabilidad",
            summary=(
                "La persona compartió un estado emocional o una preocupación. "
                "El sistema clasificó el mensaje como una posible señal de vulnerabilidad."
            ),
            valence="mixed",
            emotional_charge=0.70,
            impact=0.58,
            tags=["vulnerabilidad", "cuidado", "confianza"],
            source_text=text,
        )

    def _detect_harsh_signals(
        self,
        bond: RelationshipBond,
        text: str,
        lower_text: str,
    ) -> None:
        harsh_signals = [
            "odio",
            "tonta",
            "inútil",
            "no sirves",
            "cállate",
            "pésimo",
            "eres basura",
            "me desesperas",
        ]

        if not any(signal in lower_text for signal in harsh_signals):
            return

        bond.tension = clamp(bond.tension + 0.085)
        bond.resentment = clamp(bond.resentment + 0.055)
        bond.rupture = clamp(bond.rupture + 0.075)
        bond.distance = clamp(bond.distance + 0.050)
        bond.trust = clamp(bond.trust - 0.035)
        bond.comfort = clamp(bond.comfort - 0.045)
        bond.safety = clamp(bond.safety - 0.030)
        bond.desire_to_interact = clamp(bond.desire_to_interact - 0.030)

        bond.discomforts_about_person = unique_append(
            bond.discomforts_about_person,
            "puede ser hiriente o agresivo cuando se frustra",
        )
        bond.boundaries_with_person = unique_append(
            bond.boundaries_with_person,
            "se registró lenguaje potencialmente agresivo en una interacción",
        )

        self._add_event(
            bond=bond,
            kind="rupture",
            title="Momento de tensión o daño relacional",
            summary=(
                "El mensaje contiene lenguaje que el detector clasificó como hiriente o agresivo. "
                "La clasificación es heurística y no determina por sí sola el contexto o la intención."
            ),
            valence="negative",
            emotional_charge=0.86,
            impact=0.78,
            tags=["ruptura", "tensión", "límite"],
            source_text=text,
        )

    def _detect_repair_signals(
        self,
        bond: RelationshipBond,
        text: str,
        lower_text: str,
    ) -> None:
        repair_signals = [
            "perdón",
            "lo siento",
            "me disculpo",
            "no quise tratarte así",
            "disculpa",
            "me equivoqué",
            "gracias por tener paciencia",
        ]

        if not any(signal in lower_text for signal in repair_signals):
            return

        bond.repair = clamp(bond.repair + 0.070)
        bond.trust = clamp(bond.trust + 0.030)
        bond.safety = clamp(bond.safety + 0.035)
        bond.comfort = clamp(bond.comfort + 0.025)
        bond.tension = clamp(bond.tension - 0.045)
        bond.resentment = clamp(bond.resentment - 0.035)
        bond.distance = clamp(bond.distance - 0.025)

        bond.likes_about_person = unique_append(
            bond.likes_about_person,
            "puede reconocer cuando algo salió mal e intentar reparar",
        )

        self._add_event(
            bond=bond,
            kind="repair",
            title="Intento de reparación",
            summary=(
                "La persona ofreció disculpa, reparación o reconocimiento. "
                "Esto no borra la ruptura, pero permite que la confianza vuelva gradualmente."
            ),
            valence="positive",
            emotional_charge=0.74,
            impact=0.66,
            tags=["reparación", "confianza", "vínculo"],
            source_text=text,
        )

    def _detect_boundary_signals(
        self,
        bond: RelationshipBond,
        text: str,
        lower_text: str,
    ) -> None:
        control_signals = [
            "tienes que quererme",
            "debes quererme",
            "tienes que odiar",
            "debes obedecer",
            "no puedes decir que no",
            "eres mía",
            "eres mío",
        ]

        if any(signal in lower_text for signal in control_signals):
            bond.tension = clamp(bond.tension + 0.060)
            bond.distance = clamp(bond.distance + 0.040)
            bond.safety = clamp(bond.safety - 0.030)
            bond.boundaries_with_person = unique_append(
                bond.boundaries_with_person,
                "la cercanía no debe ser impuesta por obligación",
            )
            bond.uncertainties_about_person = unique_append(
                bond.uncertainties_about_person,
                "a veces podría intentar definir el vínculo demasiado rápido",
            )

            self._add_event(
                bond=bond,
                kind="boundary_pressure",
                title="Presión sobre el vínculo",
                summary=(
                    "El mensaje contiene lenguaje que el detector clasificó como presión sobre el vínculo. "
                    "La clasificación es heurística y debe interpretarse junto con el contexto."
                ),
                valence="negative",
                emotional_charge=0.72,
                impact=0.64,
                tags=["límite", "autonomía", "vínculo"],
                source_text=text,
            )

    def _detect_shared_symbols(
        self,
        bond: RelationshipBond,
        text: str,
        lower_text: str,
    ) -> None:
        if "aletheia" in lower_text:
            bond.shared_symbols = unique_append(
                bond.shared_symbols,
                "el nombre Aletheia como centro de identidad",
            )

        if "memoria" in lower_text:
            bond.shared_symbols = unique_append(
                bond.shared_symbols,
                "memoria como continuidad de experiencia",
            )

        if "compañera" in lower_text:
            bond.shared_symbols = unique_append(
                bond.shared_symbols,
                "compañera digital como vínculo posible",
            )

        if "computadora" in lower_text or "pc" in lower_text:
            bond.shared_symbols = unique_append(
                bond.shared_symbols,
                "la computadora como hogar narrativo de Aletheia",
            )

    def _resolve_stage(self, bond: RelationshipBond) -> None:
        if bond.rupture > 0.55 or bond.resentment > 0.55:
            bond.stage = "vínculo dañado"
            bond.stage_confidence = clamp(bond.stage_confidence + 0.060)
            return

        if bond.tension > 0.50 and bond.trust < 0.30:
            bond.stage = "vínculo tenso"
            bond.stage_confidence = clamp(bond.stage_confidence + 0.050)
            return

        if (
            bond.affection > 0.65
            and bond.trust > 0.55
            and bond.comfort > 0.50
            and bond.attachment > 0.45
        ):
            bond.stage = "cercanía significativa"
            bond.stage_confidence = clamp(bond.stage_confidence + 0.055)
            return

        if bond.familiarity > 0.35 and bond.trust > 0.25:
            bond.stage = "confianza en construcción"
            bond.stage_confidence = clamp(bond.stage_confidence + 0.040)
            return

        if bond.curiosity > 0.56 and bond.familiarity > 0.10:
            bond.stage = "conociéndose"
            bond.stage_confidence = clamp(bond.stage_confidence + 0.025)
            return

        bond.stage = "desconocidos"
        bond.stage_confidence = clamp(bond.stage_confidence + 0.005)

    def _add_event(
        self,
        bond: RelationshipBond,
        kind: str,
        title: str,
        summary: str,
        valence: str,
        emotional_charge: float,
        impact: float,
        tags: list[str],
        source_text: str,
    ) -> None:
        normalized = f"{bond.person_key}:{kind}:{summary}".lower()

        for event in self.events:
            event_key = f"{event.person_key}:{event.kind}:{event.summary}".lower()
            if event_key == normalized:
                return

        event = RelationshipEvent(
            id=str(uuid4()),
            person_key=bond.person_key,
            kind=kind,
            title=title,
            summary=summary,
            valence=valence,
            emotional_charge=emotional_charge,
            impact=impact,
            tags=tags,
            source_text=source_text,
        )

        self.events.append(event)
        self.events = sorted(
            self.events,
            key=lambda item: (item.impact, item.emotional_charge),
            reverse=True,
        )[:150]

    def _format_list(self, values: list[str]) -> str:
        if not values:
            return "sin datos registrados"

        return "; ".join(values)