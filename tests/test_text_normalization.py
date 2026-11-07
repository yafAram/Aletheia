from app.core.text_normalization import normalize_text


def test_normalize_text_removes_accents_and_case_differences() -> None:
    assert normalize_text("¿Qué te gustaría hacer?") == "¿que te gustaria hacer?"


def test_normalize_text_collapses_whitespace() -> None:
    assert normalize_text("  Aletheia\n\t usa   memoria  ") == "aletheia usa memoria"


def test_normalize_text_preserves_original_input() -> None:
    value = "Árbol   Azul"
    normalize_text(value)
    assert value == "Árbol   Azul"
