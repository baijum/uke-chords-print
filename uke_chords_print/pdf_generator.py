"""
Lay out chord diagrams in a grid on printable pages and generate PDF.

Supports US Letter and A4 page sizes with configurable grid dimensions.
"""

from __future__ import annotations

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import mm, inch
from reportlab.pdfgen import canvas
from reportlab.graphics import renderPDF

from .parser import ChordVoicing, PAGE_BREAK, is_heading
from .diagram import draw_chord_diagram, DIAGRAM_WIDTH, DIAGRAM_HEIGHT

# Page margins
MARGIN_TOP = 0.3 * inch
MARGIN_BOTTOM = 0.4 * inch
MARGIN_LEFT = 0.25 * inch
MARGIN_RIGHT = 0.25 * inch

# Title area
TITLE_HEIGHT = 0.15 * inch
TITLE_FONT_SIZE = 16

# Section heading
HEADING_FONT_SIZE = 14
HEADING_HEIGHT = 0.25 * inch

PAGE_SIZES = {
    "letter": letter,
    "a4": A4,
}


def generate_pdf(
    voicings: list[ChordVoicing],
    output_path: str = "chords.pdf",
    title: str = "",
    paper: str = "letter",
    cols: int = 4,
    rows: int = 5,
    show_root: bool = False,
    no_fingers: bool = False,
) -> str:
    """
    Generate a PDF with chord diagrams laid out in a grid.

    Args:
        voicings: List of ChordVoicing objects to render.
        output_path: Output PDF file path.
        title: Optional title for the first page.
        paper: Paper size ("letter" or "a4").
        cols: Number of columns per page.
        rows: Number of rows per page.

    Returns:
        The output file path.
    """
    page_size = PAGE_SIZES.get(paper.lower(), letter)
    page_width, page_height = page_size

    # Calculate available space
    usable_width = page_width - MARGIN_LEFT - MARGIN_RIGHT
    usable_height = page_height - MARGIN_TOP - MARGIN_BOTTOM

    # Calculate cell size (space allocated to each diagram)
    cell_width = usable_width / cols
    cell_height = usable_height / rows

    # Scale factor to fit diagram into cell
    scale_x = cell_width / DIAGRAM_WIDTH
    scale_y = cell_height / DIAGRAM_HEIGHT
    scale = min(scale_x, scale_y) * 0.98  # slight margin within cell

    c = canvas.Canvas(output_path, pagesize=page_size)
    c.setTitle(title or "Ukulele Chord Diagrams")
    c.setAuthor("uke-chords-print")

    page_num = 0
    cur_col = 0
    cur_row = 0
    title_offset = 0
    heading_offset = 0.0   # extra vertical offset from headings

    def _start_page():
        """Begin a new page and draw its header / footer."""
        nonlocal page_num, cur_col, cur_row, title_offset, heading_offset
        if page_num > 0:
            c.showPage()

        title_offset = 0
        if title and page_num == 0:
            c.setFont("Helvetica-Bold", TITLE_FONT_SIZE)
            c.drawCentredString(
                page_width / 2,
                page_height - MARGIN_TOP + 2 * mm,
                title,
            )
            title_offset = TITLE_HEIGHT

        # Page number footer
        c.setFont("Helvetica", 8)
        c.drawCentredString(
            page_width / 2,
            MARGIN_BOTTOM / 4,
            f"Page {page_num + 1}",
        )

        cur_col = 0
        cur_row = 0
        heading_offset = 0.0
        page_num += 1

    def _cursor_y() -> float:
        """Return the y coordinate for the top of the current row."""
        return (page_height - MARGIN_TOP - title_offset
                - cur_row * cell_height - heading_offset)

    def _remaining_height() -> float:
        """Return the usable height left on the current page."""
        return _cursor_y() - MARGIN_BOTTOM

    # --- Start first page ---
    _start_page()

    for voicing in voicings:
        # Page break sentinel
        if voicing is PAGE_BREAK:
            _start_page()
            continue

        # Section heading -- full-width line, compact height
        if is_heading(voicing):
            # If we're partway through a row, move to the next row first
            if cur_col > 0:
                cur_row += 1
                cur_col = 0

            # Need a new page if there's no room for heading + at least one row
            if _remaining_height() < HEADING_HEIGHT + cell_height:
                _start_page()

            y_top = _cursor_y()
            c.setFont("Helvetica-Bold", HEADING_FONT_SIZE)
            c.drawCentredString(
                page_width / 2,
                y_top - HEADING_HEIGHT + 2 * mm,
                voicing.notes,
            )

            # Only consume the compact heading height, not a full row
            heading_offset += HEADING_HEIGHT
            cur_col = 0
            continue

        # --- Normal chord diagram ---

        # New page if not enough room for another row
        if _remaining_height() < cell_height:
            _start_page()

        x = MARGIN_LEFT + cur_col * cell_width
        y = _cursor_y()

        # Center the diagram within the cell
        x_offset = (cell_width - DIAGRAM_WIDTH * scale) / 2
        y_offset = (cell_height - DIAGRAM_HEIGHT * scale) / 2

        # Hide "Root" inversion label unless --show-root is set
        if not show_root and voicing.inversion == "Root":
            voicing.inversion = ""

        # Hide finger numbers inside dots when --no-fingers is set
        if no_fingers:
            voicing.fingers = ""

        drawing = draw_chord_diagram(voicing)

        draw_x = x + x_offset
        draw_y = y - cell_height + y_offset

        c.saveState()
        c.translate(draw_x, draw_y)
        c.scale(scale, scale)
        renderPDF.draw(drawing, c, 0, 0)
        c.restoreState()

        # Advance cursor
        cur_col += 1
        if cur_col >= cols:
            cur_col = 0
            cur_row += 1

    c.save()
    return output_path
