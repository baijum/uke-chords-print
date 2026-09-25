"""
Shared reference data and helpers for the test suite.

Two independent references check the generator:

- FORMULAS: textbook interval formulas (semitones above the root) for
  every chord type in chords-db, written out by hand rather than taken from
  pychord.
- chords-db (tests/data/chords-db): 2,114 hand-compiled ukulele shapes in
  standard tuning, each checked against FORMULAS before use.
"""

from __future__ import annotations

import base64
import json
import re
import zlib
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = Path(__file__).resolve().parent / "data"
CATALOG_DIR = REPO_ROOT / "catalog"

STANDARD_MIDI = (67, 60, 64, 69)  # G4 C4 E4 A4

PITCH_CLASS = {
    "C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3, "E": 4, "F": 5,
    "F#": 6, "Gb": 6, "G": 7, "G#": 8, "Ab": 8, "A": 9, "A#": 10, "Bb": 10,
    "B": 11,
}
ROOTS = ["C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"]
ALL_TUNINGS = ["standard", "low-g", "baritone", "d-tuning"]


@dataclass(frozen=True)
class Formula:
    """A chord type: its name in this tool and its intervals.

    Attributes:
        quality: Spelling after the root, as users type it (e.g. "m7").
        intervals: Semitones above the root that define the chord.
        optional: Tones a resolver may add that players leave out (the
            natural 11th of a 13th chord clashes with the major 3rd).
    """
    quality: str
    intervals: frozenset[int]
    optional: frozenset[int] = field(default_factory=frozenset)


def _f(quality: str, *intervals: int, optional: tuple[int, ...] = ()) -> Formula:
    return Formula(quality, frozenset(intervals), frozenset(optional))


# chords-db suffix -> formula. Intervals: 1=b9, 2=9, 3=m3/#9, 4=M3, 5=11,
# 6=b5/#11, 7=5, 8=#5/b13, 9=6/13, 10=b7, 11=M7.
FORMULAS: dict[str, Formula] = {
    "major": _f("", 0, 4, 7),
    "minor": _f("m", 0, 3, 7),
    "dim": _f("dim", 0, 3, 6),
    "dim7": _f("dim7", 0, 3, 6, 9),
    "sus2": _f("sus2", 0, 2, 7),
    "sus4": _f("sus4", 0, 5, 7),
    "7sus4": _f("7sus4", 0, 5, 7, 10),
    "aug": _f("aug", 0, 4, 8),
    "6": _f("6", 0, 4, 7, 9),
    "69": _f("69", 0, 4, 7, 9, 2),
    "7": _f("7", 0, 4, 7, 10),
    "7b5": _f("7b5", 0, 4, 6, 10),
    "aug7": _f("aug7", 0, 4, 8, 10),
    "9": _f("9", 0, 4, 7, 10, 2),
    "9b5": _f("9b5", 0, 4, 6, 10, 2),
    "aug9": _f("aug9", 0, 4, 8, 10, 2),
    "7b9": _f("7b9", 0, 4, 7, 10, 1),
    "7b9#5": _f("7b9#5", 0, 4, 8, 10, 1),
    "7#9": _f("7#9", 0, 4, 7, 10, 3),
    "11": _f("11", 0, 4, 7, 10, 2, 5),
    "9#11": _f("9#11", 0, 4, 7, 10, 2, 6),
    "13": _f("13", 0, 4, 7, 10, 2, 9, optional=(5,)),
    "13b9": _f("13b9", 0, 4, 7, 10, 1, 9, optional=(5,)),
    "13b5b9": _f("13b5b9", 0, 4, 6, 10, 1, 9),
    "b13b9": _f("7b9b13", 0, 4, 7, 10, 1, 8, optional=(5,)),
    "b13#9": _f("7#9b13", 0, 4, 7, 10, 3, 8),
    "maj7": _f("maj7", 0, 4, 7, 11),
    "maj7b5": _f("maj7b5", 0, 4, 6, 11),
    "maj7#5": _f("maj7#5", 0, 4, 8, 11),
    "maj9": _f("maj9", 0, 4, 7, 11, 2),
    "maj11": _f("maj11", 0, 4, 7, 11, 2, 5),
    "maj13": _f("maj13", 0, 4, 7, 11, 2, 9, optional=(5,)),
    "m6": _f("m6", 0, 3, 7, 9),
    "m7": _f("m7", 0, 3, 7, 10),
    "m7b5": _f("m7b5", 0, 3, 6, 10),
    "m9": _f("m9", 0, 3, 7, 10, 2),
    "m69": _f("m69", 0, 3, 7, 9, 2),
    "m9b5": _f("m9b5", 0, 3, 6, 10, 2),
    "m11": _f("m11", 0, 3, 7, 10, 2, 5),
    "mmaj7": _f("mM7", 0, 3, 7, 11),
    "mmaj7b5": _f("mM7b5", 0, 3, 6, 11),
    "mmaj9": _f("mM9", 0, 3, 7, 11, 2),
    "mmaj11": _f("mM11", 0, 3, 7, 11, 2, 5),
    "add9": _f("add9", 0, 4, 7, 2),
    "madd9": _f("madd9", 0, 3, 7, 2),
}

