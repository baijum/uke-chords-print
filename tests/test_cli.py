"""The command-line interface, end to end."""

from __future__ import annotations

import subprocess
import sys

import pytest

from uke_chords_print import __version__, fonts
from uke_chords_print.cli import main

from .support import REPO_ROOT, pdf_page_count, pdf_text


@pytest.fixture
def run(tmp_path, capsys):
    """Run main() and return (exit code, stdout, stderr, output path)."""
    def run(*args: str):
        out = tmp_path / "out.pdf"
        argv = list(args)
        if "-o" not in argv and "--list" not in argv:
            argv += ["-o", str(out)]
        try:
            main(argv)
            code = 0
        except SystemExit as e:
            code = e.code
        captured = capsys.readouterr()
        return code, captured.out, captured.err, out
    return run


def test_defaults():
    from uke_chords_print.cli import build_parser
    args = build_parser().parse_args([])
    assert vars(args) == {
        "chords": [], "files": [], "output": "chords.pdf", "title": "",
        "paper": "a4", "cols": 4, "rows": 4, "list_chords": False,
        "show_root": False, "single": False, "no_fingers": False,
        "tuning": "standard",
    }


def test_short_flags():
    from uke_chords_print.cli import build_parser
    args = build_parser().parse_args(
        ["-f", "a.txt", "--file", "b.txt", "-o", "x.pdf", "-t", "T", "Am"])
    assert (args.files, args.output, args.title, args.chords) == (
        ["a.txt", "b.txt"], "x.pdf", "T", ["Am"])


def test_options_reach_the_pdf(run):
    code, _, _, pdf = run("F:2010:fingers=2010", "G:0003", "C", "--single",
                          "--paper", "letter", "--cols", "1", "--rows", "1",
                          "--no-fingers", "--tuning", "baritone")
    assert code == 0
    data = pdf.read_bytes()
    assert b"/MediaBox [ 0 0 612 792 ]" in data     # letter
    assert pdf_page_count(data) == 3                  # 1 x 1 grid
    text = pdf_text(data)
    assert "(2) Tj" not in text                       # no finger numbers
    assert "(D) Tj" in text and "(B) Tj" in text      # G:0003 in baritone
    assert "\\(D-G-B-E\\)) Tj" in text                 # tuning labels


def test_chord_names(run):
    code, out, err, pdf = run("C", "Am", "G7", "F", "--single")
    assert code == 0
    assert "Generated 4 chord diagram(s)" in out
    assert err == ""
    assert pdf_page_count(pdf.read_bytes()) == 1


def test_all_voicings_by_default(run):
    code, out, _, _ = run("C")
    assert "Generated 3 chord diagram(s)" in out


def test_explicit_voicing_and_options(run):
    code, _, _, pdf = run("C:0003:fingers=0003", "-t", "Title", "--cols", "2",
                          "--rows", "3", "--paper", "letter", "--show-root")
    assert code == 0
    text = pdf_text(pdf.read_bytes())
    assert "(Title) Tj" in text
    assert "(Root) Tj" in text


def test_files_in_order_then_args(run, tmp_path):
    first = tmp_path / "a.txt"
    second = tmp_path / "b.txt"
    first.write_text("= First\nCmaj7\n", encoding="utf-8")
    second.write_text("= Second\nG7\n", encoding="utf-8")
    code, out, _, pdf = run("--file", str(first), "-f", str(second), "Am7",
                            "--single")
    assert code == 0
    assert "Generated 3 chord diagram(s)" in out  # headings aren't counted
    text = pdf_text(pdf.read_bytes())
    order = [text.index(s) for s in ["(First) Tj", "(Cmaj7) Tj",
                                     "(Second) Tj", "(G7) Tj", "(Am7) Tj"]]
    assert order == sorted(order)


@pytest.mark.parametrize("tuning", ["standard", "gcea", "low-g", "baritone",
                                    "dgbe", "d-tuning", "Baritone", "LOW-G",
                                    "ADF#B"])
def test_tunings(run, tuning):
    code, _, _, _ = run("C", "--tuning", tuning)
    assert code == 0


