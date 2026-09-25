"""
Font fallback for characters the built-in PDF fonts can't show.

ReportLab's standard fonts (Helvetica, Courier) only cover the Windows-1252
character set, so text like "♪", "歌" or "Ж" used to print as boxes. Text is
split into runs: characters the standard font covers keep it, and the rest
are drawn with the first bundled font that has them (see
bundled_fonts/README.md). Anything the bundled fonts lack (e.g. emoji) falls
back to an installed TrueType font, found with fontconfig (fc-match) or from
common macOS / Windows / Linux font files. Characters no font covers are
recorded so the CLI can warn about them.

ReportLab can only embed fonts with TrueType outlines (not CFF/OpenType
.otf), and draws text left to right without shaping, so right-to-left
scripts and color emoji are not supported.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from collections.abc import Iterator
from pathlib import Path

from reportlab.graphics.shapes import String
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Shipped with the package; tried first, in this order
_BUNDLED_DIR = Path(__file__).parent / "bundled_fonts"
_BUNDLED_FILES = [
    "DejaVuSans-Bold.ttf",        # Latin ext., Greek, Cyrillic, symbols
    "DroidSansFallbackFull.ttf",  # Chinese, Japanese
    "BaekmukDotum.ttf",           # Korean
]

# System font files tried when fontconfig isn't available (or finds nothing
# usable) for characters the bundled fonts lack
_WINDOWS_FONTS = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts")
_CANDIDATE_FILES = [
    # macOS
    "/Library/Fonts/Arial Unicode.ttf",
    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/System/Library/Fonts/Apple Symbols.ttf",
    # Windows
    os.path.join(_WINDOWS_FONTS, "arialbd.ttf"),
    os.path.join(_WINDOWS_FONTS, "seguisym.ttf"),
    os.path.join(_WINDOWS_FONTS, "msyh.ttc"),
    os.path.join(_WINDOWS_FONTS, "msgothic.ttc"),
    os.path.join(_WINDOWS_FONTS, "malgun.ttf"),
    # Linux without fontconfig
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
]

_fallback_fonts: list[str] = []            # registered names, oldest first
_tried_files: set[tuple[str, int]] = set()
_char_font: dict[tuple[str, bool], str | None] = {}
_missing: set[str] = set()


def _in_standard_font(ch: str) -> bool:
    """Check whether the built-in fonts can show a character."""
    try:
        ch.encode("cp1252")
    except UnicodeEncodeError:
        return False
    return True


def _covers(font_name: str, ch: str) -> bool:
    """Check whether a registered TrueType font has a glyph for ch."""
    return ord(ch) in pdfmetrics.getFont(font_name).face.charToGlyph


def _register(path: str, index: int) -> str | None:
    """Register a font file once; None if it's unusable or already tried."""
    if (path, index) in _tried_files:
        return None
    _tried_files.add((path, index))
    name = f"UkeFallback{len(_fallback_fonts)}"
    try:
        pdfmetrics.registerFont(TTFont(name, path, subfontIndex=index))
    except Exception:  # CFF outlines, unreadable file, bad collection index
        return None
    _fallback_fonts.append(name)
    return name


def _fc_match(ch: str, bold: bool) -> tuple[str, int] | None:
    """Ask fontconfig for a sans font containing ch: (file, index)."""
    if not shutil.which("fc-match"):
        return None
    pattern = f"sans{':bold' if bold else ''}:charset={ord(ch):x}"
    try:
        out = subprocess.run(
            ["fc-match", "-f", "%{file}\n%{index}", pattern],
            capture_output=True, text=True, timeout=10, check=True,
        ).stdout
    except (OSError, subprocess.SubprocessError):
        return None
    path, _, index = out.partition("\n")
    return (path, int(index or 0)) if path else None


def _candidate_files(ch: str, bold: bool) -> Iterator[tuple[str, int]]:
    """Font files to try for ch: bundled first, then system fonts."""
    for name in _BUNDLED_FILES:
        yield str(_BUNDLED_DIR / name), 0
    match = _fc_match(ch, bold)  # only reached if no bundled font has ch
    if match:
        yield match
    for path in _CANDIDATE_FILES:
        if os.path.exists(path):
            yield path, 0


def _fallback_for(ch: str, bold: bool) -> str | None:
    """Find (and cache) a registered font that can show ch."""
    key = (ch, bold)
    if key not in _char_font:
        font = next((f for f in _fallback_fonts if _covers(f, ch)), None)
        if font is None:
            for path, index in _candidate_files(ch, bold):
                name = _register(path, index)
                if name and _covers(name, ch):
                    font = name
                    break
        _char_font[key] = font
    return _char_font[key]


def text_runs(text: str, font_name: str) -> list[tuple[str, str]]:
    """Split text into (font, text) runs that together can show all of it.

    Args:
        text: Text to draw.
        font_name: Preferred standard font (e.g. "Helvetica-Bold").

    Returns:
        Runs in order. Characters no installed font covers stay in
        font_name (and print as boxes) and are recorded for
        missing_characters().
    """
    bold = "Bold" in font_name
    runs: list[tuple[str, str]] = []
    for ch in text:
        font = font_name
        if not _in_standard_font(ch):
            font = _fallback_for(ch, bold) or font_name
            if font == font_name:
                _missing.add(ch)
        if runs and runs[-1][0] == font:
            runs[-1] = (font, runs[-1][1] + ch)
        else:
            runs.append((font, ch))
    return runs


def text_width(text: str, font_name: str, font_size: float) -> float:
    """Width of text in points, measured with its fallback fonts."""
    return sum(
        pdfmetrics.stringWidth(run, font, font_size)
        for font, run in text_runs(text, font_name)
    )


def draw_centred(
    c, x: float, y: float, text: str, font_name: str, font_size: float
) -> None:
    """Draw text centred on x on a ReportLab canvas, with fallback fonts."""
    runs = text_runs(text, font_name)
    x -= sum(pdfmetrics.stringWidth(r, f, font_size) for f, r in runs) / 2
    for font, run in runs:
        c.setFont(font, font_size)
        c.drawString(x, y, run)
        x += pdfmetrics.stringWidth(run, font, font_size)


def centred_strings(
    x: float, y: float, text: str, font_name: str, font_size: float, **attrs
) -> list[String]:
    """Build Drawing Strings for text centred on x, with fallback fonts.

    Args:
        x: Centre of the text.
        y: Baseline.
        text: Text to draw.
        font_name: Preferred standard font.
        font_size: Font size in points.
        **attrs: Extra String attributes (e.g. fillColor).

    Returns:
        One String per font run, left-anchored side by side.
    """
    runs = text_runs(text, font_name)
    x -= sum(pdfmetrics.stringWidth(r, f, font_size) for f, r in runs) / 2
    strings = []
    for font, run in runs:
        strings.append(String(
            x, y, run, fontName=font, fontSize=font_size,
            textAnchor="start", **attrs,
        ))
        x += pdfmetrics.stringWidth(run, font, font_size)
    return strings


def missing_characters() -> set[str]:
    """Characters seen so far that no installed font could show."""
    return set(_missing)
