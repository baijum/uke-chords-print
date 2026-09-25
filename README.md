# Uke Chords Print

**Generate printable PDF chord diagrams for ukulele** -- perfect for keeping on a music stand while practicing.

Chords are generated algorithmically from music theory using [pychord](https://github.com/yuma-m/pychord), so any chord name works out of the box -- 108 standard chords with up to 3 voicings each, ranked by a research-backed playability score.

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

Just want printable sheets? Download ready-made PDFs from the [v0.5.0 release](https://github.com/baijum/uke-chords-print/releases/tag/v0.5.0) (see [Chord Sheet Catalog](#chord-sheet-catalog)).

To make your own (Python 3.11+):

```bash
git clone https://github.com/baijum/uke-chords-print.git
cd uke-chords-print
pip install -r requirements.txt

# Generate a PDF with common beginner chords
python3 -m uke_chords_print C Am G7 F -t "Beginner Chords"
# -> chords.pdf: up to 3 voicings of each chord, 16 diagrams per A4 page
```

## Usage

```
python3 -m uke_chords_print [CHORDS...] [OPTIONS]
```

| Option | Default | Description |
|--------|---------|-------------|
| `CHORDS` | | Chord names (`Am7`) or explicit voicings (`name:frets[:option=value...]`, see below) |
| `--file`, `-f` | | Read chords from a text file (repeat to combine files) |
| `--output`, `-o` | `chords.pdf` | Output PDF file path |
| `--title`, `-t` | *(none)* | Title printed at the top of the first page |
| `--paper` | `a4` | Paper size: `a4` or `letter` |
| `--cols` | `4` | Columns per page |
| `--rows` | `4` | Rows per page |
| `--single` | | Show only the primary (easiest) voicing per chord |
| `--show-root` | | Show 'Root' inversion label (hidden by default) |
| `--no-fingers` | | Hide finger numbers inside the fret dots |
| `--tuning` | `standard` | Ukulele tuning: `standard`, `low-g`, `baritone`, or `d-tuning` (any case) |
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

# Mix generated and explicit voicings
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

Options after the frets are separated by `:` and are the same as in text files (`fingers=`, `starting_fret=`, `notes=`, `inversion=`).

### 3. Text files

```bash
python3 -m uke_chords_print --file my_chords.txt -t "Practice Sheet"
```

**File format:**

```text
# Comments start with #
@tuning standard               # Explicit voicings below are for this tuning

= Key of C                    # Section heading (space after = optional)
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
| Frets | No | `0003` | 4-character string, one fret per string in tuning order |
| `fingers=` | No | `fingers=0003` | Finger per string: 4 characters, `1`-`4`, or `0`/`_` for none (open and muted strings can't have a finger) |
| `notes=` | No | `notes=G C E C` | Note names shown below the fretboard, one per string (`-` for a muted string); worked out from the chord name when omitted, with notes outside the chord in flats for flat keys, else sharps |
| `starting_fret=` | No | `starting_fret=5` | First fret shown on diagram (derived from the frets when omitted; the shape must fit the 4 frets shown) |
| `inversion=` | No | `inversion=Root` | Inversion label (worked out from the chord name when omitted) |

Explicit fret shapes only make sense in the tuning they were written for. The optional `@tuning <name>` line says which tuning that is for the explicit voicings after it (the bundled catalog files declare `@tuning standard`). When you print with a different `--tuning`:

- **Baritone or D tuning** (different shapes): each explicit line is replaced by the easiest generated voicing for its chord name. Different pinned shapes of one chord get different replacements, so two E shapes don't print the same diagram, while a shape repeated through a song always gets the same one.
- **Standard ↔ low-G** (same shapes): explicit lines are kept; only a pinned `inversion=` is worked out again, since low-G's lowest note is the G string.
- **Lines that can't be replaced print as written**: all-muted shapes like `N.C., XXXX` silently, and names that aren't chords (`My riff, 0003`) or chords with no playable voicing in that tuning with a warning naming the line.

Without `@tuning`, explicit voicings are always used as written.

Inline comments start with whitespace, then `#`, then whitespace (as in the example above). This keeps sharps like `C#` and heading text like `= Track #1` intact.

Mistakes stop with an error naming the line: an unknown option, a `fingers=` that isn't 4 characters or puts a finger on an open or muted string, a `notes=` without one name per string, a `starting_fret=` below 1, a shape that doesn't fit the 4 frets shown, or an empty heading. A file with no chords (only headings, say) is an error too. Files are read as UTF-8 (a byte-order mark, as Windows Notepad adds, is fine). Long titles and headings shrink to fit the page.

Titles, headings, chord names, notes, and inversion labels can use any script: characters outside basic Latin (e.g. `♪ ♭`, Greek, Cyrillic, Chinese, Japanese, Korean) are drawn with fonts bundled in [`uke_chords_print/bundled_fonts/`](uke_chords_print/bundled_fonts/), so sheets look the same on every machine. Other characters (e.g. most emoji) use an installed system font if one has them; otherwise they print as boxes and the CLI prints a warning. Right-to-left scripts are not shaped.

See [`example_chords.txt`](example_chords.txt) for a complete sample.

## Supported Chords

There's no fixed chord list: voicings are generated from the chord's notes. `--list` shows the **108 standard chords** (12 roots x 9 qualities), each with up to 3 voicings ranked by playability:

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

Other chords pychord understands work too. Chords with more than four notes (9ths, 11ths, 13ths, `6/9`) drop the 5th first, then the natural 9th/11th, then the root, since a ukulele has only four strings -- e.g. `C9` is voiced as C-E-Bb-D and `C13` as C-E-Bb-A. Altered tones that name the chord are kept over the root: `C9b5` is E-Gb-Bb-D, not a plain C9. Slash chords like `C/G` put the named bass note lowest when a playable shape allows it. Added-tone spellings `6/9`, `7/9`, `maj7/9` and `7/13` are read as `69`, `9`, `maj9` and `13`; other numbers after `/` are rejected rather than guessed.

Common chord-chart spellings work too: `C+` (aug), `C°` / `Co` (dim), `C°7`, `Cø` (m7b5), `CΔ` / `CΔ7` (maj7), `CΔ9`, `Cma7`, `Cm/maj7` / `Cm(maj7)` / `CmΔ7` (minor-major 7th), `Cmin7` / `Cmi7` / `C-7`, `C7(#9)`, `C+7` / `Caug7` (7#5), `C+9` / `Caug9` (9#5), `Cmaj7#5`, `Cmaj7b5`, `Cm9b5`, `Cmaj11`, `Cm(maj9)` / `CmM9`, `CmM7b5`, `CmM11`, `C7#9b13`, `C13b5b9`, `C7sus` (7sus4), `Cmi`, `Cadd2` (add9), and `♭` / `♯` accidentals (`B♭m7`). The diagram shows the name as you typed it. Note names are capital letters (`Am`, `C/G`); a lowercase one gets a suggestion instead of a guess.

Sharp and flat spellings of the same root both work (`Db` / `C#`, `Gb` / `F#`, ...).

```bash
python3 -m uke_chords_print --list   # See all chords with voicings
```

## Difficulty Scoring

Every voicing is scored for playability using 7 factors derived from the [ISMIR 2023 playability rubric](https://ismir2023program.ismir.net/poster_225.html) and the [Radicioni biomechanical fingering model](https://www.di.unito.it/~radicion/papers/radicioni05guitar.pdf):

| Factor | What it measures |
|--------|-----------------|
| Fret span | Distance between lowest and highest fretted note |
| Barre complexity | Sustained pressure across consecutive strings |
| Finger count | Number of fretted strings, and fingers needed (a barre counts once, but can't cross an open string) |
| Fret position | Higher frets = tighter spacing; leaving first position (above fret 4) costs extra |
| Open strings | Easier in first position; harder with the hand up the neck, or when a finger must arch over one (Em `0402`) |
| Finger independence | Large gaps between non-barre fingers |
| Compact shape | Clustered frets are familiar and easier |

The weights are calibrated against [chords-db](https://github.com/tombatossals/chords-db): for 163 of 180 common chords, the easiest voicing is the shape chord charts show first (C `0003`, Em `0432`, Fmaj7 `2413`, Cm7 `3333`, ...).

Voicings are printed easiest first, so the primary voicing (`--single`) is always the most accessible. Internally each score also maps to **easy**, **moderate**, **hard** or **very hard**; those tiers were used to build the [Challenging chords](catalog/challenging_chords.txt) sheet and aren't printed on diagrams.

## Chord Diagram

Each diagram on the PDF includes:

- **Chord name** in bold at the top
- **Fretboard grid** with 4 strings and 4 frets
- **Nut** (thick top line) for open position, or a **fret indicator** (`5fr`) for higher positions
- **Filled dots** with **finger numbers** inside (`--no-fingers` hides them)
- **Open circles** for open strings, **X marks** for muted strings
- **Note names** below each string
- **Fret string** (`0 - 0 - 0 - 3`) and **inversion label** at the bottom (`Root` only with `--show-root`)
- **String names** for every tuning except standard (e.g. `D-G-B-E` for baritone, `G-C-E-A` for low-G, so low-G sheets can be told apart)

## Chord Sheet Catalog

A ready-to-use collection of chord sheets lives in [`catalog/`](catalog/):

| Category | Files |
|----------|-------|
| **Reference** | [Popular chords](catalog/popular_chords.txt) ([PDF](https://github.com/baijum/uke-chords-print/releases/download/v0.5.0/popular_chords.pdf)), [All 108 chords](catalog/all_chords.txt) ([PDF](https://github.com/baijum/uke-chords-print/releases/download/v0.5.0/all_chords.pdf)), [Challenging chords](catalog/challenging_chords.txt) ([PDF](https://github.com/baijum/uke-chords-print/releases/download/v0.5.0/challenging_chords.pdf)) |
| **Progressions** | [Pop anthems](catalog/progressions/pop_anthems.txt) ([PDF](https://github.com/baijum/uke-chords-print/releases/download/v0.5.0/pop_anthems.pdf)), [12-bar blues](catalog/progressions/12_bar_blues.txt) ([PDF](https://github.com/baijum/uke-chords-print/releases/download/v0.5.0/12_bar_blues.pdf)), [Jazz essentials](catalog/progressions/jazz_essentials.txt) ([PDF](https://github.com/baijum/uke-chords-print/releases/download/v0.5.0/jazz_essentials.pdf)), [Classic rock](catalog/progressions/classic_rock.txt) ([PDF](https://github.com/baijum/uke-chords-print/releases/download/v0.5.0/classic_rock.pdf)), [50s doo-wop](catalog/progressions/50s_doo_wop.txt) ([PDF](https://github.com/baijum/uke-chords-print/releases/download/v0.5.0/50s_doo_wop.pdf)) |
| **Songs** | [Beginner hits](catalog/songs/beginner_hits.txt) ([PDF](https://github.com/baijum/uke-chords-print/releases/download/v0.5.0/beginner_hits.pdf)), [Pop classics](catalog/songs/pop_classics.txt) ([PDF](https://github.com/baijum/uke-chords-print/releases/download/v0.5.0/pop_classics.pdf)), [Campfire songs](catalog/songs/campfire_songs.txt) ([PDF](https://github.com/baijum/uke-chords-print/releases/download/v0.5.0/campfire_songs.pdf)) |
| **Classical** | [Ode to Joy, Pachelbel Canon, Amazing Grace, Greensleeves...](catalog/classical/classical_pieces.txt) ([PDF](https://github.com/baijum/uke-chords-print/releases/download/v0.5.0/classical_pieces.pdf)) |
| **World Music** | [Latin/Bossa Nova](catalog/world/latin_bossa.txt) ([PDF](https://github.com/baijum/uke-chords-print/releases/download/v0.5.0/latin_bossa.pdf)), [Hawaiian/Reggae](catalog/world/island_hawaiian.txt) ([PDF](https://github.com/baijum/uke-chords-print/releases/download/v0.5.0/island_hawaiian.pdf)), [Folk traditions](catalog/world/folk_traditions.txt) ([PDF](https://github.com/baijum/uke-chords-print/releases/download/v0.5.0/folk_traditions.pdf)) |

```bash
python3 -m uke_chords_print --file catalog/songs/beginner_hits.txt \
  --single -t "Beginner Hits"
```

The PDFs are standard tuning with one voicing per chord; build any sheet yourself for another tuning or layout (add `--tuning baritone`, drop `--single`, ...). See the [Catalog README](catalog/README.md) for what each sheet contains.

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

For every tuning except standard, the string names are shown on each diagram (e.g. `D-G-B-E` for baritone).

## Voicing Notation

Voicings use a **4-character string** representing each string from left to right:

| Character | Meaning |
|-----------|---------|
| `0` | Open string |
| `1`-`9` | Fret number |
| `X` or `x` | Muted string |

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

- Python 3.11+
- [ReportLab](https://pypi.org/project/reportlab/) -- PDF generation
- [pychord](https://pypi.org/project/pychord/) 1.4+ -- music theory (chord-to-notes resolution)

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
    fonts.py             # Fallback fonts for non-Latin text
    bundled_fonts/       # DejaVu Sans, Droid Sans Fallback, Baekmuk (with licenses)
  catalog/               # Pre-made chord sheets (popular, all, challenging chords)
    progressions/        # Named chord progressions
    songs/               # Hit songs by difficulty
    classical/           # Classical music
    world/               # World music and folk traditions
  tests/                 # pytest suite
    data/chords-db/      # Reference chord shapes (chords-db, MIT)
  example_chords.txt     # Sample input file
  generate_catalog.sh    # Build every catalog PDF into catalog/pdf/
  requirements.txt       # Python dependencies
  requirements-dev.txt   # + pytest, pytest-cov
  AGENTS.md              # Notes for contributors and coding agents
```

## How the Voicing Generator Works

The generator uses [pychord](https://github.com/yuma-m/pychord) for music theory and a fretboard search for playable shapes:

1. **Resolve notes** -- `pychord.Chord("Am7").components()` returns `['A', 'C', 'E', 'G']` (chart spellings like `C°` are respelled first)
2. **Search fretboard** -- iterate valid fret combinations on all 4 strings (frets 0-9)
3. **Filter** -- all notes must be chord tones, all required chord tones must be present (chords with 5+ notes omit the 5th, then natural extensions, then the root), fret span <= 3; slash chords keep shapes with the named bass lowest when any exist
4. **Finger** -- assign fingers the way chord charts do (one finger per fret from the index, index barres)
5. **Score** -- rank by the difficulty score above
6. **Return** -- top 3 voicings, easiest first

## Development

```bash
pip install -r requirements-dev.txt
python3 -m pytest          # ~10 s
python3 -m pytest --cov    # with line and branch coverage (must stay at 100%)
./generate_catalog.sh      # rebuild every catalog PDF into catalog/pdf/
```

See [AGENTS.md](AGENTS.md) for the architecture, conventions, and gotchas.

The suite (about 10,000 tests) checks the generator against two independent references:

- **Interval formulas** for 46 chord types, written out by hand in `tests/support.py`
- **[chords-db](https://github.com/tombatossals/chords-db)**, 2,114 hand-compiled ukulele shapes, vendored at a pinned commit in `tests/data/chords-db/` (see its README for errata found in the data)

It also covers properties of every generated voicing in all four tunings, parsing, PDF layout, font fallback, the CLI, and the catalog files. Known gaps are marked `xfail`; they pass once fixed and then fail, which is a reminder to remove the marker.

[GitHub Actions](.github/workflows/tests.yml) runs the suite with coverage on Python 3.11–3.14 for every push and pull request (failing below 100% line and branch coverage, see `.coveragerc`), and builds every catalog PDF (downloadable from the run as the `catalog-pdfs` artifact).

## License

[MIT](LICENSE). The bundled fonts have their own licenses, listed in [`uke_chords_print/bundled_fonts/`](uke_chords_print/bundled_fonts/README.md).