def test_list(run):
    code, out, _, _ = run("--list")
    assert code == 0
    lines = out.splitlines()
    assert lines[0] == ("Built-in ukulele chord database "
                        "[standard (G-C-E-A)]:")
    assert lines[1] == "=" * 60
    assert "  C          3 voicings   [0003, 0403, 0433]" in lines
    assert "  Ddim       1 voicing    [7545]" in lines  # singular
    assert lines[-1] == "Total: 108 chords"
    assert len(lines) == 2 + 108 + 2


def test_list_other_tuning(run):
    _, out, _, _ = run("--list", "--tuning", "baritone")
    assert "[baritone (D-G-B-E)]" in out
    assert "  G          3 voicings   [0003," in out  # baritone shapes


@pytest.mark.parametrize("args, message", [
    ((), "No chords specified"),
    (("Cxyz",), "Error: Cannot parse chord 'Cxyz'"),
    (("C:12",), "Error: Invalid frets"),
    (("--file", "/nonexistent/chords.txt"), "Error: File not found"),
    (("C", "--cols", "0"), "Error generating PDF: cols and rows"),
])
def test_errors_exit_1(run, args, message):
    code, out, err, _ = run(*args)
    assert code == 1
    if args:
        assert message in err and out == ""  # errors go to stderr
    else:
        assert out == ("No chords specified. Use chord names, --file, or "
                       "--list.\nRun with --help for usage information.\n")


def test_headings_only_is_no_chords(run, tmp_path):
    path = tmp_path / "h.txt"
    path.write_text("= Just a heading\n---\n", encoding="utf-8")
    code, out, _, pdf = run("--file", str(path))
    assert code == 1
    assert "No chords specified" in out
    assert not pdf.exists()


def test_file_warnings_are_printed(run, tmp_path):
    path = tmp_path / "song.txt"
    path.write_text("@tuning standard\nC\nMy riff, 0003\n", encoding="utf-8")
    code, out, err, _ = run("--file", str(path), "--tuning", "baritone")
    assert code == 0
    assert (f"Warning: {path}: Line 3: 'My riff' isn't a chord name" in err)
    assert "Generated 4 chord diagram(s)" in out


def test_unreadable_file(run, tmp_path):
    code, _, err, _ = run("--file", str(tmp_path))
    assert code == 1
    assert "Cannot read" in err


def test_file_parse_error(run, tmp_path):
    bad = tmp_path / "bad.txt"
    bad.write_text("C\nC, 12\n", encoding="utf-8")
    code, _, err, _ = run("--file", str(bad))
    assert code == 1
    assert f"Error parsing file {bad}: Line 2: Invalid frets" in err


def test_bad_tuning_rejected_by_argparse(run):
    code, _, err, _ = run("C", "--tuning", "banjo")
    assert code == 2
    assert "invalid choice" in err


def test_warns_about_unprintable_characters(run, monkeypatch):
    monkeypatch.setattr(fonts, "_fc_match", lambda ch, bold: None)
    monkeypatch.setattr(fonts, "_CANDIDATE_FILES", [])
    code, _, err, _ = run("C", "-t", "Song \U0010FFFD\U0010FFFC")
    assert code == 0
    assert err == ("Warning: no available font can show "
                   "\U0010FFFC \U0010FFFD; they print as boxes.\n")


def test_module_entry_point(tmp_path):
    result = subprocess.run(
        [sys.executable, "-m", "uke_chords_print", "--help"],
        cwd=REPO_ROOT, capture_output=True, text=True, check=True,
    )
    assert "usage: uke-chords-print" in result.stdout


# runpy notes that the cli module was already imported; that's expected
@pytest.mark.filterwarnings("ignore:.*found in sys.modules:RuntimeWarning")
@pytest.mark.parametrize("module", ["uke_chords_print",
                                    "uke_chords_print.cli"])
def test_entry_points_in_process(module, monkeypatch, capsys):
    import runpy
    monkeypatch.setattr(sys, "argv", ["uke-chords-print", "--list"])
    runpy.run_module(module, run_name="__main__", alter_sys=True)
    assert "Total: 108 chords" in capsys.readouterr().out


def test_version_is_semver():
    parts = __version__.split(".")
    assert len(parts) == 3 and all(p.isdigit() for p in parts)
