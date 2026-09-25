"""
Properties of generated voicings, checked from first principles for every
standard chord in every tuning, plus unit tests of the generator's helpers.
"""

from __future__ import annotations

import pytest

from uke_chords_print.chord_db import STANDARD_CHORDS
from uke_chords_print.tunings import get_tuning_midi
from uke_chords_print.voicing_gen import (
    _assign_fingers,
    _difficulty_label,
    _finger_units,
    _note_to_pc,
    _required_pcs,
    _resolve_chord,
    _score_voicing,
    compute_starting_fret,
    describe_voicing,
    generate_voicings,
)

from .support import ALL_TUNINGS, PITCH_CLASS, ROOTS, sounding_midi

INVERSIONS = ["Root", "1st Inv", "2nd Inv", "3rd Inv"]
EXTENDED = ["C9", "Am9", "G13", "Cmaj9", "D11", "E7b9", "Bb7#9", "C69",
            "A7/9/E", "C/G", "Am7/G", "D/F#"]


def _frets(voicing: dict) -> tuple[int, ...]:
    return tuple(int(ch) for ch in voicing["frets"])


def _transpose(chord: str, semitones: int) -> str:
    """Transpose a chord name, including any slash bass note."""
    def move(name: str) -> str:
        note = name[:2] if name[1:2] in ("#", "b") else name[:1]
        return ROOTS[(PITCH_CLASS[note] + semitones) % 12] + name[len(note):]

    head, sep, bass = chord.rpartition("/")
    if sep and bass[:1].isalpha():
        return move(head) + "/" + move(bass)
    return move(chord)


@pytest.mark.parametrize("tuning", ALL_TUNINGS)
@pytest.mark.parametrize("chord", STANDARD_CHORDS + EXTENDED)
def test_voicing_properties(chord, tuning):
    voicings = generate_voicings(chord, tuning=tuning)
    assert 1 <= len(voicings) <= 3
    assert len({v["frets"] for v in voicings}) == len(voicings)

    components, root, bass, base = _resolve_chord(chord)
    chord_pcs = {_note_to_pc(n) for n in components}
    base_pcs = [_note_to_pc(n) for n in base]
    required = _required_pcs(
        [_note_to_pc(n) for n in components], _note_to_pc(root),
        bass_pc=_note_to_pc(bass) if bass else None,
    )
    tuning_midi = get_tuning_midi(tuning)
    scores = []

    for v in voicings:
        frets = _frets(v)
        assert len(v["frets"]) == 4 and v["frets"].isdigit()
        fretted = [f for f in frets if f > 0]
        if fretted:
            assert max(fretted) - min(fretted) <= 3

        midi = sounding_midi(v["frets"], tuning_midi)
        pcs = [m % 12 for m in midi]
        assert set(pcs) <= chord_pcs
        assert required <= set(pcs)

        # Notes name the sounding pitches, spelled as the chord spells them
        names = v["notes"].split()
        assert [_note_to_pc(n) for n in names] == pcs
        assert set(names) <= set(components)

        # Inversion comes from the lowest pitch, not the leftmost string
        idx = base_pcs.index(min(midi) % 12) if min(midi) % 12 in base_pcs else 9
        assert v["inversion"] == (INVERSIONS[idx] if idx < 4 else "")

        assert v.get("starting_fret", 1) == compute_starting_fret(frets)
        assert v["fingers"] == _assign_fingers(frets)
        score = _score_voicing(frets)
        assert v["difficulty"] == _difficulty_label(score)
        scores.append(score)

    assert scores == sorted(scores)


@pytest.mark.parametrize("chord", STANDARD_CHORDS + EXTENDED)
def test_d_tuning_is_standard_up_a_tone(chord):
    """ADF#B is GCEA two semitones up, so chord X in standard and X+2 in
    D tuning use the same shapes."""
    standard = generate_voicings(chord, tuning="standard")
    d_tuning = generate_voicings(_transpose(chord, 2), tuning="d-tuning")
    key = [(v["frets"], v["fingers"], v["inversion"]) for v in standard]
    assert key == [(v["frets"], v["fingers"], v["inversion"])
                   for v in d_tuning]


