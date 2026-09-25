"""
Public API for using uke_chords_print as a library.

Everything here is re-exported from the package root and listed in its
__all__; that is the stable interface. The other modules are internal and
may change between releases.

Importing the package registers a few chord types pychord lacks (maj7b5,
mM9, ...) with pychord's shared quality table, so other code in the same
process that uses pychord sees them too.
"""

from __future__ import annotations

import os
from collections.abc import Iterable
from typing import BinaryIO

from reportlab.graphics import renderSVG
from reportlab.graphics.shapes import Drawing

from .diagram import displayed, draw_chord_diagram
from .parser import (
    PAGE_BREAK,
    Voicing,
    _explicit_voicing,
    _parse_options,
    make_heading,
    parse_file,
    parse_lines,
    validate_frets,
    voicing_from_entry,
)
from .pdf_generator import PAGE_SIZES, generate_pdf
from .tunings import display_labels, get_tuning
from .voicing_gen import generate_voicings


def voicings(
    name: str, tuning: str = "standard", limit: int = 3
) -> list[Voicing]:
    """Generate playable voicings for a chord, easiest first.

    Args:
        name: Chord name, e.g. "Am7", "C/G", "Bbmaj7", "C°".
        tuning: Tuning name or alias ("standard", "low-g", "baritone",
            "d-tuning", ...).
        limit: Most voicings to return.

    Returns:
        Up to limit voicings (empty if no shape fits frets 0-9 with a
        3-fret span).

    Raises:
        ValueError: For an unknown chord name or tuning, or limit < 1.
    """
    if limit < 1:
        raise ValueError("limit must be at least 1")
    entries = generate_voicings(name, tuning=tuning, max_results=limit)
    return [voicing_from_entry(name, entry) for entry in entries]


def voicing(
    name: str,
    frets: str,
    *,
    fingers: str | None = None,
    notes: str | None = None,
    inversion: str | None = None,
    starting_fret: int | None = None,
    tuning: str = "standard",
) -> Voicing:
    """Build a voicing for a fret shape you choose.

    Omitted notes, inversion and starting_fret are worked out from the
    chord name and tuning (a name that isn't a chord, like "N.C.", just
    gets no note labels).

    Args:
        name: Chord name shown above the diagram.
        frets: One character per string in tuning order: 0 open, 1-9 fret,
            X muted (e.g. "0003").
        fingers: One character per string: 1-4, or 0/_ for no finger.
        notes: Space-separated note names, one per string ("-" if muted).
        inversion: Inversion label.
        starting_fret: First fret the diagram shows.
        tuning: Tuning the shape is played in.

    Returns:
        The voicing.

    Raises:
        ValueError: If any value is invalid (same rules as chord files).
    """
    if not validate_frets(frets):
        raise ValueError(
            f"Invalid frets '{frets}'. Expected 4 characters (digits or X)."
        )
    options = [
        f"{key}={value}"
        for key, value in (
            ("fingers", fingers), ("notes", notes), ("inversion", inversion),
            ("starting_fret", starting_fret),
        )
        if value is not None
    ]
    kwargs = _parse_options(options)
    return _explicit_voicing(name, frets, kwargs, get_tuning(tuning).name)


def heading(text: str) -> Voicing:
    """A section heading to put between voicings in render_pdf.

    Raises:
        ValueError: If text is empty.
    """
    if not text.strip():
        raise ValueError("Heading text is empty")
    return make_heading(text.strip())


def parse_sheet(
    text: str, *, tuning: str = "standard", single: bool = False
) -> list[Voicing]:
    """Parse chord-file text (the --file format) into voicings.

    The result can include headings and PAGE_BREAK, ready for render_pdf.
    Lines that are kept as written with a caveat issue ChordWarning.

    Args:
        text: File contents: chord names, explicit shapes, "= headings",
            "---" page breaks, "@tuning" lines and comments.
        tuning: Tuning to print in.
        single: Keep only the easiest voicing of each named chord.

    Returns:
        Voicings, headings and page breaks in file order.

    Raises:
        ValueError: On a malformed line, prefixed with its line number.
    """
    return parse_lines(
        text.removeprefix("﻿").splitlines(), single=single, tuning=tuning
    )


def read_sheet(
    path: str | os.PathLike[str],
    *,
    tuning: str = "standard",
    single: bool = False,
) -> list[Voicing]:
    """Read a chord file (UTF-8) into voicings; see parse_sheet.

    Raises:
        OSError: If the file can't be read.
        ValueError: On a malformed line, prefixed with its line number.
    """
    return parse_file(path, single=single, tuning=tuning)


def diagram(
    voicing: Voicing,
    tuning: str = "standard",
    *,
    show_root: bool = False,
    show_fingers: bool = True,
) -> Drawing:
    """Draw one chord diagram as a ReportLab Drawing.

    Render it with reportlab.graphics (renderPDF, renderPM for PNG,
    renderSVG), or use diagram_svg.

    Args:
        voicing: The voicing to draw.
        tuning: Tuning, for the string names shown on every tuning except
            standard.
        show_root: Show a "Root" inversion label.
        show_fingers: Show finger numbers inside the dots.

    Returns:
        A Drawing in points, about 136 x 238.
    """
    return draw_chord_diagram(
        displayed(voicing, show_root, show_fingers),
        string_labels=display_labels(tuning),
    )


def diagram_svg(
    voicing: Voicing,
    tuning: str = "standard",
    *,
    show_root: bool = False,
    show_fingers: bool = True,
) -> str:
    """Draw one chord diagram as an SVG document; see diagram.

    Text outside Windows-1252 names the bundled fonts, which a browser
    may not have, so it can fall back to another font there.
    """
    return renderSVG.drawToString(diagram(
        voicing, tuning, show_root=show_root, show_fingers=show_fingers,
    ))


def render_pdf(
    items: Iterable[Voicing],
    output: str | os.PathLike[str] | BinaryIO = "chords.pdf",
    *,
    title: str = "",
    paper: str = "a4",
    cols: int = 4,
    rows: int = 4,
    tuning: str = "standard",
    show_root: bool = False,
    show_fingers: bool = True,
) -> None:
    """Lay out voicings as a printable PDF, like the command line does.

    Args:
        items: Voicings, headings (see heading) and PAGE_BREAK, in order.
        output: File path, or a binary file object such as io.BytesIO.
        title: Title at the top of the first page.
        paper: "a4" or "letter".
        cols: Diagrams per row.
        rows: Rows per page.
        tuning: Tuning, for the string names on diagrams.
        show_root: Show "Root" inversion labels.
        show_fingers: Show finger numbers inside the dots.

    Raises:
        ValueError: For an unknown paper size or tuning, a grid under 1x1,
            or too many headings on one page.
    """
    if paper.lower() not in PAGE_SIZES:
        raise ValueError(
            f"Unknown paper '{paper}'. Valid options: "
            f"{', '.join(sorted(PAGE_SIZES))}"
        )
    get_tuning(tuning)
    generate_pdf(
        list(items), output, title=title, paper=paper, cols=cols, rows=rows,
        show_root=show_root, no_fingers=not show_fingers, tuning=tuning,
    )


__all__ = [
    "PAGE_BREAK",
    "Voicing",
    "diagram",
    "diagram_svg",
    "heading",
    "parse_sheet",
    "read_sheet",
    "render_pdf",
    "voicing",
    "voicings",
]
