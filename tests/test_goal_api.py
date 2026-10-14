from fastapi.testclient import TestClient

from app.api.routes import (
    get_goal_engine,
    get_goal_store,
    get_initiative_engine,
    get_initiative_store,
)
from app.infrastructure.goal_store import GoalStore
from app.infrastructure.initiative_store import InitiativeStore
from app.main import create_app
from app.modules.goal_engine import GoalEngine
from app.modules.initiative_engine import InitiativeEngine


def test_goal_api_create_and_complete_goal(tmp_path) -> None:
    app = create_app()
    goal_engine = GoalEngine()
    goal_store = GoalStore(str(tmp_path / "goals.json"))
    app.dependency_overrides[get_goal_engine] = lambda: goal_engine
    app.dependency_overrides[get_goal_store] = lambda: goal_store

    try:
        with TestClient(app) as client:
            created = client.post(
                "/api/goals",
                json={"description": "Probar los objetivos persistentes", "priority": 0.7},
            )
            assert created.status_code == 200
            goal_id = created.json()["id"]

            listed = client.get("/api/goals")
            assert listed.status_code == 200
            assert listed.json()["total"] == 1

            completed = client.post(f"/api/goals/{goal_id}/complete")
            assert completed.status_code == 200
            assert completed.json()["status"] == "completed"
            assert goal_store.load_engine().goals[0].status == "completed"
    finally:
        app.dependency_overrides.clear()


def test_initiative_api_persists_autonomy_toggle(tmp_path) -> None:
    app = create_app()
    engine = InitiativeEngine()
    store = InitiativeStore(
        state_path=str(tmp_path / "state.json"),
        observations_path=str(tmp_path / "observations.json"),
        actions_path=str(tmp_path / "actions.json"),
    )
    app.dependency_overrides[get_initiative_engine] = lambda: engine
    app.dependency_overrides[get_initiative_store] = lambda: store

    try:
        with TestClient(app) as client:
            response = client.post("/api/initiative/autonomy", json={"enabled": False})
            assert response.status_code == 200
            assert response.json()["state"]["autonomy_enabled"] is False
            assert store.load_engine().state.autonomy_enabled is False
    finally:
        app.dependency_overrides.clear()
