"""
CLI entry point for uke-chords-print.

Usage:
  python -m uke_chords_print C Am G7 F
  python -m uke_chords_print --file my_chords.txt
  python -m uke_chords_print --list
"""

from __future__ import annotations

import argparse
import sys

from .chord_db import list_all_chords, lookup_chord, CHORD_DB
from .parser import parse_cli_args, parse_file, ChordVoicing
from .pdf_generator import generate_pdf


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="uke-chords-print",
        description="Generate printable PDF pages of ukulele chord diagrams.",
        epilog=(
            "Examples:\n"
            "  python -m uke_chords_print C Am G7 F\n"
            "  python -m uke_chords_print \"C:0003\" \"F:2010:fingers=2_1_\"\n"
            "  python -m uke_chords_print --file my_chords.txt\n"
            "  python -m uke_chords_print --list\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "chords",
        nargs="*",
        help="Chord names or name:voicing pairs (e.g., C, Am, \"G:0232\")",
    )
    parser.add_argument(
        "--file", "-f",
        help="Read chords from a text file",
    )
    parser.add_argument(
        "--output", "-o",
        default="chords.pdf",
        help="Output PDF file path (default: chords.pdf)",
    )
    parser.add_argument(
        "--title", "-t",
        default="",
        help="Title printed at the top of the first page",
    )
    parser.add_argument(
        "--paper",
        choices=["letter", "a4"],
        default="a4",
        help="Paper size (default: a4)",
    )
    parser.add_argument(
        "--cols",
        type=int,
        default=4,
        help="Number of columns per page (default: 4)",
    )
    parser.add_argument(
        "--rows",
        type=int,
        default=4,
        help="Number of rows per page (default: 4)",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        dest="list_chords",
        help="List all chords in the built-in database and exit",
    )
    parser.add_argument(
        "--show-root",
        action="store_true",
        dest="show_root",
        help="Show 'Root' inversion label (hidden by default; non-root inversions always show)",
    )
    parser.add_argument(
        "--single",
        action="store_true",
        help="Show only the primary voicing for each chord (default: show all voicings)",
    )

    return parser


def print_chord_list():
    """Print all chords in the built-in database."""
    print("Built-in ukulele chord database:")
    print("=" * 60)

    chords = list_all_chords()
    # Group by type
    for name in chords:
        voicings = CHORD_DB[name]
        count = len(voicings)
        frets_list = ", ".join(v["frets"] for v in voicings)
        suffix = "voicing" if count == 1 else "voicings"
        print(f"  {name:<10s} {count} {suffix:<10s} [{frets_list}]")

    print(f"\nTotal: {len(chords)} chords")


def main(argv: list[str] | None = None):
    parser = build_parser()
    args = parser.parse_args(argv)

    # Handle --list
    if args.list_chords:
        print_chord_list()
        return

    # Collect voicings from all sources
    voicings: list[ChordVoicing] = []

    if args.file:
        try:
            voicings.extend(parse_file(args.file, single=args.single))
        except FileNotFoundError:
            print(f"Error: File not found: {args.file}", file=sys.stderr)
            sys.exit(1)
        except ValueError as e:
            print(f"Error parsing file: {e}", file=sys.stderr)
            sys.exit(1)

    if args.chords:
        try:
            voicings.extend(parse_cli_args(args.chords, single=args.single))
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    if not voicings:
        print("No chords specified. Use chord names, --file, or --list.")
        print("Run with --help for usage information.")
        sys.exit(1)

    # Generate PDF
    try:
        output = generate_pdf(
            voicings=voicings,
            output_path=args.output,
            title=args.title,
            paper=args.paper,
            cols=args.cols,
            rows=args.rows,
            show_root=args.show_root,
        )
        print(f"Generated {len(voicings)} chord diagram(s) -> {output}")
    except Exception as e:
        print(f"Error generating PDF: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
