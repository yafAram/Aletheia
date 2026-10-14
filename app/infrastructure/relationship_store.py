import json
from pathlib import Path

from app.modules.relationship_engine import (
    RelationshipBond,
    RelationshipEngine,
    RelationshipEvent,
)


class RelationshipStore:
    """Persistencia local del sistema de vínculo."""

    def __init__(
        self,
        bonds_path: str = "storage/bond_state.json",
        events_path: str = "storage/bond_events.json",
    ) -> None:
        self.bonds_path = Path(bonds_path)
        self.events_path = Path(events_path)

    def load_engine(self) -> RelationshipEngine:
        bonds = self._load_bonds()
        events = self._load_events()

        return RelationshipEngine(
            bonds=bonds,
            events=events,
        )

    def save_engine(self, engine: RelationshipEngine) -> None:
        self._write_json(
            self.bonds_path,
            {
                key: bond.as_dict()
                for key, bond in engine.bonds.items()
            },
        )
        self._write_json(
            self.events_path,
            [
                event.as_dict()
                for event in engine.events
            ],
        )

    def reset(self) -> RelationshipEngine:
        engine = RelationshipEngine()
        self.save_engine(engine)
        return engine

    def _load_bonds(self) -> dict[str, RelationshipBond]:
        data = self._read_json(self.bonds_path, default={})

        if not isinstance(data, dict):
            return {}

        bonds: dict[str, RelationshipBond] = {}

        for key, value in data.items():
            if not isinstance(value, dict):
                continue

            bonds[key] = RelationshipBond(
                person_key=value.get("person_key", key),
                known_name=value.get("known_name"),
                familiarity=float(value.get("familiarity", 0.0)),
                trust=float(value.get("trust", 0.5)),
                affection=float(value.get("affection", 0.0)),
                curiosity=float(value.get("curiosity", 0.5)),
                comfort=float(value.get("comfort", 0.5)),
                safety=float(value.get("safety", 0.5)),
                vulnerability=float(value.get("vulnerability", 0.00)),
                tension=float(value.get("tension", 0.02)),
                resentment=float(value.get("resentment", 0.00)),
                distance=float(value.get("distance", 0.5)),
                rupture=float(value.get("rupture", 0.00)),
                repair=float(value.get("repair", 0.00)),
                admiration=float(value.get("admiration", 0.0)),
                attachment=float(value.get("attachment", 0.0)),
                desire_to_interact=float(value.get("desire_to_interact", 0.0)),
                stage=value.get("stage", "sin_evaluar"),
                stage_confidence=float(value.get("stage_confidence", 0.0)),
                likes_about_person=self._clean_list(
                    value.get("likes_about_person", [])
                ),
                discomforts_about_person=self._clean_list(
                    value.get("discomforts_about_person", [])
                ),
                uncertainties_about_person=self._clean_list(
                    value.get("uncertainties_about_person", [])
                ),
                boundaries_with_person=self._clean_list(
                    value.get("boundaries_with_person", [])
                ),
                shared_symbols=self._clean_list(
                    value.get("shared_symbols", [])
                ),
                recurring_patterns=self._clean_list(
                    value.get("recurring_patterns", [])
                ),
                recent_impressions=self._clean_list(
                    value.get("recent_impressions", [])
                ),
                last_interaction_at=value.get("last_interaction_at"),
                last_interaction_summary=value.get("last_interaction_summary"),
            )

        return bonds

    def _load_events(self) -> list[RelationshipEvent]:
        data = self._read_json(self.events_path, default=[])

        if not isinstance(data, list):
            return []

        events: list[RelationshipEvent] = []

        for item in data:
            if not isinstance(item, dict):
                continue

            events.append(
                RelationshipEvent(
                    id=item.get("id", ""),
                    person_key=item.get("person_key", "persona_desconocida"),
                    kind=item.get("kind", "unknown"),
                    title=item.get("title", "Evento sin título"),
                    summary=item.get("summary", ""),
                    valence=item.get("valence", "neutral"),
                    emotional_charge=float(item.get("emotional_charge", 0.5)),
                    impact=float(item.get("impact", 0.5)),
                    tags=self._clean_list(item.get("tags", [])),
                    source_text=item.get("source_text", ""),
                    created_at=item.get("created_at", ""),
                )
            )

        return events

    def _read_json(self, path: Path, default):
        if not path.exists():
            return default

        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return default

    def _write_json(self, path: Path, data) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)

        path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _clean_list(self, values) -> list[str]:
        if not isinstance(values, list):
            return []

        return [
            str(value).strip()
            for value in values
            if str(value).strip()
        ]