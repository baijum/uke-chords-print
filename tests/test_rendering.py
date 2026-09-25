"""Page layout, PDF output, and single-diagram drawing."""

from __future__ import annotations

import itertools
import re

import pytest
from reportlab.graphics.shapes import Circle, Line, String
from reportlab.lib.colors import white
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.units import mm

from uke_chords_print.diagram import (
    CHORD_NAME_SIZE,
    DIAGRAM_HEIGHT,
    DIAGRAM_WIDTH,
    DOT_COLOR,
    DOT_RADIUS,
    FRETBOARD_HEIGHT,
    FRETBOARD_WIDTH,
    FRET_SPACING,
    NUM_FRETS,
    NUM_STRINGS,
    NUT_THICKNESS,
    OPEN_RADIUS,
    STRING_SPACING,
    LABEL_MAX_WIDTH,
    PAD_LEFT,
    PAD_TOP,
    draw_chord_diagram,
    fit_font_size,
)
from uke_chords_print.fonts import text_width
from uke_chords_print.parser import (
    PAGE_BREAK,
    Voicing,
    make_heading,
    parse_cli_args,
)
from uke_chords_print.pdf_generator import _paginate, generate_pdf

from .support import pdf_page_count, pdf_text


def _chords(n: int) -> list[Voicing]:
    return [Voicing(name=f"C{i}", frets="0003") for i in range(n)]


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
        d = draw_chord_diagram(Voicing(name="C", frets="0003"))
        assert (d.width, d.height) == (DIAGRAM_WIDTH, DIAGRAM_HEIGHT)

    def test_open_chord(self):
        d = draw_chord_diagram(Voicing(
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
        d = draw_chord_diagram(Voicing(
            name="C", frets="5433", fingers="3211", starting_fret=3,
        ))
        assert "3fr" in self._strings(d)
        # Frets 5, 4, 3, 3 fall in the 3rd, 2nd, 1st, 1st spaces shown
        fb_top = DIAGRAM_HEIGHT - PAD_TOP
        dots = [c for c in d.contents
                if isinstance(c, Circle) and c.fillColor == DOT_COLOR]
        assert [round((fb_top - c.cy) / FRET_SPACING + 0.5, 6)
                for c in dots] == [3, 2, 1, 1]

    def test_fret_label_without_fretted_strings(self):
        # Only open/muted strings: the label sits left of the fretboard
        d = draw_chord_diagram(Voicing(
            name="N.C.", frets="XX00", starting_fret=5,
        ))
        [label] = [s for s in d.contents
                   if isinstance(s, String) and s.text == "5fr"]
        assert 0 <= label.x < PAD_LEFT

    @pytest.mark.parametrize("frets, start, spaces", [
        ("1003", 3, [1, 1]),   # below the window: clamped to the first space
        ("0009", 3, [4]),      # above it: clamped to the last
    ])
    def test_dots_outside_window_are_clamped(self, frets, start, spaces):
        # The parser rejects these; the drawing still stays in bounds
        d = draw_chord_diagram(Voicing(
            name="C", frets=frets, starting_fret=start,
        ))
        fb_top = DIAGRAM_HEIGHT - PAD_TOP
        dots = [c for c in d.contents
                if isinstance(c, Circle) and c.fillColor == DOT_COLOR]
        assert [round((fb_top - c.cy) / FRET_SPACING + 0.5, 6)
                for c in dots] == spaces

    def test_short_fingers_are_padded(self):
        d = draw_chord_diagram(Voicing(name="C", frets="2003",
                                            fingers="1"))
        assert self._strings(d)[:2] == ["1", "C"]

    def test_fret_label_stays_inside(self):
        d = draw_chord_diagram(Voicing(
            name="C", frets="0007", starting_fret=7,
        ))
        [label] = [s for s in d.contents
                   if isinstance(s, String) and s.text == "7fr"]
        width = text_width("7fr", label.fontName, label.fontSize)
        assert label.x + width <= DIAGRAM_WIDTH

    def test_muted_string_draws_x_and_skips_note(self):
        plain = draw_chord_diagram(Voicing(name="C", frets="0003"))
        muted = draw_chord_diagram(Voicing(
            name="C", frets="X003", notes="- C E C",
        ))
        lines = lambda d: sum(isinstance(s, Line) for s in d.contents)
        assert lines(muted) == lines(plain) + 2
        assert "-" not in self._strings(muted)
        assert "X - 0 - 0 - 3" in self._strings(muted)

    def test_hidden_fingers(self):
        d = draw_chord_diagram(Voicing(name="F", frets="2010",
                                            fingers=""))
        assert self._strings(d) == ["F", "2 - 0 - 1 - 0"]

    def test_string_labels(self):
        d = draw_chord_diagram(Voicing(name="G", frets="0003"),
                               string_labels=("D", "G", "B", "E"))
        assert "0-0-0-3  (D-G-B-E)" in self._strings(d)

    @pytest.mark.parametrize("name", [
        "C", "Cmaj13#11/Bb", "A very long chord name indeed", "歌の和音",
    ])
    def test_labels_fit_inside(self, name):
        """Every label, including fallback-font runs drawn side by side,
        stays inside the diagram so it can't spill into the next cell."""
        d = draw_chord_diagram(Voicing(
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


class TestDiagramGeometry:
    """Where each part of a diagram goes, from the layout constants."""

    FB_LEFT = PAD_LEFT
    FB_TOP = DIAGRAM_HEIGHT - PAD_TOP
    FB_BOTTOM = FB_TOP - FRETBOARD_HEIGHT
    MARKER_Y = FB_TOP + 5 * mm

    @staticmethod
    def _parts(voicing):
        d = draw_chord_diagram(voicing)
        lines = [s for s in d.contents if isinstance(s, Line)]
        circles = [s for s in d.contents if isinstance(s, Circle)]
        strings = [s for s in d.contents if isinstance(s, String)]
        return lines, circles, strings

    def _string_x(self, i):
        return self.FB_LEFT + i * STRING_SPACING

    @staticmethod
    def _centre(s):
        if s.textAnchor == "middle":
            return s.x
        return s.x + text_width(s.text, s.fontName, s.fontSize) / 2

    @pytest.mark.parametrize("start, nut", [(1, True), (5, False)])
    def test_grid(self, start, nut):
        frets = "0003" if nut else "0557"
        lines, _, _ = self._parts(Voicing(name="C", frets=frets,
                                               starting_fret=start))
        verticals = [ln for ln in lines if ln.x1 == ln.x2]
        horizontals = [ln for ln in lines if ln.y1 == ln.y2]
        assert [(ln.x1, ln.y1, ln.y2) for ln in verticals] == [
            (pytest.approx(self._string_x(i)), pytest.approx(self.FB_TOP),
             pytest.approx(self.FB_BOTTOM)) for i in range(NUM_STRINGS)]
        ys = sorted((ln.y1 for ln in horizontals), reverse=True)
        assert ys == pytest.approx(
            [self.FB_TOP - i * FRET_SPACING for i in range(NUM_FRETS + 1)])
        for ln in horizontals:
            assert (ln.x1, ln.x2) == pytest.approx(
                (self.FB_LEFT, self.FB_LEFT + FRETBOARD_WIDTH))
        top = next(ln for ln in horizontals if ln.y1 == pytest.approx(self.FB_TOP))
        others = [ln.strokeWidth for ln in horizontals if ln is not top]
        if nut:  # thick nut in open position
            assert top.strokeWidth == NUT_THICKNESS
            assert all(w < NUT_THICKNESS / 2 for w in others)
        else:
            assert top.strokeWidth < NUT_THICKNESS / 2

    def test_open_and_muted_markers(self):
        lines, circles, _ = self._parts(Voicing(name="C", frets="X003"))
        [open1, open2] = [c for c in circles if c.fillColor != DOT_COLOR]
        for circle, i in ((open1, 1), (open2, 2)):
            assert (circle.cx, circle.cy, circle.r) == pytest.approx(
                (self._string_x(i), self.MARKER_Y, OPEN_RADIUS))
            assert circle.fillColor == white
        # The X: two lines crossing at the marker point, at ±45 degrees
        cross = [ln for ln in lines if ln.x1 != ln.x2 and ln.y1 != ln.y2]
        assert len(cross) == 2
        for ln in cross:
            assert ((ln.x1 + ln.x2) / 2, (ln.y1 + ln.y2) / 2) == pytest.approx(
                (self._string_x(0), self.MARKER_Y))
            assert abs(ln.x2 - ln.x1) == pytest.approx(abs(ln.y2 - ln.y1))
        slopes = sorted((ln.y2 - ln.y1) / (ln.x2 - ln.x1) for ln in cross)
        assert slopes == pytest.approx([-1, 1])

    @pytest.mark.parametrize("frets, fingers, start", [
        ("2010", "2010", 1), ("5433", "3211", 3), ("0787", "0132", 7),
    ])
    def test_dots_and_finger_numbers(self, frets, fingers, start):
        _, circles, strings = self._parts(Voicing(
            name="C", frets=frets, fingers=fingers, starting_fret=start))
        dots = [c for c in circles if c.fillColor == DOT_COLOR]
        fretted = [(i, int(f)) for i, f in enumerate(frets) if f != "0"]
        assert len(dots) == len(fretted)
        numbers = [s for s in strings if s.fillColor == white]
        for dot, number, (i, fret) in zip(dots, numbers, fretted):
            space = fret - start + 1  # 1-based space in the 4 shown
            assert (dot.cx, dot.cy, dot.r) == pytest.approx((
                self._string_x(i), self.FB_TOP - (space - 0.5) * FRET_SPACING,
                DOT_RADIUS))
            assert number.text == fingers[i]
            assert number.textAnchor == "middle"
            assert number.x == pytest.approx(dot.cx)
            assert dot.cy - dot.r < number.y < dot.cy  # sits inside the dot

    def test_labels_centred_and_stacked(self):
        _, circles, strings = self._parts(Voicing(
            name="Am7", frets="0000", fingers="0000", notes="G C E A",
            inversion="1st Inv"))
        name, *notes, frets_line, inversion = strings
        centre = self.FB_LEFT + FRETBOARD_WIDTH / 2
        assert name.text == "Am7" and name.fontSize == CHORD_NAME_SIZE
        for label in (name, frets_line, inversion):
            assert self._centre(label) == pytest.approx(centre)
        for i, note in enumerate(notes):
            assert self._centre(note) == pytest.approx(self._string_x(i))
        # Top to bottom: name, open markers, fretboard, notes, frets, inversion
        marker_top = max(c.cy + c.r for c in circles)
        assert name.y > marker_top
        assert all(n.y < self.FB_BOTTOM for n in notes)
        assert frets_line.y < notes[0].y
        assert inversion.y < frets_line.y
        assert inversion.y > 0

    def test_fret_label_between_fretboard_and_name(self):
        _, _, strings = self._parts(Voicing(
            name="C", frets="5433", starting_fret=3))
        name = next(s for s in strings if s.fontSize == CHORD_NAME_SIZE)
        label = next(s for s in strings if s.text == "3fr")
        assert self.FB_TOP < label.y < name.y
        # Starts over the first fretted string
        assert label.x == pytest.approx(self._string_x(0))


class RecordingCanvas:
    """Canvas stand-in that records where text and diagrams are placed."""

    instances: list["RecordingCanvas"] = []

    def __init__(self, path, pagesize):
        self.pagesize = pagesize
        self.page = 0
        self.stack = []
        self.tx = self.ty = 0.0
        self.s = 1.0
        self.texts = []      # (page, x, y, text, size)
        self.diagrams = []   # (page, x, y, scale, drawing)
        self.meta = {}
        RecordingCanvas.instances.append(self)

    def setTitle(self, t): self.meta["title"] = t
    def setAuthor(self, a): self.meta["author"] = a
    def showPage(self): self.page += 1
    def save(self): self.meta["saved"] = True
    def setFont(self, name, size): self.size = size
    def saveState(self): self.stack.append((self.tx, self.ty, self.s))
    def restoreState(self): self.tx, self.ty, self.s = self.stack.pop()

    def translate(self, x, y):
        self.tx += x * self.s
        self.ty += y * self.s

    def scale(self, x, y):
        assert x == y
        self.s *= x

    def drawString(self, x, y, text):
        self.texts.append((self.page, x, y, text, self.size))

    def drawCentredString(self, x, y, text):
        self.texts.append((self.page, x, y, text, self.size))


class TestPageLayout:
    @pytest.fixture
    def layout(self, monkeypatch):
        import uke_chords_print.pdf_generator as pg

        RecordingCanvas.instances.clear()
        monkeypatch.setattr(pg.canvas, "Canvas", RecordingCanvas)

        def fake_draw(drawing, c, x, y):
            c.diagrams.append((c.page, c.tx, c.ty, c.s, drawing))

        monkeypatch.setattr(pg.renderPDF, "draw", fake_draw)

        def layout(voicings, **kwargs):
            generate_pdf(voicings, "unused.pdf", **kwargs)
            [c] = RecordingCanvas.instances
            return c
        return layout

    @staticmethod
    def _boxes(c):
        return [(p, x, y, x + DIAGRAM_WIDTH * s, y + DIAGRAM_HEIGHT * s)
                for p, x, y, s, _ in c.diagrams]

    @pytest.mark.parametrize("paper", ["a4", "letter"])
    @pytest.mark.parametrize("cols, rows", [(4, 4), (2, 3), (6, 8), (1, 1)])
    def test_diagrams_fit_margins_without_overlap(self, layout, paper,
                                                  cols, rows):
        from uke_chords_print import pdf_generator as pg
        voicings = _chords(2 * cols * rows + 1)
        voicings.insert(3, make_heading("Heading"))
        c = layout(voicings, paper=paper, cols=cols, rows=rows, title="T")
        width, height = c.pagesize
        boxes = self._boxes(c)
        assert len(boxes) == len(voicings) - 1
        assert len({s for _, _, _, s, _ in c.diagrams}) == 1  # one size
        for _, x0, y0, x1, y1 in boxes:
            assert x0 >= pg.MARGIN_LEFT - 1e-6
            assert x1 <= width - pg.MARGIN_RIGHT + 1e-6
            assert y0 >= pg.MARGIN_BOTTOM - 1e-6
            assert y1 <= height - pg.MARGIN_TOP + 1e-6
        for a, b in itertools.combinations(boxes, 2):
            if a[0] == b[0]:
                assert (a[3] <= b[1] + 1e-6 or b[3] <= a[1] + 1e-6
                        or a[4] <= b[2] + 1e-6 or b[4] <= a[2] + 1e-6)

    def test_grid_order(self, layout):
        c = layout(_chords(8), cols=4, rows=2)
        xs = [round(x, 3) for _, x, _, _, _ in c.diagrams]
        ys = [round(y, 3) for _, _, y, _, _ in c.diagrams]
        assert len(xs) == 8
        assert xs[:4] == sorted(xs[:4]) and xs[:4] == xs[4:]  # columns
        assert len(set(ys[:4])) == 1 and ys[4] < ys[0]         # rows go down

    def test_more_columns_means_smaller_diagrams(self, layout):
        small = layout(_chords(1), cols=8).diagrams[0][3]
        RecordingCanvas.instances.clear()
        large = layout(_chords(1), cols=2).diagrams[0][3]
        assert small < large

    def test_title_footer_and_headings(self, layout):
        from uke_chords_print import pdf_generator as pg
        voicings = _chords(2) + [make_heading("Chorus")] + _chords(20)
        c = layout(voicings, cols=4, rows=4, title="Songbook")
        width, height = c.pagesize
        texts = {t: (p, x, y, size) for p, x, y, t, size in c.texts}
        page, x, y, size = texts["Songbook"]
        assert page == 0 and size == pg.TITLE_FONT_SIZE
        assert y > max(y1 for p, _, _, _, y1 in self._boxes(c) if p == 0)
        assert x == pytest.approx(
            width / 2 - text_width("Songbook", "Helvetica-Bold", size) / 2)
        pages = max(p for p, *_ in c.diagrams) + 1
        for n in range(pages):
            p, x, y, _ = texts[f"Page {n + 1}"]
            assert (p, x, y) == (n, width / 2, pg.FOOTER_Y)
        # The heading sits between the first row and the next one
        _, _, hy, _ = texts["Chorus"]
        first_row = [b for b in self._boxes(c) if b[0] == 0][:2]
        next_row = [b for b in self._boxes(c) if b[0] == 0][2]
        assert next_row[4] <= hy <= first_row[0][2]

    def test_title_only_on_first_page(self, layout):
        c = layout(_chords(40), title="Once")
        assert [p for p, *_, t, _ in c.texts if t == "Once"] == [0]
        assert c.meta == {"title": "Once", "author": "uke-chords-print",
                          "saved": True}

    def test_untitled_metadata(self, layout):
        c = layout(_chords(1))
        assert c.meta["title"] == "Ukulele Chord Diagrams"


class TestPageLayoutExact:
    """Exact placement, from the layout constants in pdf_generator."""

    @pytest.fixture
    def layout(self, monkeypatch):
        import uke_chords_print.pdf_generator as pg

        RecordingCanvas.instances.clear()
        monkeypatch.setattr(pg.canvas, "Canvas", RecordingCanvas)
        monkeypatch.setattr(
            pg.renderPDF, "draw",
            lambda d, c, x, y: c.diagrams.append((c.page, c.tx + x * c.s,
                                                  c.ty + y * c.s, c.s, d)))

        def layout(voicings, **kwargs):
            generate_pdf(voicings, "unused.pdf", **kwargs)
            return RecordingCanvas.instances[-1]
        return layout

    @pytest.mark.parametrize("title", ["", "Songs"])
    def test_cells(self, layout, title):
        from uke_chords_print import pdf_generator as pg
        cols, rows = 3, 2
        c = layout(_chords(12), cols=cols, rows=rows, title=title)
        width, height = c.pagesize
        usable_w = width - pg.MARGIN_LEFT - pg.MARGIN_RIGHT
        usable_h = height - pg.MARGIN_TOP - pg.MARGIN_BOTTOM
        reserved = pg.TITLE_HEIGHT if title else 0  # page 1 only
        cell_w, cell_h = usable_w / cols, (usable_h - reserved) / rows
        scale = min(cell_w / DIAGRAM_WIDTH, cell_h / DIAGRAM_HEIGHT) * 0.98
        for n, (page, x, y, s, _) in enumerate(c.diagrams):
            row, col = divmod(n % (cols * rows), cols)
            top = height - pg.MARGIN_TOP - (reserved if page == 0 else 0)
            assert page == n // (cols * rows)
            assert s == pytest.approx(scale)
            # Centred in its cell
            assert x == pytest.approx(pg.MARGIN_LEFT + col * cell_w
                                      + (cell_w - DIAGRAM_WIDTH * s) / 2)
            assert y == pytest.approx(top - (row + 1) * cell_h
                                      + (cell_h - DIAGRAM_HEIGHT * s) / 2)

    def test_text_positions_and_sizes(self, layout):
        from uke_chords_print import pdf_generator as pg
        long_heading = "A very long heading " * 8
        c = layout([make_heading("Verse"), make_heading(long_heading)]
                   + _chords(1), title="Songs")
        width, height = c.pagesize
        usable_w = width - pg.MARGIN_LEFT - pg.MARGIN_RIGHT
        texts = {t: (x, y, size) for _, x, y, t, size in c.texts}

        def left(text, size):
            return width / 2 - text_width(text, "Helvetica-Bold", size) / 2

        top = height - pg.MARGIN_TOP
        assert texts["Songs"] == pytest.approx((
            left("Songs", pg.TITLE_FONT_SIZE),
            top - 0.75 * pg.TITLE_FONT_SIZE, pg.TITLE_FONT_SIZE))
        y = top - pg.TITLE_HEIGHT
        assert texts["Verse"] == pytest.approx((
            left("Verse", pg.HEADING_FONT_SIZE),
            y - pg.HEADING_HEIGHT + 2 * mm, pg.HEADING_FONT_SIZE))
        # A long heading shrinks to the page width, not a diagram's width
        size = fit_font_size(long_heading, "Helvetica-Bold",
                             pg.HEADING_FONT_SIZE, usable_w)
        assert size < pg.HEADING_FONT_SIZE
        assert texts[long_heading] == pytest.approx((
            left(long_heading, size),
            y - 2 * pg.HEADING_HEIGHT + 2 * mm, size))
        assert texts["Page 1"] == (width / 2, pg.FOOTER_Y, 8)

    def test_defaults(self, layout):
        c = layout(_chords(17))  # a4, 4 x 4 grid
        assert c.pagesize == A4
        assert [p for p, *_ in c.diagrams].count(0) == 16

    def test_unknown_paper_is_a4(self, layout):
        assert layout(_chords(1), paper="tabloid").pagesize == A4

    @staticmethod
    def _labels(drawing):
        return [s.text for s in drawing.contents if isinstance(s, String)]

    def test_hidden_labels_are_not_drawn(self, layout):
        voicing = Voicing(name="C", frets="0003", fingers="0003",
                               notes="G C E C", inversion="Root")
        shown = layout([voicing], show_root=True).diagrams[0][4]
        hidden = layout([voicing], no_fingers=True).diagrams[0][4]
        assert self._labels(shown) == ["3", "C", "G", "C", "E", "C",
                                       "0 - 0 - 0 - 3", "Root"]
        assert self._labels(hidden) == ["C", "G", "C", "E", "C",
                                        "0 - 0 - 0 - 3"]
