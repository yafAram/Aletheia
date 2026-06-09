import json
from dataclasses import fields
from pathlib import Path

from app.modules.personality_engine import PersonalityProfile


class PersonalityStore:
    """Persistencia local del perfil de personalidad de Aletheia."""

    def __init__(self, file_path: str = "storage/aletheia_personality.json") -> None:
        self.file_path = Path(file_path)

    def load(self) -> PersonalityProfile:
        if not self.file_path.exists():
            profile = PersonalityProfile()
            self.save(profile)
            return profile

        try:
            data = json.loads(self.file_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            profile = PersonalityProfile()
            self.save(profile)
            return profile

        allowed_fields = {field.name for field in fields(PersonalityProfile)}
        clean_data = {
            key: float(value)
            for key, value in data.items()
            if key in allowed_fields
        }

        return PersonalityProfile(**clean_data)

    def save(self, profile: PersonalityProfile) -> None:
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

        self.file_path.write_text(
            json.dumps(profile.as_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def reset(self) -> PersonalityProfile:
        profile = PersonalityProfile()
        self.save(profile)
        return profile