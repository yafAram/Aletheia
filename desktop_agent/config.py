"""Configuration for the host-side desktop agent."""
from __future__ import annotations

import json
import os
import platform
import secrets
from dataclasses import dataclass
from pathlib import Path


_DEFAULT_APPS: dict[str, dict[str, list[str]]] = {
    "notepad": {
        "Windows": ["notepad.exe"],
        "Linux": ["mousepad"],
    },
    "calculator": {
        "Windows": ["calc.exe"],
        "Linux": ["gnome-calculator"],
    },
    "file_manager": {
        "Windows": ["explorer.exe"],
        "Linux": ["xdg-open", "."],
    },
}


@dataclass(frozen=True, slots=True)
class AgentSettings:
    host: str
    port: int
    token: str
    cors_origins: tuple[str, ...]
    allowed_apps: dict[str, list[str]]
    max_capture_width: int
    token_file: str | None = None


def _allowed_apps_from_env() -> dict[str, list[str]]:
    """Allow only JSON string arrays. No shell strings are ever accepted."""
    raw = os.getenv("ALETHEIA_DESKTOP_ALLOWED_APPS", "").strip()
    if not raw:
        os_name = platform.system()
        return {
            alias: commands[os_name]
            for alias, commands in _DEFAULT_APPS.items()
            if os_name in commands
        }

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError("ALETHEIA_DESKTOP_ALLOWED_APPS debe ser JSON válido") from exc
    if not isinstance(parsed, dict):
        raise ValueError("ALETHEIA_DESKTOP_ALLOWED_APPS debe ser un objeto JSON")

    result: dict[str, list[str]] = {}
    for alias, command in parsed.items():
        if not isinstance(alias, str) or not alias.replace("_", "").isalnum():
            raise ValueError("Los alias de aplicaciones solo pueden contener letras, números y _")
        if not isinstance(command, list) or not command or not all(
            isinstance(part, str) and part and "\\x00" not in part for part in command
        ):
            raise ValueError(f"Comando inválido para la aplicación {alias!r}")
        result[alias] = command
    return result


def _shared_token_file() -> Path:
    configured = os.getenv("ALETHEIA_DESKTOP_TOKEN_FILE", "").strip()
    if configured:
        return Path(configured).expanduser()
    return Path.home() / ".config" / "aletheia" / "desktop-agent-token"


def _ensure_shared_token(path: Path) -> str:
    """Create one private token file if needed; existing file is canonical."""
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    try:
        path.parent.chmod(0o700)
    except OSError:
        pass
    if not path.exists():
        # An explicit legacy env token is imported once, then the file becomes canonical.
        initial = os.getenv("ALETHEIA_DESKTOP_TOKEN", "").strip() or secrets.token_urlsafe(48)
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(initial + "\n")
            stream.flush()
            os.fsync(stream.fileno())
    try:
        path.chmod(0o600)
    except OSError:
        pass
    token = path.read_text(encoding="utf-8").strip()
    if len(token) < 20:
        raise RuntimeError(f"El archivo de token compartido no contiene un secreto válido: {path}")
    return token


def get_agent_settings() -> AgentSettings:
    token_file = _shared_token_file()
    token = _ensure_shared_token(token_file)
    origins = tuple(
        item.strip()
        for item in os.getenv(
            "ALETHEIA_DESKTOP_CORS_ORIGINS",
            "http://localhost:5173,http://127.0.0.1:5173",
        ).split(",")
        if item.strip()
    )
    return AgentSettings(
        host=os.getenv("ALETHEIA_DESKTOP_HOST", "127.0.0.1"),
        port=int(os.getenv("ALETHEIA_DESKTOP_PORT", "8765")),
        token=token,
        cors_origins=origins,
        allowed_apps=_allowed_apps_from_env(),
        max_capture_width=max(320, min(3840, int(os.getenv("ALETHEIA_DESKTOP_MAX_CAPTURE_WIDTH", "1920")))),
        token_file=str(token_file),
    )
