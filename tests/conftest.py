"""Test fixtures shared by every module."""

from __future__ import annotations

import pytest

from uke_chords_print import fonts


@pytest.fixture(autouse=True)
def _reset_missing_characters(monkeypatch):
    """Start each test with no characters recorded as unprintable, since
    fonts keeps them for the whole process (one CLI run)."""
    monkeypatch.setattr(fonts, "_missing", set())
