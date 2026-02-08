"""
Draw a single ukulele chord diagram using ReportLab drawing primitives.

The diagram looks like a miniature fretboard:
  - 4 vertical lines (strings: G C E A)
  - Horizontal lines (frets)
  - A thick top line for the nut (open position) or a fret number label
  - Filled circles for fretted positions
  - Open circles for open strings
  - X marks for muted strings
  - Labels: chord name (top), notes (bottom), fingering, inversion
"""

from __future__ import annotations

from reportlab.lib.units import mm
from reportlab.graphics.shapes import (
    Drawing, Line, Circle, String, Group, Rect,
)
from reportlab.graphics import renderPDF
from reportlab.lib.colors import black, white, HexColor

from .parser import ChordVoicing

# --- Layout constants (all in mm, converted to points) ---
# These define the geometry of a single chord diagram.
# Sized for a 3-column x 4-row grid on A4 -- large and readable from a distance.

STRING_SPACING = 12 * mm      # horizontal distance between strings
FRET_SPACING = 12 * mm        # vertical distance between frets
NUM_FRETS = 4                 # frets shown on the diagram
NUM_STRINGS = 4               # G C E A

FRETBOARD_WIDTH = STRING_SPACING * (NUM_STRINGS - 1)   # 36mm
FRETBOARD_HEIGHT = FRET_SPACING * NUM_FRETS             # 48mm

# Padding around the fretboard for labels
PAD_TOP = 16 * mm       # space for chord name + open/mute markers
PAD_BOTTOM = 20 * mm    # space for notes/frets/inversion
PAD_LEFT = 8 * mm       # space for fret numbers
PAD_RIGHT = 4 * mm

DIAGRAM_WIDTH = PAD_LEFT + FRETBOARD_WIDTH + PAD_RIGHT
DIAGRAM_HEIGHT = PAD_TOP + FRETBOARD_HEIGHT + PAD_BOTTOM

DOT_RADIUS = 4.2 * mm
OPEN_RADIUS = 3.2 * mm
NUT_THICKNESS = 2.8 * mm

# Colors
FRET_COLOR = HexColor("#444444")
STRING_COLOR = HexColor("#333333")
DOT_COLOR = HexColor("#2F5233")       # dark green, similar to the app
LABEL_COLOR = black

# Font sizes -- large for readability at a distance
CHORD_NAME_SIZE = 18
FRET_NUM_SIZE = 12
FINGER_SIZE = 11
NOTE_SIZE = 12
FRETS_DISPLAY_SIZE = 14
INVERSION_SIZE = 14


