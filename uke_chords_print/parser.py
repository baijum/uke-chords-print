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
                                   (the space after "=" is optional)
  - @tuning standard            -> explicit voicings below are written for
                                   this tuning; they are regenerated from the
                                   chord name when --tuning needs other shapes
                                   (see _fallback_voicing)
  - # comment lines are ignored; an inline comment is whitespace, "#",
    then whitespace or end of line (so "C#" and "= Track #1" are kept)
  - blank lines are ignored
"""

from __future__ import annotations

import re
import warnings
from dataclasses import dataclass

from .chord_db import lookup_chord
from .tunings import get_tuning, shapes_compatible
from .voicing_gen import compute_starting_fret, describe_voicing


class ChordWarning(UserWarning):
    """A problem in the input that doesn't stop the sheet being printed."""


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
    """Check that frets is a valid 4-character fret string (0-9 or X)."""
    return len(frets) == 4 and all(ch in "0123456789xX" for ch in frets)


_OPTION_KEYS = ("fingers", "starting_fret", "notes", "inversion")


def _parse_options(extras: list[str]) -> dict:
    """Parse key=value options that follow an explicit voicing's frets.

    Args:
        extras: Option strings, e.g. ["fingers=___3", "starting_fret=3"].
            Empty strings (from a trailing separator) are ignored.

    Returns:
        ChordVoicing keyword arguments.

    Raises:
        ValueError: On a missing "=", an unknown key, a fingers value that
            isn't 4 characters of 0-4 or "_", or a non-numeric or < 1
            starting_fret.
    """
    kwargs: dict = {}
    for extra in extras:
        if not extra.strip():
            continue
        key, sep, val = extra.partition("=")
        key = key.strip()
        val = val.strip()
        if not sep:
            raise ValueError(f"Expected key=value, got '{extra.strip()}'")
        if key not in _OPTION_KEYS:
            raise ValueError(
                f"Unknown option '{key}'. "
                f"Valid options: {', '.join(_OPTION_KEYS)}"
            )
        if key == "fingers":
            if len(val) != 4 or any(ch not in "01234_" for ch in val):
                raise ValueError(
                    f"Invalid fingers '{val}'. Expected 4 characters, "
                    f"each 1-4 or 0/_ for no finger."
                )
            kwargs["fingers"] = val
        elif key == "starting_fret":
            if not (val.isascii() and val.isdigit()) or int(val) < 1:
                raise ValueError(
                    f"Invalid starting_fret '{val}'. Expected a number >= 1."
                )
            kwargs["starting_fret"] = int(val)
        else:
            kwargs[key] = val
    return kwargs


def _explicit_voicing(
    name: str, frets: str, kwargs: dict, tuning: str = "standard"
) -> ChordVoicing:
    """Build an explicit voicing, filling in fields that weren't given.

    starting_fret is derived from the frets. notes and inversion are
    worked out from the chord name and tuning, as for generated voicings,
    unless the chord name isn't recognized (e.g. "C (alt)").

    Args:
        name: Chord name shown above the diagram.
        frets: Validated 4-character fret string.
        kwargs: Extra ChordVoicing fields parsed from the input.
        tuning: Tuning the shape is played in.

    Returns:
        The ChordVoicing.

    Raises:
        ValueError: If the fretted notes don't fit the 4 frets a diagram
            shows, a finger is given for an open or muted string, or notes
            doesn't name one note per string.
    """
    fret_values = tuple(_parse_fret_value(ch) for ch in frets)
    fingers = kwargs.get("fingers", "")
    for i, (fret, finger) in enumerate(zip(fret_values, fingers)):
        if fret <= 0 and finger not in "0_":
            state = "open" if fret == 0 else "muted"
            raise ValueError(
                f"Finger {finger} is on string {i + 1}, which is {state} "
                f"in '{frets}'. Use 0 or _ for strings without a finger."
            )
    if "notes" in kwargs and len(kwargs["notes"].split()) != len(frets):
        raise ValueError(
            f"notes= names {len(kwargs['notes'].split())} notes for "
            f"{len(frets)} strings. Give one per string, - for a muted one."
        )
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

    if "notes" not in kwargs or "inversion" not in kwargs:
        try:
            notes, inversion = describe_voicing(name, fret_values, tuning)
        except ValueError:
            pass  # unrecognized name: draw without note/inversion labels
        else:
            kwargs.setdefault("notes", notes)
            kwargs.setdefault("inversion", inversion)
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
      "C:0003:fingers=___3:notes=G C E C" -> any option from _parse_options
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

    kwargs = _parse_options(parts[2:])
    return [_explicit_voicing(name, frets, kwargs, tuning)]