@pytest.mark.parametrize("chord", STANDARD_CHORDS + EXTENDED)
def test_baritone_is_low_g_down_a_fourth(chord):
    """DGBE is linear GCEA five semitones down."""
    baritone = generate_voicings(chord, tuning="baritone")
    low_g = generate_voicings(_transpose(chord, 5), tuning="low-g")
    key = [(v["frets"], v["fingers"], v["inversion"]) for v in baritone]
    assert key == [(v["frets"], v["fingers"], v["inversion"]) for v in low_g]


@pytest.mark.parametrize("chord", STANDARD_CHORDS)
def test_low_g_uses_standard_shapes(chord):
    """Low-G only moves the G string down an octave: same pitch classes,
    same shapes; only the inversion can change."""
    standard = generate_voicings(chord, tuning="standard")
    low_g = generate_voicings(chord, tuning="low-g")
    assert [v["frets"] for v in standard] == [v["frets"] for v in low_g]
    assert [v["notes"] for v in standard] == [v["notes"] for v in low_g]


def test_low_g_changes_inversion():
    # C 0003: the high G string isn't the bass in standard; low G is
    assert generate_voicings("C", tuning="standard")[0]["inversion"] == "Root"
    assert generate_voicings("C", tuning="low-g")[0]["inversion"] == "2nd Inv"


@pytest.mark.parametrize("tuning", ALL_TUNINGS)
@pytest.mark.parametrize("root", ROOTS)
@pytest.mark.parametrize("quality", ["13", "maj13", "13b9"])
def test_thirteenth_chords_avoid_the_eleventh(quality, root, tuning):
    """pychord includes the natural 11th in 13th chords; it clashes with
    the major 3rd, so no candidate voicing may contain it."""
    eleventh = (PITCH_CLASS[root] + 5) % 12
    for v in generate_voicings(root + quality, tuning=tuning,
                               max_results=10**6):
        midi = sounding_midi(v["frets"], get_tuning_midi(tuning))
        assert eleventh not in {m % 12 for m in midi}, v["frets"]


class TestSearchLimits:
    def test_max_results(self):
        assert len(generate_voicings("C", max_results=1)) == 1
        assert len(generate_voicings("C", max_results=10)) == 10

    def test_max_span(self):
        for v in generate_voicings("C", max_span=1, max_results=100):
            fretted = [f for f in _frets(v) if f > 0]
            assert not fretted or max(fretted) - min(fretted) <= 1

    def test_max_fret(self):
        for v in generate_voicings("F", max_fret=3, max_results=100):
            assert max(_frets(v)) <= 3

    def test_no_voicing_found(self):
        assert generate_voicings("C#", max_fret=0) == []

    def test_unknown_chord(self):
        with pytest.raises(ValueError, match="Cannot parse chord"):
            generate_voicings("Cxyz")

    def test_unknown_tuning(self):
        with pytest.raises(ValueError, match="Unknown tuning"):
            generate_voicings("C", tuning="banjo")


