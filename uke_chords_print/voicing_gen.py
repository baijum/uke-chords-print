"""
Algorithmic ukulele chord voicing generator.

Uses pychord for chord-to-notes resolution and searches all fret
combinations for playable voicings. Supports multiple tunings
(standard, low-g, baritone, d-tuning).
"""

from __future__ import annotations

from itertools import product

from pychord import Chord

from .tunings import get_tuning_midi, DEFAULT_TUNING

# Note name -> pitch class (0-11, C=0)
# Includes enharmonic equivalents, double-sharps, and double-flats
# that pychord may return for theoretically-spelled chords.
_NOTE_TO_PC: dict[str, int] = {
    "C": 0, "B#": 0, "Dbb": 0,
    "C#": 1, "Db": 1, "B##": 1,
    "D": 2, "C##": 2, "Ebb": 2,
    "D#": 3, "Eb": 3, "Fbb": 3,
    "E": 4, "Fb": 4, "D##": 4,
    "F": 5, "E#": 5, "Gbb": 5,
    "F#": 6, "Gb": 6, "E##": 6,
    "G": 7, "F##": 7, "Abb": 7,
    "G#": 8, "Ab": 8,
    "A": 9, "G##": 9, "Bbb": 9,
    "A#": 10, "Bb": 10, "Cbb": 10,
    "B": 11, "Cb": 11, "A##": 11,
}


def _note_to_pc(name: str) -> int:
    """Convert note name to pitch class (0-11)."""
    pc = _NOTE_TO_PC.get(name)
    if pc is None:
        raise ValueError(f"Unknown note name: {name!r}")
    return pc


def _assign_fingers(frets: tuple[int, ...]) -> str:
    """Assign finger numbers to a fret combination.

    Uses a stretch-aware heuristic based on standard ukulele technique:
    - Open strings = 0
    - Strings at the same fret share one finger (barre / flat finger) only
      when every string between them is fretted higher; a finger can't
      lie across a string that must ring open or sound a lower fret
    - Finger number based on offset from lowest fret (one-finger-per-fret),
      always increasing with fret and never above 4
    """
    if all(f == 0 for f in frets):
        return "0" * len(frets)

    fingers = [0] * len(frets)
    non_zero = [f for f in frets if f > 0]
    min_fret = min(non_zero)

    # Build finger units: strings at one fret that a single finger can
    # cover together, in fret order (then string order).
    finger_units: list[tuple[int, list[int]]] = []
    for fret_val in sorted(set(non_zero)):
        strings = [i for i, f in enumerate(frets) if f == fret_val]
        unit = [strings[0]]
        for s in strings[1:]:
            if all(frets[k] > fret_val for k in range(unit[-1] + 1, s)):
                unit.append(s)
            else:
                finger_units.append((fret_val, unit))
                unit = [s]
        finger_units.append((fret_val, unit))

    # Assign fingers: stretch-aware, strictly increasing, and leaving
    # enough fingers (max 4) for the units still to come
    next_finger = 1
    for i, (fret_val, string_indices) in enumerate(finger_units):
        target = fret_val - min_fret + 1
        last_allowed = 4 - (len(finger_units) - 1 - i)
        fn = min(max(min(target, 4), next_finger), last_allowed)
        for s in string_indices:
            fingers[s] = fn
        next_finger = fn + 1

    return "".join(str(f) for f in fingers)


def _detect_inversion(
    component_pcs: list[int],
    midi_notes: tuple[int, ...],
) -> str:
    """Determine inversion from the lowest-pitched note."""
    lowest_pc = min(midi_notes) % 12

    try:
        idx = component_pcs.index(lowest_pc)
    except ValueError:
        return ""

    if idx == 0:
        return "Root"

    labels = {1: "1st Inv", 2: "2nd Inv", 3: "3rd Inv"}
    return labels.get(idx, "")


