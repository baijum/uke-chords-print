"""
Ukulele chord database.

Generates chord voicings algorithmically using pychord for music theory
and a fretboard search on standard ukulele tuning (G4-C4-E4-A4).

Each voicing dict contains:
  - frets: 4-character string, each char is the fret number for G-C-E-A
           (0 = open, X = muted)
  - fingers: 4-character string (1=index, 2=middle, 3=ring, 4=pinky,
             0=open/not used)
  - notes: space-separated note names (G-C-E-A string order)
  - inversion: "Root", "1st Inv", "2nd Inv", "3rd Inv", or ""
  - starting_fret: int, 1 means open position (default)
"""

from __future__ import annotations

from .voicing_gen import generate_voicings

# Standard chord names for --list (12 roots x 9 qualities)
_ROOTS = ["C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"]
_QUALITIES = ["", "m", "7", "maj7", "m7", "dim", "aug", "sus2", "sus4"]
STANDARD_CHORDS = [f"{root}{q}" for root in _ROOTS for q in _QUALITIES]

# Common enharmonic aliases
CHORD_ALIASES: dict[str, str] = {
    "Db": "C#",
    "D#": "Eb",
    "D#m": "Ebm",
    "Gb": "F#",
    "G#": "Ab",
    "G#m": "Abm",
    "A#": "Bb",
    "A#m": "Bbm",
}


def lookup_chord(name: str) -> list[dict] | None:
    """Look up chord voicings by name. Returns list of voicing dicts or None."""
    # Try direct generation
    try:
        voicings = generate_voicings(name)
        if voicings:
            return voicings
    except ValueError:
        pass

    # Try alias
    canonical = CHORD_ALIASES.get(name)
    if canonical:
        try:
            voicings = generate_voicings(canonical)
            if voicings:
                return voicings
        except ValueError:
            pass

    return None


def list_all_chords() -> list[str]:
    """Return sorted list of all standard chord names."""
    return sorted(STANDARD_CHORDS)
