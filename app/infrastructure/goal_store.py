"""Atomic JSON persistence for user goals."""

from __future__ import annotations

import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile

from app.modules.goal_engine import Goal, GoalEngine


class GoalStore:
    def __init__(self, path: str = "storage/goals.json") -> None:
        self.path = Path(path)

    def load_engine(self) -> GoalEngine:
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return GoalEngine()
        records = data.get("goals", []) if isinstance(data, dict) else []
        goals: list[Goal] = []
        if isinstance(records, list):
            for item in records:
                if not isinstance(item, dict) or not item.get("id") or not item.get("description"):
                    continue
                try:
                    goals.append(
                        Goal(
                            id=str(item["id"]),
                            description=str(item["description"])[:180],
                            status=str(item.get("status", "active")),
                            source=str(item.get("source", "legacy")),
                            priority=max(0.0, min(1.0, float(item.get("priority", 0.5)))),
                            confidence=max(0.0, min(1.0, float(item.get("confidence", 0.5)))),
                            created_at=str(item.get("created_at", "")),
                            updated_at=str(item.get("updated_at", "")),
                            last_mentioned_at=str(item.get("last_mentioned_at", "")),
                            last_check_in_at=item.get("last_check_in_at"),
                        )
                    )
                except (TypeError, ValueError):
                    continue
        return GoalEngine(goals=goals[-100:])

    def save_engine(self, engine: GoalEngine) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(engine.as_dict(), ensure_ascii=False, indent=2)
        temporary_path: str | None = None
        try:
            with NamedTemporaryFile(
                "w", encoding="utf-8", dir=self.path.parent, delete=False
            ) as temporary:
                temporary.write(payload)
                temporary.flush()
                os.fsync(temporary.fileno())
                temporary_path = temporary.name
            os.replace(temporary_path, self.path)
        finally:
            if temporary_path and os.path.exists(temporary_path):
                os.unlink(temporary_path)
