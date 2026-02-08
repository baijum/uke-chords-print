# Uke Chords Print

A Python CLI tool that generates **printable PDF pages** of ukulele chord diagrams. Perfect for beginners who want a quick-reference sheet of finger positions to keep on a music stand while practicing -- a different kind of sight reading!

Chords can be specified by name (looked up from a built-in database of 78 chords / 92 voicings) or by explicit 4-digit voicing notation.

## Requirements

- Python 3.9+
- [ReportLab](https://pypi.org/project/reportlab/) (PDF generation)

## Installation

```bash
git clone https://github.com/<your-username>/uke-chords-print.git
cd uke-chords-print
pip install -r requirements.txt
```

## Quick Start

```bash
# Generate a PDF with common beginner chords
python3 -m uke_chords_print C Am G7 F -t "Beginner Chords"

# Output: chords.pdf (16 chord diagrams per A4 page)
```

## Usage

```
python3 -m uke_chords_print [CHORDS...] [OPTIONS]
```

### Positional Arguments

| Argument | Description |
|----------|-------------|
| `CHORDS` | One or more chord names or `name:voicing` pairs |

### Options

| Option | Default | Description |
|--------|---------|-------------|
| `--file`, `-f` | | Read chords from a text file |
| `--output`, `-o` | `chords.pdf` | Output PDF file path |
| `--title`, `-t` | *(none)* | Title printed at the top of the first page |
| `--paper` | `a4` | Paper size: `a4` or `letter` |
| `--cols` | `4` | Number of columns per page |
| `--rows` | `4` | Number of rows per page |
| `--single` | | Show only the primary voicing for each chord (useful for progressions/songs) |
| `--show-root` | | Show 'Root' inversion label (hidden by default; non-root inversions always show) |
| `--list` | | List all chords in the built-in database and exit |
| `--help`, `-h` | | Show help message and exit |

## Input Methods

There are three ways to specify which chords to print. They can be mixed freely.

### 1. Chord Names (database lookup)

Pass chord names directly as arguments. All voicings for that chord are included.

```bash
python3 -m uke_chords_print C Am G7 F
```

### 2. Explicit Voicing Notation

Use `name:frets` or `name:frets:fingers=XXXX` to specify exact finger positions.

```bash
python3 -m uke_chords_print "C:0003" "F:2010:fingers=2_1_"
```

### 3. Text File

Create a text file with one chord per line and pass it with `--file`.

```bash
python3 -m uke_chords_print --file my_chords.txt -t "Practice Sheet"
```

**File format:**

```
# Lines starting with # are comments
# Blank lines are ignored

# Chord name only -> all voicings from database
C
Am

# Chord name with explicit voicing
C, 0003
F, 2010, fingers=2_1_

# Higher position chord with starting fret
Dm7, 7988, fingers=1423, starting_fret=6

---

# A line containing only --- forces a new page in the PDF.
# Useful for separating sections (e.g., different keys).
G
D
Em
```

**Supported fields per line (comma-separated):**

| Field | Required | Example | Description |
|-------|----------|---------|-------------|
| Chord name | Yes | `C`, `Am7` | Name shown above the diagram |
| Frets | No | `0003` | 4-digit string (G-C-E-A fret numbers) |
| `fingers=` | No | `fingers=0003` | Which finger to use (1-4, `_` or `0` = open) |
| `starting_fret=` | No | `starting_fret=5` | First fret shown on diagram (for higher positions) |
| `notes=` | No | `notes=G C E C` | Note names shown below the fretboard |
| `inversion=` | No | `inversion=Root` | Inversion label (Root, 1st Inv, 2nd Inv) |

An example input file is included: [`example_chords.txt`](example_chords.txt).

## Voicing Notation

Ukulele voicings use a **4-character string** where each character represents the fret number for a string in standard tuning order (**G-C-E-A**):

| Character | Meaning |
|-----------|---------|
| `0` | Open string (unfretted) |
| `1`-`9` | Fret number to press |
| `X` | Muted string (don't play) |

**Examples:**

| Voicing | Chord | Explanation |
|---------|-------|-------------|
| `0003` | C major | G open, C open, E open, A at 3rd fret |
| `2010` | F major | G at 2nd fret, C open, E at 1st fret, A open |
| `0232` | G major | G open, C at 2nd fret, E at 3rd fret, A at 2nd fret |
| `2000` | A minor | G at 2nd fret, C open, E open, A open |

## What Each Diagram Shows

Each chord diagram on the PDF includes:

- **Chord name** in bold at the top (e.g., "C", "Am7")
- **Fretboard grid** with 4 vertical string lines (G-C-E-A) and 4 horizontal fret lines
- **Nut** (thick top line) for open-position chords, or a **fret indicator** (e.g., "5fr") for higher positions
- **Filled dots** at fretted positions with **fingering numbers** inside (white text)
- **Open circles** above the nut for open strings
- **X marks** above the nut for muted strings
- **Note names** below the fretboard (e.g., G C E C)
- **Fret numbers** in dash-separated format (e.g., 0 - 0 - 0 - 3)
- **Inversion label** at the bottom (Root, 1st Inv, etc.)

## Built-in Chord Database

The database includes **78 chords with 92 voicings** across all common types:

| Type | Count | Chords |
|------|-------|--------|
| **Major** | 14 | A, Ab, B, Bb, C, C#, D, Db, E, Eb, F, F#, G, Gb |
| **Minor** | 12 | Am, Abm, Bm, Bbm, Cm, C#m, Dm, Ebm, Em, Fm, F#m, Gm |
| **Dominant 7th** | 10 | A7, Ab7, B7, Bb7, C7, D7, E7, Eb7, F7, G7 |
| **Major 7th** | 8 | Amaj7, Bbmaj7, Bmaj7, Cmaj7, Dmaj7, Emaj7, Fmaj7, Gmaj7 |
| **Minor 7th** | 8 | Am7, Bbm7, Bm7, Cm7, Dm7, Em7, Fm7, Gm7 |
| **Diminished** | 7 | Adim, Bdim, Cdim, Ddim, Edim, Fdim, Gdim |
| **Augmented** | 7 | Aaug, Bbaug, Caug, Daug, Eaug, Faug, Gaug |
| **Suspended 2nd** | 6 | Asus2, Csus2, Dsus2, Esus2, Fsus2, Gsus2 |
| **Suspended 4th** | 6 | Asus4, Csus4, Dsus4, Esus4, Fsus4, Gsus4 |

Many chords include multiple voicings (root position + inversions).

To see the full list with fret positions:

```bash
python3 -m uke_chords_print --list
```

**Enharmonic aliases** are supported: `Db` = `C#`, `Eb` = `D#`, `Gb` = `F#`, `Ab` = `G#`, `Bb` = `A#` (and their minor variants).

## PDF Layout

- **Default grid:** 4 columns x 4 rows = 16 diagrams per page
- **Default paper:** A4 (210mm x 297mm). Use `--paper letter` for US Letter.
- **Print-friendly:** Black and white, clean lines, large text readable from a music stand
- **Multi-page:** Automatically spans multiple pages when needed, with page numbers at the bottom
- **Customizable:** Adjust grid with `--cols` and `--rows`

## Examples

```bash
# All C chord voicings (major, minor, 7th, maj7, dim, aug, sus2, sus4)
python3 -m uke_chords_print C Cm C7 Cmaj7 Cm7 Cdim Caug Csus2 Csus4 \
  -t "C Family" -o c_chords.pdf

# Beginner essentials on US Letter paper
python3 -m uke_chords_print C Am F G G7 D Em A7 \
  --paper letter -t "Starter Chords" -o starter.pdf

# From a practice file with custom layout
python3 -m uke_chords_print --file example_chords.txt \
  --cols 3 --rows 3 -t "Weekly Practice"

# Mix database lookup and explicit voicings
python3 -m uke_chords_print Am G7 "F:2010:fingers=2_1_" -o mixed.pdf
```

## Chord Sheet Catalog

A ready-to-use collection of chord sheet files is included in the [`catalog/`](catalog/) directory, organized by category:

- **Chord Progressions** -- Pop (I-V-vi-IV), 50s Doo-Wop, 12-Bar Blues, Classic Rock, Jazz
- **Hit Songs** -- Beginner hits, pop classics, campfire singalongs
- **Classical Music** -- Ode to Joy, Pachelbel Canon, Amazing Grace, Greensleeves
- **World Music** -- Latin/Bossa Nova, Hawaiian/Reggae, folk traditions from 10+ countries

```bash
python3 -m uke_chords_print --file catalog/songs/beginner_hits.txt -t "Beginner Hits"
```

See the full list in the [Catalog README](catalog/README.md).

## Project Structure

```
uke-chords-print/
  uke_chords_print/
    __init__.py          # Package metadata
    __main__.py          # python -m entry point
    cli.py               # Argument parsing and CLI logic
    chord_db.py          # Built-in chord database (78 chords)
    parser.py            # Input parsing (CLI args + text files)
    diagram.py           # Chord diagram renderer (ReportLab)
    pdf_generator.py     # Page layout and PDF output
  catalog/               # Pre-made chord sheet files (see catalog/README.md)
    progressions/        # Named chord progressions
    songs/               # Hit songs by difficulty
    classical/           # Classical music
    world/               # World music and folk traditions
  example_chords.txt     # Sample input file
  requirements.txt       # Python dependencies
  README.md
```

## License

MIT
