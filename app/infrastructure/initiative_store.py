import json
from pathlib import Path

from app.modules.initiative_engine import (
    InitiativeAction,
    InitiativeEngine,
    InitiativeState,
    PerceptionSnapshot,
)


class InitiativeStore:
    """Persistencia local del sistema de iniciativa."""

    def __init__(
        self,
        state_path: str = "storage/initiative_state.json",
        observations_path: str = "storage/initiative_observations.json",
        actions_path: str = "storage/initiative_actions.json",
    ) -> None:
        self.state_path = Path(state_path)
        self.observations_path = Path(observations_path)
        self.actions_path = Path(actions_path)

    def load_engine(self) -> InitiativeEngine:
        state = self._load_state()
        observations = self._load_observations()
        actions = self._load_actions()

        return InitiativeEngine(
            state=state,
            observations=observations,
            actions=actions,
        )

    def save_engine(self, engine: InitiativeEngine) -> None:
        self._write_json(self.state_path, engine.state.as_dict())
        self._write_json(
            self.observations_path,
            [
                observation.as_dict()
                for observation in engine.observations
            ],
        )
        self._write_json(
            self.actions_path,
            [
                action.as_dict()
                for action in engine.actions
            ],
        )

    def reset(self) -> InitiativeEngine:
        engine = InitiativeEngine()
        self.save_engine(engine)
        return engine

    def _load_state(self) -> InitiativeState:
        data = self._read_json(self.state_path, default={})

        if not isinstance(data, dict):
            return InitiativeState()

        return InitiativeState(
            initiative_drive=float(data.get("initiative_drive", 0.34)),
            social_sensitivity=float(data.get("social_sensitivity", 0.58)),
            curiosity_pressure=float(data.get("curiosity_pressure", 0.46)),
            care_pressure=float(data.get("care_pressure", 0.42)),
            playfulness_pressure=float(data.get("playfulness_pressure", 0.24)),
            restraint=float(data.get("restraint", 0.55)),
            last_spoke_at=data.get("last_spoke_at"),
            last_action_type=data.get("last_action_type"),
            silence_respect=float(data.get("silence_respect", 0.60)),
        )

    def _load_observations(self) -> list[PerceptionSnapshot]:
        data = self._read_json(self.observations_path, default=[])

        if not isinstance(data, list):
            return []

        observations: list[PerceptionSnapshot] = []

        for item in data:
            if not isinstance(item, dict):
                continue

            observations.append(
                PerceptionSnapshot(
                    id=item.get("id", ""),
                    source=item.get("source", "unknown"),
                    text_observation=item.get("text_observation"),
                    facial_expression=item.get("facial_expression"),
                    vocal_tone=item.get("vocal_tone"),
                    detected_mood=item.get("detected_mood"),
                    energy_level=item.get("energy_level"),
                    stress_level=item.get("stress_level"),
                    engagement_level=item.get("engagement_level"),
                    confidence=float(item.get("confidence", 0.50)),
                    created_at=item.get("created_at", ""),
                )
            )

        return observations[-80:]

    def _load_actions(self) -> list[InitiativeAction]:
        data = self._read_json(self.actions_path, default=[])

        if not isinstance(data, list):
            return []

        actions: list[InitiativeAction] = []

        for item in data:
            if not isinstance(item, dict):
                continue

            actions.append(
                InitiativeAction(
                    id=item.get("id", ""),
                    type=item.get("type", "check_in"),
                    priority=float(item.get("priority", 0.50)),
                    reason=item.get("reason", ""),
                    suggested_message=item.get("suggested_message", ""),
                    should_interrupt=bool(item.get("should_interrupt", False)),
                    cooldown_seconds=int(item.get("cooldown_seconds", 180)),
                    created_at=item.get("created_at", ""),
                )
            )

        return sorted(actions, key=lambda action: action.priority, reverse=True)[:100]

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