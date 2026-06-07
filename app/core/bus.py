import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field

from app.core.events import Event, EventType

EventHandler = Callable[[Event], Awaitable[None]]


@dataclass(slots=True)
class EventBus:
    _queue: asyncio.PriorityQueue = field(default_factory=asyncio.PriorityQueue)
    _handlers: dict[EventType, list[EventHandler]] = field(default_factory=dict)

    def subscribe(self, event_type: EventType, handler: EventHandler) -> None:
        self._handlers.setdefault(event_type, []).append(handler)

    async def publish(self, event: Event) -> None:
        await self._queue.put((event.priority, event.created_at.timestamp(), event))

    async def run_forever(self) -> None:
        while True:
            _, _, event = await self._queue.get()
            handlers = self._handlers.get(event.type, [])
            await asyncio.gather(*(handler(event) for handler in handlers))
            self._queue.task_done()
