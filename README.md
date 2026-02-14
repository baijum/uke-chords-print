# Uke Chords Print

**Generate printable PDF chord diagrams for ukulele** -- perfect for keeping on a music stand while practicing.

Chords are generated algorithmically from music theory using [pychord](https://github.com/yuma-m/pychord), so any chord name works out of the box -- 108 standard chords with 3 voicings each, ranked by a research-backed playability score.

---

## Features

- **Any chord, instantly** -- type a chord name and get a diagram. No static database to maintain.
- **Multiple tunings** -- supports standard (high-G), low-G, baritone, and D-tuning ukuleles.
- **Smart voicing selection** -- voicings are ranked by a 7-factor difficulty score based on the [ISMIR 2023 playability rubric](https://ismir2023program.ismir.net/poster_225.html) and the Radicioni biomechanical model.
- **Print-ready PDFs** -- clean black-and-white diagrams sized for A4 or US Letter, readable from a music stand.
- **Catalog included** -- ready-made chord sheets for popular progressions, hit songs, classical pieces, and world music.
- **Flexible input** -- pass chord names on the command line, use explicit voicing notation, or load from text files.
- **Customizable layout** -- adjust columns, rows, paper size, and titles.

## Quick Start

```bash
git clone https://github.com/<your-username>/uke-chords-print.git
cd uke-chords-print
pip install -r requirements.txt

# Generate a PDF with common beginner chords
python3 -m uke_chords_print C Am G7 F -t "Beginner Chords"
# -> chords.pdf (16 chord diagrams per A4 page)
```

## Usage

```
python3 -m uke_chords_print [CHORDS...] [OPTIONS]
```

| Option | Default | Description |
|--------|---------|-------------|
| `CHORDS` | | One or more chord names or `name:voicing` pairs |
| `--file`, `-f` | | Read chords from a text file |
| `--output`, `-o` | `chords.pdf` | Output PDF file path |
| `--title`, `-t` | *(none)* | Title printed at the top of the first page |
| `--paper` | `a4` | Paper size: `a4` or `letter` |
| `--cols` | `4` | Columns per page |
| `--rows` | `4` | Rows per page |
| `--single` | | Show only the primary (easiest) voicing per chord |
| `--show-root` | | Show 'Root' inversion label (hidden by default) |
| `--no-fingers` | | Hide finger numbers inside the fret dots |
| `--tuning` | `standard` | Ukulele tuning: `standard`, `low-g`, or `baritone` |
| `--list` | | List all 108 standard chords and exit |

### Examples

```bash
# All C chord voicings
python3 -m uke_chords_print C Cm C7 Cmaj7 Cm7 Cdim Caug Csus2 Csus4 \
  -t "C Family" -o c_chords.pdf

# Beginner essentials on US Letter paper
python3 -m uke_chords_print C Am F G G7 D Em A7 \
  --paper letter -t "Starter Chords"

# From a text file with custom layout
python3 -m uke_chords_print --file catalog/popular_chords.txt \
  --cols 3 --rows 3 -t "Popular Chords"

# Mix database lookup and explicit voicings
python3 -m uke_chords_print Am G7 "F:2010:fingers=2_1_" -o mixed.pdf

# Baritone ukulele (D-G-B-E tuning)
python3 -m uke_chords_print --tuning baritone C Am G7 F -o baritone.pdf

# Low-G ukulele (linear tuning)
python3 -m uke_chords_print --tuning low-g C Am G7 F
```

## Input Methods

### 1. Chord names

```bash
python3 -m uke_chords_print C Am G7 F
```

### 2. Explicit voicing notation

```bash
python3 -m uke_chords_print "C:0003" "F:2010:fingers=2_1_"
```

### 3. Text files

```bash
python3 -m uke_chords_print --file my_chords.txt -t "Practice Sheet"
```

**File format:**

```text
# Comments start with #

= Key of C                    # Section heading
C                              # Chord name -> best voicings from generator
Am
F, 2010, fingers=2010          # Explicit voicing with fingering
G

---                            # Page break

= Key of G
G
D
Em
```

| Field | Required | Example | Description |
|-------|----------|---------|-------------|
| Chord name | Yes | `C`, `Am7` | Name shown above the diagram |
| Frets | No | `0003` | 4-digit string (G-C-E-A fret numbers) |
| `fingers=` | No | `fingers=0003` | Finger to use (1-4, `0` = open) |
| `notes=` | No | `notes=G C E C` | Note names shown below the fretboard |
| `starting_fret=` | No | `starting_fret=5` | First fret shown on diagram |
| `inversion=` | No | `inversion=Root` | Inversion label |

See [`example_chords.txt`](example_chords.txt) for a complete sample.

## Chord Database

The voicing generator supports **108 standard chords** (12 roots x 9 qualities), each with up to 3 voicings ranked by playability:

| Type | Example | All 12 roots |
|------|---------|--------------|
| **Major** | C, D, G | C C# D Eb E F F# G Ab A Bb B |
| **Minor** | Am, Dm, Em | Cm C#m Dm Ebm Em Fm F#m Gm Abm Am Bbm Bm |
| **Dominant 7th** | G7, C7 | C7 C#7 D7 Eb7 E7 F7 F#7 G7 Ab7 A7 Bb7 B7 |
| **Major 7th** | Cmaj7 | Cmaj7 ... Bmaj7 |
| **Minor 7th** | Am7, Dm7 | Cm7 ... Bm7 |
| **Diminished** | Cdim | Cdim ... Bdim |
| **Augmented** | Caug | Caug ... Baug |
| **Suspended 2nd** | Dsus2 | Csus2 ... Bsus2 |
| **Suspended 4th** | Gsus4 | Csus4 ... Bsus4 |

Enharmonic aliases are supported: `Db` = `C#`, `Gb` = `F#`, `Ab` = `G#`, `Bb` = `A#`, etc.

```bash
python3 -m uke_chords_print --list   # See all chords with voicings
```

## Difficulty Scoring

Every voicing is scored for playability using 7 factors derived from the [ISMIR 2023 playability rubric](https://ismir2023program.ismir.net/poster_225.html) and the [Radicioni biomechanical fingering model](https://www.di.unito.it/~radicion/papers/radicioni05guitar.pdf):

| Factor | What it measures |
|--------|-----------------|
| Fret span | Distance between lowest and highest fretted note |
| Barre complexity | Sustained pressure across consecutive strings |
| Finger count | Number of fretted strings |
| Fret position | Higher frets = tighter spacing |
| Open strings | More open strings = easier |
| Finger independence | Large gaps between non-barre fingers |
| Compact shape | Clustered frets are familiar and easier |

Each voicing gets a label: **easy**, **moderate**, **hard**, or **very hard**. The generator returns voicings sorted easiest-first, so the primary voicing (`--single`) is always the most accessible.

## Chord Diagram

Each diagram on the PDF includes:

- **Chord name** in bold at the top
- **Fretboard grid** with 4 strings and 4 frets
- **Nut** (thick top line) for open position, or **fret indicator** for higher positions
- **Filled dots** with **fingering numbers** inside
- **Open circles** for open strings, **X marks** for muted strings
- **Note names** below the fretboard
- **Fret numbers** and **inversion label** at the bottom
- **Tuning indicator** for non-standard tunings (e.g., D-G-B-E for baritone)

## Chord Sheet Catalog

A ready-to-use collection of chord sheets lives in [`catalog/`](catalog/):

| Category | Files |
|----------|-------|
| **Reference** | [Popular chords](catalog/popular_chords.txt) ([PDF](https://github.com/baijum/uke-chords-print/releases/download/v0.3.0/popular_chords.pdf)), [All 108 chords](catalog/all_chords.txt) ([PDF](https://github.com/baijum/uke-chords-print/releases/download/v0.3.0/all_chords.pdf)), [Challenging chords](catalog/challenging_chords.txt) ([PDF](https://github.com/baijum/uke-chords-print/releases/download/v0.3.0/challenging_chords.pdf)) |
| **Progressions** | [Pop anthems](catalog/progressions/pop_anthems.txt), [12-bar blues](catalog/progressions/12_bar_blues.txt), [Jazz essentials](catalog/progressions/jazz_essentials.txt), [Classic rock](catalog/progressions/classic_rock.txt), [50s doo-wop](catalog/progressions/50s_doo_wop.txt) |
| **Songs** | [Beginner hits](catalog/songs/beginner_hits.txt), [Pop classics](catalog/songs/pop_classics.txt), [Campfire songs](catalog/songs/campfire_songs.txt) |
| **Classical** | [Ode to Joy, Pachelbel Canon, Amazing Grace, Greensleeves...](catalog/classical/classical_pieces.txt) |
| **World Music** | [Latin/Bossa Nova](catalog/world/latin_bossa.txt), [Hawaiian/Reggae](catalog/world/island_hawaiian.txt), [Folk traditions](catalog/world/folk_traditions.txt) |

```bash
python3 -m uke_chords_print --file catalog/songs/beginner_hits.txt \
  --single -t "Beginner Hits"
```

See the full list in the [Catalog README](catalog/README.md).

## Tunings

Four ukulele tunings are supported:

| Tuning | Aliases | Notes | Description |
|--------|---------|-------|-------------|
| `standard` | `gcea`, `high-g` | G4-C4-E4-A4 | Re-entrant high-G (default) |
| `low-g` | `gcea-low`, `linear` | G3-C4-E4-A4 | Linear low-G |
| `baritone` | `dgbe` | D3-G3-B3-E4 | Baritone ukulele |
| `d-tuning` | `adf#b` | A4-D4-F#4-B4 | Standard raised a whole step |

```bash
# Standard tuning (default)
python3 -m uke_chords_print C Am G7 F

# Low-G tuning
python3 -m uke_chords_print --tuning low-g C Am G7 F

# Baritone tuning (same chord shapes as guitar)
python3 -m uke_chords_print --tuning baritone C Am G7 F -o baritone.pdf

# List chords for baritone
python3 -m uke_chords_print --list --tuning baritone
```

For non-standard tunings, the string names are shown on each diagram (e.g., `D-G-B-E` for baritone).

## Voicing Notation

Voicings use a **4-character string** representing each string from left to right:

| Character | Meaning |
|-----------|---------|
| `0` | Open string |
| `1`-`9` | Fret number |
| `X` | Muted string |

**Standard tuning (G-C-E-A):**

| Voicing | Chord | Strings |
|---------|-------|---------|
| `0003` | C | G open, C open, E open, A at 3rd fret |
| `2010` | F | G at 2nd, C open, E at 1st, A open |
| `0232` | G | G open, C at 2nd, E at 3rd, A at 2nd |
| `2000` | Am | G at 2nd, C open, E open, A open |

**Baritone tuning (D-G-B-E):**

| Voicing | Chord | Strings |
|---------|-------|---------|
| `2010` | C | D at 2nd, G open, B at 1st, E open |
| `2220` | A | D at 2nd, G at 2nd, B at 2nd, E open |
| `0232` | D | D open, G at 2nd, B at 3rd, E at 2nd |

## Requirements

- Python 3.9+
- [ReportLab](https://pypi.org/project/reportlab/) -- PDF generation
- [pychord](https://pypi.org/project/pychord/) -- music theory (chord-to-notes resolution)

## Project Structure

```
uke-chords-print/
  uke_chords_print/
    __init__.py          # Package metadata
    __main__.py          # python -m entry point
    cli.py               # Argument parsing and CLI logic
    chord_db.py          # Chord lookup (wraps voicing generator)
    voicing_gen.py       # Algorithmic voicing generator + difficulty scoring
    tunings.py           # Tuning definitions (standard, low-g, baritone, d-tuning)
    parser.py            # Input parsing (CLI args + text files)
    diagram.py           # Chord diagram renderer (ReportLab)
    pdf_generator.py     # Page layout and PDF output
  catalog/               # Pre-made chord sheet files
    progressions/        # Named chord progressions
    songs/               # Hit songs by difficulty
    classical/           # Classical music
    world/               # World music and folk traditions
  example_chords.txt     # Sample input file
  requirements.txt       # Python dependencies
```

## How the Voicing Generator Works

The generator uses [pychord](https://github.com/yuma-m/pychord) for music theory and a fretboard search for playable shapes:

1. **Resolve notes** -- `pychord.Chord("Am7").components()` returns `['A', 'C', 'E', 'G']`
2. **Search fretboard** -- iterate valid fret combinations on all 4 strings (frets 0-9)
3. **Filter** -- all notes must be chord tones, all chord tones must be present, fret span <= 3
4. **Score** -- rank by 7-factor difficulty heuristic
5. **Return** -- top 3 voicings, easiest first

## License

MIT