def _required_pcs(
    component_pcs: list[int],
    root_pc: int,
    max_tones: int = 4,
    bass_pc: int | None = None,
) -> set[int]:
    """Choose the chord tones every voicing must contain.

    A ukulele has four strings, so chords with more distinct notes (9ths,
    11ths, 13ths) drop tones the way players do: the perfect 5th first,
    then inner extensions from the top down. The root, 3rd, 7th and the
    highest (naming) extension are always kept, as is a slash chord's bass.

    Args:
        component_pcs: Chord tone pitch classes in pychord order.
        root_pc: Pitch class of the chord root.
        max_tones: Number of strings available.
        bass_pc: Pitch class of a slash chord's bass note, if any.

    Returns:
        Set of pitch classes a voicing must include. Has more than
        max_tones entries only if nothing more can be dropped.
    """
    tones = list(dict.fromkeys(component_pcs))
    if len(tones) <= max_tones:
        return set(tones)

    keep_intervals = {0, 3, 4, 10, 11}  # root, 3rds, 7ths
    top = tones[-1]
    droppable = [
        pc for pc in tones if (pc - root_pc) % 12 == 7 and pc != bass_pc
    ]
    droppable += [
        pc for pc in reversed(tones)
        if pc not in (top, bass_pc) and pc not in droppable
        and (pc - root_pc) % 12 not in keep_intervals
    ]

    required = list(tones)
    for pc in droppable:
        if len(required) <= max_tones:
            break
        required.remove(pc)
    return set(required)


def compute_starting_fret(frets: tuple[int, ...]) -> int:
    """Compute starting_fret for diagram display.

    If all non-zero frets fit within 1-4, returns 1 (open position).
    Otherwise returns the lowest non-zero fret so the diagram window
    covers all fretted positions. Muted strings (negative values) are
    ignored.
    """
    non_zero = [f for f in frets if f > 0]
    if not non_zero or max(non_zero) <= 4:
        return 1
    return min(non_zero)


def _score_voicing(frets: tuple[int, ...]) -> float:
    """Research-backed difficulty score (lower = easier).

    Based on the ISMIR 2023 playability rubric (Vélez Vásquez et al.)
    and the Radicioni biomechanical model, adapted for ukulele.

    Seven factors are combined:
      1. Fret span          – wider stretch = harder hand position
      2. Barre complexity    – sustained pressure across strings
      3. Finger count        – more distinct positions = more coordination
      4. Fret position       – higher frets = tighter spacing, less comfortable
      5. Open string count   – more open strings = easier
      6. Finger independence – non-barre fingers far apart = harder
      7. Compact shape       – clustered frets are familiar / easier
    """
    non_zero = [f for f in frets if f > 0]
    if not non_zero:
        return 0.0  # all open strings — easiest possible

    num_fretted = len(non_zero)
    num_open = 4 - num_fretted
    fret_span = max(non_zero) - min(non_zero)
    avg_fret = sum(non_zero) / len(non_zero)

    # --- Barre detection: consecutive strings at the same fret ---
    barre_count = 0
    for fret_val in set(non_zero):
        strings_at_fret = [i for i, f in enumerate(frets) if f == fret_val]
        for j in range(len(strings_at_fret) - 1):
            if strings_at_fret[j + 1] - strings_at_fret[j] == 1:
                barre_count += 1
                break  # one barre per fret value

    # --- Distinct finger positions (unique non-zero fret values) ---
    unique_frets = len(set(non_zero))

    # --- Finger independence: max gap between non-barre fingers ---
    # After removing barre frets, check if remaining fingers are spread
    independence_penalty = 0.0
    if unique_frets > 1:
        sorted_unique = sorted(set(non_zero))
        max_gap = max(
            sorted_unique[i + 1] - sorted_unique[i]
            for i in range(len(sorted_unique) - 1)
        )
        if max_gap > 2:
            independence_penalty = (max_gap - 2) * 1.5

    # --- Compact shape: all fretted notes within 2 adjacent frets ---
    is_compact = 1.0 if fret_span <= 1 else 0.0

    score = (
        fret_span * 2.0             # wider stretch = harder
        + num_fretted * 2.0         # more fingers needed
        + barre_count * 1.5         # barres require sustained pressure
        + avg_fret * 1.0            # higher position = less comfortable
        + unique_frets * 1.0        # more distinct positions = harder
        + independence_penalty      # large gaps between fingers
        - num_open * 1.5            # open strings reduce difficulty
        - is_compact * 2.0          # compact shapes are familiar
    )
    return max(score, 0.0)