class TestSlashChords:
    @pytest.mark.parametrize("tuning", ALL_TUNINGS)
    @pytest.mark.parametrize("chord", [
        "C/G", "C/E", "Am/G", "D/F#", "G/B", "F/C", "Em/B", "C/Bb",
    ])
    def test_bass_is_lowest_when_possible(self, chord, tuning):
        """Every candidate has the bass lowest, unless no shape can."""
        bass_pc = _note_to_pc(chord.split("/")[1])
        candidates = generate_voicings(chord, tuning=tuning,
                                       max_results=10**6)
        assert candidates
        has_bass = [
            min(sounding_midi(v["frets"], get_tuning_midi(tuning))) % 12
            == bass_pc
            for v in candidates
        ]
        assert all(has_bass) or not any(has_bass)

    @pytest.mark.parametrize("chord, tuning", [
        ("C/G", "standard"), ("C/E", "low-g"), ("D/F#", "baritone"),
        ("Am/G", "d-tuning"),
    ])
    def test_bass_is_lowest(self, chord, tuning):
        bass_pc = _note_to_pc(chord.split("/")[1])
        for v in generate_voicings(chord, tuning=tuning):
            midi = sounding_midi(v["frets"], get_tuning_midi(tuning))
            assert min(midi) % 12 == bass_pc

    def test_unreachable_bass_still_gives_voicings(self):
        # In high-G tuning nothing below the C string can sound a B
        voicings = generate_voicings("G/B")
        assert [v["frets"] for v in voicings][0] == "0232"

    def test_inversion_named_from_chord_above_bass(self):
        # G is the 5th of C: every C/G voicing is a 2nd inversion
        for v in generate_voicings("C/G"):
            assert v["inversion"] == "2nd Inv"

    def test_non_chord_bass(self):
        # Bb isn't in C major; it becomes the lowest note of C/Bb
        voicings = generate_voicings("C/Bb", tuning="low-g")
        assert voicings
        for v in voicings:
            midi = sounding_midi(v["frets"], get_tuning_midi("low-g"))
            assert min(midi) % 12 == 10
            assert v["inversion"] == ""


class TestRequiredTones:
    @staticmethod
    def _required(chord: str) -> set[str]:
        components, root, bass, _ = _resolve_chord(chord)
        pcs = _required_pcs(
            [_note_to_pc(n) for n in components], _note_to_pc(root),
            bass_pc=_note_to_pc(bass) if bass else None,
        )
        return {n for n in components if _note_to_pc(n) in pcs}

    @pytest.mark.parametrize("chord, tones", [
        ("C", {"C", "E", "G"}),
        ("C7", {"C", "E", "G", "Bb"}),
        ("C9", {"C", "E", "Bb", "D"}),        # drop the 5th
        ("Cmaj9", {"C", "E", "B", "D"}),
        ("C69", {"C", "E", "A", "D"}),
        ("C7b9", {"C", "E", "Bb", "Db"}),
        ("C11", {"C", "E", "Bb", "F"}),        # 5th, then the 9th
        ("Cm11", {"C", "Eb", "Bb", "F"}),
        ("C13", {"C", "E", "Bb", "A"}),        # 5th, 11th, 9th
        ("C9/G", {"G", "E", "Bb", "D"}),       # bass kept, root dropped
        ("A9/E", {"E", "C#", "G", "B"}),
    ])
    def test_tones_kept(self, chord, tones):
        assert self._required(chord) == tones

    def test_small_chords_keep_everything(self):
        assert _required_pcs([0, 4, 7, 10], 0) == {0, 4, 7, 10}

    def test_duplicates_ignored(self):
        assert _required_pcs([0, 4, 7, 0], 0) == {0, 4, 7}

    def test_more_strings(self):
        assert _required_pcs([0, 4, 7, 10, 2], 0, max_tones=5) == {
            0, 4, 7, 10, 2}


