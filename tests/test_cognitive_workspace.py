from app.application.prompt_builder import PromptBuilder
from app.domain.cognitive_workspace import CognitiveWorkspace


def test_workspace_omits_empty_prompt_sections_and_preserves_order() -> None:
    workspace = CognitiveWorkspace(
        memory_context="recuerdo relevante",
        self_prompt="autoconocimiento",
        bond_prompt="vínculo",
        emotional_prompt="estado emocional",
    )

    assert workspace.prompt_sections() == (
        "autoconocimiento",
        "vínculo",
        "estado emocional",
    )


def test_prompt_builder_includes_base_memory_and_sections() -> None:
    workspace = CognitiveWorkspace(
        memory_context="El usuario está construyendo Aletheia.",
        personality_prompt="Personalidad estable.",
        emotional_prompt="Estado emocional actual.",
    )

    prompt = PromptBuilder(base_prompt="Identidad base.").build(workspace)

    assert prompt.startswith("Identidad base.")
    assert "El usuario está construyendo Aletheia." in prompt
    assert "Personalidad estable." in prompt
    assert "Estado emocional actual." in prompt
    assert "Respond to the current user message." in prompt


def test_prompt_builder_handles_empty_memory_and_sections() -> None:
    prompt = PromptBuilder(base_prompt="Identidad base.").build(CognitiveWorkspace())

    assert "No relevant semantic memories retrieved." in prompt
    assert "Identidad base." in prompt