def _difficulty_label(score: float) -> str:
    """Map a numeric difficulty score to a human-readable label."""
    if score <= 4:
        return "easy"
    elif score <= 11:
        return "moderate"
    elif score <= 15:
        return "hard"
    return "very hard"


def generate_voicings(
    chord_name: str,
    *,
    max_fret: int = 9,
    max_span: int = 3,
    max_results: int = 3,
    tuning: str = DEFAULT_TUNING,
) -> list[dict]:
    """Generate playable ukulele voicings for a chord.

    Uses pychord to resolve the chord's component notes, then searches
    all fret combinations on the 4 ukulele strings for voicings where
    every note is a chord tone and all required chord tones are present.
    Chords with more than four distinct notes omit the 5th (and, if
    needed, inner extensions); see _required_pcs. For slash chords
    (e.g. "C/G"), shapes with the named bass as the lowest-pitched note
    are returned when any exist; otherwise the bass is not enforced.

    Args:
        chord_name: Chord name (e.g., "Am7", "C", "F#dim").
        max_fret: Highest fret to search (0-9 for single-digit format).
        max_span: Maximum fret span among fretted notes.
        max_results: Maximum voicings to return.
        tuning: Tuning name or alias (e.g., "standard", "low-g", "baritone").

    Returns:
        List of voicing dicts with keys: frets, fingers, notes, inversion,
        and optionally starting_fret.

    Raises:
        ValueError: If the chord name is not recognized by pychord.
    """
    tuning_midi = get_tuning_midi(tuning)

    # pychord reads "/<digit>" as an inversion, so "C6/9" would lose its 9th
    pychord_name = chord_name.replace("6/9", "69")

    try:
        chord = Chord(pychord_name)
        components = chord.components()
        root = chord.root
        bass = chord.on
        # A slash chord's inversion is named from the chord above the bass
        base_components = (
            Chord(pychord_name[:pychord_name.rindex("/")]).components()
            if bass else components
        )
    except Exception as e:
        raise ValueError(f"Cannot parse chord '{chord_name}': {e}") from e

    component_pcs = [_note_to_pc(n) for n in components]
    target_pcs = set(component_pcs)
    base_pcs = [_note_to_pc(n) for n in base_components]
    bass_pc = _note_to_pc(bass) if bass else None
    required_pcs = _required_pcs(
        component_pcs, _note_to_pc(root), bass_pc=bass_pc
    )
    pc_to_name = {_note_to_pc(n): n for n in components}

    # Precompute valid frets per string (only those producing a chord tone)
    valid_frets_per_string: list[list[int]] = []
    for open_midi in tuning_midi:
        valid = [
            fret
            for fret in range(max_fret + 1)
            if (open_midi + fret) % 12 in target_pcs
        ]
        valid_frets_per_string.append(valid)

    scored: list[tuple[float, dict, bool]] = []

    for frets in product(*valid_frets_per_string):
        midi_notes = tuple(tuning_midi[i] + frets[i] for i in range(4))
        pcs = tuple(m % 12 for m in midi_notes)

        # All required chord tones must be present
        if not required_pcs <= set(pcs):
            continue

        # Playability: fret span check
        non_zero = [f for f in frets if f > 0]
        if non_zero and (max(non_zero) - min(non_zero)) > max_span:
            continue

        # Build voicing dict
        fret_str = "".join(str(f) for f in frets)
        fingers = _assign_fingers(frets)
        note_names = " ".join(pc_to_name[pc] for pc in pcs)
        inversion = _detect_inversion(base_pcs, midi_notes)
        has_bass = bass_pc is None or min(midi_notes) % 12 == bass_pc
        starting_fret = compute_starting_fret(frets)

        score = _score_voicing(frets)

        voicing: dict = {
            "frets": fret_str,
            "fingers": fingers,
            "notes": note_names,
            "inversion": inversion,
            "difficulty": _difficulty_label(score),
        }
        if starting_fret > 1:
            voicing["starting_fret"] = starting_fret

        scored.append((score, voicing, has_bass))

    # Slash chords: prefer shapes with the named bass lowest, if any exist
    if any(has_bass for _, _, has_bass in scored):
        scored = [s for s in scored if s[2]]

    scored.sort(key=lambda x: x[0])
    return [v for _, v, _ in scored[:max_results]]
