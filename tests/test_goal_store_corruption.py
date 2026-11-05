from pathlib import Path

from app.infrastructure.goal_store import GoalStore


def test_corrupt_goal_file_is_preserved_for_recovery(tmp_path: Path) -> None:
    path = tmp_path / "goals.json"
    original = '{"goals": [ broken'
    path.write_text(original, encoding="utf-8")

    engine = GoalStore(str(path)).load_engine()

    assert engine.goals == []
    assert not path.exists()
    backups = list(tmp_path.glob("goals.json.corrupt-*"))
    assert len(backups) == 1
    assert backups[0].read_text(encoding="utf-8") == original


def test_missing_goal_file_starts_empty_without_creating_file(tmp_path: Path) -> None:
    path = tmp_path / "goals.json"
    engine = GoalStore(str(path)).load_engine()
    assert engine.goals == []
    assert not path.exists()
