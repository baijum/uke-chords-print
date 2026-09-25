"""The shipped chord sheets in catalog/."""

from __future__ import annotations

import pytest

from uke_chords_print.parser import (
    PAGE_BREAK,
    _parse_fret_value,
    _parse_options,
    _strip_comment,
    is_heading,
    parse_file,
)
from uke_chords_print.voicing_gen import (
    _assign_fingers,
    _note_to_pc,
    _required_pcs,
    _resolve_chord,
    describe_voicing,
)

from .support import (
    ALL_TUNINGS,
    CATALOG_DIR,
    REPO_ROOT,
    STANDARD_MIDI,
    fingering_problems,
)

CATALOG_FILES = sorted(CATALOG_DIR.rglob("*.txt"))
IDS = [str(p.relative_to(CATALOG_DIR)) for p in CATALOG_FILES]
# Every shipped chord file, including the README's example
SHEETS = CATALOG_FILES + [REPO_ROOT / "example_chords.txt"]
SHEET_IDS = [str(p.relative_to(REPO_ROOT)) for p in SHEETS]


def _explicit_lines(path):
    """(line number, name, frets, options) for each pinned voicing."""
    for lineno, line in enumerate(path.read_text("utf-8").splitlines(), 1):
        line = _strip_comment(line)
        if not line or line.startswith(("#", "=", "@", "---")):
            continue
        parts = [p.strip() for p in line.split(",")]
        if len(parts) > 1:
            frets = tuple(_parse_fret_value(ch) for ch in parts[1])
            yield lineno, parts[0], frets, _parse_options(parts[2:])


def _explicit_params():
    return [
        pytest.param(name, frets, opts, id=f"{path.name}:{lineno}:{name}")
        for path in SHEETS
        for lineno, name, frets, opts in _explicit_lines(path)
    ]


EXPLICIT = _explicit_params()



def test_catalog_found():
    assert len(CATALOG_FILES) >= 15


@pytest.mark.parametrize("tuning", ALL_TUNINGS)
@pytest.mark.parametrize("path", SHEETS, ids=SHEET_IDS)
def test_parses_in_every_tuning(path, tuning):
    voicings = parse_file(str(path), single=True, tuning=tuning)
    chords = [v for v in voicings if v is not PAGE_BREAK and not is_heading(v)]
    assert chords


@pytest.mark.parametrize("path", CATALOG_FILES, ids=IDS)
def test_first_line_is_title(path):
    # generate_catalog.sh uses line 1 as the PDF title
    first = path.read_text("utf-8").splitlines()[0]
    assert first.startswith("# ") and len(first) > 2


@pytest.mark.parametrize("path", CATALOG_FILES, ids=IDS)
def test_listed_in_readme_and_script(path):
    readme = (CATALOG_DIR / "README.md").read_text("utf-8")
    script = (REPO_ROOT / "generate_catalog.sh").read_text("utf-8")
    rel = path.relative_to(CATALOG_DIR).as_posix()
    assert f"({rel})" in readme or f"`{rel}`" in readme
    glob = f"catalog/{path.parent.relative_to(CATALOG_DIR).as_posix()}/*.txt"
    assert f"catalog/{rel}" in script or glob in script


@pytest.mark.parametrize("path", SHEETS, ids=SHEET_IDS)
def test_pinned_shapes_declare_tuning(path):
    lines = path.read_text("utf-8").splitlines()
    if any(True for _ in _explicit_lines(path)):
        assert "@tuning standard" in lines[1:]


@pytest.mark.parametrize("name, frets, opts", EXPLICIT)
def test_pinned_shape_is_the_chord(name, frets, opts):
    components, root, bass, _ = _resolve_chord(name)
    chord_pcs = {_note_to_pc(n) for n in components}
    required = _required_pcs(
        [_note_to_pc(n) for n in components], _note_to_pc(root),
        bass_pc=_note_to_pc(bass) if bass else None,
    )
    sounding = {(m + f) % 12 for m, f in zip(STANDARD_MIDI, frets) if f >= 0}
    assert sounding <= chord_pcs
    assert required <= sounding


@pytest.mark.parametrize("name, frets, opts", EXPLICIT)
def test_pinned_labels_match_the_shape(name, frets, opts):
    notes, inversion = describe_voicing(name, frets)
    if "notes" in opts:
        pinned = [_note_to_pc(n) for n in opts["notes"].split()]
        assert pinned == [_note_to_pc(n) for n in notes.split()]
    if "inversion" in opts:
        assert opts["inversion"] == inversion


@pytest.mark.parametrize("name, frets, opts", EXPLICIT)
def test_pinned_notes_spelled_as_the_chord(name, frets, opts):
    if "notes" in opts:
        assert opts["notes"].split() == describe_voicing(name, frets)[0].split()


@pytest.mark.parametrize("name, frets, opts", EXPLICIT)
def test_pinned_fingers_are_playable(name, frets, opts):
    if "fingers" in opts:
        assert fingering_problems(frets, opts["fingers"], strict=False) == []


def test_challenging_fingers_mirror_generator():
    # AGENTS.md: pinned fingers in challenging_chords.txt match the generator
    path = CATALOG_DIR / "challenging_chords.txt"
    pinned = [(name, frets, opts) for _, name, frets, opts
              in _explicit_lines(path) if "fingers" in opts]
    assert pinned
    for name, frets, opts in pinned:
        assert opts["fingers"] == _assign_fingers(frets), name
