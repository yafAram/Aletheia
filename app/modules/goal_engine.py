"""Persistent user-goal tracking based on explicit language, not inferred desires."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from uuid import uuid4

from app.core.text_normalization import normalize_text


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize(value: str) -> str:
    return normalize_text(value)


@dataclass(slots=True)
class Goal:
    id: str
    description: str
    status: str = "active"
    source: str = "conversation"
    priority: float = 0.5
    confidence: float = 0.85
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)
    last_mentioned_at: str = field(default_factory=_now_iso)
    last_check_in_at: str | None = None

    def as_dict(self) -> dict:
        return asdict(self)


class GoalEngine:
    """Tracks explicitly expressed user goals and offers low-pressure follow-ups.

    Extraction is deliberately conservative and heuristic. It does not infer
    hidden goals, and every stored item retains its source.
    """

    _PATTERNS = (
        re.compile(
            r"\b(?:mi objetivo es|mi meta es|estoy intentando|estoy trabajando en|"
            r"estoy construyendo|quiero desarrollar|quiero crear|quiero aprender|"
            r"quiero terminar|me gustar[ií]a desarrollar|me gustar[ií]a crear|"
            r"me gustar[ií]a aprender|quiero mejorar)\s+(.{5,180})",
            re.I,
        ),
        re.compile(
            r"\b(?:quiero|me gustar[ií]a|necesito)\s+(?:que\s+)?(.{8,160})",
            re.I,
        ),
    )
    _GENERIC = {
        "hablar contigo", "saber mas", "saber más", "que me ayudes",
        "que me ayudes con esto", "hacer una pregunta", "entender",
        "ver que pasa", "ver qué pasa", "conversar", "descansar",
    }

    def __init__(self, goals: list[Goal] | None = None) -> None:
        self.goals = goals or []

    def observe_user_message(self, message: str) -> Goal | None:
        clean = " ".join(message.strip().split())
        if not clean or clean.endswith("?") or len(clean) > 1200:
            self._refresh_mentions(clean)
            return None

        candidate = self._extract_goal(clean)
        if not candidate:
            self._refresh_mentions(clean)
            return None

        normalized = _normalize(candidate).strip(" .,!;:")
        if normalized in {_normalize(item) for item in self._GENERIC}:
            return None

        # Avoid near-duplicate active goals using normalized substring overlap.
        for goal in self.goals:
            existing = _normalize(goal.description)
            if goal.status == "active" and (
                normalized == existing
                or normalized in existing
                or existing in normalized
            ):
                goal.last_mentioned_at = _now_iso()
                goal.updated_at = goal.last_mentioned_at
                return goal

        goal = Goal(
            id=str(uuid4()),
            description=candidate.strip(" .,!;:")[:180],
            source="conversation",
            priority=0.55,
            confidence=0.82,
        )
        self.goals.append(goal)
        self.goals = self.goals[-100:]
        return goal

    def add_goal(
        self,
        description: str,
        priority: float = 0.6,
        source: str = "user_manual",
    ) -> Goal:
        clean = " ".join(description.strip().split())
        if not clean:
            raise ValueError("La descripción del objetivo no puede estar vacía.")
        if len(clean) > 180:
            raise ValueError("La descripción del objetivo no puede superar 180 caracteres.")

        normalized = _normalize(clean)
        for goal in self.goals:
            if goal.status == "active" and _normalize(goal.description) == normalized:
                goal.last_mentioned_at = _now_iso()
                goal.updated_at = goal.last_mentioned_at
                return goal

        goal = Goal(
            id=str(uuid4()),
            description=clean,
            source=source,
            priority=max(0.0, min(1.0, float(priority))),
            confidence=1.0 if source == "user_manual" else 0.82,
        )
        self.goals.append(goal)
        self.goals = self.goals[-100:]
        return goal

    def complete_goal(self, goal_id: str) -> Goal | None:
        goal = next((item for item in self.goals if item.id == goal_id), None)
        if goal is None:
            return None
        goal.status = "completed"
        goal.updated_at = _now_iso()
        return goal

    def get_follow_up_goal(self, now: datetime | None = None) -> Goal | None:
        current = now or datetime.now(timezone.utc)
        eligible: list[Goal] = []
        for goal in self.goals:
            if goal.status != "active":
                continue
            if not goal.last_check_in_at:
                eligible.append(goal)
                continue
            try:
                last = datetime.fromisoformat(goal.last_check_in_at.replace("Z", "+00:00"))
                if last.tzinfo is None:
                    last = last.replace(tzinfo=timezone.utc)
                if (current - last).total_seconds() >= 4 * 60 * 60:
                    eligible.append(goal)
            except (TypeError, ValueError):
                eligible.append(goal)
        if not eligible:
            return None
        return max(eligible, key=lambda item: (item.priority, item.updated_at))

    def mark_checked_in(self, goal_id: str, at: datetime | None = None) -> None:
        goal = next((item for item in self.goals if item.id == goal_id), None)
        if goal:
            timestamp = (at or datetime.now(timezone.utc)).isoformat()
            goal.last_check_in_at = timestamp
            goal.updated_at = timestamp

    def list_goals(self, status: str | None = None) -> list[Goal]:
        values = self.goals
        if status:
            values = [goal for goal in values if goal.status == status]
        return sorted(
            values,
            key=lambda item: (
                item.status != "active",
                -item.priority,
                item.updated_at,
            ),
            reverse=False,
        )

    def build_prompt(self, limit: int = 8) -> str:
        selected = self.list_goals()[:max(0, limit)]
        if not selected:
            return "User-goal records: none."
        lines = [
            "User-stated goals and projects (context, not goals owned by Aletheia):"
        ]
        for goal in selected:
            lines.append(
                f"- id={goal.id}; status={goal.status}; description={goal.description}; "
                f"source={goal.source}; priority={goal.priority:.2f}; "
                f"confidence={goal.confidence:.2f}; "
                f"last_check_in={goal.last_check_in_at or 'never'}"
            )
        lines.append(
            "Use these only when relevant. Do not claim to have worked on a goal "
            "outside actual recorded actions."
        )
        return "\n".join(lines)

    def as_dict(self) -> dict:
        return {"goals": [goal.as_dict() for goal in self.goals]}

    def _extract_goal(self, message: str) -> str | None:
        for index, pattern in enumerate(self._PATTERNS):
            match = pattern.search(message)
            if not match:
                continue
            candidate = re.split(r"[\n.!?;]", match.group(1), maxsplit=1)[0].strip(" ,:")
            candidate = candidate[:180].strip()
            if len(candidate) < (5 if index == 0 else 9):
                continue
            normalized = _normalize(candidate)
            if normalized.startswith(("que ", "si ", "solo ", "mucho ", "un poco ")):
                continue
            if normalized in {_normalize(item) for item in self._GENERIC}:
                continue
            return candidate
        return None

    def _refresh_mentions(self, message: str) -> None:
        if not message:
            return
        normalized = _normalize(message)
        for goal in self.goals:
            if goal.status == "active" and _normalize(goal.description) in normalized:
                goal.last_mentioned_at = _now_iso()
                goal.updated_at = goal.last_mentioned_at
