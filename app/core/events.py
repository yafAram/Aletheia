from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from uuid import uuid4


class EventType(StrEnum):
    USER_MESSAGE = "user_message"
    ASSISTANT_RESPONSE = "assistant_response"
    MEMORY_WRITE = "memory_write"
    ERROR = "error"


@dataclass(slots=True, frozen=True)
class Event:
    type: EventType
    payload: dict
    priority: int = 5
    id: str = field(default_factory=lambda: str(uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