def draw_chord_diagram(voicing: ChordVoicing) -> Drawing:
    """
    Create a ReportLab Drawing for a single chord diagram.

    Returns a Drawing object of size DIAGRAM_WIDTH x DIAGRAM_HEIGHT.
    """
    d = Drawing(DIAGRAM_WIDTH, DIAGRAM_HEIGHT)

    # Origin of the fretboard grid (bottom-left of the fretboard area)
    # In ReportLab, y=0 is at the bottom.
    fb_left = PAD_LEFT
    fb_top = DIAGRAM_HEIGHT - PAD_TOP
    fb_bottom = fb_top - FRETBOARD_HEIGHT

    # --- Draw fretboard background (subtle) ---

    # --- Nut or starting fret indicator ---
    starting_fret = voicing.starting_fret
    is_open_position = (starting_fret <= 1)

    if is_open_position:
        # Draw thick nut line at the top
        d.add(Line(
            fb_left, fb_top, fb_left + FRETBOARD_WIDTH, fb_top,
            strokeColor=STRING_COLOR, strokeWidth=NUT_THICKNESS
        ))
    else:
        # Draw normal top line
        d.add(Line(
            fb_left, fb_top, fb_left + FRETBOARD_WIDTH, fb_top,
            strokeColor=FRET_COLOR, strokeWidth=0.8
        ))
        # Draw fret number label above the fretboard, left-aligned
        fret_label = f"{starting_fret}fr"
        d.add(String(
            fb_left, fb_top + 2 * mm,
            fret_label,
            fontSize=FRET_NUM_SIZE,
            fillColor=LABEL_COLOR,
            textAnchor="start",
            fontName="Helvetica-Bold",
        ))

    # --- Draw horizontal fret lines ---
    for i in range(1, NUM_FRETS + 1):
        y = fb_top - i * FRET_SPACING
        d.add(Line(
            fb_left, y, fb_left + FRETBOARD_WIDTH, y,
            strokeColor=FRET_COLOR, strokeWidth=0.7
        ))

    # --- Draw vertical string lines ---
    for i in range(NUM_STRINGS):
        x = fb_left + i * STRING_SPACING
        d.add(Line(
            x, fb_top, x, fb_bottom,
            strokeColor=STRING_COLOR, strokeWidth=0.8
        ))

    # --- Draw fret numbers along the top ---
    if is_open_position:
        for i in range(NUM_FRETS + 1):
            fret_num = i
            if i == 0:
                x_pos = fb_left - 3 * mm
            else:
                x_pos = fb_left - 3 * mm
            # We'll show fret numbers on the left side for reference
            # Actually, let's show them at the top like in the reference image
            pass  # Fret numbers shown implicitly by position

    # --- Parse frets and draw finger dots / open markers / mutes ---
    frets_str = voicing.frets
    fingers_str = voicing.fingers if voicing.fingers else "____"

    # Pad fingers string if needed
    while len(fingers_str) < 4:
        fingers_str += "_"

    for string_idx in range(NUM_STRINGS):
        x = fb_left + string_idx * STRING_SPACING
        fret_ch = frets_str[string_idx] if string_idx < len(frets_str) else "0"
        finger_ch = fingers_str[string_idx]

        if fret_ch.upper() == "X":
            # Muted string - draw X above the nut
            x_size = 2.6 * mm
            y_marker = fb_top + 5 * mm
            d.add(Line(x - x_size, y_marker - x_size, x + x_size, y_marker + x_size,
                        strokeColor=LABEL_COLOR, strokeWidth=1.4))
            d.add(Line(x - x_size, y_marker + x_size, x + x_size, y_marker - x_size,
                        strokeColor=LABEL_COLOR, strokeWidth=1.4))
        elif fret_ch == "0":
            # Open string - draw open circle above the nut
            y_marker = fb_top + 5 * mm
            d.add(Circle(x, y_marker, OPEN_RADIUS,
                          strokeColor=LABEL_COLOR, strokeWidth=1.2,
                          fillColor=white))
        else:
            # Fretted position - draw filled dot
            fret_num = int(fret_ch)
            if is_open_position:
                display_fret = fret_num
            else:
                display_fret = fret_num - starting_fret + 1

            # Clamp to visible range
            if display_fret < 1:
                display_fret = 1
            if display_fret > NUM_FRETS:
                display_fret = NUM_FRETS

            # Position: center of the fret space
            y_dot = fb_top - (display_fret - 0.5) * FRET_SPACING
            d.add(Circle(x, y_dot, DOT_RADIUS,
                          strokeColor=DOT_COLOR, strokeWidth=0,
                          fillColor=DOT_COLOR))

            # Draw finger number inside the dot (white text)
            if finger_ch not in ("_", "0", " ", ""):
                d.add(String(
                    x, y_dot - FINGER_SIZE / 3,
                    finger_ch,
                    fontSize=FINGER_SIZE,
                    fillColor=white,
                    textAnchor="middle",
                    fontName="Helvetica-Bold",
                ))

    # --- Chord name at the top ---
    d.add(String(
        fb_left + FRETBOARD_WIDTH / 2,
        DIAGRAM_HEIGHT - 4 * mm,
        voicing.name,
        fontSize=CHORD_NAME_SIZE,
        fillColor=LABEL_COLOR,
        textAnchor="middle",
        fontName="Helvetica-Bold",
    ))

    # --- Notes below the fretboard ---
    if voicing.notes:
        note_parts = voicing.notes.split()
        for i, note in enumerate(note_parts):
            if i < NUM_STRINGS:
                x = fb_left + i * STRING_SPACING
                d.add(String(
                    x, fb_bottom - 4 * mm,
                    note,
                    fontSize=NOTE_SIZE,
                    fillColor=LABEL_COLOR,
                    textAnchor="middle",
                    fontName="Helvetica",
                ))

    # --- Frets string below notes ---
    frets_display = " - ".join(frets_str)
    d.add(String(
        fb_left + FRETBOARD_WIDTH / 2,
        fb_bottom - 11 * mm,
        frets_display,
        fontSize=FRETS_DISPLAY_SIZE,
        fillColor=HexColor("#333333"),
        textAnchor="middle",
        fontName="Courier-Bold",
    ))

    # --- Inversion label at the bottom ---
    if voicing.inversion:
        d.add(String(
            fb_left + FRETBOARD_WIDTH / 2,
            fb_bottom - 17 * mm,
            voicing.inversion,
            fontSize=INVERSION_SIZE,
            fillColor=HexColor("#444444"),
            textAnchor="middle",
            fontName="Helvetica-Bold",
        ))

    return d
