"""
Algorithmic ukulele chord voicing generator.

Uses pychord for chord-to-notes resolution and searches all fret
combinations for playable voicings. Supports multiple tunings
(standard, low-g, baritone, d-tuning).
"""

from __future__ import annotations

import re
from functools import lru_cache
from itertools import product

from pychord import Chord, QualityManager

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


# Spelling for notes outside a chord (e.g. a passing tone in an explicit
# voicing): flats for chords spelled with flats (and F), otherwise sharps
_PC_TO_SHARP = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
_PC_TO_FLAT = ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"]

# Common added-tone spellings that pychord would read as inversions
_SLASH_EXTENSIONS = {"6/9": "69", "7/9": "9", "7/13": "13"}

# Chord types pychord lacks, registered with it at import (intervals as
# pychord writes them). Extended chords list only the tones players use.
_EXTRA_QUALITIES: dict[str, tuple[str, ...]] = {
    "maj7b5": ("1", "3", "b5", "7"),
    "maj11": ("1", "3", "5", "7", "9", "11"),
    "m9b5": ("1", "b3", "b5", "b7", "9"),
    "mM7b5": ("1", "b3", "b5", "7"),
    "mM9": ("1", "b3", "5", "7", "9"),
    "mM11": ("1", "b3", "5", "7", "9", "11"),
    "7#9b13": ("1", "3", "5", "b7", "#9", "b13"),
    "13b5b9": ("1", "3", "b5", "b7", "b9", "13"),
}


def _register_extra_qualities() -> None:
    """Add _EXTRA_QUALITIES to pychord, leaving any it already defines."""
    manager = QualityManager()
    for name, intervals in _EXTRA_QUALITIES.items():
        if name not in manager.get_qualities():
            manager.set_quality(name, intervals)


_register_extra_qualities()

# Chord-chart spellings pychord doesn't know, applied in order to a quality
# (the part after the root, before any /bass) only if pychord rejects it
_QUALITY_RULES: list[tuple[str, str]] = [
    (r"[()]", ""),                       # C7(#9) -> C7#9, Cm(maj7) -> Cmmaj7
    (r"^(min|mi|-)", "m"),               # Cmi, Cmin7, C-7 -> Cm, Cm7
    (r"ø7?", "m7b5"),                    # Cø, Cø7 -> Cm7b5
    (r"^[°o]", "dim"),                   # C°, Co7 -> Cdim, Cdim7
    (r"Δ(?!\d)", "maj7"),                # CΔ, CmΔ -> Cmaj7, Cmmaj7
    (r"Δ|Maj|ma(?=\d)", "maj"),          # CΔ9, CMaj7, Cma7 -> Cmaj9, Cmaj7
    (r"^M(?=\d)", "maj"),                # CM7b5, CM11 -> Cmaj7b5, Cmaj11
    (r"^mmaj(?=\d)", "mM"),              # Cmmaj9, Cm(maj9) -> CmM9
    (r"(?<=\d)-5", "b5"),                # Cm9-5 -> Cm9b5
    (r"^M$", ""),                        # CM -> C
    (r"^\+$", "aug"),                    # C+ -> Caug
    (r"^(\+7|7\+|aug7|7aug)$", "7+5"),    # C+7, Caug7 -> C7+5
    (r"^(\+9|9\+|aug9|9aug)$", "9+5"),    # C+9, Caug9 -> C9+5
    (r"^(\+maj7|maj7\+|maj7aug|maj7#5)$", "maj7+5"),  # Cmaj7#5 -> Cmaj7+5
    (r"(?<=\d)sus$", "sus4"),            # C7sus -> C7sus4
    (r"add2$", "add9"),                  # Cadd2, Cmadd2 -> Cadd9, Cmadd9
]


def _note_to_pc(name: str) -> int:
    """Convert note name to pitch class (0-11)."""
    pc = _NOTE_TO_PC.get(name)
    if pc is None:
        raise ValueError(f"Unknown note name: {name!r}")
    return pc


