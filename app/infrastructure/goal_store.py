"""Atomic JSON persistence for user goals, preserving malformed files for recovery."""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from tempfile import NamedTemporaryFile

from app.modules.goal_engine import Goal, GoalEngine

logger = logging.getLogger(__name__)


class GoalStore:
    def __init__(self, path: str = "storage/goals.json") -> None:
        self.path = Path(path)

    def load_engine(self) -> GoalEngine:
        try:
            raw = self.path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return GoalEngine()
        except OSError:
            logger.exception("Could not read goal state at %s", self.path)
            return GoalEngine()

        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            # Preserve the malformed file instead of silently losing the only copy.
            stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
            backup_path = self.path.with_name(f"{self.path.name}.corrupt-{stamp}")
            try:
                os.replace(self.path, backup_path)
                logger.error(
                    "Goal state JSON was invalid; preserved original at %s",
                    backup_path,
                )
            except OSError:
                logger.exception(
                    "Goal state JSON is invalid and could not be backed up: %s",
                    self.path,
                )
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
