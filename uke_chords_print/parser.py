"""
Parse chord input from CLI arguments and text files.

Supports two input styles:
1. Chord name only (e.g., "C", "Am") -> looks up all voicings from database
2. Explicit voicing (e.g., "C, 0003, fingers=2_1_") -> uses provided data

CLI argument format:
  - "C"                         -> chord name lookup
  - "C:0003"                    -> name with explicit frets
  - "C:0003:fingers=___3"       -> name with frets and fingering

Text file format (one chord per line):
  - C                           -> chord name lookup
  - C, 0003                    -> name with explicit frets
  - C, 0003, fingers=___3      -> with fingering
  - C, 0003, fingers=___3, starting_fret=3  -> with starting fret
                                   (derived from the frets when omitted)
  - ---                         -> force a new page in the PDF
  - = Section Heading            -> section heading rendered in the PDF
  - @tuning standard            -> explicit voicings below are written for
                                   this tuning; they are regenerated from the
                                   chord name when --tuning needs other shapes
  - # comment lines are ignored; an inline comment is whitespace, "#",
    then whitespace or end of line (so "C#" and "= Track #1" are kept)
  - blank lines are ignored
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .chord_db import lookup_chord
from .tunings import get_tuning, shapes_compatible
from .voicing_gen import compute_starting_fret


@dataclass
class ChordVoicing:
    """A single chord voicing ready for rendering."""
    name: str
    frets: str          # e.g., "0003"
    fingers: str = ""   # e.g., "___3" or "0003"
    notes: str = ""     # e.g., "G C E C"
    inversion: str = ""  # e.g., "Root", "1st Inv"
    starting_fret: int = 1


# Inline comment: whitespace, "#", then whitespace or end of line.
_INLINE_COMMENT = re.compile(r"\s+#(\s.*)?$")


def _strip_comment(line: str) -> str:
    """Remove surrounding whitespace and any inline comment from a line."""
    return _INLINE_COMMENT.sub("", line.strip()).strip()


# Sentinel object used to signal a page break in the voicings list.
PAGE_BREAK = ChordVoicing(name="__PAGE_BREAK__", frets="0000")


def make_heading(text: str) -> ChordVoicing:
    """Create a heading sentinel carrying the heading text in the notes field."""
    return ChordVoicing(name="__HEADING__", frets="0000", notes=text)


def is_heading(v: ChordVoicing) -> bool:
    """Check whether a ChordVoicing is a heading sentinel."""
    return v.name == "__HEADING__"


def _parse_fret_value(ch: str) -> int:
    """Parse a single fret character to int. 'X'/'x' -> -1, digit -> int."""
    if ch.upper() == "X":
        return -1
    return int(ch)


def validate_frets(frets: str) -> bool:
    """Check that frets is a valid 4-character fret string."""
    if len(frets) != 4:
        return False
    for ch in frets:
        if ch.upper() == "X":
            continue
        if not ch.isdigit():
            return False
    return True


def _explicit_voicing(name: str, frets: str, kwargs: dict) -> ChordVoicing:
    """Build an explicit voicing, deriving starting_fret when not given.

    Args:
        name: Chord name shown above the diagram.
        frets: Validated 4-character fret string.
        kwargs: Extra ChordVoicing fields parsed from the input.

    Returns:
        The ChordVoicing.

    Raises:
        ValueError: If the fretted notes don't fit the 4 frets a diagram
            shows.
    """
    fret_values = tuple(_parse_fret_value(ch) for ch in frets)
    if "starting_fret" not in kwargs:
        kwargs["starting_fret"] = compute_starting_fret(fret_values)

    start = max(kwargs["starting_fret"], 1)
    fretted = [f for f in fret_values if f > 0]
    # Diagrams show 4 frets: start .. start + 3
    if fretted and (min(fretted) < start or max(fretted) > start + 3):
        raise ValueError(
            f"Frets '{frets}' don't fit the 4 frets shown from fret {start}. "
            f"Adjust starting_fret or use a shape spanning at most 4 frets."
        )
    return ChordVoicing(name=name, frets=frets, **kwargs)


def parse_cli_arg(
    arg: str, single: bool = False, tuning: str = "standard"
) -> list[ChordVoicing]:
    """
    Parse a single CLI argument into chord voicings.

    Formats:
      "C"                       -> database lookup
      "C:0003"                  -> explicit
      "C:0003:fingers=___3"     -> explicit with fingering
    """
    parts = arg.split(":")
    name = parts[0].strip()

    if len(parts) == 1:
        # Just a chord name -> look up from database
        return _lookup_voicings(name, single=single, tuning=tuning)

    # Explicit voicing
    frets = parts[1].strip()
    if not validate_frets(frets):
        raise ValueError(f"Invalid frets '{frets}' in argument '{arg}'. "
                         f"Expected 4 characters (digits or X).")

    kwargs = {}
    for extra in parts[2:]:
        key, _, val = extra.partition("=")
        key = key.strip()
        val = val.strip()
        if key == "fingers":
            kwargs["fingers"] = val
        elif key == "starting_fret":
            kwargs["starting_fret"] = int(val)

    return [_explicit_voicing(name, frets, kwargs)]


def parse_file_line(
    line: str,
    single: bool = False,
    tuning: str = "standard",
    voicing_tuning: str | None = None,
    fallback_used: set[tuple[str, str]] | None = None,
) -> list[ChordVoicing]:
    """
    Parse a single line from a text input file.

    Formats:
      C                                     -> database lookup
      C, 0003                              -> explicit frets
      C, 0003, fingers=___3                -> with fingering
      C, 0003, fingers=___3, starting_fret=3  -> with starting fret

    If voicing_tuning is set and its fret shapes don't match the active
    tuning, explicit voicings are replaced by a generated voicing (see
    _fallback_voicing; fallback_used tracks replacements within one file).
    """
    # Strip comments and whitespace
    line = _strip_comment(line)
    if not line or line.startswith("#"):
        return []

    # Page break directive
    if line == "---":
        return [PAGE_BREAK]

    # Section heading
    if line.startswith("= "):
        return [make_heading(line[2:].strip())]

    parts = [p.strip() for p in line.split(",")]
    name = parts[0]

    if len(parts) == 1:
        # Just a chord name
        return _lookup_voicings(name, single=single, tuning=tuning)

    # Has explicit frets
    frets = parts[1]
    if not validate_frets(frets):
        raise ValueError(f"Invalid frets '{frets}' in line '{line}'. "
                         f"Expected 4 characters (digits or X).")

    # Explicit shape written for a tuning with different fingerings
    if voicing_tuning and not shapes_compatible(voicing_tuning, tuning):
        return _fallback_voicing(name, tuning, fallback_used)

    kwargs = {}
    for extra in parts[2:]:
        key, _, val = extra.partition("=")
        key = key.strip()
        val = val.strip()
        if key == "fingers":
            kwargs["fingers"] = val
        elif key == "starting_fret":
            kwargs["starting_fret"] = int(val)
        elif key == "notes":
            kwargs["notes"] = val
        elif key == "inversion":
            kwargs["inversion"] = val

    return [_explicit_voicing(name, frets, kwargs)]


def parse_file(
    filepath: str, single: bool = False, tuning: str = "standard"
) -> list[ChordVoicing]:
    """Parse an entire text file and return all chord voicings."""
    voicings = []
    voicing_tuning = None
    fallback_used: set[tuple[str, str]] = set()
    with open(filepath, "r") as f:
        for lineno, line in enumerate(f, 1):
            try:
                # Tuning directive for the explicit voicings that follow
                directive = _strip_comment(line).split()
                if directive and directive[0] == "@tuning":
                    if len(directive) != 2:
                        raise ValueError("Expected '@tuning <name>'")
                    voicing_tuning = get_tuning(directive[1]).name
                    continue
                voicings.extend(parse_file_line(
                    line, single=single, tuning=tuning,
                    voicing_tuning=voicing_tuning,
                    fallback_used=fallback_used,
                ))
            except ValueError as e:
                raise ValueError(f"Line {lineno}: {e}") from e
    return voicings


def parse_cli_args(
    args: list[str], single: bool = False, tuning: str = "standard"
) -> list[ChordVoicing]:
    """Parse a list of CLI arguments into chord voicings."""
    voicings = []
    for arg in args:
        voicings.extend(parse_cli_arg(arg, single=single, tuning=tuning))
    return voicings


def _fallback_voicing(
    name: str, tuning: str, used: set[tuple[str, str]] | None
) -> list[ChordVoicing]:
    """Replace an explicit voicing written for another tuning.

    Returns the easiest generated voicing not already used in place of an
    earlier explicit line, so a file that pins several shapes for one chord
    (e.g. two E voicings) doesn't print the same diagram twice.

    Args:
        name: Chord name from the explicit line.
        tuning: Active tuning.
        used: (name, frets) pairs already used as replacements, updated in
            place; None disables the check.

    Returns:
        A single-item list with the replacement voicing.
    """
    options = _lookup_voicings(name, tuning=tuning)
    for voicing in options:
        key = (voicing.name, voicing.frets)
        if used is None or key not in used:
            if used is not None:
                used.add(key)
            return [voicing]
    return options[:1]


def _lookup_voicings(
    name: str, single: bool = False, tuning: str = "standard"
) -> list[ChordVoicing]:
    """Look up chord voicings from the built-in database.

    If single=True, return only the first (primary) voicing.
    """
    entries = lookup_chord(name, tuning=tuning)
    if entries is None:
        raise ValueError(
            f"Chord '{name}' not found in database. "
            f"Use --list to see available chords, or provide explicit frets."
        )
    if single:
        entries = entries[:1]
    voicings = []
    for entry in entries:
        voicings.append(ChordVoicing(
            name=name,
            frets=entry["frets"],
            fingers=entry.get("fingers", ""),
            notes=entry.get("notes", ""),
            inversion=entry.get("inversion", ""),
            starting_fret=entry.get("starting_fret", 1),
        ))
    return voicings
