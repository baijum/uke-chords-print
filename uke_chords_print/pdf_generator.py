"""
Lay out chord diagrams in a grid on printable pages and generate PDF.

Supports US Letter and A4 page sizes with configurable grid dimensions.
"""

from __future__ import annotations

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import mm, inch
from reportlab.pdfgen import canvas
from reportlab.graphics import renderPDF

from .parser import ChordVoicing
from .diagram import draw_chord_diagram, DIAGRAM_WIDTH, DIAGRAM_HEIGHT

# Page margins
MARGIN_TOP = 0.3 * inch
MARGIN_BOTTOM = 0.4 * inch
MARGIN_LEFT = 0.25 * inch
MARGIN_RIGHT = 0.25 * inch

# Title area
TITLE_HEIGHT = 0.15 * inch
TITLE_FONT_SIZE = 16

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

    chords_per_page = cols * rows

    c = canvas.Canvas(output_path, pagesize=page_size)
    c.setTitle(title or "Ukulele Chord Diagrams")
    c.setAuthor("uke-chords-print")

    total_chords = len(voicings)
    page_num = 0

    for start_idx in range(0, total_chords, chords_per_page):
        if page_num > 0:
            c.showPage()

        page_voicings = voicings[start_idx:start_idx + chords_per_page]

        # Draw title on first page
        title_offset = 0
        if title and page_num == 0:
            c.setFont("Helvetica-Bold", TITLE_FONT_SIZE)
            c.drawCentredString(
                page_width / 2,
                page_height - MARGIN_TOP + 2 * mm,
                title,
            )
            title_offset = TITLE_HEIGHT

        # Draw each chord diagram
        for idx, voicing in enumerate(page_voicings):
            col = idx % cols
            row = idx // cols

            # Position: top-left of this cell
            # ReportLab origin is bottom-left, so we work from top
            x = MARGIN_LEFT + col * cell_width
            y = page_height - MARGIN_TOP - title_offset - row * cell_height

            # Center the diagram within the cell
            x_offset = (cell_width - DIAGRAM_WIDTH * scale) / 2
            y_offset = (cell_height - DIAGRAM_HEIGHT * scale) / 2

            # Draw the diagram
            drawing = draw_chord_diagram(voicing)

            # Render at position (x, y is the top of the cell, but
            # renderPDF.draw uses bottom-left of the drawing)
            draw_x = x + x_offset
            draw_y = y - cell_height + y_offset

            c.saveState()
            c.translate(draw_x, draw_y)
            c.scale(scale, scale)
            renderPDF.draw(drawing, c, 0, 0)
            c.restoreState()

        # Page number footer
        c.setFont("Helvetica", 8)
        c.drawCentredString(
            page_width / 2,
            MARGIN_BOTTOM / 4,
            f"Page {page_num + 1}",
        )

        page_num += 1

    c.save()
    return output_path