# chords-db entries whose notes don't match the chord (see the data README)
CHORDS_DB_ERRATA = {
    ("B", "madd9", (2, 0, 0, 2)),
    ("B", "madd9", (5, 4, 5, 2)),
    ("B", "madd9", (4, 4, 5, 3)),
    ("F", "11", (1, 2, 2, 0)),
}

# chords-db shapes whose fingers cross (a lower finger on a higher fret)
CHORDS_DB_FINGERING_ERRATA = {
    ("Ab", "maj11", (5, 7, 6, 4)),   # fingers 2134
    ("Eb", "alt", (8, 7, 5, 6)),     # fingers 3412
}


@dataclass(frozen=True)
class Shape:
    """One chords-db shape with absolute fret numbers.

    Attributes:
        key: chords-db key (flat spelling, e.g. "Db").
        suffix: chords-db suffix (e.g. "minor").
        position: Index in the entry (0 = the chart's first shape).
        frets: Absolute fret per string (0 open, -1 muted), G-C-E-A.
        fingers: chords-db finger per string (0 = none).
        midi: Sounding MIDI pitch per non-muted string.
    """
    key: str
    suffix: str
    position: int
    frets: tuple[int, ...]
    fingers: tuple[int, ...]
    midi: tuple[int, ...]

    @property
    def name(self) -> str:
        """Chord name in this tool's spelling (e.g. "Dbm7")."""
        return self.key + FORMULAS[self.suffix].quality

    @property
    def fret_string(self) -> str:
        """Frets in this tool's 4-character format."""
        return "".join("X" if f < 0 else str(f) for f in self.frets)

    @property
    def pitch_classes(self) -> set[int]:
        return {m % 12 for m in self.midi}

    @property
    def id(self) -> str:
        """Test id, e.g. "C-major-0003"."""
        return f"{self.key}-{self.suffix}-{self.fret_string}"


def formula_pcs(key: str, suffix: str, with_optional: bool = False) -> set[int]:
    """Pitch classes of a chord from FORMULAS."""
    formula = FORMULAS[suffix]
    intervals = formula.intervals | (formula.optional if with_optional else set())
    return {(PITCH_CLASS[key] + i) % 12 for i in intervals}


@lru_cache(maxsize=None)
def chords_db() -> dict:
    """The raw chords-db ukulele data."""
    with open(DATA_DIR / "chords-db" / "ukulele.json", encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=None)
