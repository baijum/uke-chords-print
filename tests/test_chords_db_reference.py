"""
The generator checked against chords-db, an independent, hand-compiled
database of ukulele chord shapes (tests/data/chords-db).
"""

from __future__ import annotations

from collections import defaultdict

import pytest

from uke_chords_print.voicing_gen import (
    _assign_fingers,
    _note_to_pc,
    _required_pcs,
    _resolve_chord,
    describe_voicing,
    generate_voicings,
)

from .support import (
    CHORDS_DB_ERRATA,
    CHORDS_DB_FINGERING_ERRATA,
    FORMULAS,
    PITCH_CLASS,
    STANDARD_MIDI,
    chords_db,
    chords_db_shapes,
    fingering_problems,
    formula_pcs,
    usable_shapes,
)

ALL_SHAPES = chords_db_shapes()


# --- The reference data itself ---

def test_dataset_is_the_pinned_one():
    data = chords_db()
    assert data["tunings"]["standard"] == ["G4", "C4", "E4", "A4"]
    assert len(data["keys"]) == 12
    assert set(data["suffixes"]) == set(FORMULAS) | {"alt"}
    assert len(chords_db_shapes(include_errata=True)) == 2114


def test_midi_matches_frets_in_standard_tuning():
    for shape in ALL_SHAPES:
        expected = tuple(
            m + f for m, f in zip(STANDARD_MIDI, shape.frets) if f >= 0
        )
        assert shape.midi == expected, shape.id


def test_shapes_only_use_chord_tones():
    for shape in ALL_SHAPES:
        if shape.suffix in FORMULAS:
            allowed = formula_pcs(shape.key, shape.suffix, with_optional=True)
            assert shape.pitch_classes <= allowed, shape.id


def test_errata_really_are_wrong():
    # Keeps CHORDS_DB_ERRATA honest: each excluded shape has foreign notes
    errata = [
        s for s in chords_db_shapes(include_errata=True)
        if (s.key, s.suffix, s.frets) in CHORDS_DB_ERRATA
    ]
    assert len(errata) == len(CHORDS_DB_ERRATA)
    for shape in errata:
        assert not shape.pitch_classes <= formula_pcs(shape.key, shape.suffix)


# --- Generator coverage ---

def _required(chord_name: str) -> set[int]:
    components, root, bass, _ = _resolve_chord(chord_name)
    return _required_pcs(
        [_note_to_pc(n) for n in components], _note_to_pc(root),
        bass_pc=_note_to_pc(bass) if bass else None,
    )


def _shapes_by_chord() -> dict[str, list]:
    grouped = defaultdict(list)
    for shape in usable_shapes():
        grouped[shape.name].append(shape)
    return grouped


SHAPES_BY_CHORD = _shapes_by_chord()


@pytest.mark.parametrize("chord", sorted(SHAPES_BY_CHORD))
def test_generator_finds_every_textbook_shape(chord):
    """Every chart shape that has the tones the generator requires (within
    frets 0-9 and a 3-fret span) is among its candidates."""
    candidates = {
        v["frets"] for v in generate_voicings(chord, max_results=10**6)
    }
    required = _required(chord)
    for shape in SHAPES_BY_CHORD[chord]:
        if required <= shape.pitch_classes:
            assert shape.fret_string in candidates, shape.id


def test_skipped_textbook_shapes_are_rootless_extended_chords():
    """chords-db voices 5+ note chords without the root (and 13b5b9 without
    the 3rd); the generator drops the 5th and natural extensions first.
    Nothing else is skipped."""
    skipped = 0
    for shape in usable_shapes():
        required = _required(shape.name)
        if required <= shape.pitch_classes:
            continue
        skipped += 1
        assert len(FORMULAS[shape.suffix].intervals) >= 5, shape.id
        root = PITCH_CLASS[shape.key]
        missing = required - shape.pitch_classes
        if shape.suffix == "13b5b9":
            assert missing == {(root + 4) % 12}, shape.id
        else:
            assert missing == {root}, shape.id
    assert skipped > 0


# The first shape chords-db lists is the one chord charts show
COMMON_SUFFIXES = [
    "major", "minor", "7", "m7", "maj7", "6", "m6", "dim7", "aug", "m7b5",
    "7sus4",
]
CHART_SUFFIXES = COMMON_SUFFIXES + ["sus2", "sus4", "dim", "add9"]


