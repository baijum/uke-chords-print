# AGENTS.md

Guidance for AI coding agents working in this repository. User-facing docs
live in [README.md](README.md) and [catalog/README.md](catalog/README.md);
this file covers what you need to change the code safely.

## What this is

A small Python CLI that turns ukulele chord names into printable PDF chord
diagrams. Voicings are **generated algorithmically** (pychord for theory +
a brute-force fretboard search + a difficulty score). There is no static chord
database, despite the `chord_db` module name.

- Python 3.9+ (uses `from __future__ import annotations` for `list[...]` /
  `X | None` hints — keep that import in every module).
- Runtime deps: `reportlab`, `pychord` (see `requirements.txt`, unpinned).
- No `pyproject.toml`/`setup.py`: the tool is run as a module, not installed.
- No test suite, linter, formatter config, or CI.

## Commands

```bash
pip install -r requirements.txt

# Run the CLI
python3 -m uke_chords_print C Am G7 F -t "Title" -o out.pdf
python3 -m uke_chords_print --file catalog/popular_chords.txt --single
python3 -m uke_chords_print --list --tuning baritone

# Inspect generator output directly (fastest feedback loop)
python3 -c "from uke_chords_print.voicing_gen import generate_voicings as g; print(g('Am7', tuning='low-g'))"

# Regenerate every catalog PDF into catalog/pdf/ (git-ignored) — a good
# end-to-end smoke test after any change
./generate_catalog.sh
```

Write scratch PDFs outside the repo or rely on `.gitignore` (`*.pdf` is
ignored everywhere). Never commit generated PDFs.

## Architecture

Data flows in one direction:

```
cli.py ──► parser.py ──► chord_db.py ──► voicing_gen.py ──► tunings.py
   │           │ (ChordVoicing list)
   └──────────►pdf_generator.py ──► diagram.py (one ReportLab Drawing per chord)
```

| Module | Responsibility |
|--------|----------------|
| `cli.py` | argparse, collects voicings from each `--file` (repeatable, in order) then positional args, calls `generate_pdf`. |
| `parser.py` | `ChordVoicing` dataclass; parses CLI args (`name:frets:key=val`) and file lines (`name, frets, key=val`); page-break / heading sentinels. |
| `chord_db.py` | `lookup_chord()` wraps the generator and retries with enharmonic `CHORD_ALIASES`; `STANDARD_CHORDS` (12 roots × 9 qualities = 108) backs `--list`. |
| `voicing_gen.py` | Chord → pitch classes → search frets 0–9 on 4 strings → filter (required chord tones present — 5+ note chords drop the 5th, then inner extensions; span ≤ 3) → score → top 3. Also finger assignment and inversion detection. |
| `tunings.py` | `Tuning` dataclass + `TUNINGS` dict (MIDI notes per string, labels, aliases). `TUNING_CHOICES` feeds argparse. |
| `pdf_generator.py` | `_paginate` splits voicings into pages of headings and rows (max `rows` rows per page, no empty pages), then draws them. Cell height reserves room for the title and the most headings on any page, so every page fits all its rows at one diagram size. |
| `fonts.py` | Font fallback: splits text into runs; characters outside Windows-1252 (the built-in PDF fonts) use `bundled_fonts/` first, then system fonts (`fc-match` / known paths). `draw_centred` (canvas) and `centred_strings` (Drawing) render the runs; `missing_characters()` feeds the CLI warning. |
| `diagram.py` | Draws a single fretboard (nut/`Nfr` label, dots with finger numbers, open/mute markers, notes, fret string, inversion). Geometry constants in mm at the top. |

### Voicing representation

Generator output is a dict; the parser converts it into `ChordVoicing`:

- `frets`: exactly 4 chars, one per string in tuning order (left→right on the
  diagram). `0` open, `1`–`9` fret, `X` muted. Single-digit only — this is why
  the generator caps `max_fret` at 9.
- `fingers`: 4 chars, `1`–`4` fingers, `0` or `_` = no finger drawn.
- `notes`: space-separated note names in string order.
- `inversion`: `"Root"`, `"1st Inv"`, … or `""`. Determined by the lowest
  **MIDI pitch**, not the leftmost string — matters for re-entrant tunings
  (standard high-G, d-tuning).
- `starting_fret`: 1 = open position (nut drawn); >1 draws an `Nfr` label and
  offsets dots. Explicit voicings derive it via `compute_starting_fret` when
  omitted, and the parser rejects shapes that don't fit the 4 frets shown
  (the diagram would otherwise clamp dots silently).
- `difficulty` is produced by the generator but dropped by the parser; it is
  not rendered.
- Explicit voicings get `notes` / `inversion` from
  `voicing_gen.describe_voicing` (chord name + active tuning) unless given;
  a muted string's note is `-`. Unrecognized names just get no labels.

### Sentinels

`parser.PAGE_BREAK` is a singleton compared with `is`. Headings are
`ChordVoicing(name="__HEADING__", notes=<heading text>)` and checked with
`is_heading()`. Any code that iterates or counts voicings must skip both
(see the count in `cli.main`).

## Gotchas

