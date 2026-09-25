"""Font fallback for text the built-in PDF fonts can't show."""

from __future__ import annotations

from pathlib import Path

import pytest
from reportlab.pdfbase import pdfmetrics

from uke_chords_print import fonts

BUNDLED = Path(fonts.__file__).parent / "bundled_fonts"


def _font_file(font_name: str) -> str:
    return Path(pdfmetrics.getFont(font_name).face.filename).name


@pytest.fixture
def no_system_fonts(monkeypatch):
    """Only the bundled fonts, as on a machine without extra fonts."""
    monkeypatch.setattr(fonts, "_fc_match", lambda ch, bold: None)
    monkeypatch.setattr(fonts, "_CANDIDATE_FILES", [])


@pytest.mark.parametrize("text", ["Am7", "C#m7b5", "Café", "€ • – ‘quoted’",
                                  "Cø", "Ñandú"])
def test_windows_1252_text_uses_standard_font(text):
    assert fonts.text_runs(text, "Helvetica-Bold") == [
        ("Helvetica-Bold", text)]


@pytest.mark.parametrize("char, font_file", [
    ("Ж", "DejaVuSans-Bold.ttf"),       # Cyrillic
    ("Ω", "DejaVuSans-Bold.ttf"),       # Greek
    ("♪", "DejaVuSans-Bold.ttf"),       # music symbols
    ("♭", "DejaVuSans-Bold.ttf"),
    ("Δ", "DejaVuSans-Bold.ttf"),
    ("ő", "DejaVuSans-Bold.ttf"),       # Latin extended
    ("歌", "DroidSansFallbackFull.ttf"),  # Han
    ("か", "DroidSansFallbackFull.ttf"),  # Hiragana
    ("カ", "DroidSansFallbackFull.ttf"),  # Katakana
    ("한", "BaekmukDotum.ttf"),          # Hangul
])
def test_bundled_fonts_cover_scripts(no_system_fonts, char, font_file):
    [(font, run)] = fonts.text_runs(char, "Helvetica-Bold")
    assert run == char
    assert _font_file(font) == font_file


def test_runs_split_and_merge(no_system_fonts):
    runs = fonts.text_runs("Песня 1: 歌う", "Helvetica-Bold")
    assert [text for _, text in runs] == ["Песня", " 1: ", "歌う"]
    assert runs[1][0] == "Helvetica-Bold"
    assert "".join(text for _, text in runs) == "Песня 1: 歌う"


def test_bundled_files_exist_with_licenses():
    for name in fonts._BUNDLED_FILES:
        assert (BUNDLED / name).is_file()
    readme = (BUNDLED / "README.md").read_text(encoding="utf-8")
    for name in fonts._BUNDLED_FILES:
        assert f"`{name}`" in readme
    assert len(list(BUNDLED.glob("LICENSE-*.txt"))) == len(fonts._BUNDLED_FILES)


def test_missing_characters_are_reported(no_system_fonts):
    char = "\U0010FFFD"  # private use: no font has it
    runs = fonts.text_runs(f"C{char}", "Helvetica-Bold")
    assert runs == [("Helvetica-Bold", f"C{char}")]
    assert char in fonts.missing_characters()


def test_text_width_adds_runs(no_system_fonts):
    size = 12
    ascii_width = pdfmetrics.stringWidth("Am", "Helvetica-Bold", size)
    mixed = fonts.text_width("Am歌", "Helvetica-Bold", size)
    assert mixed > ascii_width
    assert fonts.text_width("Am", "Helvetica-Bold", size) == ascii_width


def test_centred_strings_line_up(no_system_fonts):
    strings = fonts.centred_strings(100, 50, "Ab 歌 Ж", "Helvetica-Bold", 10,
                                    fillColor=None)
    total = fonts.text_width("Ab 歌 Ж", "Helvetica-Bold", 10)
    assert strings[0].x == pytest.approx(100 - total / 2)
    for a, b in zip(strings, strings[1:]):
        assert b.x == pytest.approx(
            a.x + pdfmetrics.stringWidth(a.text, a.fontName, 10))
    assert all(s.y == 50 and s.textAnchor == "start" for s in strings)


def test_draw_centred_on_canvas(no_system_fonts):
    calls = []

    class FakeCanvas:
        def setFont(self, name, size):
            calls.append(("font", name, size))

        def drawString(self, x, y, text):
            calls.append(("draw", round(x, 3), y, text))

    fonts.draw_centred(FakeCanvas(), 200, 10, "Hi Ж", "Helvetica-Bold", 16)
    total = fonts.text_width("Hi Ж", "Helvetica-Bold", 16)
    assert calls[0] == ("font", "Helvetica-Bold", 16)
    assert calls[1] == ("draw", round(200 - total / 2, 3), 10, "Hi ")
    assert calls[2][0] == "font" and calls[2][1] != "Helvetica-Bold"
    assert calls[3][3] == "Ж"