def _finger_units(
    frets: tuple[int, ...], allow_spanning: bool
) -> list[tuple[int, list[int]]]:
    """Group fretted strings into units that one finger presses together.

    Adjacent strings at the same fret can always share a finger (flat
    finger / barre). With allow_spanning, same-fret strings at the lowest
    fret also share a finger across strings fretted higher in between (the
    index lies flat under the others, F# 3121); higher fingers don't barre
    under a neighbour (Ab 1343 -> 1243). A finger never covers an open or
    lower-fretted string.

    Args:
        frets: Fret per string (0 = open).
        allow_spanning: Allow barres across higher-fretted strings.

    Returns:
        (fret, string indices) units, ordered by fret then string.
    """
    units: list[tuple[int, list[int]]] = []
    fret_values = sorted({f for f in frets if f > 0})
    for fret_val in fret_values:
        strings = [i for i, f in enumerate(frets) if f == fret_val]
        spanning = allow_spanning and fret_val == fret_values[0]
        unit = [strings[0]]
        for s in strings[1:]:
            between = range(unit[-1] + 1, s)
            if ((spanning or not between)
                    and all(frets[k] > fret_val for k in between)):
                unit.append(s)
            else:
                units.append((fret_val, unit))
                unit = [s]
        units.append((fret_val, unit))
    return units


