from datetime import datetime, timedelta, timezone
import asyncio

from app.application.chat_use_case import ChatUseCase
from app.infrastructure.goal_store import GoalStore
from app.infrastructure.initiative_store import InitiativeStore
from app.modules.goal_engine import GoalEngine
from app.modules.initiative_engine import InitiativeEngine, InitiativeState


def test_goal_engine_tracks_explicit_project_and_deduplicates() -> None:
    engine = GoalEngine()

    first = engine.observe_user_message("Quiero desarrollar Aletheia para que tenga memoria persistente.")
    second = engine.observe_user_message("Quiero desarrollar Aletheia para que tenga memoria persistente.")

    assert first is not None
    assert second is not None
    assert first.id == second.id
    assert len(engine.goals) == 1
    assert "Aletheia" in first.description


def test_goal_engine_does_not_infer_goal_from_question() -> None:
    engine = GoalEngine()
    assert engine.observe_user_message("¿Qué te gustaría hacer hoy?") is None
    assert engine.goals == []


def test_goal_engine_manual_goal_completion_and_prompt() -> None:
    engine = GoalEngine()
    goal = engine.add_goal("Integrar memoria autobiográfica", priority=0.8)
    assert "Integrar memoria autobiográfica" in engine.build_prompt()
    completed = engine.complete_goal(goal.id)
    assert completed is not None
    assert completed.status == "completed"
    assert engine.get_follow_up_goal() is None


def test_goal_store_round_trip_is_atomic_and_tolerates_missing_file(tmp_path) -> None:
    store = GoalStore(str(tmp_path / "goals.json"))
    engine = store.load_engine()
    goal = engine.add_goal("Crear un sistema de objetivos")
    store.save_engine(engine)

    loaded = store.load_engine()
    assert len(loaded.goals) == 1
    assert loaded.goals[0].id == goal.id
    assert loaded.goals[0].description == goal.description


def test_idle_initiative_requires_idle_period_and_respects_cooldown() -> None:
    engine = InitiativeEngine()
    base = datetime(2026, 1, 1, tzinfo=timezone.utc)
    engine.register_observation(
        source="chat",
        text_observation="Estoy construyendo algo.",
        confidence=0.8,
    )
    engine.observations[-1].created_at = base.isoformat()

    assert engine.evaluate_idle_initiative(1800, 1800, base + timedelta(minutes=20)) is None
    action = engine.evaluate_idle_initiative(1800, 1800, base + timedelta(minutes=31))
    assert action is not None
    assert action.origin == "autonomous"
    assert engine.evaluate_idle_initiative(1800, 1800, base + timedelta(minutes=40)) is None


def test_idle_initiative_can_be_paused_and_delivery_is_idempotent() -> None:
    engine = InitiativeEngine(state=InitiativeState(autonomy_enabled=False))
    base = datetime(2026, 1, 1, tzinfo=timezone.utc)
    engine.register_observation(source="chat", text_observation="Hola", confidence=0.8)
    engine.observations[-1].created_at = base.isoformat()
    assert engine.evaluate_idle_initiative(1, 0, base + timedelta(minutes=5)) is None

    engine.state.autonomy_enabled = True
    action = engine.evaluate_idle_initiative(1, 0, base + timedelta(minutes=5))
    assert action is not None
    assert len(engine.pending_autonomous_actions()) == 1

    delivered = engine.mark_action_delivered(action.id)
    assert delivered is not None
    assert delivered.delivered_at is not None
    assert engine.pending_autonomous_actions() == []
    assert engine.mark_action_delivered(action.id) is delivered


def test_initiative_store_round_trip_preserves_delivery_and_autonomy(tmp_path) -> None:
    store = InitiativeStore(
        state_path=str(tmp_path / "state.json"),
        observations_path=str(tmp_path / "observations.json"),
        actions_path=str(tmp_path / "actions.json"),
    )
    engine = InitiativeEngine()
    base = datetime(2026, 1, 1, tzinfo=timezone.utc)
    engine.register_observation(source="chat", text_observation="Hola", confidence=0.8)
    engine.observations[-1].created_at = base.isoformat()
    action = engine.evaluate_idle_initiative(1, 0, base + timedelta(minutes=5))
    assert action is not None
    engine.mark_action_delivered(action.id)
    engine.state.autonomy_enabled = False
    store.save_engine(engine)

    loaded = store.load_engine()
    assert loaded.state.autonomy_enabled is False
    assert loaded.actions[0].delivered_at is not None
    assert loaded.pending_autonomous_actions() == []


def test_initiative_normalizes_spanish_accents_for_curiosity_signals() -> None:
    engine = InitiativeEngine()
    engine.process_user_message("¿De qué te gustaría hablar?")
    assert engine.state.curiosity_pressure > 0.46



def test_chat_use_case_persists_goal_and_includes_it_in_prompt(tmp_path) -> None:
    class FakeLlm:
        system_prompt = ""

        async def generate(self, message: str, system_prompt: str) -> str:
            self.system_prompt = system_prompt
            return "Podemos construirlo paso a paso."

    llm = FakeLlm()
    goal_engine = GoalEngine()
    goal_store = GoalStore(str(tmp_path / "goals.json"))
    use_case = ChatUseCase(llm=llm, goal_engine=goal_engine, goal_store=goal_store)

    result = asyncio.run(
        use_case.execute("Quiero desarrollar Aletheia con memoria persistente.", use_memory=False)
    )

    assert result.response == "Podemos construirlo paso a paso."
    assert "Aletheia con memoria persistente" in llm.system_prompt
    assert len(goal_store.load_engine().goals) == 1
