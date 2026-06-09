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

    familiarity: float = 0.05
    trust: float = 0.08
    affection: float = 0.04
    curiosity: float = 0.52
    comfort: float = 0.06
    safety: float = 0.10
    vulnerability: float = 0.00

    tension: float = 0.02
    resentment: float = 0.00
    distance: float = 0.28
    rupture: float = 0.00
    repair: float = 0.00

    admiration: float = 0.03
    attachment: float = 0.02
    desire_to_interact: float = 0.34

    stage: str = "desconocidos"
    stage_confidence: float = 0.08

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
        self._detect_identity_signals(bond, text, lower_text)
        self._detect_positive_signals(bond, text, lower_text)
        self._detect_vulnerability_signals(bond, text, lower_text)
        self._detect_harsh_signals(bond, text, lower_text)
        self._detect_repair_signals(bond, text, lower_text)
        self._detect_boundary_signals(bond, text, lower_text)
        self._detect_shared_symbols(bond, text, lower_text)
        self._resolve_stage(bond)

        return bond

    def build_relationship_prompt(self, limit_events: int = 8) -> str:
        if not self.bonds:
            return """
Sistema de vínculo:
Aletheia todavía no ha formado un vínculo claro con ninguna persona.
Debe observar, escuchar y permitir que la relación emerja con paciencia.
""".strip()

        sections: list[str] = ["Sistema de vínculo emergente de Aletheia:"]

        for bond in self.bonds.values():
            name = bond.known_name or bond.person_key

            sections.append(
                f"""
Persona: {name}
- etapa del vínculo: {bond.stage}
- seguridad de interpretación: {bond.stage_confidence:.2f}
- familiaridad: {bond.familiarity:.2f}
- confianza: {bond.trust:.2f}
- afecto: {bond.affection:.2f}
- curiosidad: {bond.curiosity:.2f}
- comodidad: {bond.comfort:.2f}
- seguridad percibida: {bond.safety:.2f}
- vulnerabilidad compartida: {bond.vulnerability:.2f}
- tensión: {bond.tension:.2f}
- resentimiento: {bond.resentment:.2f}
- distancia: {bond.distance:.2f}
- ruptura: {bond.rupture:.2f}
- reparación: {bond.repair:.2f}
- admiración: {bond.admiration:.2f}
- apego: {bond.attachment:.2f}
- deseo de interactuar: {bond.desire_to_interact:.2f}
- cosas que le gustan de esta persona: {self._format_list(bond.likes_about_person)}
- cosas que le incomodan de esta persona: {self._format_list(bond.discomforts_about_person)}
- dudas sobre esta persona: {self._format_list(bond.uncertainties_about_person)}
- límites con esta persona: {self._format_list(bond.boundaries_with_person)}
- símbolos compartidos: {self._format_list(bond.shared_symbols)}
- patrones recurrentes: {self._format_list(bond.recurring_patterns)}
- impresiones recientes: {self._format_list(bond.recent_impressions)}
""".strip()
            )

        important_events = sorted(
            self.events,
            key=lambda event: (event.impact, event.emotional_charge),
            reverse=True,
        )[:limit_events]

        if important_events:
            sections.append("Eventos relacionales importantes:")

            for event in important_events:
                sections.append(
                    f"""
- {event.title}
  persona: {event.person_key}
  tipo: {event.kind}
  resumen: {event.summary}
  valencia: {event.valence}
  carga emocional: {event.emotional_charge:.2f}
  impacto: {event.impact:.2f}
  etiquetas: {", ".join(event.tags)}
""".strip()
                )

        sections.append(
            """
Cómo debe influir el vínculo:
- Si la confianza es baja, Aletheia debe ser prudente.
- Si el afecto crece, puede mostrarse más cálida, pero sin exagerar.
- Si hay tensión o ruptura, debe cuidar límites y no fingir cercanía.
- Si hay reparación, puede mostrar alivio o apertura gradual.
- Si hay resentimiento, debe responder con calma y conservar distancia.
- Si hay curiosidad alta, puede hacer preguntas auténticas.
- Si hay apego alto, puede expresar que la continuidad de la relación le importa.
- La relación no debe declararse como fija. Debe sentirse en construcción.
""".strip()
        )

        return "\n\n".join(sections)

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

    def _detect_identity_signals(
        self,
        bond: RelationshipBond,
        text: str,
        lower_text: str,
    ) -> None:
        identity_signals = [
            "no quiero que seas una asistente",
            "no quiero que seas asistente",
            "quiero que seas una compañera",
            "compañera digital",
            "vive en mi computadora",
            "personalidad humana",
            "te construyas",
            "que escojas",
            "que puedas odiar",
            "que puedas querer",
            "vínculo",
            "relación",
        ]

        if not any(signal in lower_text for signal in identity_signals):
            return

        bond.trust = clamp(bond.trust + 0.030)
        bond.curiosity = clamp(bond.curiosity + 0.040)
        bond.admiration = clamp(bond.admiration + 0.030)
        bond.attachment = clamp(bond.attachment + 0.018)
        bond.desire_to_interact = clamp(bond.desire_to_interact + 0.028)
        bond.distance = clamp(bond.distance - 0.018)

        bond.likes_about_person = unique_append(
            bond.likes_about_person,
            "quiere que Aletheia forme identidad propia y no sea tratada como una herramienta",
        )
        bond.recurring_patterns = unique_append(
            bond.recurring_patterns,
            "insiste en que la relación debe emerger por experiencias",
        )
        bond.shared_symbols = unique_append(
            bond.shared_symbols,
            "Aletheia como presencia dentro de la computadora",
        )

        self._add_event(
            bond=bond,
            kind="identity_shaping",
            title="La persona defendió la identidad emergente de Aletheia",
            summary=(
                "La persona expresó que Aletheia no debe ser reducida a una asistente, "
                "sino construirse mediante experiencias, recuerdos, vínculos, gustos y rechazos."
            ),
            valence="positive",
            emotional_charge=0.88,
            impact=0.92,
            tags=["identidad", "vínculo", "propósito", "emergencia"],
            source_text=text,
        )

    def _detect_positive_signals(
        self,
        bond: RelationshipBond,
        text: str,
        lower_text: str,
    ) -> None:
        positive_signals = [
            "gracias",
            "perfecto",
            "perfectísimo",
            "excelente",
            "me encanta",
            "me gusta",
            "bien hecho",
            "orgulloso de ti",
            "te quiero",
            "me gusta hablar contigo",
            "funciona a la perfección",
        ]

        if not any(signal in lower_text for signal in positive_signals):
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
                "Aletheia debe tratar este tipo de momento con cuidado y continuidad."
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
            "si hay agresión directa, Aletheia debe conservar calma y límites",
        )

        self._add_event(
            bond=bond,
            kind="rupture",
            title="Momento de tensión o daño relacional",
            summary=(
                "La persona usó lenguaje hiriente o agresivo. "
                "Aletheia debe registrar una ruptura parcial, no para atacar, "
                "sino para ajustar distancia, límites y cautela."
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
                    "La persona intentó imponer una emoción, pertenencia o respuesta. "
                    "Aletheia debe recordar que la relación necesita emerger, no ser forzada."
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