def parse_file_line(
    line: str,
    single: bool = False,
    tuning: str = "standard",
    voicing_tuning: str | None = None,
    fallback_shapes: dict[tuple[str, str], ChordVoicing] | None = None,
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
    _fallback_voicing; fallback_shapes tracks replacements within one
    file).

    Raises:
        ValueError: On malformed input or an unknown chord name to look up.
    """
    # Strip comments and whitespace
    line = _strip_comment(line)
    if not line or line.startswith("#"):
        return []

    # Page break directive
    if line == "---":
        return [PAGE_BREAK]

    # Section heading ("= Verse" or "=Verse")
    if line.startswith("="):
        text = line[1:].strip()
        if not text:
            raise ValueError("Heading text missing after '='")
        return [make_heading(text)]

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

    # Parse options first so typos are reported under any --tuning
    kwargs = _parse_options(parts[2:])

    # Explicit shape written for a tuning with different fingerings
    if voicing_tuning and not shapes_compatible(voicing_tuning, tuning):
        replacement = _fallback_voicing(
            name, frets, voicing_tuning, tuning, fallback_shapes
        )
        if replacement:
            return replacement
        # Kept as written: label it for the tuning it's printed in
        kwargs.pop("notes", None)
        kwargs.pop("inversion", None)
    elif voicing_tuning and voicing_tuning != get_tuning(tuning).name:
        # Same shapes (standard / low-G) but a different lowest string, so
        # an inversion pinned for one tuning can be wrong in the other
        kwargs.pop("inversion", None)

    return [_explicit_voicing(name, frets, kwargs, tuning)]


def parse_file(
    filepath: str, single: bool = False, tuning: str = "standard"
) -> list[ChordVoicing]:
    """Parse an entire text file and return all chord voicings.

    Problems that don't stop the sheet (see _fallback_voicing) are issued
    as ChordWarning, prefixed with the line number.

    Raises:
        ValueError: On a malformed line, prefixed with its line number.
    """
    voicings = []
    voicing_tuning = None
    fallback_shapes: dict[tuple[str, str], ChordVoicing] = {}
    # utf-8-sig also accepts files saved with a byte-order mark (Notepad)
    with open(filepath, "r", encoding="utf-8-sig") as f:
        for lineno, line in enumerate(f, 1):
            try:
                # Tuning directive for the explicit voicings that follow
                directive = _strip_comment(line).split()
                if directive and directive[0] == "@tuning":
                    if len(directive) != 2:
                        raise ValueError("Expected '@tuning <name>'")
                    voicing_tuning = get_tuning(directive[1]).name
                    continue
                with warnings.catch_warnings(record=True) as caught:
                    warnings.simplefilter("always", ChordWarning)
                    voicings.extend(parse_file_line(
                        line, single=single, tuning=tuning,
                        voicing_tuning=voicing_tuning,
                        fallback_shapes=fallback_shapes,
                    ))
            except ValueError as e:
                raise ValueError(f"Line {lineno}: {e}") from e
            for w in caught:
                if issubclass(w.category, ChordWarning):
                    warnings.warn(f"Line {lineno}: {w.message}", ChordWarning)
                else:
                    warnings.warn_explicit(
                        w.message, w.category, w.filename, w.lineno
                    )
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
    name: str,
    frets: str,
    voicing_tuning: str,
    tuning: str,
    chosen: dict[tuple[str, str], ChordVoicing] | None,
) -> list[ChordVoicing]:
    """Replace an explicit voicing written for another tuning.

    Each pinned shape of a chord gets the easiest generated voicing not
    already standing in for a different shape of that chord, so a file that
    pins two E voicings doesn't print the same diagram twice, while a shape
    repeated through a song (C 0003 in every verse) is always replaced the
    same way.

    Shapes that can't be replaced are kept as written (an empty list tells
    the caller so): all-muted shapes, which are the same in every tuning,
    and, with a ChordWarning, names that aren't chords ("N.C.", "My riff")
    or chords with no playable voicing in the active tuning.

    Args:
        name: Chord name from the explicit line.
        frets: The explicit shape.
        voicing_tuning: Tuning the shape was written for.
        tuning: Active tuning.
        chosen: Replacements so far, keyed by (name, shape), updated in
            place; None disables the bookkeeping.

    Returns:
        The replacement voicing in a single-item list, or [] to keep the
        shape as written.
    """
    if all(ch in "xX" for ch in frets):
        return []
    key = (name, frets.upper())
    if chosen is not None and key in chosen:
        return [chosen[key]]

    try:
        options = _lookup_voicings(name, tuning=tuning)
    except ValueError:
        try:
            lookup_chord(name, tuning=tuning)
            problem = f"'{name}' has no playable {tuning} voicing"
        except ValueError:
            problem = f"'{name}' isn't a chord name"
        warnings.warn(
            f"{problem}, so its {voicing_tuning} shape {frets} is printed "
            f"as written",
            ChordWarning,
        )
        return []

    taken = {
        v.frets for (other, _), v in (chosen or {}).items() if other == name
    }
    voicing = next((v for v in options if v.frets not in taken), options[0])
    if chosen is not None:
        chosen[key] = voicing
    return [voicing]


def _lookup_voicings(
    name: str, single: bool = False, tuning: str = "standard"
) -> list[ChordVoicing]:
    """Look up chord voicings from the built-in database.

    If single=True, return only the first (primary) voicing.
    """
    try:
        entries = lookup_chord(name, tuning=tuning)
    except ValueError as e:
        raise ValueError(
            f"{e}. Use --list to see standard chords, or provide explicit frets."
        ) from e
    if entries is None:
        raise ValueError(
            f"No playable voicing found for '{name}'. "
            f"Provide explicit frets instead."
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
