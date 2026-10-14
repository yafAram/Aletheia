"""Frozen top-level snapshot of the cognitive context for one chat turn.

The workspace contains presentation-ready prompt sections as well as state
snapshots for observability. It does not own engines or persistence.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class CognitiveWorkspace:
    """A consistent, per-turn snapshot assembled by the application layer."""

    memory_context: str = ""
    emotional_prompt: str = ""
    personality_prompt: str = ""
    self_prompt: str = ""
    self_relationship_prompt: str = ""
    significant_memory_prompt: str = ""
    bond_prompt: str = ""
    initiative_prompt: str = ""
    goals_prompt: str = ""
    emotion_state: dict[str, Any] = field(default_factory=dict)
    personality_state: dict[str, Any] = field(default_factory=dict)
    self_state: dict[str, Any] = field(default_factory=dict)
    relationship_state: dict[str, Any] = field(default_factory=dict)
    bond_state: dict[str, Any] = field(default_factory=dict)
    initiative_state: dict[str, Any] = field(default_factory=dict)

    def prompt_sections(self) -> tuple[str, ...]:
        """Return non-empty prompt sections in a stable order."""
        return tuple(
            section.strip()
            for section in (
                self.self_prompt,
                self.self_relationship_prompt,
                self.significant_memory_prompt,
                self.bond_prompt,
                self.goals_prompt,
                self.initiative_prompt,
                self.personality_prompt,
                self.emotional_prompt,
            )
            if section and section.strip()
        )
