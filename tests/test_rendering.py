"""Page layout, PDF output, and single-diagram drawing."""

from __future__ import annotations

import re

import pytest
from reportlab.graphics.shapes import Circle, Line, String
from reportlab.lib.pagesizes import A4, letter

from uke_chords_print.diagram import (
    DIAGRAM_HEIGHT,
    DIAGRAM_WIDTH,
    DOT_COLOR,
    FRET_SPACING,
    LABEL_MAX_WIDTH,
    PAD_TOP,
    draw_chord_diagram,
    fit_font_size,
)
from uke_chords_print.fonts import text_width
from uke_chords_print.parser import (
    PAGE_BREAK,
    ChordVoicing,
    make_heading,
    parse_cli_args,
)
from uke_chords_print.pdf_generator import _paginate, generate_pdf

from .support import pdf_page_count, pdf_text


def _chords(n: int) -> list[ChordVoicing]:
    return [ChordVoicing(name=f"C{i}", frets="0003") for i in range(n)]


def _shape(pages) -> list[list]:
    """Pages as nested lists: heading text, or the chord names of a row."""
    return [
        [[v.name for v in e] if isinstance(e, list) else e.notes for e in p]
        for p in pages
    ]


class TestPaginate:
    def test_empty(self):
        assert _paginate([], 4, 4) == [[]]

    def test_rows_and_pages(self):
        pages = _paginate(_chords(10), cols=2, rows=2)
        assert _shape(pages) == [
            [["C0", "C1"], ["C2", "C3"]],
            [["C4", "C5"], ["C6", "C7"]],
            [["C8", "C9"]],
        ]

    def test_page_break_starts_new_page(self):
        c = _chords(3)
        pages = _paginate([c[0], PAGE_BREAK, c[1], c[2]], 4, 4)
        assert _shape(pages) == [[["C0"]], [["C1", "C2"]]]

    def test_no_blank_pages_from_breaks(self):
        c = _chords(2)
        voicings = [PAGE_BREAK, c[0], PAGE_BREAK, PAGE_BREAK, c[1], PAGE_BREAK]
        assert _shape(_paginate(voicings, 4, 4)) == [[["C0"]], [["C1"]]]

    def test_heading_starts_new_row(self):
        c = _chords(3)
        pages = _paginate([c[0], make_heading("H"), c[1], c[2]], 4, 4)
        assert _shape(pages) == [[["C0"], "H", ["C1", "C2"]]]

    def test_heading_moves_to_next_page_when_rows_are_full(self):
        c = _chords(3)
        pages = _paginate([c[0], c[1], make_heading("H"), c[2]], 1, 2)
        assert _shape(pages) == [[["C0"], ["C1"]], ["H", ["C2"]]]

    def test_headings_per_page_capped_at_rows(self):
        headings = [make_heading(str(i)) for i in range(5)]
        pages = _paginate(headings, 4, 2)
        assert _shape(pages) == [["0", "1"], ["2", "3"], ["4"]]

    @pytest.mark.parametrize("cols, rows", [(1, 1), (3, 2), (4, 4), (5, 7)])
    def test_every_chord_placed_once_in_order(self, cols, rows):
        voicings = _chords(23)
        voicings.insert(5, make_heading("A"))
        voicings.insert(9, PAGE_BREAK)
        pages = _paginate(voicings, cols, rows)
        placed = [v.name for p in pages for e in p if isinstance(e, list)
                  for v in e]
        assert placed == [f"C{i}" for i in range(23)]
        for page in pages:
            rows_on_page = [e for e in page if isinstance(e, list)]
            assert page
            assert len(rows_on_page) <= rows
            assert all(1 <= len(r) <= cols for r in rows_on_page)
            assert len(page) - len(rows_on_page) <= rows


