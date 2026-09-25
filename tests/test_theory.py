"""
Chord-name resolution checked against textbook interval formulas.

The formulas in support.FORMULAS are written out by hand and validated
against the chords-db shapes (test_chords_db_reference.py), so these tests
don't just compare pychord with itself.
"""

from __future__ import annotations

import pytest

from uke_chords_print.chord_db import STANDARD_CHORDS
from uke_chords_print.voicing_gen import (
    _known_quality,
    _note_to_pc,
    _pychord_name,
    _resolve_chord,
)

from .support import (
    FORMULAS,
    PITCH_CLASS,
    ROOTS,
    formula_pcs,
)

SUPPORTED = list(FORMULAS)


def _pcs(chord_name: str) -> set[int]:
    components, _, _, _ = _resolve_chord(chord_name)
    return {_note_to_pc(n) for n in components}


@pytest.mark.parametrize("root", ROOTS)
@pytest.mark.parametrize("suffix", SUPPORTED)
def test_chord_tones_match_formula(suffix, root):
    got = _pcs(root + FORMULAS[suffix].quality)
    assert formula_pcs(root, suffix) <= got
    assert got <= formula_pcs(root, suffix, with_optional=True)


@pytest.mark.parametrize("root", ROOTS)
@pytest.mark.parametrize("suffix", SUPPORTED)
def test_root_is_first_component(suffix, root):
    components, chord_root, bass, base = _resolve_chord(
        root + FORMULAS[suffix].quality
    )
    assert _note_to_pc(chord_root) == PITCH_CLASS[root]
    assert _note_to_pc(components[0]) == PITCH_CLASS[root]
    assert bass is None
    assert base == components


# Chord-chart spellings -> the name pychord knows for the same chord
EQUIVALENT_SPELLINGS = [
    ("C+", "Caug"),
    ("C°", "Cdim"),
    ("Co", "Cdim"),
    ("C°7", "Cdim7"),
    ("Co7", "Cdim7"),
    ("Cø", "Cm7b5"),
    ("Cø7", "Cm7b5"),
    ("CΔ", "Cmaj7"),
    ("CΔ7", "Cmaj7"),
    ("CΔ9", "Cmaj9"),
    ("CM7", "Cmaj7"),
    ("CMaj7", "Cmaj7"),
    ("Cma7", "Cmaj7"),
    ("Cma9", "Cmaj9"),
    ("CM", "C"),
    ("Cmin", "Cm"),
    ("Cmi", "Cm"),
    ("C-", "Cm"),
    ("Cmin7", "Cm7"),
    ("Cmi7", "Cm7"),
    ("C-7", "Cm7"),
    ("Cm/maj7", "CmM7"),
    ("Cm(maj7)", "CmM7"),
    ("CmΔ7", "CmM7"),
    ("Cmmaj7", "CmM7"),
    ("C-Δ7", "CmM7"),
    ("C7(#9)", "C7#9"),
    ("C7(b9)", "C7b9"),
    ("C(add9)", "Cadd9"),
    ("C+7", "C7+5"),
    ("C7+", "C7+5"),
    ("Caug7", "C7+5"),
    ("C7aug", "C7+5"),
    ("C+maj7", "Cmaj7+5"),
    ("Cmaj7+", "Cmaj7+5"),
    ("C7sus", "C7sus4"),
    ("Cmaj7#5", "Cmaj7+5"),
    ("CΔ7#5", "Cmaj7+5"),
    ("Caug9", "C9+5"),
    ("C+9", "C9+5"),
    ("C9+", "C9+5"),
    ("CM7b5", "Cmaj7b5"),
    ("Cmaj7-5", "Cmaj7b5"),
    ("CM11", "Cmaj11"),
    ("Cm9-5", "Cm9b5"),
    ("Cmmaj9", "CmM9"),
    ("Cm(maj9)", "CmM9"),
    ("CmΔ9", "CmM9"),
    ("Cmmaj7b5", "CmM7b5"),
    ("Cmmaj11", "CmM11"),
    ("Cmi9", "Cm9"),
    ("Cadd2", "Cadd9"),
    ("C(add2)", "Cadd9"),
    ("Cmadd2", "Cmadd9"),
    ("B♭", "Bb"),
    ("B♭m7", "Bbm7"),
    ("F♯", "F#"),
    ("F♯m7♭5", "F#m7b5"),
    ("C6/9", "C69"),
    ("A7/9", "A9"),
    ("G7/13", "G13"),
    ("Cmaj7/9", "Cmaj9"),
    ("Cm6/9", "Cm69"),
    ("C6/9/E", "C69/E"),
]


@pytest.mark.parametrize("spelling, canonical", EQUIVALENT_SPELLINGS)
def test_equivalent_spellings(spelling, canonical):
    assert _resolve_chord(spelling)[0] == _resolve_chord(canonical)[0]


@pytest.mark.parametrize(
    "name", STANDARD_CHORDS + [
        r + FORMULAS[s].quality for r in ("C", "F#") for s in SUPPORTED
        if _known_quality(FORMULAS[s].quality)
    ]
)
def test_pychord_names_pass_through_unchanged(name):
    assert _pychord_name(name) == name


class TestSlashChords:
    def test_bass_note_is_added_below(self):
        components, root, bass, base = _resolve_chord("C/Bb")
        assert components[0] == "Bb"
        assert root == "C"
        assert bass == "Bb"
        assert base == ["C", "E", "G"]

    def test_chord_tone_bass_keeps_chord_above(self):
        components, _, bass, base = _resolve_chord("Am7/G")
        assert bass == "G"
        assert base == ["A", "C", "E", "G"]
        assert {_note_to_pc(n) for n in components} == {9, 0, 4, 7}

    def test_respelled_extension_keeps_bass(self):
        _, _, bass, base = _resolve_chord("A7/9/E")
        assert bass == "E"
        assert base == _resolve_chord("A9")[0]


class TestRejectedNames:
    @pytest.mark.parametrize("name", ["C/9", "Am/11", "G7/5", "C6/9/2"])
    def test_number_after_slash(self, name):
        with pytest.raises(ValueError, match="number after '/'"):
            _resolve_chord(name)

    @pytest.mark.parametrize("name", ["H7", "Cxyz", "", "c", "C#m7q"])
    def test_unknown_names(self, name):
        with pytest.raises(ValueError, match="Cannot parse chord"):
            _resolve_chord(name)

    def test_error_names_what_was_typed(self):
        # The o -> dim rule must not leak into the message ("dimmit3")
        with pytest.raises(ValueError) as exc:
            _resolve_chord("Comit3")
        assert "omit3" in str(exc.value)
        assert "dimmit3" not in str(exc.value)


@pytest.mark.parametrize("name, pc", [
    ("C", 0), ("B#", 0), ("Dbb", 0), ("C#", 1), ("Db", 1), ("E#", 5),
    ("Fb", 4), ("Cb", 11), ("A##", 11), ("Gbb", 5),
])
def test_note_to_pc_enharmonics(name, pc):
    assert _note_to_pc(name) == pc


def test_note_to_pc_rejects_unknown():
    with pytest.raises(ValueError):
        _note_to_pc("H")
