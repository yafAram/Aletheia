from dataclasses import dataclass


@dataclass(slots=True)
class EmotionState:
    curiosity: float = 0.50
    calm: float = 0.70
    energy: float = 0.60


class EmotionEngine:
    def __init__(self) -> None:
        self.state = EmotionState()

    def update_from_text(self, text: str) -> EmotionState:
        lowered = text.lower()
        if "gracias" in lowered:
            self.state.calm = min(1.0, self.state.calm + 0.05)
        if "urgente" in lowered or "error" in lowered:
            self.state.energy = min(1.0, self.state.energy + 0.10)
            self.state.calm = max(0.0, self.state.calm - 0.10)
        return self.state