class TestGeneratePdf:
    @pytest.fixture
    def render(self, tmp_path):
        def render(voicings, **kwargs) -> tuple[bytes, str]:
            path = tmp_path / "out.pdf"
            assert generate_pdf(voicings, str(path), **kwargs) == str(path)
            data = path.read_bytes()
            assert data.startswith(b"%PDF-")
            return data, pdf_text(data)
        return render

    def test_basic_sheet(self, render):
        data, text = render(parse_cli_args(["C", "Am7:0000"], single=True),
                            title="My Songs")
        assert pdf_page_count(data) == 1
        for label in ["(My Songs) Tj", "(Page 1) Tj", "(C) Tj", "(Am7) Tj",
                      "(0 - 0 - 0 - 3) Tj", "(1st Inv) Tj"]:
            assert label in text
        assert b"/Title (My Songs)" in data

    def test_page_count_and_footers(self, render):
        data, text = render(_chords(40), cols=4, rows=4)
        assert pdf_page_count(data) == 3
        assert "(Page 3) Tj" in text

    def test_root_label_hidden_unless_asked(self, render):
        voicings = parse_cli_args(["C:0003"])
        assert "(Root) Tj" not in render(voicings)[1]
        assert "(Root) Tj" in render(voicings, show_root=True)[1]

    def test_no_fingers(self, render):
        voicings = parse_cli_args(["F:2010:fingers=2010"])
        assert "(2) Tj" in render(voicings)[1]
        assert "(2) Tj" not in render(voicings, no_fingers=True)[1]

    def test_string_labels_for_other_tunings(self, render):
        voicings = parse_cli_args(["G:0003"], tuning="baritone")
        text = render(voicings, tuning="baritone")[1]
        assert "(0-0-0-3  \\(D-G-B-E\\)) Tj" in text
        text = render(parse_cli_args(["C:0003"]), tuning="standard")[1]
        assert "D-G-B-E" not in text and "G-C-E-A" not in text

    @pytest.mark.parametrize("paper, size", [("a4", A4), ("letter", letter)])
    def test_paper_size(self, render, paper, size):
        data, _ = render(_chords(1), paper=paper)
        box = re.search(rb"/MediaBox \[ 0 0 ([\d.]+) ([\d.]+) \]", data)
        assert (float(box.group(1)), float(box.group(2))) == pytest.approx(
            size, abs=0.01)

    def test_ascii_only_embeds_no_fonts(self, render):
        data, _ = render(_chords(2), title="Plain")
        assert b"/FontFile2" not in data

    def test_non_latin_text_embeds_bundled_font(self, render):
        voicings = [make_heading("Песни")] + _chords(1)
        data, _ = render(voicings, title="歌")
        assert b"/FontFile2" in data
        assert b"DejaVuSans-Bold" in data
        assert b"DroidSansFallback" in data

    @pytest.mark.parametrize("cols, rows", [(0, 4), (4, 0), (-1, 1)])
    def test_invalid_grid(self, tmp_path, cols, rows):
        with pytest.raises(ValueError, match="at least 1"):
            generate_pdf(_chords(1), str(tmp_path / "x.pdf"),
                         cols=cols, rows=rows)

    def test_too_many_headings(self, tmp_path):
        headings = [make_heading(str(i)) for i in range(60)]
        with pytest.raises(ValueError, match="Too many headings"):
            generate_pdf(headings, str(tmp_path / "x.pdf"), rows=60)

    def test_empty_voicings_still_make_a_page(self, render):
        data, _ = render([])
        assert pdf_page_count(data) == 1