class TestFingering:
    @pytest.mark.parametrize("frets, fingers", [
        ("0003", "0003"),   # C: ring finger, matching the fret
        ("0001", "0001"),   # C7
        ("0232", "0132"),   # G: no barre across the higher E-string fret
        ("0212", "0213"),   # G7
        ("2010", "2010"),   # F
        ("2100", "2100"),   # A
        ("2220", "1110"),   # D: adjacent strings share a flat finger
        ("0432", "0321"),   # Em: index on the lowest fret
        ("1013", "1024"),   # Fm: one finger per fret
        ("3121", "3121"),   # F#: barre only when every string is fretted
        ("2322", "1211"),   # B7
        ("3211", "3211"),   # Bb
        ("5433", "3211"),
        ("1111", "1111"),
        ("7777", "1111"),
        ("0007", "0001"),   # high lone note: index, not finger 7
        ("0000", "0000"),
    ])
    def test_assign_fingers(self, frets, fingers):
        assert _assign_fingers(tuple(int(c) for c in frets)) == fingers

    def test_muted_strings_get_no_finger(self):
        assert _assign_fingers((-1, 0, 0, 3)) == "0003"

    @pytest.mark.parametrize("frets, spanning, units", [
        ((2, 2, 2, 0), False, [(2, [0, 1, 2])]),
        ((2, 3, 2, 2), True, [(2, [0, 2, 3]), (3, [1])]),
        ((2, 3, 2, 2), False, [(2, [0]), (2, [2, 3]), (3, [1])]),
        ((2, 0, 2, 3), True, [(2, [0]), (2, [2]), (3, [3])]),  # open between
        ((3, 2, 3, 0), True, [(2, [1]), (3, [0]), (3, [2])]),  # lower between
    ])
    def test_finger_units(self, frets, spanning, units):
        assert _finger_units(frets, allow_spanning=spanning) == units


class TestStartingFret:
    @pytest.mark.parametrize("frets, start", [
        ((0, 0, 0, 0), 1),
        ((0, 0, 0, 3), 1),
        ((2, 4, 3, 1), 1),
        ((0, 0, 0, 5), 5),
        ((5, 4, 3, 3), 3),
        ((0, 7, 8, 7), 7),
        ((-1, 0, 0, 7), 7),   # muted strings are ignored
        ((-1, -1, -1, -1), 1),
    ])
    def test_compute(self, frets, start):
        assert compute_starting_fret(frets) == start


class TestDifficulty:
    def test_all_open_is_easiest(self):
        assert _score_voicing((0, 0, 0, 0)) == 0.0

    def test_score_never_negative(self):
        assert _score_voicing((0, 0, 0, 1)) >= 0

    def test_open_position_easier_than_barre(self):
        assert _score_voicing((0, 0, 0, 3)) < _score_voicing((5, 4, 3, 3))

    def test_wider_stretch_is_harder(self):
        assert _score_voicing((2, 2, 2, 2)) < _score_voicing((2, 2, 2, 5))

    @pytest.mark.parametrize("score, label", [
        (0, "easy"), (4, "easy"), (4.1, "moderate"), (11, "moderate"),
        (11.5, "hard"), (15, "hard"), (15.1, "very hard"),
    ])
    def test_labels(self, score, label):
        assert _difficulty_label(score) == label


class TestDescribeVoicing:
    def test_open_c(self):
        assert describe_voicing("C", (0, 0, 0, 3)) == ("G C E C", "Root")

    def test_muted_string_is_dash(self):
        assert describe_voicing("C", (-1, 0, 0, 3)) == ("- C E C", "Root")

    def test_all_muted(self):
        assert describe_voicing("C", (-1, -1, -1, -1)) == ("- - - -", "")

    def test_non_chord_tone_uses_sharp_name(self):
        notes, _ = describe_voicing("C", (0, 0, 0, 4))
        assert notes == "G C E C#"

    def test_chord_spelling_is_kept(self):
        notes, _ = describe_voicing("Bb", (3, 2, 1, 1))
        assert notes == "Bb D F Bb"

    def test_inversion_from_lowest_pitch(self):
        assert describe_voicing("C", (0, 0, 0, 3), "low-g")[1] == "2nd Inv"
        assert describe_voicing("Am7", (0, 0, 0, 0))[1] == "1st Inv"

    def test_tuning(self):
        notes, inversion = describe_voicing("G", (0, 0, 0, 3), "baritone")
        assert notes == "D G B G"
        assert inversion == "2nd Inv"

    def test_unknown_chord(self):
        with pytest.raises(ValueError):
            describe_voicing("C (alt)", (0, 0, 0, 3))
