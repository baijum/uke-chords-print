"""The public library API: only names from the package root.

These tests pin what library users rely on, so internal refactors that
keep them passing are safe.
"""

from __future__ import annotations

import io
import subprocess
import sys
import warnings

import pytest
from reportlab.graphics.shapes import Drawing, String

import uke_chords_print as ukc

from .support import REPO_ROOT, pdf_page_count, pdf_text

PUBLIC = [
    "PAGE_BREAK", "STANDARD_CHORDS", "TUNINGS", "ChordWarning", "Tuning",
    "Voicing", "__version__", "diagram", "diagram_svg", "get_tuning",
    "heading", "parse_sheet", "read_sheet", "render_pdf", "voicing",
    "voicings",
]


def test_public_names():
    assert sorted(ukc.__all__) == sorted(PUBLIC)
    for name in PUBLIC:
        assert hasattr(ukc, name), name


def test_typed_package():
    assert (REPO_ROOT / "uke_chords_print" / "py.typed").is_file()


def test_import_has_no_output():
    result = subprocess.run(
        [sys.executable, "-c", "import uke_chords_print"],
        cwd=REPO_ROOT, capture_output=True, text=True, check=True,
    )
    assert (result.stdout, result.stderr) == ("", "")


class TestVoicings:
    def test_generated(self):
        am7 = ukc.voicings("Am7")
        assert len(am7) == 3
        assert am7[0] == ukc.Voicing(
            name="Am7", frets="0000", fingers="0000", notes="G C E A",
            inversion="1st Inv", starting_fret=1, difficulty="easy",
        )

    def test_limit_and_tuning(self):
        assert len(ukc.voicings("C", limit=1)) == 1
        assert len(ukc.voicings("C", limit=10)) == 10
        assert ukc.voicings("G", tuning="baritone")[0].frets == "0003"
        assert ukc.voicings("G", tuning="DGBE")[0].frets == "0003"

    def test_high_position_has_starting_fret(self):
        assert ukc.voicings("Cdim")[0].starting_fret == 2

    def test_chart_spellings(self):
        assert ukc.voicings("C°")[0].frets == ukc.voicings("Cdim")[0].frets

    def test_no_playable_voicing_is_empty(self):
        assert ukc.voicings("Fmaj9", tuning="d-tuning") == []

    @pytest.mark.parametrize("kwargs, message", [
        ({"name": "Cxyz"}, "Cannot parse chord 'Cxyz'"),
        ({"name": "am"}, "did you mean 'Am'"),
        ({"name": "C", "tuning": "banjo"}, "Unknown tuning 'banjo'"),
        ({"name": "C", "limit": 0}, "limit must be at least 1"),
    ])
    def test_errors(self, kwargs, message):
        with pytest.raises(ValueError, match=message):
            ukc.voicings(**kwargs)


class TestVoicing:
    def test_labels_worked_out(self):
        v = ukc.voicing("C", "X003", fingers="0003")
        assert v == ukc.Voicing(name="C", frets="X003", fingers="0003",
                                notes="- C E C", inversion="Root")

    def test_given_values_kept(self):
        v = ukc.voicing("C", "5433", fingers="3211", notes="w x y z",
                        inversion="Custom", starting_fret=2)
        assert (v.notes, v.inversion, v.starting_fret) == (
            "w x y z", "Custom", 2)

    def test_tuning(self):
        assert ukc.voicing("G", "0003", tuning="baritone").notes == "D G B G"

    def test_non_chord_name(self):
        v = ukc.voicing("N.C.", "XXXX")
        assert (v.notes, v.inversion) == ("", "")

    @pytest.mark.parametrize("kwargs, message", [
        ({"frets": "003"}, "Invalid frets"),
        ({"frets": "0003", "fingers": "1003"}, "Finger 1 is on string 1"),
        ({"frets": "0003", "fingers": "12"}, "Invalid fingers"),
        ({"frets": "0003", "notes": "C E"}, "names 2 notes for 4 strings"),
        ({"frets": "0003", "starting_fret": 0}, "Invalid starting_fret"),
        ({"frets": "0009", "starting_fret": 1}, "don't fit the 4 frets"),
    ])
    def test_errors(self, kwargs, message):
        with pytest.raises(ValueError, match=message):
            ukc.voicing("C", **kwargs)