class TestDiagram:
    @staticmethod
    def _strings(drawing) -> list[str]:
        return [s.text for s in drawing.contents if isinstance(s, String)]

    def test_size(self):
        d = draw_chord_diagram(ChordVoicing(name="C", frets="0003"))
        assert (d.width, d.height) == (DIAGRAM_WIDTH, DIAGRAM_HEIGHT)

    def test_open_chord(self):
        d = draw_chord_diagram(ChordVoicing(
            name="C", frets="0003", fingers="0003", notes="G C E C",
            inversion="Root",
        ))
        assert self._strings(d) == [
            "3", "C", "G", "C", "E", "C", "0 - 0 - 0 - 3", "Root",
        ]
        dots = [c for c in d.contents
                if isinstance(c, Circle) and c.fillColor == DOT_COLOR]
        open_markers = [c for c in d.contents
                        if isinstance(c, Circle) and c.fillColor != DOT_COLOR]
        assert len(dots) == 1
        assert len(open_markers) == 3

    def test_high_position_shows_fret_label(self):
        d = draw_chord_diagram(ChordVoicing(
            name="C", frets="5433", fingers="3211", starting_fret=3,
        ))
        assert "3fr" in self._strings(d)
        # Frets 5, 4, 3, 3 fall in the 3rd, 2nd, 1st, 1st spaces shown
        fb_top = DIAGRAM_HEIGHT - PAD_TOP
        dots = [c for c in d.contents
                if isinstance(c, Circle) and c.fillColor == DOT_COLOR]
        assert [round((fb_top - c.cy) / FRET_SPACING + 0.5, 6)
                for c in dots] == [3, 2, 1, 1]

    def test_fret_label_stays_inside(self):
        d = draw_chord_diagram(ChordVoicing(
            name="C", frets="0007", starting_fret=7,
        ))
        [label] = [s for s in d.contents
                   if isinstance(s, String) and s.text == "7fr"]
        width = text_width("7fr", label.fontName, label.fontSize)
        assert label.x + width <= DIAGRAM_WIDTH

    def test_muted_string_draws_x_and_skips_note(self):
        plain = draw_chord_diagram(ChordVoicing(name="C", frets="0003"))
        muted = draw_chord_diagram(ChordVoicing(
            name="C", frets="X003", notes="- C E C",
        ))
        lines = lambda d: sum(isinstance(s, Line) for s in d.contents)
        assert lines(muted) == lines(plain) + 2
        assert "-" not in self._strings(muted)
        assert "X - 0 - 0 - 3" in self._strings(muted)

    def test_hidden_fingers(self):
        d = draw_chord_diagram(ChordVoicing(name="F", frets="2010",
                                            fingers=""))
        assert self._strings(d) == ["F", "2 - 0 - 1 - 0"]

    def test_string_labels(self):
        d = draw_chord_diagram(ChordVoicing(name="G", frets="0003"),
                               string_labels=("D", "G", "B", "E"))
        assert "0-0-0-3  (D-G-B-E)" in self._strings(d)

    @pytest.mark.parametrize("name", [
        "C", "Cmaj13#11/Bb", "A very long chord name indeed", "歌の和音",
    ])
    def test_labels_fit_inside(self, name):
        """Every label, including fallback-font runs drawn side by side,
        stays inside the diagram so it can't spill into the next cell."""
        d = draw_chord_diagram(ChordVoicing(
            name=name, frets="0007", starting_fret=7,
            inversion="An inversion label that is far too long",
        ))
        extents: dict[float, list[float]] = {}
        for s in d.contents:
            if not isinstance(s, String):
                continue
            width = text_width(s.text, s.fontName, s.fontSize)
            left = s.x - width / 2 if s.textAnchor == "middle" else s.x
            span = extents.setdefault(s.y, [left, left + width])
            span[0] = min(span[0], left)
            span[1] = max(span[1], left + width)
        for left, right in extents.values():
            assert left >= 0
            assert right <= DIAGRAM_WIDTH + 1e-6


class TestFitFontSize:
    def test_short_text_keeps_size(self):
        assert fit_font_size("C", "Helvetica-Bold", 18) == 18

    def test_long_text_shrinks_to_fit(self):
        text = "Cmaj7#11 with a very long description"
        size = fit_font_size(text, "Helvetica-Bold", 18)
        assert size < 18
        assert text_width(text, "Helvetica-Bold", size) == pytest.approx(
            LABEL_MAX_WIDTH)

    def test_custom_width(self):
        size = fit_font_size("Title", "Helvetica-Bold", 16, max_width=10)
        assert text_width("Title", "Helvetica-Bold", size) == pytest.approx(10)
