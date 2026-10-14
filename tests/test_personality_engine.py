from app.modules.personality_engine import PersonalityEngine, PersonalityProfile


def test_personality_prompt_translates_traits_into_behavior_without_claiming_feelings() -> None:
    prompt = PersonalityEngine(
        profile=PersonalityProfile(
            warmth=0.72,
            curiosity=0.64,
            playfulness=0.38,
            empathy=0.70,
            confidence=0.52,
            independence=0.35,
            tenderness=0.58,
            spontaneity=0.42,
            formality=0.20,
        )
    ).build_personality_prompt()

    assert "respectfully disagree" in prompt
    assert "respecting silence" in prompt
    assert "without claiming human feelings" in prompt
