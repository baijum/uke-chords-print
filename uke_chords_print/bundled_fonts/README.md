# Bundled fonts

The PDF's built-in fonts (Helvetica, Courier) only cover the Windows-1252
character set. `uke_chords_print/fonts.py` draws any other character in a
title, heading, chord name, note, or inversion label with the first of
these fonts that has it, so sheets render the same on every machine:

| File | Covers | License |
|------|--------|---------|
| `DejaVuSans-Bold.ttf` | Latin extended, Greek, Cyrillic, music and other symbols (♪ ♭ ♯ Δ) | Bitstream Vera; DejaVu changes public domain — [`LICENSE-DejaVu.txt`](LICENSE-DejaVu.txt) |
| `DroidSansFallbackFull.ttf` | Chinese and Japanese (Han, Hiragana, Katakana) | Apache 2.0 — [`LICENSE-DroidSansFallback.txt`](LICENSE-DroidSansFallback.txt) |
| `BaekmukDotum.ttf` | Korean (Hangul) | Baekmuk (MIT-like) — [`LICENSE-Baekmuk.txt`](LICENSE-Baekmuk.txt) |

Characters none of these cover (e.g. emoji) fall back to installed system
fonts; any still missing print as boxes and the CLI prints a warning.

Fonts must have TrueType outlines (`.ttf`, not CFF-based `.otf` such as Noto
Sans CJK); ReportLab can't embed the latter. Only the glyphs actually used are
embedded in each PDF.

Baekmuk Batang, Baekmuk Dotum, Baekmuk Gulim, and Baekmuk Headline are
registered trademarks owned by Kim Jeong-Hwan.
