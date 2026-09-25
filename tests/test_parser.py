"""Parsing CLI arguments, chord files, options and directives."""

from __future__ import annotations

import pytest

from uke_chords_print.parser import (
    PAGE_BREAK,
    ChordVoicing,
    ChordWarning,
    _strip_comment,
    is_heading,
    make_heading,
    parse_cli_arg,
    parse_cli_args,
    parse_file,
    parse_file_line,
    validate_frets,
)
from uke_chords_print.voicing_gen import generate_voicings


@pytest.fixture
def chord_file(tmp_path):
    """Write lines to a chord file and return its path."""
    def write(text: str, encoding: str = "utf-8") -> str:
        path = tmp_path / "chords.txt"
        path.write_text(text, encoding=encoding)
        return str(path)
    return write


class TestComments:
    @pytest.mark.parametrize("line, expected", [
        ("C  # comment", "C"),
        ("C\t#", "C"),
        ("C#", "C#"),
        ("C#m7 # sharp chord", "C#m7"),
        ("= Track #1", "= Track #1"),
        ("C #note", "C #note"),
        ("  Am  ", "Am"),
        ("# whole line", "# whole line"),
    ])
    def test_strip_comment(self, line, expected):
        assert _strip_comment(line) == expected

    @pytest.mark.parametrize("line", ["", "   ", "# comment", "#", "\n"])
    def test_ignored_lines(self, line):
        assert parse_file_line(line) == []


