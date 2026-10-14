"""Shared deterministic text normalization for Spanish keyword heuristics."""

from __future__ import annotations

import unicodedata


def normalize_text(value: str) -> str:
    """Case-fold, remove diacritics, and collapse whitespace for comparisons only."""
    decomposed = unicodedata.normalize("NFKD", value.casefold())
    without_marks = "".join(char for char in decomposed if not unicodedata.combining(char))
    return " ".join(without_marks.split())
