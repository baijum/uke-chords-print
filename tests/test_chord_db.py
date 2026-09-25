"""The chord lookup wrapper and the standard chord list."""

from __future__ import annotations

import pytest

from uke_chords_print import chord_db
from uke_chords_print.chord_db import (
    CHORD_ALIASES,
    STANDARD_CHORDS,
    list_all_chords,
    lookup_chord,
)
from uke_chords_print.voicing_gen import generate_voicings

from .support import ALL_TUNINGS


def test_standard_chords():
    assert len(STANDARD_CHORDS) == 108
    assert len(set(STANDARD_CHORDS)) == 108
    assert list_all_chords() == sorted(STANDARD_CHORDS)


@pytest.mark.parametrize("tuning", ALL_TUNINGS)
def test_every_standard_chord_has_a_voicing(tuning):
    for name in STANDARD_CHORDS:
        assert 1 <= len(lookup_chord(name, tuning=tuning)) <= 3, name


@pytest.mark.parametrize("alias, canonical", sorted(CHORD_ALIASES.items()))
def test_aliases_give_the_same_shapes(alias, canonical):
    assert ([v["frets"] for v in lookup_chord(alias)]
            == [v["frets"] for v in lookup_chord(canonical)])


def test_alias_used_when_name_fails(monkeypatch):
    calls = []

    def fake_generate(name, tuning):
        calls.append(name)
        if name == "Db":
            raise ValueError("nope")
        return generate_voicings(name, tuning=tuning)

    monkeypatch.setattr(chord_db, "generate_voicings", fake_generate)
    assert lookup_chord("Db")[0]["frets"] == "1114"
    assert calls == ["Db", "C#"]


@pytest.mark.parametrize("alias_result", [[], ValueError("alias")])
def test_alias_failure_keeps_original_error(monkeypatch, alias_result):
    def fake_generate(name, tuning):
        if name == "Db":
            raise ValueError("original")
        if isinstance(alias_result, Exception):
            raise alias_result
        return alias_result

    monkeypatch.setattr(chord_db, "generate_voicings", fake_generate)
    with pytest.raises(ValueError, match="original"):
        lookup_chord("Db")


def test_alias_not_tried_for_other_names(monkeypatch):
    calls = []
    monkeypatch.setattr(chord_db, "generate_voicings",
                        lambda name, tuning: calls.append(name) or [])
    assert lookup_chord("C") is None
    assert calls == ["C"]


def test_unknown_name_raises_original_error():
    with pytest.raises(ValueError, match="Cannot parse chord 'Cxyz'"):
        lookup_chord("Cxyz")


def test_no_voicing_returns_none(monkeypatch):
    monkeypatch.setattr(chord_db, "generate_voicings", lambda n, tuning: [])
    assert lookup_chord("C") is None
