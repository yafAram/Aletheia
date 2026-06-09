from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile


class AudioStore:
    """Guarda archivos de audio temporales para STT."""

    def __init__(self, base_path: str = "storage/audio") -> None:
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    async def save_upload(self, file: UploadFile) -> str:
        suffix = Path(file.filename or "").suffix.lower()

        allowed_extensions = {
            ".wav",
            ".mp3",
            ".m4a",
            ".webm",
            ".ogg",
            ".flac",
        }

        if suffix not in allowed_extensions:
            raise ValueError(
                "Unsupported audio format. Use wav, mp3, m4a, webm, ogg or flac."
            )

        filename = f"{uuid4()}{suffix}"
        path = self.base_path / filename

        content = await file.read()
        path.write_bytes(content)

        return str(path)