class TestFileLines:
    @pytest.mark.parametrize("name", ["Am", "C#m7", "F", "Cdim"])
    def test_chord_name_gives_generated_voicings(self, name):
        # Every field of the generated voicing reaches the diagram
        voicings = parse_file_line(name)
        assert voicings == [
            ChordVoicing(
                name=name, frets=v["frets"], fingers=v["fingers"],
                notes=v["notes"], inversion=v["inversion"],
                starting_fret=v.get("starting_fret", 1),
            )
            for v in generate_voicings(name)
        ]
        assert any(v.starting_fret > 1 for v in parse_file_line("Cdim"))

    def test_single(self):
        assert len(parse_file_line("Am", single=True)) == 1

    def test_page_break(self):
        assert parse_file_line("---") == [PAGE_BREAK]
        assert parse_file_line("---  # new page") == [PAGE_BREAK]

    def test_heading(self):
        [heading] = parse_file_line("= Verse  # comment")
        assert is_heading(heading)
        assert heading.notes == "Verse"

    def test_heading_without_space(self):
        [heading] = parse_file_line("=Intro")
        assert is_heading(heading)
        assert heading.notes == "Intro"

    @pytest.mark.parametrize("line", ["=", "= ", "=   # comment"])
    def test_empty_heading(self, line):
        with pytest.raises(ValueError, match="^Heading text missing after '='$"):
            parse_file_line(line)

    def test_explicit_voicing_fills_labels(self):
        [v] = parse_file_line("C, 0003")
        assert v == ChordVoicing(
            name="C", frets="0003", notes="G C E C", inversion="Root",
            starting_fret=1,
        )

    def test_explicit_options(self):
        [v] = parse_file_line(
            "Bb, 3211, fingers=3211, notes=x y z w, inversion=Custom"
        )
        assert v.fingers == "3211"
        assert v.notes == "x y z w"
        assert v.inversion == "Custom"

    def test_trailing_comma_ignored(self):
        [v] = parse_file_line("C, 0003, fingers=0003,")
        assert v.fingers == "0003"

    def test_empty_option_between_others_skipped(self):
        [v] = parse_file_line("C, 0003,, fingers=0003")
        assert v.fingers == "0003"

    def test_option_value_may_contain_equals(self):
        [v] = parse_file_line("C, 0003, inversion=Root=I")
        assert v.inversion == "Root=I"

    def test_notes_given_inversion_worked_out(self):
        [v] = parse_file_line("C, 0003, notes=w x y z")
        assert (v.notes, v.inversion) == ("w x y z", "Root")

    def test_inversion_given_notes_worked_out(self):
        [v] = parse_file_line("C, 0003, inversion=Custom")
        assert (v.notes, v.inversion) == ("G C E C", "Custom")

    def test_starting_fret_one_is_valid(self):
        [v] = parse_file_line("C, 0003, starting_fret=1")
        assert v.starting_fret == 1

    def test_unknown_option_lists_valid_ones(self):
        with pytest.raises(ValueError) as exc:
            parse_file_line("C, 0003, color=red")
        assert str(exc.value) == (
            "Unknown option 'color'. "
            "Valid options: fingers, starting_fret, notes, inversion"
        )

    def test_muted_string(self):
        [v] = parse_file_line("C, X003")
        assert v.frets == "X003"
        assert v.notes == "- C E C"

    def test_starting_fret_derived(self):
        [v] = parse_file_line("C, 5433")
        assert v.starting_fret == 3

    def test_starting_fret_given(self):
        [v] = parse_file_line("C, 5433, starting_fret=2")
        assert v.starting_fret == 2

    def test_unknown_chord_name_draws_without_labels(self):
        [v] = parse_file_line("Mystery chord, 0003")
        assert v.notes == ""
        assert v.inversion == ""

    def test_labels_follow_tuning(self):
        [v] = parse_file_line("G, 0003", tuning="baritone")
        assert v.notes == "D G B G"

    @pytest.mark.parametrize("line, message", [
        ("C, 003", "Invalid frets"),
        ("C, 00a3", "Invalid frets"),
        ("C, 00003", "Invalid frets"),
        ("C, 000³", "Invalid frets"),         # non-ASCII digits
        ("C, 000٣", "Invalid frets"),
        ("C, 0003, fingers", "Expected key=value"),
        ("C, 0003, finger=0003", "Unknown option 'finger'"),
        ("C, 0003, fingers=003", "Invalid fingers"),
        ("C, 0003, fingers=0005", "Invalid fingers"),
        ("C, 0003, fingers=000X", "Invalid fingers"),
        ("C, 0003, starting_fret=0", "Invalid starting_fret"),
        ("C, 0003, starting_fret=x", "Invalid starting_fret"),
        ("C, 0003, starting_fret=²", "Invalid starting_fret"),
        ("C, 0019", "don't fit the 4 frets"),
        ("C, 5433, starting_fret=4", "don't fit the 4 frets"),
        ("C, 1006", "don't fit the 4 frets"),
        ("C, 0005, starting_fret=1", "don't fit the 4 frets"),  # 1-4 shown
        ("C, 1000, starting_fret=2", "don't fit the 4 frets"),  # below
    ])
    def test_invalid_explicit_voicings(self, line, message):
        with pytest.raises(ValueError, match=message):
            parse_file_line(line)

    def test_unknown_chord_lookup(self):
        with pytest.raises(ValueError, match="Use --list"):
            parse_file_line("Cxyz")

    def test_unplayable_chord_lookup(self):
        with pytest.raises(ValueError, match="No playable voicing"):
            parse_file_line("Fmaj9", tuning="d-tuning")


class TestCliArgs:
    def test_name(self):
        assert parse_cli_arg("G7", single=True)[0].frets == "0212"

    def test_explicit(self):
        [v] = parse_cli_arg("F:2010:fingers=2010")
        assert (v.name, v.frets, v.fingers) == ("F", "2010", "2010")
        assert v.notes == "A C F A"

    def test_notes_option_with_spaces(self):
        [v] = parse_cli_arg("C:0003:notes=G C E C")
        assert v.notes == "G C E C"

    def test_invalid_frets(self):
        with pytest.raises(ValueError, match="Invalid frets"):
            parse_cli_arg("C:03")

    def test_bad_option(self):
        with pytest.raises(ValueError, match="Unknown option"):
            parse_cli_arg("C:0003:finger=0003")

    def test_many(self):
        voicings = parse_cli_args(["C", "G:0232"], single=True)
        assert [v.frets for v in voicings] == ["0003", "0232"]

    def test_tuning(self):
        [v] = parse_cli_arg("G", single=True, tuning="baritone")
        assert v.frets == "0003"

    def test_all_voicings_by_default(self):
        assert len(parse_cli_arg("C")) == 3
        assert len(parse_cli_args(["C"])) == 3

    def test_explicit_labels_follow_tuning(self):
        [v] = parse_cli_arg("G:0003", tuning="baritone")
        assert v.notes == "D G B G"
        [v] = parse_cli_args(["G:0003"], tuning="baritone")
        assert v.notes == "D G B G"