def chords_db_shapes(include_errata: bool = False) -> tuple[Shape, ...]:
    """Every chords-db shape, as absolute frets."""
    shapes = []
    for entries in chords_db()["chords"].values():
        for entry in entries:
            for i, pos in enumerate(entry["positions"]):
                base = pos["baseFret"]
                frets = tuple(
                    f if f <= 0 else f + base - 1 for f in pos["frets"]
                )
                shape = Shape(
                    key=entry["key"], suffix=entry["suffix"], position=i,
                    frets=frets, fingers=tuple(pos["fingers"]),
                    midi=tuple(pos["midi"]),
                )
                errata = (shape.key, shape.suffix, frets) in CHORDS_DB_ERRATA
                if include_errata or not errata:
                    shapes.append(shape)
    return tuple(shapes)


def usable_shapes(max_fret: int = 9, max_span: int = 3) -> list[Shape]:
    """chords-db shapes within the generator's search limits and spelling."""
    result = []
    for s in chords_db_shapes():
        if s.suffix not in FORMULAS:
            continue
        fretted = [f for f in s.frets if f > 0]
        if min(s.frets) < 0 or (fretted and (
                max(fretted) > max_fret
                or max(fretted) - min(fretted) > max_span)):
            continue
        result.append(s)
    return result


def sounding_midi(frets: str, tuning_midi: tuple[int, ...]) -> list[int]:
    """MIDI pitch of each non-muted string for a fret string like "0003"."""
    return [
        m + int(f) for m, f in zip(tuning_midi, frets) if f.upper() != "X"
    ]


def fingering_problems(
    frets: tuple[int, ...], fingers: str, strict: bool = True
) -> list[str]:
    """Ways a fingering is unplayable (empty if it's fine).

    Args:
        frets: Fret per string (0 open, -1 muted).
        fingers: 4 characters, 1-4 or 0/_ for no finger.
        strict: Also apply this tool's convention that a finger spans
            higher-fretted strings only when every string is fretted.
    """
    problems = []
    fingers_ = [0 if ch == "_" else int(ch) for ch in fingers]
    fretted = [i for i, f in enumerate(frets) if f > 0]
    for i, f in enumerate(frets):
        if not 0 <= fingers_[i] <= 4:
            problems.append(f"string {i}: finger {fingers_[i]}")
        if (fingers_[i] == 0) != (f <= 0):
            problems.append(f"string {i}: finger {fingers_[i]} on fret {f}")
    for i in fretted:
        for j in fretted:
            fi, fj = fingers_[i], fingers_[j]
            if frets[i] < frets[j] and fi >= fj:
                problems.append(f"strings {i},{j}: finger order")
            if fi == fj and frets[i] != frets[j]:
                problems.append(f"strings {i},{j}: one finger, two frets")
            if i < j and fi == fj:
                between = frets[i + 1:j]
                if any(f < frets[i] for f in between):
                    problems.append(f"strings {i},{j}: finger across a "
                                    f"lower or open string")
                if strict and len(fretted) < 4 and any(
                        f != frets[i] for f in between):
                    problems.append(f"strings {i},{j}: spanning barre")
    return problems


# --- PDF inspection (no PDF library needed) ---

def pdf_page_count(data: bytes) -> int:
    """Number of page objects in a PDF written by ReportLab."""
    return len(re.findall(rb"/Type /Page\b(?!s)", data))


def pdf_text(data: bytes) -> str:
    """Decompressed content streams of a PDF, joined, for searching.

    Text in the built-in fonts appears literally, e.g. "(Am7) Tj".
    """
    chunks = []
    for m in re.finditer(rb"stream\r?\n(.*?)endstream", data, re.S):
        raw = m.group(1)
        # ReportLab's default filters: ASCII85 then Flate
        try:
            raw = zlib.decompress(base64.a85decode(
                re.sub(rb"\s", b"", raw).removesuffix(b"~>")
            ))
        except (ValueError, zlib.error):
            pass  # not an encoded content stream (e.g. an embedded font)
        chunks.append(raw.decode("latin-1"))
    return "\n".join(chunks)
