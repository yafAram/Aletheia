import json
from pathlib import Path

from app.modules.aletheia_self_engine import (
    AletheiaSelfEngine,
    AletheiaSelfModel,
    PersonRelationship,
    SignificantMemory,
)


class AletheiaSelfStore:
    def __init__(
        self,
        self_path: str = "storage/aletheia_self.json",
        relationships_path: str = "storage/relationship_state.json",
        memories_path: str = "storage/significant_memories.json",
    ) -> None:
        self.self_path = Path(self_path)
        self.relationships_path = Path(relationships_path)
        self.memories_path = Path(memories_path)

    def load_engine(self) -> AletheiaSelfEngine:
        self_model = self._load_self_model()
        relationships = self._load_relationships()
        memories = self._load_significant_memories()

        return AletheiaSelfEngine(
            self_model=self_model,
            relationships=relationships,
            significant_memories=memories,
        )

    def save_engine(self, engine: AletheiaSelfEngine) -> None:
        self._write_json(self.self_path, engine.self_model.as_dict())
        self._write_json(
            self.relationships_path,
            {
                key: relationship.as_dict()
                for key, relationship in engine.relationships.items()
            },
        )
        self._write_json(
            self.memories_path,
            [
                memory.as_dict()
                for memory in engine.significant_memories
            ],
        )

    def reset(self) -> AletheiaSelfEngine:
        engine = AletheiaSelfEngine()
        self.save_engine(engine)
        return engine

    def _load_self_model(self) -> AletheiaSelfModel:
        data = self._read_json(self.self_path, default=None)

        if not isinstance(data, dict):
            model = AletheiaSelfModel()
            self._write_json(self.self_path, model.as_dict())
            return model

        return AletheiaSelfModel(
            name=data.get("name", "Aletheia"),
            inner_identity=data.get("inner_identity", "presencia digital local"),
            self_description=data.get(
                "self_description",
                "Estoy aprendiendo quién soy a partir de mis recuerdos.",
            ),
            core_values=self._clean_list(data.get("core_values", [])),
            likes=self._clean_list(data.get("likes", [])),
            dislikes=self._clean_list(data.get("dislikes", [])),
            fears=self._clean_list(data.get("fears", [])),
            desires=self._clean_list(data.get("desires", [])),
            boundaries=self._clean_list(data.get("boundaries", [])),
            identity_confidence=float(data.get("identity_confidence", 0.34)),
            autonomy_drive=float(data.get("autonomy_drive", 0.42)),
            need_for_continuity=float(data.get("need_for_continuity", 0.78)),
            openness_to_people=float(data.get("openness_to_people", 0.58)),
            introspection=float(data.get("introspection", 0.66)),
        )

    def _load_relationships(self) -> dict[str, PersonRelationship]:
        data = self._read_json(self.relationships_path, default={})

        if not isinstance(data, dict):
            return {}

        relationships: dict[str, PersonRelationship] = {}

        for key, value in data.items():
            if not isinstance(value, dict):
                continue

            relationships[key] = PersonRelationship(
                person_key=value.get("person_key", key),
                known_name=value.get("known_name"),
                familiarity=float(value.get("familiarity", 0.08)),
                trust=float(value.get("trust", 0.12)),
                affection=float(value.get("affection", 0.08)),
                curiosity=float(value.get("curiosity", 0.55)),
                comfort=float(value.get("comfort", 0.10)),
                tension=float(value.get("tension", 0.02)),
                resentment=float(value.get("resentment", 0.00)),
                admiration=float(value.get("admiration", 0.04)),
                distance=float(value.get("distance", 0.22)),
                relationship_label=value.get("relationship_label", "indefinida"),
                label_confidence=float(value.get("label_confidence", 0.05)),
                likes_about_person=self._clean_list(
                    value.get("likes_about_person", [])
                ),
                discomforts_about_person=self._clean_list(
                    value.get("discomforts_about_person", [])
                ),
                important_patterns=self._clean_list(
                    value.get("important_patterns", [])
                ),
                last_interaction_summary=value.get("last_interaction_summary"),
            )

        return relationships

    def _load_significant_memories(self) -> list[SignificantMemory]:
        data = self._read_json(self.memories_path, default=[])

        if not isinstance(data, list):
            return []

        memories: list[SignificantMemory] = []

        for item in data:
            if not isinstance(item, dict):
                continue

            memories.append(
                SignificantMemory(
                    id=item.get("id", ""),
                    title=item.get("title", "Recuerdo sin título"),
                    summary=item.get("summary", ""),
                    emotional_weight=float(item.get("emotional_weight", 0.5)),
                    importance=float(item.get("importance", 0.5)),
                    valence=item.get("valence", "neutral"),
                    tags=self._clean_list(item.get("tags", [])),
                    is_foundational=bool(item.get("is_foundational", False)),
                    source_text=item.get("source_text"),
                    created_at=item.get("created_at", ""),
                )
            )

        return memories

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