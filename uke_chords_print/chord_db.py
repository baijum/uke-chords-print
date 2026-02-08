"""
Built-in ukulele chord database.

Standard ukulele tuning: G4-C4-E4-A4 (re-entrant high-G).

Each chord entry contains:
  - frets: 4-character string, each char is the fret number for G-C-E-A
           (0 = open, X = muted)
  - fingers: 4-character string (1=index, 2=middle, 3=ring, 4=pinky,
             0 or _=open/not used)
  - notes: string notes produced (G-C-E-A order)
  - inversion: "Root", "1st Inv", "2nd Inv", or ""
  - starting_fret: int, 1 means open position (default)
"""

# Chord voicing dataclass-style dict
# Each key is the chord name (e.g., "C", "Am", "G7")
# Each value is a list of voicing dicts

CHORD_DB = {
    # =========================================================================
    # MAJOR CHORDS
    # =========================================================================
    "C": [
        {"frets": "0003", "fingers": "0003", "notes": "G C E C", "inversion": "Root"},
        {"frets": "5433", "fingers": "4211", "notes": "C E G C", "inversion": "Root", "starting_fret": 3},
        {"frets": "0433", "fingers": "0211", "notes": "G E G C", "inversion": "1st Inv"},
    ],
    "C#": [
        {"frets": "1114", "fingers": "1114", "notes": "G# C# F C#", "inversion": "Root"},
    ],
    "Db": [
        {"frets": "1114", "fingers": "1114", "notes": "Ab Db F Db", "inversion": "Root"},
    ],
    "D": [
        {"frets": "2220", "fingers": "1230", "notes": "A D F# A", "inversion": "Root"},
        {"frets": "2225", "fingers": "1114", "notes": "A D F# D", "inversion": "Root"},
    ],
    "Eb": [
        {"frets": "3331", "fingers": "3341", "notes": "Bb Eb G Bb", "inversion": "Root"},
        {"frets": "0331", "fingers": "0231", "notes": "G Eb G Bb", "inversion": "1st Inv"},
    ],
    "E": [
        {"frets": "4442", "fingers": "3341", "notes": "B E G# B", "inversion": "Root"},
        {"frets": "1402", "fingers": "1302", "notes": "G# E G# B", "inversion": "1st Inv"},
    ],
    "F": [
        {"frets": "2010", "fingers": "2010", "notes": "A C F A", "inversion": "Root"},
        {"frets": "5558", "fingers": "1114", "notes": "C F A F", "inversion": "Root", "starting_fret": 5},
    ],
    "F#": [
        {"frets": "3121", "fingers": "3121", "notes": "A# C# F# A#", "inversion": "Root"},
    ],
    "Gb": [
        {"frets": "3121", "fingers": "3121", "notes": "Bb Db Gb Bb", "inversion": "Root"},
    ],
    "G": [
        {"frets": "0232", "fingers": "0132", "notes": "G D G B", "inversion": "Root"},
        {"frets": "4232", "fingers": "4132", "notes": "B D G B", "inversion": "1st Inv"},
    ],
    "Ab": [
        {"frets": "5343", "fingers": "4132", "notes": "C Eb Ab C", "inversion": "Root", "starting_fret": 3},
        {"frets": "1343", "fingers": "1243", "notes": "Ab Eb Ab C", "inversion": "Root"},
    ],
    "A": [
        {"frets": "2100", "fingers": "2100", "notes": "A C# E A", "inversion": "Root"},
    ],
    "Bb": [
        {"frets": "3211", "fingers": "3211", "notes": "Bb D F Bb", "inversion": "Root"},
    ],
    "B": [
        {"frets": "4322", "fingers": "4211", "notes": "B D# F# B", "inversion": "Root"},
    ],

    # =========================================================================
    # MINOR CHORDS
    # =========================================================================
    "Cm": [
        {"frets": "0333", "fingers": "0111", "notes": "G C Eb C", "inversion": "Root"},
        {"frets": "0333", "fingers": "0234", "notes": "G C Eb C", "inversion": "Root"},
    ],
    "C#m": [
        {"frets": "1444", "fingers": "1222", "notes": "G# C# E C#", "inversion": "Root"},
    ],
    "Dm": [
        {"frets": "2210", "fingers": "2310", "notes": "A D F A", "inversion": "Root"},
    ],
    "Ebm": [
        {"frets": "3321", "fingers": "3421", "notes": "Bb Eb Gb Bb", "inversion": "Root"},
    ],
    "Em": [
        {"frets": "0432", "fingers": "0321", "notes": "G E G B", "inversion": "1st Inv"},
        {"frets": "4432", "fingers": "3421", "notes": "B E G B", "inversion": "Root"},
    ],
    "Fm": [
        {"frets": "1013", "fingers": "1024", "notes": "Ab C F Ab", "inversion": "Root"},
    ],
    "F#m": [
        {"frets": "2120", "fingers": "2130", "notes": "A C# F# A", "inversion": "Root"},
    ],
    "Gm": [
        {"frets": "0231", "fingers": "0231", "notes": "G D G Bb", "inversion": "Root"},
    ],
    "Abm": [
        {"frets": "1342", "fingers": "1342", "notes": "Ab Eb Ab B", "inversion": "Root"},
    ],
    "Am": [
        {"frets": "2000", "fingers": "1000", "notes": "A C E A", "inversion": "Root"},
        {"frets": "2003", "fingers": "2004", "notes": "A C E C", "inversion": "Root"},
    ],
    "Bbm": [
        {"frets": "3111", "fingers": "3111", "notes": "Bb Db F Bb", "inversion": "Root"},
    ],
    "Bm": [
        {"frets": "4222", "fingers": "4111", "notes": "B D F# B", "inversion": "Root"},
    ],

    # =========================================================================
    # DOMINANT 7TH CHORDS
    # =========================================================================
    "C7": [
        {"frets": "0001", "fingers": "0001", "notes": "G C E Bb", "inversion": "Root"},
        {"frets": "0303", "fingers": "0102", "notes": "G Eb E C", "inversion": "Root"},
    ],
    "D7": [
        {"frets": "2223", "fingers": "1112", "notes": "A D F# C", "inversion": "Root"},
        {"frets": "2020", "fingers": "1020", "notes": "A D F# A", "inversion": "Root"},
    ],
    "E7": [
        {"frets": "1202", "fingers": "1302", "notes": "G# D E B", "inversion": "Root"},
    ],
    "F7": [
        {"frets": "2313", "fingers": "2314", "notes": "A Eb F A", "inversion": "Root"},
    ],
    "G7": [
        {"frets": "0212", "fingers": "0213", "notes": "G D F B", "inversion": "Root"},
    ],
    "A7": [
        {"frets": "0100", "fingers": "0100", "notes": "G C# E A", "inversion": "Root"},
    ],
    "B7": [
        {"frets": "2322", "fingers": "1211", "notes": "A D# F# B", "inversion": "Root"},
    ],
    "Bb7": [
        {"frets": "1211", "fingers": "1211", "notes": "Ab D F Bb", "inversion": "Root"},
    ],
    "Eb7": [
        {"frets": "3334", "fingers": "1112", "notes": "Bb Eb G Db", "inversion": "Root"},
    ],
    "Ab7": [
        {"frets": "1323", "fingers": "1324", "notes": "Ab Eb Gb C", "inversion": "Root"},
    ],

    # =========================================================================
    # MAJOR 7TH CHORDS
    # =========================================================================
    "Cmaj7": [
        {"frets": "0002", "fingers": "0002", "notes": "G C E B", "inversion": "Root"},
    ],
    "Dmaj7": [
        {"frets": "2224", "fingers": "1113", "notes": "A D F# C#", "inversion": "Root"},
    ],
    "Emaj7": [
        {"frets": "1302", "fingers": "1302", "notes": "G# D# E B", "inversion": "Root"},
    ],
    "Fmaj7": [
        {"frets": "2410", "fingers": "1300", "notes": "A E F A", "inversion": "Root"},
    ],
    "Gmaj7": [
        {"frets": "0222", "fingers": "0111", "notes": "G D F# B", "inversion": "Root"},
    ],
    "Amaj7": [
        {"frets": "1100", "fingers": "1200", "notes": "G# C# E A", "inversion": "Root"},
    ],
    "Bbmaj7": [
        {"frets": "3210", "fingers": "3210", "notes": "Bb D F A", "inversion": "Root"},
    ],
    "Bmaj7": [
        {"frets": "4321", "fingers": "4321", "notes": "B D# F# A#", "inversion": "Root"},
    ],

    # =========================================================================
    # MINOR 7TH CHORDS
    # =========================================================================
    "Cm7": [
        {"frets": "3333", "fingers": "1111", "notes": "Bb Eb G C", "inversion": "Root", "starting_fret": 3},
    ],
    "Dm7": [
        {"frets": "2213", "fingers": "2213", "notes": "A D F C", "inversion": "Root"},
    ],
    "Em7": [
        {"frets": "0202", "fingers": "0102", "notes": "G D E B", "inversion": "Root"},
    ],
    "Fm7": [
        {"frets": "1313", "fingers": "1324", "notes": "Ab Eb F Ab", "inversion": "Root"},
    ],
    "Gm7": [
        {"frets": "0211", "fingers": "0211", "notes": "G D F Bb", "inversion": "Root"},
    ],
    "Am7": [
        {"frets": "0000", "fingers": "0000", "notes": "G C E A", "inversion": "Root"},
        {"frets": "0030", "fingers": "0020", "notes": "G C G A", "inversion": "Root"},
    ],
    "Bm7": [
        {"frets": "2222", "fingers": "1111", "notes": "A D F# B", "inversion": "Root"},
    ],
    "Bbm7": [
        {"frets": "1111", "fingers": "1111", "notes": "Ab Db F Bb", "inversion": "Root"},
    ],

    # =========================================================================
    # DIMINISHED CHORDS
    # =========================================================================
    "Cdim": [
        {"frets": "0332", "fingers": "0231", "notes": "G C Eb Bb", "inversion": "Root"},
    ],
    "Ddim": [
        {"frets": "1210", "fingers": "1320", "notes": "G# D F A", "inversion": "Root"},
    ],
    "Edim": [
        {"frets": "0101", "fingers": "0102", "notes": "G C# E Bb", "inversion": "Root"},
    ],
    "Fdim": [
        {"frets": "1212", "fingers": "1324", "notes": "Ab Cb F Ab", "inversion": "Root"},
    ],
    "Gdim": [
        {"frets": "0131", "fingers": "0132", "notes": "G Db F Bb", "inversion": "Root"},
    ],
    "Adim": [
        {"frets": "2320", "fingers": "1320", "notes": "A Eb E A", "inversion": "Root"},
    ],
    "Bdim": [
        {"frets": "1202", "fingers": "1203", "notes": "G# D F B", "inversion": "Root"},
    ],

    # =========================================================================
    # AUGMENTED CHORDS
    # =========================================================================
    "Caug": [
        {"frets": "1003", "fingers": "1004", "notes": "G# C E C", "inversion": "Root"},
    ],
    "Daug": [
        {"frets": "3221", "fingers": "4231", "notes": "Bb D F# Bb", "inversion": "Root"},
    ],
    "Eaug": [
        {"frets": "1003", "fingers": "1003", "notes": "G# C E C", "inversion": "Root"},
    ],
    "Faug": [
        {"frets": "2110", "fingers": "2110", "notes": "A C# F A", "inversion": "Root"},
    ],
    "Gaug": [
        {"frets": "0332", "fingers": "0221", "notes": "G Eb G B", "inversion": "Root"},
    ],
    "Aaug": [
        {"frets": "2110", "fingers": "3210", "notes": "A C# F A", "inversion": "Root"},
    ],
    "Bbaug": [
        {"frets": "3221", "fingers": "3221", "notes": "Bb D F# Bb", "inversion": "Root"},
    ],

    # =========================================================================
    # SUSPENDED 2ND CHORDS
    # =========================================================================
    "Csus2": [
        {"frets": "0233", "fingers": "0123", "notes": "G D G C", "inversion": "Root"},
    ],
    "Dsus2": [
        {"frets": "2200", "fingers": "1200", "notes": "A D E A", "inversion": "Root"},
    ],
    "Esus2": [
        {"frets": "4420", "fingers": "2310", "notes": "B D E A", "inversion": "Root"},
    ],
    "Fsus2": [
        {"frets": "0013", "fingers": "0012", "notes": "G C G Bb", "inversion": "Root"},
    ],
    "Gsus2": [
        {"frets": "0230", "fingers": "0120", "notes": "G D G A", "inversion": "Root"},
    ],
    "Asus2": [
        {"frets": "2400", "fingers": "1300", "notes": "A E E A", "inversion": "Root"},
    ],

    # =========================================================================
    # SUSPENDED 4TH CHORDS
    # =========================================================================
    "Csus4": [
        {"frets": "0013", "fingers": "0013", "notes": "G C F C", "inversion": "Root"},
    ],
    "Dsus4": [
        {"frets": "2230", "fingers": "1230", "notes": "A D G A", "inversion": "Root"},
    ],
    "Esus4": [
        {"frets": "2442", "fingers": "1331", "notes": "A E A B", "inversion": "Root"},
    ],
    "Fsus4": [
        {"frets": "3011", "fingers": "3011", "notes": "Bb C F Bb", "inversion": "Root"},
    ],
    "Gsus4": [
        {"frets": "0233", "fingers": "0123", "notes": "G D G C", "inversion": "Root"},
    ],
    "Asus4": [
        {"frets": "2200", "fingers": "1200", "notes": "A D E A", "inversion": "Root"},
    ],
}

# Common aliases
CHORD_ALIASES = {
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
    # Direct lookup
    if name in CHORD_DB:
        return CHORD_DB[name]
    # Try alias
    canonical = CHORD_ALIASES.get(name)
    if canonical and canonical in CHORD_DB:
        return CHORD_DB[canonical]
    return None


def list_all_chords() -> list[str]:
    """Return sorted list of all chord names in the database."""
    return sorted(CHORD_DB.keys())
