"""Background loop for low-pressure conversational initiative."""

from __future__ import annotations

import asyncio
import logging
from app.infrastructure.goal_store import GoalStore
from app.infrastructure.initiative_store import InitiativeStore
from app.modules.goal_engine import GoalEngine
from app.modules.initiative_engine import InitiativeEngine

logger = logging.getLogger(__name__)


class InitiativeAutonomyLoop:
    """Periodically evaluate whether a proactive conversational prompt is warranted.

    The loop only queues a text suggestion in local state. It does not call the LLM,
    access devices, execute tools, or perform actions outside the conversation UI.
    """

    def __init__(
        self,
        engine: InitiativeEngine,
        store: InitiativeStore,
        *,
        tick_seconds: int = 30,
        idle_threshold_seconds: int = 1800,
        cooldown_seconds: int = 1800,
        goal_engine: GoalEngine | None = None,
        goal_store: GoalStore | None = None,
    ) -> None:
        self.engine = engine
        self.store = store
        self.tick_seconds = max(1, tick_seconds)
        self.idle_threshold_seconds = max(0, idle_threshold_seconds)
        self.cooldown_seconds = max(0, cooldown_seconds)
        self.goal_engine = goal_engine
        self.goal_store = goal_store
        self._stop_event = asyncio.Event()

    async def run(self) -> None:
        logger.info(
            "Conversational autonomy loop started (tick=%ss, idle=%ss)",
            self.tick_seconds,
            self.idle_threshold_seconds,
        )
        while not self._stop_event.is_set():
            try:
                await asyncio.wait_for(
                    self._stop_event.wait(), timeout=self.tick_seconds
                )
                continue
            except asyncio.TimeoutError:
                pass

            try:
                action = self.engine.evaluate_idle_initiative(
                    idle_threshold_seconds=self.idle_threshold_seconds,
                    cooldown_seconds=self.cooldown_seconds,
                )
                if action is not None:
                    goal = (
                        self.goal_engine.get_follow_up_goal()
                        if self.goal_engine
                        else None
                    )
                    if goal is not None:
                        action.goal_id = goal.id
                        action.suggested_message = (
                            f"Me acordé de que estabas trabajando en "
                            f"«{goal.description}». ¿Cómo va? Si ahora no te "
                            "apetece hablar del tema, lo retomamos cuando quieras."
                        )
                        action.reason = (
                            "Seguimiento de un objetivo que el usuario expresó "
                            "explícitamente."
                        )
                        self.goal_engine.mark_checked_in(goal.id)
                    # Persist the queued initiative first so a goal-store failure
                    # cannot consume the cooldown and silently lose the action.
                    self.store.save_engine(self.engine)
                    if action.goal_id and self.goal_engine and self.goal_store:
                        self.goal_store.save_engine(self.goal_engine)
                    logger.info(
                        "Queued proactive initiative type=%s goal_id=%s",
                        action.type,
                        action.goal_id,
                    )
            except Exception:
                # A failed initiative check must not crash the API server.
                logger.exception("Failed while evaluating conversational initiative")

    def stop(self) -> None:
        self._stop_event.set()
