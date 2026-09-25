"""Font fallback for text the built-in PDF fonts can't show."""

from __future__ import annotations

from pathlib import Path

import pytest
from reportlab.lib.colors import red
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
                                    fillColor=red)
    assert all(s.fillColor == red for s in strings)
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
    left = 200 - total / 2
    assert calls[0] == ("font", "Helvetica-Bold", 16)
    assert calls[1] == ("draw", round(left, 3), 10, "Hi ")
    assert calls[2][0] == "font" and calls[2][1] != "Helvetica-Bold"
    # The next run starts where the first one ends
    first = pdfmetrics.stringWidth("Hi ", "Helvetica-Bold", 16)
    assert calls[3] == ("draw", round(left + first, 3), 10, "Ж")


# --- System font discovery (fontconfig and known paths) ---

DEJAVU = str(BUNDLED / "DejaVuSans-Bold.ttf")


@pytest.fixture
def fresh_cache(monkeypatch):
    """Start with no fallback fonts registered or looked up."""
    monkeypatch.setattr(fonts, "_fallback_fonts", [])
    monkeypatch.setattr(fonts, "_tried_files", set())
    monkeypatch.setattr(fonts, "_char_font", {})


class FakeRun:
    """Stand-in for subprocess.run that records its arguments."""

    def __init__(self, stdout="", error=None):
        self.stdout, self.error, self.calls = stdout, error, []

    def __call__(self, args, **kwargs):
        # Text output, captured, bounded in time, and errors raised
        assert kwargs == {"capture_output": True, "text": True,
                          "timeout": 10, "check": True}
        self.calls.append(args)
        if self.error:
            raise self.error
        return type("Result", (), {"stdout": self.stdout})()


class TestFcMatch:
    @pytest.fixture(autouse=True)
    def have_fc_match(self, monkeypatch):
        installed = {"fc-match": "/usr/bin/fc-match"}
        monkeypatch.setattr(fonts.shutil, "which", installed.get)

    def test_query(self, monkeypatch):
        run = FakeRun("/fonts/a.ttc\n2")
        monkeypatch.setattr(fonts.subprocess, "run", run)
        assert fonts._fc_match("♪", bold=True) == ("/fonts/a.ttc", 2)
        assert run.calls == [["fc-match", "-f", "%{file}\n%{index}",
                              "sans:bold:charset=266a"]]

    def test_regular_weight_and_missing_index(self, monkeypatch):
        run = FakeRun("/fonts/b.ttf\n")
        monkeypatch.setattr(fonts.subprocess, "run", run)
        assert fonts._fc_match("A", bold=False) == ("/fonts/b.ttf", 0)
        assert run.calls[0][-1] == "sans:charset=41"

    def test_no_match(self, monkeypatch):
        monkeypatch.setattr(fonts.subprocess, "run", FakeRun(""))
        assert fonts._fc_match("A", bold=False) is None

    @pytest.mark.parametrize("error", [
        OSError("gone"),
        fonts.subprocess.TimeoutExpired("fc-match", 10),
        fonts.subprocess.CalledProcessError(1, "fc-match"),
    ])
    def test_failures(self, monkeypatch, error):
        monkeypatch.setattr(fonts.subprocess, "run", FakeRun(error=error))
        assert fonts._fc_match("A", bold=False) is None

    def test_not_installed(self, monkeypatch):
        monkeypatch.setattr(fonts.shutil, "which", lambda cmd: None)
        monkeypatch.setattr(fonts.subprocess, "run", FakeRun(error=AssertionError))
        assert fonts._fc_match("A", bold=False) is None


def test_candidate_order(monkeypatch, tmp_path):
    present = tmp_path / "present.ttf"
    present.write_bytes(b"")
    monkeypatch.setattr(fonts, "_fc_match", lambda ch, bold: ("/fc.ttf", 1))
    monkeypatch.setattr(fonts, "_CANDIDATE_FILES",
                        [str(tmp_path / "absent.ttf"), str(present)])
    bundled = [(str(BUNDLED / name), 0) for name in fonts._BUNDLED_FILES]
    assert list(fonts._candidate_files("x", False)) == bundled + [
        ("/fc.ttf", 1), (str(present), 0)]


def test_font_found_by_fontconfig(monkeypatch, fresh_cache):
    monkeypatch.setattr(fonts, "_BUNDLED_FILES", [])
    monkeypatch.setattr(fonts, "_fc_match", lambda ch, bold: (DEJAVU, 0))
    monkeypatch.setattr(fonts, "_CANDIDATE_FILES", [])
    [(font, _)] = fonts.text_runs("Ж", "Helvetica-Bold")
    assert _font_file(font) == "DejaVuSans-Bold.ttf"


def test_font_found_at_known_path(monkeypatch, fresh_cache, tmp_path):
    not_a_font = tmp_path / "broken.ttf"
    not_a_font.write_text("not a font")
    monkeypatch.setattr(fonts, "_BUNDLED_FILES", [])
    monkeypatch.setattr(fonts, "_fc_match", lambda ch, bold: None)
    monkeypatch.setattr(fonts, "_CANDIDATE_FILES", [str(not_a_font), DEJAVU])
    [(font, _)] = fonts.text_runs("Ж", "Helvetica-Bold")
    assert _font_file(font) == "DejaVuSans-Bold.ttf"


def test_registered_fonts_are_reused(monkeypatch, fresh_cache):
    monkeypatch.setattr(fonts, "_BUNDLED_FILES", [])
    monkeypatch.setattr(fonts, "_CANDIDATE_FILES", [])
    calls = []
    monkeypatch.setattr(fonts, "_fc_match",
                        lambda ch, bold: calls.append(ch) or (DEJAVU, 0))
    fonts.text_runs("Ж", "Helvetica-Bold")
    fonts.text_runs("Ω", "Helvetica-Bold")  # also in DejaVu: no new lookup
    assert calls == ["Ж"]


@pytest.mark.parametrize("font_name, bold", [
    ("Helvetica-Bold", True), ("Helvetica", False),
])
def test_lookup_passes_weight_and_collection_index(
        monkeypatch, fresh_cache, font_name, bold):
    # fc-match is asked for the weight in use, and a .ttc collection's
    # face index reaches the font loader
    monkeypatch.setattr(fonts, "_BUNDLED_FILES", [])
    monkeypatch.setattr(fonts, "_CANDIDATE_FILES", [])
    asked = []
    monkeypatch.setattr(fonts, "_fc_match",
                        lambda ch, bold: asked.append(bold) or (DEJAVU, 3))
    loaded = []
    real_ttfont = fonts.TTFont

    def fake_ttfont(name, path, subfontIndex):
        loaded.append((path, subfontIndex))
        return real_ttfont(name, path)

    monkeypatch.setattr(fonts, "TTFont", fake_ttfont)
    fonts.text_runs("Ж", font_name)
    assert asked == [bold]
    assert loaded == [(DEJAVU, 3)]


def test_register_skips_bad_and_repeated_files(fresh_cache, tmp_path):
    bad = tmp_path / "bad.ttf"
    bad.write_text("not a font")
    assert fonts._register(str(bad), 0) is None
    name = fonts._register(DEJAVU, 0)
    assert name is not None and name in fonts._fallback_fonts
    assert fonts._register(DEJAVU, 0) is None  # tried already
