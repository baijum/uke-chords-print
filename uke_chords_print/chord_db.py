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
        {"frets": "5433", "fingers": "4211", "notes": "C E G C", "inversion": "1st Inv", "starting_fret": 3},
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
        {"frets": "0331", "fingers": "0231", "notes": "G Eb G Bb", "inversion": "Root"},
    ],
    "E": [
        {"frets": "4442", "fingers": "3341", "notes": "B E G# B", "inversion": "Root"},
        {"frets": "1402", "fingers": "1302", "notes": "G# E E B", "inversion": "Root"},
    ],
    "F": [
        {"frets": "2010", "fingers": "2010", "notes": "A C F A", "inversion": "2nd Inv"},
        {"frets": "5558", "fingers": "1114", "notes": "C F A F", "inversion": "Root", "starting_fret": 5},
    ],
    "F#": [
        {"frets": "3121", "fingers": "3121", "notes": "A# C# F# A#", "inversion": "2nd Inv"},
    ],
    "Gb": [
        {"frets": "3121", "fingers": "3121", "notes": "Bb Db Gb Bb", "inversion": "2nd Inv"},
    ],
    "G": [
        {"frets": "0232", "fingers": "0132", "notes": "G D G B", "inversion": "2nd Inv"},
        {"frets": "4232", "fingers": "4132", "notes": "B D G B", "inversion": "2nd Inv"},
    ],
    "Ab": [
        {"frets": "5343", "fingers": "4132", "notes": "C Eb Ab C", "inversion": "2nd Inv", "starting_fret": 3},
        {"frets": "1343", "fingers": "1243", "notes": "Ab Eb Ab C", "inversion": "2nd Inv"},
    ],
    "A": [
        {"frets": "2100", "fingers": "2100", "notes": "A C# E A", "inversion": "1st Inv"},
    ],
    "Bb": [
        {"frets": "3211", "fingers": "3211", "notes": "Bb D F Bb", "inversion": "1st Inv"},
    ],
    "B": [
        {"frets": "4322", "fingers": "4211", "notes": "B D# F# B", "inversion": "1st Inv"},
    ],

    # =========================================================================
    # MINOR CHORDS
    # =========================================================================
    "Cm": [
        {"frets": "0333", "fingers": "0111", "notes": "G Eb G C", "inversion": "1st Inv"},
        {"frets": "0333", "fingers": "0234", "notes": "G Eb G C", "inversion": "1st Inv"},
    ],
    "C#m": [
        {"frets": "1444", "fingers": "1222", "notes": "G# E G# C#", "inversion": "1st Inv"},
    ],
    "Dm": [
        {"frets": "2210", "fingers": "2310", "notes": "A D F A", "inversion": "Root"},
    ],
    "Ebm": [
        {"frets": "3321", "fingers": "3421", "notes": "Bb Eb Gb Bb", "inversion": "Root"},
    ],
    "Em": [
        {"frets": "0432", "fingers": "0321", "notes": "G E G B", "inversion": "Root"},
        {"frets": "4432", "fingers": "3421", "notes": "B E G B", "inversion": "Root"},
    ],
    "Fm": [
        {"frets": "1013", "fingers": "1024", "notes": "Ab C F C", "inversion": "2nd Inv"},
    ],
    "F#m": [
        {"frets": "2120", "fingers": "2130", "notes": "A C# F# A", "inversion": "2nd Inv"},
    ],
    "Gm": [
        {"frets": "0231", "fingers": "0231", "notes": "G D G Bb", "inversion": "2nd Inv"},
    ],
    "Abm": [
        {"frets": "1342", "fingers": "1342", "notes": "Ab Eb Ab B", "inversion": "2nd Inv"},
    ],
    "Am": [
        {"frets": "2000", "fingers": "1000", "notes": "A C E A", "inversion": "1st Inv"},
        {"frets": "2003", "fingers": "2004", "notes": "A C E C", "inversion": "1st Inv"},
    ],
    "Bbm": [
        {"frets": "3111", "fingers": "3111", "notes": "Bb Db F Bb", "inversion": "1st Inv"},
    ],
    "Bm": [
        {"frets": "4222", "fingers": "4111", "notes": "B D F# B", "inversion": "1st Inv"},
    ],

    # =========================================================================
    # DOMINANT 7TH CHORDS
    # =========================================================================
    "C7": [
        {"frets": "0001", "fingers": "0001", "notes": "G C E Bb", "inversion": "Root"},
        {"frets": "0303", "fingers": "0102", "notes": "G Eb E C", "inversion": ""},
    ],
    "D7": [
        {"frets": "2223", "fingers": "1112", "notes": "A D F# C", "inversion": "Root"},
        {"frets": "2020", "fingers": "1020", "notes": "A C F# A", "inversion": "3rd Inv"},
    ],
    "E7": [
        {"frets": "1202", "fingers": "1302", "notes": "G# D E B", "inversion": "3rd Inv"},
    ],
    "F7": [
        {"frets": "2313", "fingers": "2314", "notes": "A Eb F C", "inversion": "3rd Inv"},
    ],
    "G7": [
        {"frets": "0212", "fingers": "0213", "notes": "G D F B", "inversion": "2nd Inv"},
    ],
    "A7": [
        {"frets": "0100", "fingers": "0100", "notes": "G C# E A", "inversion": "1st Inv"},
    ],
    "B7": [
        {"frets": "2322", "fingers": "1211", "notes": "A D# F# B", "inversion": "1st Inv"},
    ],
    "Bb7": [
        {"frets": "1211", "fingers": "1211", "notes": "Ab D F Bb", "inversion": "1st Inv"},
    ],
    "Eb7": [
        {"frets": "3334", "fingers": "1112", "notes": "Bb Eb G Db", "inversion": "Root"},
    ],
    "Ab7": [
        {"frets": "1323", "fingers": "1324", "notes": "Ab Eb Gb C", "inversion": "2nd Inv"},
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
        {"frets": "1302", "fingers": "1302", "notes": "G# D# E B", "inversion": "3rd Inv"},
    ],
    "Fmaj7": [
        {"frets": "2410", "fingers": "1300", "notes": "A E F A", "inversion": "3rd Inv"},
    ],
    "Gmaj7": [
        {"frets": "0222", "fingers": "0111", "notes": "G D F# B", "inversion": "2nd Inv"},
    ],
    "Amaj7": [
        {"frets": "1100", "fingers": "1200", "notes": "G# C# E A", "inversion": "1st Inv"},
    ],
    "Bbmaj7": [
        {"frets": "3210", "fingers": "3210", "notes": "Bb D F A", "inversion": "1st Inv"},
    ],
    "Bmaj7": [
        {"frets": "4321", "fingers": "4321", "notes": "B D# F# A#", "inversion": "1st Inv"},
    ],

    # =========================================================================
    # MINOR 7TH CHORDS
    # =========================================================================
    "Cm7": [
        {"frets": "3333", "fingers": "1111", "notes": "Bb Eb G C", "inversion": "1st Inv", "starting_fret": 3},
    ],
    "Dm7": [
        {"frets": "2213", "fingers": "2213", "notes": "A D F C", "inversion": "Root"},
    ],
    "Em7": [
        {"frets": "0202", "fingers": "0102", "notes": "G D E B", "inversion": "3rd Inv"},
    ],
    "Fm7": [
        {"frets": "1313", "fingers": "1324", "notes": "Ab Eb F C", "inversion": "3rd Inv"},
    ],
    "Gm7": [
        {"frets": "0211", "fingers": "0211", "notes": "G D F Bb", "inversion": "2nd Inv"},
    ],
    "Am7": [
        {"frets": "0000", "fingers": "0000", "notes": "G C E A", "inversion": "1st Inv"},
        {"frets": "0030", "fingers": "0020", "notes": "G C G A", "inversion": "1st Inv"},
    ],
    "Bm7": [
        {"frets": "2222", "fingers": "1111", "notes": "A D F# B", "inversion": "1st Inv"},
    ],
    "Bbm7": [
        {"frets": "1111", "fingers": "1111", "notes": "Ab Db F Bb", "inversion": "1st Inv"},
    ],

    # =========================================================================
    # DIMINISHED CHORDS
    # =========================================================================
    "Cdim": [
        {"frets": "0332", "fingers": "0231", "notes": "G Eb G B", "inversion": "1st Inv"},
    ],
    "Ddim": [
        {"frets": "1210", "fingers": "1320", "notes": "G# D F A", "inversion": "Root"},
    ],
    "Edim": [
        {"frets": "0101", "fingers": "0102", "notes": "G C# E Bb", "inversion": ""},
    ],
    "Fdim": [
        {"frets": "1212", "fingers": "1324", "notes": "Ab D F B", "inversion": ""},
    ],
    "Gdim": [
        {"frets": "0131", "fingers": "0132", "notes": "G Db G Bb", "inversion": "2nd Inv"},
    ],
    "Adim": [
        {"frets": "2320", "fingers": "1320", "notes": "A Eb Gb A", "inversion": "2nd Inv"},
    ],
    "Bdim": [
        {"frets": "1202", "fingers": "1203", "notes": "Ab D E B", "inversion": "1st Inv"},
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
        {"frets": "1003", "fingers": "1003", "notes": "G# C E C", "inversion": "2nd Inv"},
    ],
    "Faug": [
        {"frets": "2110", "fingers": "2110", "notes": "A C# F A", "inversion": "2nd Inv"},
    ],
    "Gaug": [
        {"frets": "0332", "fingers": "0221", "notes": "G Eb G B", "inversion": "2nd Inv"},
    ],
    "Aaug": [
        {"frets": "2110", "fingers": "3210", "notes": "A C# F A", "inversion": "1st Inv"},
    ],
    "Bbaug": [
        {"frets": "3221", "fingers": "3221", "notes": "Bb D F# Bb", "inversion": "1st Inv"},
    ],

    # =========================================================================
    # SUSPENDED 2ND CHORDS
    # =========================================================================
    "Csus2": [
        {"frets": "0233", "fingers": "0123", "notes": "G D G C", "inversion": "1st Inv"},
    ],
    "Dsus2": [
        {"frets": "2200", "fingers": "1200", "notes": "A D E A", "inversion": "Root"},
    ],
    "Esus2": [
        {"frets": "4420", "fingers": "2310", "notes": "B E F# A", "inversion": "Root"},
    ],
    "Fsus2": [
        {"frets": "0013", "fingers": "0012", "notes": "G C F C", "inversion": "2nd Inv"},
    ],
    "Gsus2": [
        {"frets": "0230", "fingers": "0120", "notes": "G D G A", "inversion": "2nd Inv"},
    ],
    "Asus2": [
        {"frets": "2400", "fingers": "1300", "notes": "A E E A", "inversion": "2nd Inv"},
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
        {"frets": "2442", "fingers": "1331", "notes": "A E G# B", "inversion": "Root"},
    ],
    "Fsus4": [
        {"frets": "3011", "fingers": "3011", "notes": "Bb C F Bb", "inversion": "2nd Inv"},
    ],
    "Gsus4": [
        {"frets": "0233", "fingers": "0123", "notes": "G D G C", "inversion": "2nd Inv"},
    ],
    "Asus4": [
        {"frets": "2200", "fingers": "1200", "notes": "A D E A", "inversion": "1st Inv"},
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
