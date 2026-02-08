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
  - # comment lines are ignored
  - blank lines are ignored
"""

from __future__ import annotations

from dataclasses import dataclass

from .chord_db import lookup_chord


@dataclass
class ChordVoicing:
    """A single chord voicing ready for rendering."""
    name: str
    frets: str          # e.g., "0003"
    fingers: str = ""   # e.g., "___3" or "0003"
    notes: str = ""     # e.g., "G C E C"
    inversion: str = ""  # e.g., "Root", "1st Inv"
    starting_fret: int = 1


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


def parse_cli_arg(arg: str) -> list[ChordVoicing]:
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
        return _lookup_voicings(name)

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

    return [ChordVoicing(name=name, frets=frets, **kwargs)]


def parse_file_line(line: str) -> list[ChordVoicing]:
    """
    Parse a single line from a text input file.

    Formats:
      C                                     -> database lookup
      C, 0003                              -> explicit frets
      C, 0003, fingers=___3                -> with fingering
      C, 0003, fingers=___3, starting_fret=3  -> with starting fret
    """
    # Strip comments and whitespace
    line = line.strip()
    if not line or line.startswith("#"):
        return []

    # Remove inline comments
    if " #" in line:
        line = line[:line.index(" #")].strip()

    parts = [p.strip() for p in line.split(",")]
    name = parts[0]

    if len(parts) == 1:
        # Just a chord name
        return _lookup_voicings(name)

    # Has explicit frets
    frets = parts[1]
    if not validate_frets(frets):
        raise ValueError(f"Invalid frets '{frets}' in line '{line}'. "
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
        elif key == "notes":
            kwargs["notes"] = val
        elif key == "inversion":
            kwargs["inversion"] = val

    return [ChordVoicing(name=name, frets=frets, **kwargs)]


def parse_file(filepath: str) -> list[ChordVoicing]:
    """Parse an entire text file and return all chord voicings."""
    voicings = []
    with open(filepath, "r") as f:
        for lineno, line in enumerate(f, 1):
            try:
                voicings.extend(parse_file_line(line))
            except ValueError as e:
                raise ValueError(f"Line {lineno}: {e}") from e
    return voicings


def parse_cli_args(args: list[str]) -> list[ChordVoicing]:
    """Parse a list of CLI arguments into chord voicings."""
    voicings = []
    for arg in args:
        voicings.extend(parse_cli_arg(arg))
    return voicings


def _lookup_voicings(name: str) -> list[ChordVoicing]:
    """Look up chord voicings from the built-in database."""
    entries = lookup_chord(name)
    if entries is None:
        raise ValueError(
            f"Chord '{name}' not found in database. "
            f"Use --list to see available chords, or provide explicit frets."
        )
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
