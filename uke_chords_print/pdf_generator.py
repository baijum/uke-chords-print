"""
Lay out chord diagrams in a grid on printable pages and generate PDF.

Supports US Letter and A4 page sizes with configurable grid dimensions.
"""

from __future__ import annotations

import os
from typing import BinaryIO

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import mm, inch
from reportlab.pdfgen import canvas
from reportlab.graphics import renderPDF

from .fonts import draw_centred
from .parser import Voicing, PAGE_BREAK, is_heading
from .diagram import (
    draw_chord_diagram, displayed, fit_font_size, DIAGRAM_WIDTH,
    DIAGRAM_HEIGHT,
)
from .tunings import display_labels

# Page margins
MARGIN_TOP = 0.3 * inch
MARGIN_BOTTOM = 0.4 * inch
MARGIN_LEFT = 0.25 * inch
MARGIN_RIGHT = 0.25 * inch

# Title area -- drawn below the top margin so printers don't clip it
TITLE_FONT_SIZE = 16
TITLE_HEIGHT = TITLE_FONT_SIZE * 1.1  # cap height + descenders + gap

# Page number baseline, inside the bottom margin but clear of the edge
FOOTER_Y = 0.25 * inch

# Section heading
HEADING_FONT_SIZE = 14
HEADING_HEIGHT = 0.25 * inch

PAGE_SIZES = {
    "letter": letter,
    "a4": A4,
}


def _paginate(
    voicings: list[Voicing], cols: int, rows: int
) -> list[list[Voicing | list[Voicing]]]:
    """Split voicings into pages of headings and rows of diagrams.

    Each page holds at most `rows` rows and at most `rows` headings, which
    bounds the space headings reserve. A heading always starts a new row
    and moves to the next page when no row (or heading) would fit after it. Pages are only created when something is drawn on them, so
    leading, trailing, or repeated page breaks never produce blank pages.

    Args:
        voicings: Chord voicings, headings, and PAGE_BREAK sentinels.
        cols: Diagrams per row.
        rows: Rows per page.

    Returns:
        List of pages; each page is a list of heading voicings and rows
        (lists of chord voicings), in drawing order.
    """
    pages: list[list] = []
    page: list | None = None
    row: list | None = None
    page_rows = 0
    page_headings = 0

    for voicing in voicings:
        if voicing is PAGE_BREAK:
            page = None  # the next item starts a fresh page
            continue

        heading = is_heading(voicing)
        needs_row = not heading and (row is None or len(row) >= cols)
        page_full = (
            (heading or needs_row) and page_rows >= rows
            or heading and page_headings >= rows
        )
        if page is None or page_full:
            page = []
            pages.append(page)
            row = None
            page_rows = 0
            page_headings = 0

        if heading:
            page.append(voicing)
            page_headings += 1
            row = None
            continue

        if row is None or len(row) >= cols:
            row = []
            page.append(row)
            page_rows += 1
        row.append(voicing)

    return pages or [[]]


def generate_pdf(
    voicings: list[Voicing],
    output_path: str | os.PathLike[str] | BinaryIO = "chords.pdf",
    title: str = "",
    paper: str = "a4",
    cols: int = 4,
    rows: int = 4,
    show_root: bool = False,
    no_fingers: bool = False,
    tuning: str = "standard",
) -> str | os.PathLike[str] | BinaryIO:
    """
    Generate a PDF with chord diagrams laid out in a grid.

    Args:
        voicings: List of Voicing objects to render.
        output_path: Output file path, or a binary file object (e.g.
            io.BytesIO) to write the PDF to.
        title: Optional title for the first page.
        paper: Paper size ("letter" or "a4").
        cols: Number of columns per page.
        rows: Number of rows per page.
        show_root: Show the "Root" inversion label.
        no_fingers: Hide finger numbers inside the fret dots.
        tuning: Tuning name for string label display.

    Returns:
        output_path, as given.

    Raises:
        ValueError: If the grid is empty or headings leave no room for rows.
    """
    if cols < 1 or rows < 1:
        raise ValueError("cols and rows must be at least 1")

    page_size = PAGE_SIZES.get(paper.lower(), A4)
    page_width, page_height = page_size

    string_labels = display_labels(tuning)

    pages = _paginate(voicings, cols, rows)

    # Calculate available space
    usable_width = page_width - MARGIN_LEFT - MARGIN_RIGHT
    usable_height = page_height - MARGIN_TOP - MARGIN_BOTTOM

    # Reserve room for the title and for the most headings any page has,
    # so every page fits all its rows at one consistent diagram size.
    reserved = max(
        (TITLE_HEIGHT if title and i == 0 else 0)
        + HEADING_HEIGHT * sum(1 for entry in page if not isinstance(entry, list))
        for i, page in enumerate(pages)
    )

    # Calculate cell size (space allocated to each diagram)
    cell_width = usable_width / cols
    cell_height = (usable_height - reserved) / rows
    if cell_height <= 0:
        raise ValueError("Too many headings on one page to fit any chords")

    # Scale factor to fit diagram into cell
    scale_x = cell_width / DIAGRAM_WIDTH
    scale_y = cell_height / DIAGRAM_HEIGHT
    scale = min(scale_x, scale_y) * 0.98  # slight margin within cell

    # Center the diagram within the cell
    x_offset = (cell_width - DIAGRAM_WIDTH * scale) / 2
    y_offset = (cell_height - DIAGRAM_HEIGHT * scale) / 2

    target = (output_path if hasattr(output_path, "write")
              else os.fspath(output_path))
    c = canvas.Canvas(target, pagesize=page_size)
    c.setTitle(title or "Ukulele Chord Diagrams")
    c.setAuthor("uke-chords-print")

    for page_num, page in enumerate(pages):
        if page_num > 0:
            c.showPage()

        # y is the top of the next heading or row
        y = page_height - MARGIN_TOP
        if title and page_num == 0:
            # Long titles shrink to fit between the side margins
            draw_centred(
                c, page_width / 2, y - 0.75 * TITLE_FONT_SIZE, title,
                "Helvetica-Bold",
                fit_font_size(
                    title, "Helvetica-Bold", TITLE_FONT_SIZE, usable_width
                ),
            )
            y -= TITLE_HEIGHT

        # Page number footer
        c.setFont("Helvetica", 8)
        c.drawCentredString(
            page_width / 2,
            FOOTER_Y,
            f"Page {page_num + 1}",
        )

        for entry in page:
            # Section heading -- full-width line, compact height
            if not isinstance(entry, list):
                draw_centred(
                    c, page_width / 2, y - HEADING_HEIGHT + 2 * mm,
                    entry.notes, "Helvetica-Bold",
                    fit_font_size(
                        entry.notes, "Helvetica-Bold", HEADING_FONT_SIZE,
                        usable_width,
                    ),
                )
                y -= HEADING_HEIGHT
                continue

            # Row of chord diagrams
            for col, voicing in enumerate(entry):
                drawing = draw_chord_diagram(
                    displayed(voicing, show_root, not no_fingers),
                    string_labels=string_labels,
                )

                c.saveState()
                c.translate(
                    MARGIN_LEFT + col * cell_width + x_offset,
                    y - cell_height + y_offset,
                )
                c.scale(scale, scale)
                renderPDF.draw(drawing, c, 0, 0)
                c.restoreState()

            y -= cell_height

    c.save()
    return output_path