@pytest.mark.parametrize("suffix", COMMON_SUFFIXES)
@pytest.mark.parametrize("key", list(chords_db()["keys"]))
def test_canonical_shape_is_offered(key, suffix):
    """The chart shape is among the generator's three voicings."""
    shape = next(
        s for s in ALL_SHAPES
        if s.key == key and s.suffix == suffix and s.position == 0
    )
    offered = [v["frets"] for v in generate_voicings(shape.name)]
    assert shape.fret_string in offered


def test_canonical_shape_is_usually_primary():
    """The chart shape comes first for 163 of 180 common chords (sus2,
    sus4 and dim charts disagree most). A guard against scoring changes;
    raise the bar when a recalibration improves it."""
    primary = sum(
        generate_voicings(s.name)[0]["frets"] == s.fret_string
        for s in ALL_SHAPES
        if s.position == 0 and s.suffix in CHART_SUFFIXES
    )
    assert primary >= 163


@pytest.mark.parametrize("suffix", ["major", "7", "m7", "6", "m6", "dim7",
                                    "aug", "m7b5", "add9"])
def test_canonical_shape_is_primary_in_every_key(suffix):
    for shape in ALL_SHAPES:
        if shape.suffix == suffix and shape.position == 0:
            voicings = generate_voicings(shape.name)
            assert voicings[0]["frets"] == shape.fret_string, shape.id


@pytest.mark.parametrize("name, frets", [
    ("C", "0003"), ("Am", "2000"), ("F", "2010"), ("G", "0232"),
    ("G7", "0212"), ("D", "2220"), ("Dm", "2210"), ("A", "2100"),
    ("C7", "0001"), ("Am7", "0000"), ("A7", "0100"), ("E7", "1202"),
    ("Cmaj7", "0002"), ("Em", "0432"), ("Fmaj7", "2413"), ("Dm7", "2213"),
    ("Cm7", "3333"), ("Fm7", "1313"), ("Bb", "3211"), ("E", "1402"),
    ("Bm", "4222"), ("B7", "2322"), ("D7", "2223"), ("Fm", "1013"),
    ("Cm", "0333"), ("Gm", "0231"), ("Em7", "0202"), ("Gmaj7", "0222"),
    ("Am6", "2423"),
])
def test_beginner_chords_are_primary(name, frets):
    assert generate_voicings(name)[0]["frets"] == frets


# --- Labels and fingering on every chords-db shape ---

@pytest.mark.parametrize("shape", [
    s for s in ALL_SHAPES
    if s.suffix in FORMULAS
], ids=lambda s: s.id)
def test_describe_voicing_names_sounding_notes(shape):
    notes, inversion = describe_voicing(shape.name, shape.frets)
    names = notes.split()
    assert len(names) == 4
    sounding = [n for n in names if n != "-"]
    assert [_note_to_pc(n) for n in sounding] == [m % 12 for m in shape.midi]

    components = _resolve_chord(shape.name)[0]
    lowest_pc = min(shape.midi) % 12
    pcs = [_note_to_pc(n) for n in components]
    labels = ["Root", "1st Inv", "2nd Inv", "3rd Inv"]
    idx = pcs.index(lowest_pc)
    assert inversion == (labels[idx] if idx < 4 else "")


@pytest.mark.parametrize("shape", ALL_SHAPES, ids=lambda s: s.id)
def test_fingering_is_playable(shape):
    """Fingering rules from AGENTS.md hold for every chart shape."""
    assert fingering_problems(shape.frets, _assign_fingers(shape.frets)) == []


@pytest.mark.parametrize("shape", ALL_SHAPES, ids=lambda s: s.id)
def test_chords_db_fingering_passes_checker(shape):
    """The checker accepts the hand-written chords-db fingerings, so it
    doesn't reject real-world technique (apart from known errata)."""
    fingers = "".join(str(f) for f in shape.fingers)
    problems = fingering_problems(shape.frets, fingers, strict=False)
    if (shape.key, shape.suffix, shape.frets) in CHORDS_DB_FINGERING_ERRATA:
        assert problems
    else:
        assert problems == []