- **Explicit voicings are tied to a tuning.** A line like
  `B7, 2322, fingers=1211, ...` is a fret shape for one tuning. Files mark
  this with an `@tuning <name>` line (the catalog uses `@tuning standard`);
  when `--tuning` has different string pitch classes
  (`tunings.shapes_compatible`), `parse_file` swaps each explicit line for the
  easiest generated voicing not already used for that chord in the file
  (`_fallback_voicing`). Without `@tuning`, explicit lines are used
  verbatim. Keep `@tuning` below the first line of catalog files —
  `generate_catalog.sh` reads line 1 as the title.
- **Fingering** (`_finger_units` / `_assign_fingers`): a finger never lies
  across an open or lower-fretted string. The displayed fingering follows
  common practice: barres across higher-fretted strings only when all four
  strings are fretted (F# `3121`, but G `0232` -> `0132`), a lone fretted
  string in open position uses the matching finger (C `0003` -> 3), else
  one finger per fret from the index on the lowest fret. The score's finger
  count uses the minimum (barres wherever possible). Pinned `fingers=` in
  `challenging_chords.txt` mirror generator output; `popular_chords.txt`
  has hand-picked ones.
- **Scoring changes ripple into content.** `_score_voicing` and
  `_difficulty_label` thresholds decide which voicing is "primary"
  (`--single`) and which chords belong in `catalog/challenging_chords.txt`.
  Previous commits calibrated these against real playing; don't retune weights
  casually, and re-check the catalog output if you do.
- **Tuning labels on diagrams** appear for every tuning whose name is not
  `"standard"`, including low-G (which shows `G-C-E-A`) — this is how a low-G
  sheet is told apart from a standard one.
- **Inline comments in files** (`parser._strip_comment`) are whitespace +
  `#` + whitespace/end of line, applied to every line kind (chords,
  headings, `---`, `@tuning`). Sharps like `C#` and heading text like
  `Track #1` are safe; `C #note` is not a comment.
- **Chord names go through `voicing_gen._pychord_name`** before pychord,
  which reads `/<number>` as an inversion: `6/9`, `7/9`, `7/13` are respelled
  (`A7/9` -> `A9`) and any other `/<number>` is rejected. `lookup_chord`
  re-raises the parse error so users see why a name failed.
- **Slash chords** (`C/G`): the generator keeps only shapes whose lowest
  MIDI pitch is the bass when any exist, and labels inversions from the
  chord above the bass (pychord puts the bass first in `components()`).
- **Free text goes through `fonts.py`.** Draw titles, headings, chord names,
  notes, and inversion labels with `draw_centred` / `centred_strings` and
  measure them with `fonts.text_width` (via `fit_font_size`), never plain
  `drawCentredString` / `String`, or non-Latin text prints as boxes.
  Bundled fonts must be TrueType-outline `.ttf` (ReportLab can't embed CFF
  `.otf`); keep their license files in `bundled_fonts/` and the table in
  its README current. Only used glyphs are embedded, so ASCII-only sheets
  don't grow.
- `__version__` in `__init__.py` should match the latest `vX.Y.Z` release
  tag; bump it when tagging a release.

## Common changes

**Add a tuning:** add an entry to `TUNINGS` in `tunings.py` (MIDI notes in
string order + labels + aliases). CLI choices, `--list`, and generation pick
it up automatically. Then update the `--tuning` help text in `cli.py` and the
Tunings table / options table in `README.md`.

**Add a CLI option:** add it in `cli.build_parser()`, thread it through
`main()` into `parse_file`/`parse_cli_args` or `generate_pdf`, and add a row
to the README options table.

**Add a file-format key:** add it to `parser._OPTION_KEYS` and handle it in
`parser._parse_options` (shared by file lines and CLI args; unknown keys are
errors), then document it in the README file-format table.

**Add a catalog sheet:** create a `.txt` under the relevant `catalog/`
subdirectory. The first line must be `# <Title>` — `generate_catalog.sh` uses
it as the PDF title. Add it to `catalog/README.md` and, if it lives outside
the globbed directories, to the loop in `generate_catalog.sh`.

**Change diagram appearance:** edit the constants at the top of `diagram.py`.
Everything is drawn in a fixed `DIAGRAM_WIDTH × DIAGRAM_HEIGHT` box that
`pdf_generator` scales, so keep new elements inside the padding areas;
size centred text with `fit_font_size` so it can't spill into neighbouring
cells at high `--cols`. Output
must stay print-friendly (black/white plus the single dark-green dot color).

## Verifying changes

There are no automated tests. Before finishing:

1. Call `generate_voicings` / `lookup_chord` for a few chords across tunings
   (e.g. `C`, `F#m7`, `Bbdim`, `E` in `standard`, `low-g`, `baritone`) and
   sanity-check frets, fingers, notes, and inversion.
2. Render a PDF that exercises the change (headings, page breaks, a
   high-position chord with `starting_fret > 1`, a muted-string explicit
   voicing like `"C:X003"`) and look at it.
3. Run `./generate_catalog.sh` to make sure every catalog file still parses.

## Conventions

- Match existing style: 4-space indent, module docstrings, type-hinted
  functions with Google-style `Args:` / `Returns:` docstrings, `_private`
  helpers.
- Keep dependencies minimal; don't add new runtime deps without a clear need.
- When behavior or options change, update `README.md` (and `catalog/README.md`
  if relevant) in the same commit.
- Commit messages: imperative, sentence-case subject (e.g. "Add D-tuning
  support for soprano ukuleles"), with a short body explaining why.
- Release PDFs are attached to GitHub releases (`vX.Y.Z` tags); README
  download links point at a specific release tag, not `/latest/`.
