"""
Ukulele tuning definitions.

Supports standard (re-entrant high-G), low-G, and baritone tunings.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Tuning:
    """A ukulele tuning definition."""
    name: str
    midi_notes: tuple[int, ...]
    string_labels: tuple[str, ...]
    aliases: tuple[str, ...]


# Tuning definitions
TUNINGS: dict[str, Tuning] = {
    "standard": Tuning(
        name="standard",
        midi_notes=(67, 60, 64, 69),  # G4, C4, E4, A4
        string_labels=("G", "C", "E", "A"),
        aliases=("gcea", "high-g"),
    ),
    "low-g": Tuning(
        name="low-g",
        midi_notes=(55, 60, 64, 69),  # G3, C4, E4, A4
        string_labels=("G", "C", "E", "A"),
        aliases=("gcea-low", "linear"),
    ),
    "baritone": Tuning(
        name="baritone",
        midi_notes=(50, 55, 59, 64),  # D3, G3, B3, E4
        string_labels=("D", "G", "B", "E"),
        aliases=("dgbe",),
    ),
    "d-tuning": Tuning(
        name="d-tuning",
        midi_notes=(69, 62, 66, 71),  # A4, D4, F#4, B4
        string_labels=("A", "D", "F#", "B"),
        aliases=("adf#b",),
    ),
}

# Build alias lookup table
_ALIAS_TO_TUNING: dict[str, str] = {}
for tuning_name, tuning in TUNINGS.items():
    _ALIAS_TO_TUNING[tuning_name] = tuning_name
    for alias in tuning.aliases:
        _ALIAS_TO_TUNING[alias] = tuning_name

# Default tuning
DEFAULT_TUNING = "standard"

# Choices for CLI argument
TUNING_CHOICES = tuple(_ALIAS_TO_TUNING.keys())


def get_tuning(name: str) -> Tuning:
    """Get a Tuning by name or alias.

    Args:
        name: Tuning name or alias (e.g., "standard", "gcea", "low-g", "baritone", "dgbe")

    Returns:
        The Tuning object.

    Raises:
        ValueError: If the tuning name is not recognized.
    """
    canonical = _ALIAS_TO_TUNING.get(name.lower())
    if canonical is None:
        valid = ", ".join(sorted(_ALIAS_TO_TUNING.keys()))
        raise ValueError(f"Unknown tuning '{name}'. Valid options: {valid}")
    return TUNINGS[canonical]


def get_tuning_midi(name: str) -> tuple[int, ...]:
    """Get MIDI note values for a tuning.

    Args:
        name: Tuning name or alias.

    Returns:
        Tuple of MIDI note values for each string.
    """
    return get_tuning(name).midi_notes