class TestSheets:
    TEXT = (
        "# Title\n"
        "= Verse\n"
        "C\n"
        "G, 0232, fingers=0132\n"
        "---\n"
        "Am  # comment\n"
    )

    def test_parse_sheet(self):
        items = ukc.parse_sheet(self.TEXT, single=True)
        assert [v.name for v in items] == [
            "__HEADING__", "C", "G", "__PAGE_BREAK__", "Am"]
        assert items[0] == ukc.heading("Verse")
        assert items[3] is ukc.PAGE_BREAK
        assert items[2].fingers == "0132"

    def test_parse_sheet_all_voicings_and_bom(self):
        assert len(ukc.parse_sheet("﻿C\n")) == 3

    def test_read_sheet_matches_parse_sheet(self, tmp_path):
        path = tmp_path / "song.txt"
        path.write_text(self.TEXT, encoding="utf-8")
        assert (ukc.read_sheet(path, tuning="baritone")
                == ukc.parse_sheet(self.TEXT, tuning="baritone"))
        assert ukc.read_sheet(str(path)) == ukc.parse_sheet(self.TEXT)

    def test_errors_and_warnings(self):
        with pytest.raises(ValueError, match="^Line 2: Invalid frets"):
            ukc.parse_sheet("C\nC, 12\n")
        with pytest.warns(ukc.ChordWarning,
                          match="^Line 2: 'Riff' isn't a chord name"):
            ukc.parse_sheet("@tuning standard\nRiff, 0003\n",
                            tuning="baritone")

    def test_missing_file(self, tmp_path):
        with pytest.raises(OSError):
            ukc.read_sheet(tmp_path / "missing.txt")

    def test_heading(self):
        assert ukc.heading("  Chorus ").notes == "Chorus"
        with pytest.raises(ValueError, match="empty"):
            ukc.heading("  ")


class TestDiagrams:
    @staticmethod
    def _texts(drawing):
        return [s.text for s in drawing.contents if isinstance(s, String)]

    def test_diagram(self):
        v = ukc.voicing("C", "0003", fingers="0003")
        d = ukc.diagram(v)
        assert isinstance(d, Drawing)
        assert self._texts(d) == ["3", "C", "G", "C", "E", "C",
                                  "0 - 0 - 0 - 3"]  # Root hidden

    def test_options(self):
        v = ukc.voicing("C", "0003", fingers="0003")
        texts = self._texts(ukc.diagram(v, show_root=True,
                                        show_fingers=False))
        assert texts == ["C", "G", "C", "E", "C", "0 - 0 - 0 - 3", "Root"]

    def test_tuning_labels(self):
        v = ukc.voicings("G", tuning="baritone")[0]
        assert "0-0-0-3  (D-G-B-E)" in self._texts(ukc.diagram(v, "baritone"))

    def test_svg(self):
        svg = ukc.diagram_svg(ukc.voicings("Am7")[0])
        assert svg.startswith("<?xml")
        assert "<svg" in svg and ">Am7<" in svg


class TestRenderPdf:
    def test_to_file_object(self):
        buf = io.BytesIO()
        items = [ukc.heading("Songs"), *ukc.voicings("C", limit=1),
                 ukc.PAGE_BREAK, *ukc.voicings("G", limit=1)]
        assert ukc.render_pdf(items, buf, title="Mine") is None
        data = buf.getvalue()
        assert pdf_page_count(data) == 2
        text = pdf_text(data)
        for label in ("(Mine) Tj", "(Songs) Tj", "(C) Tj", "(G) Tj"):
            assert label in text

    def test_to_path_with_options(self, tmp_path):
        path = tmp_path / "out.pdf"
        ukc.render_pdf(iter(ukc.voicings("F")), path, paper="LETTER",
                       cols=1, rows=1, tuning="low-g", show_root=True,
                       show_fingers=False)
        data = path.read_bytes()
        assert pdf_page_count(data) == 3
        assert b"/MediaBox [ 0 0 612 792 ]" in data
        assert "(2) Tj" not in pdf_text(data)
        assert "G-C-E-A" in pdf_text(data)

    @pytest.mark.parametrize("kwargs, message", [
        ({"paper": "tabloid"}, "Unknown paper 'tabloid'. Valid options: "
                               "a4, letter"),
        ({"tuning": "banjo"}, "Unknown tuning"),
        ({"cols": 0}, "at least 1"),
    ])
    def test_errors(self, tmp_path, kwargs, message):
        with pytest.raises(ValueError, match=message):
            ukc.render_pdf(ukc.voicings("C"), tmp_path / "x.pdf", **kwargs)


def test_tunings_and_standard_chords():
    assert set(ukc.TUNINGS) == {"standard", "low-g", "baritone", "d-tuning"}
    assert ukc.get_tuning("gcea") is ukc.TUNINGS["standard"]
    assert isinstance(ukc.TUNINGS["baritone"], ukc.Tuning)
    assert len(ukc.STANDARD_CHORDS) == 108
    for name in ukc.STANDARD_CHORDS[:12]:
        assert ukc.voicings(name)


def test_warning_category():
    assert issubclass(ukc.ChordWarning, UserWarning)
    with warnings.catch_warnings():
        warnings.simplefilter("error", ukc.ChordWarning)
        with pytest.raises(ukc.ChordWarning):
            ukc.parse_sheet("@tuning standard\nRiff, 0003\n",
                            tuning="baritone")