def _assign_fingers(frets: tuple[int, ...]) -> str:
    """Assign finger numbers to a fret combination.

    Uses a stretch-aware heuristic based on standard ukulele technique:
    - Open strings = 0
    - Adjacent strings at one fret share a finger (flat finger / barre).
      An index barre across higher-fretted strings is used only when every
      string is fretted (F# 3121, B7 2322); otherwise those strings get
      separate fingers (G 0232 -> 0132, Ab 1343 -> 1243)
    - A lone fretted string in open position uses the finger matching its
      fret (C 0003 -> ring finger); otherwise the index finger takes the
      lowest fret, one finger per fret from there (Em 0432 -> 0321)
    - Fingers always increase with fret and never exceed 4
    """
    fretted = [f for f in frets if f > 0]
    if not fretted:
        return "0" * len(frets)

    fingers = [0] * len(frets)
    finger_units = _finger_units(
        frets, allow_spanning=len(fretted) == len(frets)
    )
    anchor = 1 if len(fretted) == 1 and fretted[0] <= 4 else min(fretted)

    # Assign fingers: stretch-aware, strictly increasing, and leaving
    # enough fingers (max 4) for the units still to come
    next_finger = 1
    prev: tuple[int, int] | None = None  # (fret, finger) of previous unit
    for i, (fret_val, string_indices) in enumerate(finger_units):
        target = fret_val - anchor + 1
        if prev is not None:
            # Keep one finger per fret relative to the previous finger
            # (Fm 1013 -> 1024, not 1023)
            target = max(target, prev[1] + fret_val - prev[0])
        last_allowed = 4 - (len(finger_units) - 1 - i)
        fn = min(max(min(target, 4), next_finger), last_allowed)
        for s in string_indices:
            fingers[s] = fn
        next_finger = fn + 1
        prev = (fret_val, fn)

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
    then natural inner extensions (9th, 11th) from the top down, then the
    root (a rootless voicing, e.g. A9/E where the bass is the 5th), and
    only then altered inner tones (b5, #5, b9), which give the chord its
    name (C9b5 keeps the b5 rather than sound like C9). The 3rd, 7th,
    highest (naming) extension and a slash chord's bass are always kept.

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

    top = tones[-1]

    def inner(intervals: set[int]) -> list[int]:
        """Inner tones with these intervals, from the top down."""
        return [
            pc for pc in reversed(tones)
            if pc not in (top, bass_pc) and (pc - root_pc) % 12 in intervals
        ]

    droppable = inner({7})             # perfect 5th
    droppable += inner({2, 5, 9})      # natural 9th, 11th, 13th
    if root_pc not in (top, bass_pc):
        droppable.append(root_pc)
    droppable += inner({1, 6, 8})      # b9, b5/#11, #5/b13

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
      3. Finger count        – more distinct finger positions = more coordination
      4. Fret position       – higher frets = tighter spacing, less comfortable,
                               and leaving first position (above fret 4) is
                               a shift from the chords around it
      5. Open strings        – easier in first position; with the hand up the
                               neck (C 0066-style shapes) they are harder to
                               keep ringing, and an open string between
                               fretted ones needs arched fingers (Em 0402)
      6. Finger independence – non-barre fingers far apart = harder
      7. Compact shape       – clustered frets are familiar / easier

    The weights were calibrated so the easiest voicing matches the shape
    chord charts show first (chords-db, see tests/) for most common chords.
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

    # --- Fingers needed: fewest units, with barres wherever possible ---
    finger_count = len(_finger_units(frets, allow_spanning=True))

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

    # --- Open strings: a help in first position, a hindrance higher up ---
    first_position = max(non_zero) <= 4
    open_weight = -1.5 if first_position else 1.5
    fretted_strings = [i for i, f in enumerate(frets) if f > 0]
    sandwiched_open = sum(
        1 for i, f in enumerate(frets)
        if f == 0 and fretted_strings[0] < i < fretted_strings[-1]
    )

    score = (
        fret_span * 2.0             # wider stretch = harder
        + num_fretted * 1.5         # more fingers needed
        + barre_count * 1.5         # barres require sustained pressure
        + avg_fret * 2.0            # higher position = less comfortable
        + finger_count * 0.5        # more distinct finger positions = harder
        + independence_penalty      # large gaps between fingers
        + num_open * open_weight    # open strings (see above)
        + sandwiched_open * 4.0     # fingers arched over an open string
        + (0.0 if first_position else 4.0)  # shift out of first position
        - is_compact * 2.0          # compact shapes are familiar
    )
    return max(score, 0.0)


def _difficulty_label(score: float) -> str:
    """Map a numeric difficulty score to a human-readable label."""
    if score <= 4:
        return "easy"
    elif score <= 10:
        return "moderate"
    elif score <= 16:
        return "hard"
    return "very hard"


def _pychord_name(chord_name: str) -> str:
    """Respell chord names that pychord would misread.

    pychord reads "/<number>" as an inversion, so "C6/9" or "A7/9" would
    silently lose the added tone. Common forms are respelled ("C6/9" ->
    "C69", "A7/9" -> "A9", "Cmaj7/9" -> "Cmaj9", "G7/13" -> "G13"); any
    other "/<number>" is rejected rather than drawn as the wrong chord.

    Common chord-chart spellings pychord doesn't know are respelled too:
    ♭/♯ -> b/#, "+" -> aug, "°"/"o" -> dim, "ø" -> m7b5, "Δ" -> maj7,
    "m/maj7" and "m(maj7)" -> mM7, "mi"/"min7"/"-7" -> m/m7, "7(#9)" ->
    7#9, "maj7#5" -> maj7+5, "aug9" -> 9+5, "7sus" -> 7sus4 (see
    _QUALITY_RULES). Chord types pychord lacks entirely (maj7b5, maj11,
    m9b5, mM9, ...) are registered from _EXTRA_QUALITIES.

    Args:
        chord_name: Chord name as written by the user.

    Returns:
        The name to pass to pychord.

    Raises:
        ValueError: If the name has an unsupported "/<number>" or a
            lowercase root or bass note.
    """
    name = chord_name.replace("♭", "b").replace("♯", "#")
    # Note names are capitalized; say so rather than "Invalid note a"
    if re.match(r"[a-g]", name) or re.search(r"/[a-g]", name):
        fixed = re.sub(r"(^|/)([a-g])", lambda m: m[1] + m[2].upper(), name)
        raise ValueError(
            f"Cannot parse chord '{chord_name}': note names are capital "
            f"letters (did you mean '{fixed}'?)"
        )
    # Minor-major seventh written with a slash, before slash parsing
    name = re.sub(r"(m|min|mi|-)/(maj7|Maj7|ma7|M7|Δ7?)", "mM7", name)
    name = re.sub(
        r"(6/9|7/9|7/13)(?=/|$)",
        lambda m: _SLASH_EXTENSIONS[m.group(1)],
        name,
    )
    if re.search(r"/\d", name):
        raise ValueError(
            f"Cannot parse chord '{chord_name}': a number after '/' is not "
            f"supported. Write the extension in the name (e.g. C9, C7b9) "
            f"or use a bass note (e.g. C/E)"
        )

    m = re.fullmatch(r"([A-G][#b]?)(.*?)(/[A-G][#b]?)?", name)
    if m and not _known_quality(m.group(2)):
        root, quality, bass = m.group(1), m.group(2), m.group(3) or ""
        for pattern, repl in _QUALITY_RULES:
            quality = re.sub(pattern, repl, quality)
        # Keep the original if nothing matched, so errors name what was typed
        if _known_quality(quality):
            name = root + quality + bass
    return name


@lru_cache(maxsize=None)
def _known_quality(quality: str) -> bool:
    """Check whether pychord understands a chord quality as written."""
    try:
        Chord("C" + quality)
    except Exception:
        return False
    return True


def _resolve_chord(
    chord_name: str,
) -> tuple[list[str], str, str | None, list[str]]:
    """Resolve a chord name to its notes with pychord.

    Args:
        chord_name: Chord name (e.g., "Am7", "C/G", "A7/9").

    Returns:
        (components, root, bass, base_components): note names, the root,
        a slash chord's bass note (or None), and the notes of the chord
        above the bass (the same as components without a bass).

    Raises:
        ValueError: If the chord name is not recognized.
    """
    pychord_name = _pychord_name(chord_name)
    try:
        chord = Chord(pychord_name)
        components = chord.components()
        root = chord.root
        bass = chord.on or None
        # A slash chord's inversion is named from the chord above the bass
        base_components = (
            Chord(pychord_name[:pychord_name.rindex("/")]).components()
            if bass else components
        )
    except Exception as e:
        raise ValueError(f"Cannot parse chord '{chord_name}': {e}") from e
    return components, root, bass, base_components


def describe_voicing(
    chord_name: str,
    frets: tuple[int, ...],
    tuning: str = DEFAULT_TUNING,
) -> tuple[str, str]:
    """Name the notes and inversion of a given fret shape.

    Used to label explicit voicings the same way as generated ones.

    Args:
        chord_name: Chord name the shape is played for.
        frets: Fret per string in tuning order (-1 = muted).
        tuning: Tuning name or alias.

    Returns:
        (notes, inversion): space-separated note names in string order
        ("-" for a muted string; notes outside the chord use flats if the
        chord is spelled with flats, else sharps) and the inversion label
        ("" if the lowest note isn't a chord tone).

    Raises:
        ValueError: If the chord name is not recognized.
    """
    components, root, _, base_components = _resolve_chord(chord_name)
    pc_to_name = {_note_to_pc(n): n for n in components}
    flats = root == "F" or any("b" in n[1:] for n in components)
    other_names = _PC_TO_FLAT if flats else _PC_TO_SHARP
    tuning_midi = get_tuning_midi(tuning)

    names = []
    sounding = []
    for open_midi, fret in zip(tuning_midi, frets):
        if fret < 0:
            names.append("-")
            continue
        pc = (open_midi + fret) % 12
        names.append(pc_to_name.get(pc, other_names[pc]))
        sounding.append(open_midi + fret)

    base_pcs = [_note_to_pc(n) for n in base_components]
    inversion = _detect_inversion(base_pcs, tuple(sounding)) if sounding else ""
    return " ".join(names), inversion


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
    components, root, bass, base_components = _resolve_chord(chord_name)

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