class TestParseFile:
    def test_mixed_content(self, chord_file):
        path = chord_file(
            "# Title\n"
            "= Intro\n"
            "C\n"
            "G, 0232, fingers=0132  # pinned\n"
            "---\n"
            "\n"
            "Am7\n"
        )
        voicings = parse_file(path, single=True)
        assert [v.name for v in voicings] == [
            "__HEADING__", "C", "G", "__PAGE_BREAK__", "Am7",
        ]
        assert voicings[3] is PAGE_BREAK

    def test_all_voicings_by_default(self, chord_file):
        assert len(parse_file(chord_file("C\n"))) == 3

    def test_byte_order_mark(self, chord_file):
        path = chord_file("C\n", encoding="utf-8-sig")
        assert parse_file(path, single=True)[0].name == "C"

    def test_utf8_heading(self, chord_file):
        path = chord_file("= Première partie ♪\nC\n")
        assert parse_file(path, single=True)[0].notes == "Première partie ♪"

    def test_error_has_line_number(self, chord_file):
        path = chord_file("C\nG\nC, 12\n")
        with pytest.raises(ValueError, match=r"^Line 3: Invalid frets"):
            parse_file(path)

    def test_missing_file(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            parse_file(str(tmp_path / "nope.txt"))


class TestTuningDirective:
    FILE = (
        "@tuning standard\n"
        "E, 1402, fingers=1403\n"
        "E, 4442, fingers=2341\n"
        "C, 0003\n"
    )

    def test_compatible_tuning_keeps_explicit_shapes(self, chord_file):
        voicings = parse_file(chord_file(self.FILE), tuning="low-g")
        assert [v.frets for v in voicings] == ["1402", "4442", "0003"]
        assert voicings[0].fingers == "1403"

    def test_other_tuning_regenerates_distinct_shapes(self, chord_file):
        voicings = parse_file(chord_file(self.FILE), tuning="baritone")
        expected_e = [v["frets"] for v in generate_voicings(
            "E", tuning="baritone")]
        assert [v.frets for v in voicings[:2]] == expected_e[:2]
        assert voicings[2].frets == generate_voicings(
            "C", tuning="baritone")[0]["frets"]
        assert all(v.name in ("E", "C") for v in voicings)

    def test_directive_applies_to_lines_below(self, chord_file):
        path = chord_file("C, 0003\n@tuning standard\nC, 0003\n")
        voicings = parse_file(path, tuning="baritone")
        assert voicings[0].frets == "0003"
        assert voicings[1].frets == generate_voicings(
            "C", tuning="baritone")[0]["frets"]

    def test_repeated_shape_keeps_its_replacement(self, chord_file):
        # A song pins C 0003 in every section: one replacement throughout,
        # while the two different E shapes stay distinct
        path = chord_file(
            "@tuning standard\n"
            "C, 0003\nE, 1402\nC, 0003\nE, 4442\nC, 0003\nE, 1402\n"
        )
        voicings = parse_file(path, tuning="baritone")
        c_shapes = {v.frets for v in voicings if v.name == "C"}
        e_shapes = [v.frets for v in voicings if v.name == "E"]
        assert len(c_shapes) == 1
        assert e_shapes[0] != e_shapes[1]
        assert e_shapes[2] == e_shapes[0]

    @pytest.mark.parametrize("frets", ["XXXX", "xxxx", "xXxX"])
    def test_all_muted_shape_kept(self, chord_file, recwarn, frets):
        path = chord_file(f"@tuning standard\nN.C., {frets}\n")
        [v] = parse_file(path, tuning="baritone")
        assert (v.name, v.frets) == ("N.C.", frets)
        assert not recwarn.list

    def test_muted_letter_case_is_one_shape(self, chord_file):
        path = chord_file("@tuning standard\nC, X003\nC, x003\n")
        first, second = parse_file(path, tuning="baritone")
        assert first.frets == second.frets

    def test_more_shapes_than_voicings_reuse_the_easiest(self, chord_file):
        # Cdim has a single baritone voicing: every pinned shape gets it
        assert len(generate_voicings("Cdim", tuning="baritone")) == 1
        path = chord_file("@tuning standard\nCdim, 5323\nCdim, 8089\n")
        first, second = parse_file(path, tuning="baritone")
        assert first.frets == second.frets

    def test_non_chord_name_kept_with_warning(self, chord_file):
        path = chord_file(
            "@tuning standard\nC\nMy riff, 0003, notes=G C E C\n"
        )
        with pytest.warns(ChordWarning, match=(
                r"^Line 3: 'My riff' isn't a chord name, so its standard "
                r"shape 0003 is printed as written$")):
            voicings = parse_file(path, single=True, tuning="baritone")
        riff = voicings[1]
        assert riff.frets == "0003"
        assert riff.notes == ""  # standard-tuning labels are dropped

    def test_kept_shape_drops_pinned_inversion(self, chord_file):
        path = chord_file("@tuning standard\nFmaj9, 0000, inversion=Root\n")
        with pytest.warns(ChordWarning):
            [v] = parse_file(path, tuning="d-tuning")
        assert v.inversion == ""  # worked out for D tuning: B isn't in Fmaj9

    def test_unplayable_chord_kept_with_warning(self, chord_file):
        path = chord_file("@tuning standard\nFmaj9, 0000\n")
        with pytest.warns(ChordWarning, match="no playable d-tuning voicing"):
            [v] = parse_file(path, tuning="d-tuning")
        assert v.frets == "0000"
        assert v.notes == "A D Gb B"  # labelled for the tuning printed

    def test_other_warnings_pass_through(self, chord_file, monkeypatch):
        from uke_chords_print import parser

        original = parser.parse_file_line

        def noisy(line, **kwargs):
            import warnings
            warnings.warn("from a dependency", DeprecationWarning)
            return original(line, **kwargs)

        monkeypatch.setattr(parser, "parse_file_line", noisy)
        with pytest.warns(DeprecationWarning, match="^from a dependency$"):
            parse_file(chord_file("C\n"), single=True)

    def test_line_without_file_bookkeeping(self):
        # parse_file_line alone (no fallback_shapes) still converts
        [v] = parse_file_line("C, 0003", tuning="baritone",
                              voicing_tuning="standard")
        assert v.frets == generate_voicings("C", tuning="baritone")[0]["frets"]

    def test_alias_and_comment(self, chord_file):
        path = chord_file("@tuning gcea  # shapes below\nC, 0003\n")
        assert parse_file(path, tuning="d-tuning")[0].frets != "0003"

    def test_options_checked_under_any_tuning(self, chord_file):
        path = chord_file("@tuning standard\nC, 0003, finger=3\n")
        with pytest.raises(ValueError, match="Line 2: Unknown option"):
            parse_file(path, tuning="baritone")

    @pytest.mark.parametrize("line, message", [
        ("@tuning", "Expected '@tuning <name>'"),
        ("@tuning standard low-g", "Expected '@tuning <name>'"),
        ("@tuning banjo", "Unknown tuning"),
    ])
    def test_bad_directive(self, chord_file, line, message):
        with pytest.raises(ValueError, match=f"Line 1: {message}"):
            parse_file(chord_file(line + "\n"))


class TestHelpers:
    @pytest.mark.parametrize("frets, ok", [
        ("0003", True), ("X003", True), ("xx00", True), ("9999", True),
        ("003", False), ("00003", False), ("00-3", False), ("", False),
    ])
    def test_validate_frets(self, frets, ok):
        assert validate_frets(frets) is ok

    def test_heading_sentinel(self):
        heading = make_heading("Chorus")
        assert is_heading(heading)
        assert not is_heading(ChordVoicing(name="C", frets="0003"))
        assert not is_heading(PAGE_BREAK)
