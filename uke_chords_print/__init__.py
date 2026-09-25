"""Ukulele Chord PDF Print Tool - Generate printable chord diagram PDFs.

Use it from the command line (``uke-chords-print`` or
``python -m uke_chords_print``) or as a library::

    import uke_chords_print as ukc

    ukc.voicings("Am7")[0].frets            # '0000'
    ukc.render_pdf(ukc.voicings("C") + ukc.voicings("G"), "sheet.pdf")

The names in __all__ are the stable public API; submodules are internal.
"""

from __future__ import annotations

__version__ = "0.6.0"

from .api import (
    PAGE_BREAK,
    Voicing,
    diagram,
    diagram_svg,
    heading,
    parse_sheet,
    read_sheet,
    render_pdf,
    voicing,
    voicings,
)
from .chord_db import STANDARD_CHORDS
from .parser import ChordWarning
from .tunings import TUNINGS, Tuning, get_tuning

__all__ = [
    "PAGE_BREAK",
    "STANDARD_CHORDS",
    "TUNINGS",
    "ChordWarning",
    "Tuning",
    "Voicing",
    "__version__",
    "diagram",
    "diagram_svg",
    "get_tuning",
    "heading",
    "parse_sheet",
    "read_sheet",
    "render_pdf",
    "voicing",
    "voicings",
]
