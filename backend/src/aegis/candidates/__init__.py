"""Deterministic candidate engine: gates, confluence, sizing, exit plan (C-2)."""

from aegis.candidates.confluence import (
    ConfluenceInput,
    ConfluenceParams,
    evaluate_confluence,
)

__all__ = ["ConfluenceInput", "ConfluenceParams", "evaluate_confluence"]
