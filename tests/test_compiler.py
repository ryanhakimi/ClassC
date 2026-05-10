import os
import subprocess
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import compiler


def _write(source):
    f = tempfile.NamedTemporaryFile("w", suffix=".classc", delete=False)
    f.write(source)
    f.close()
    return f.name


def _invoke(monkeypatch, argv):
    """Call compiler.main() with the given argv. Returns the SystemExit code
    (None if the call returned normally)."""
    monkeypatch.setattr(sys, "argv", ["compiler.py"] + argv)
    try:
        compiler.main()
        return None
    except SystemExit as e:
        return e.code


def test_tokens_command(monkeypatch, capsys):
    path = _write("(println 1)")
    try:
        rc = _invoke(monkeypatch, ["tokens", path])
    finally:
        os.unlink(path)
    out = capsys.readouterr().out
    assert rc is None
    assert "PRINTLN" in out
    assert "INTEGER_LITERAL" in out


def test_parse_command(monkeypatch, capsys):
    path = _write("(println 1)")
    try:
        rc = _invoke(monkeypatch, ["parse", path])
    finally:
        os.unlink(path)
    out = capsys.readouterr().out
    assert rc is None
    assert "Program" in out
    assert "PrintlnExp" in out


def test_typecheck_command_succeeds(monkeypatch, capsys):
    path = _write("(println 1)")
    try:
        rc = _invoke(monkeypatch, ["typecheck", path])
    finally:
        os.unlink(path)
    out = capsys.readouterr().out
    assert rc is None
    assert "Typecheck succeeded" in out


def test_typecheck_command_reports_error_cleanly(monkeypatch, capsys):
    path = _write("(vardec Int x) (println x)")
    try:
        rc = _invoke(monkeypatch, ["typecheck", path])
    finally:
        os.unlink(path)
    out = capsys.readouterr().out
    assert rc == 1
    assert "Error:" in out
    assert "initialized" in out


def test_compile_command_to_stdout(monkeypatch, capsys):
    path = _write("(println 42)")
    try:
        rc = _invoke(monkeypatch, ["compile", path])
    finally:
        os.unlink(path)
    out = capsys.readouterr().out
    assert rc is None
    assert "int main(void)" in out
    assert "ClassC_print_int(42)" in out


def test_compile_command_to_file(monkeypatch):
    src = _write("(println 42)")
    with tempfile.TemporaryDirectory() as tmpdir:
        out_c = os.path.join(tmpdir, "out.c")
        try:
            rc = _invoke(monkeypatch, ["compile", src, out_c])
        finally:
            os.unlink(src)
        assert rc is None
        with open(out_c) as f:
            contents = f.read()
        assert "int main(void)" in contents


def test_unknown_command_reports_usage(monkeypatch, capsys):
    path = _write("(println 1)")
    try:
        rc = _invoke(monkeypatch, ["bogus", path])
    finally:
        os.unlink(path)
    out = capsys.readouterr().out
    assert rc == 1
    assert "Unknown command" in out


def test_missing_file_reports_error(monkeypatch, capsys):
    rc = _invoke(monkeypatch, ["typecheck", "/no/such/file.classc"])
    out = capsys.readouterr().out
    assert rc == 1
    assert "File not found" in out


def test_no_arguments_prints_usage(monkeypatch, capsys):
    rc = _invoke(monkeypatch, [])
    out = capsys.readouterr().out
    assert rc == 1
    assert "Usage:" in out


def test_parse_error_handled_cleanly(monkeypatch, capsys):
    path = _write("(")
    try:
        rc = _invoke(monkeypatch, ["parse", path])
    finally:
        os.unlink(path)
    out = capsys.readouterr().out
    assert rc == 1
    assert "Error:" in out


def test_tokenizer_error_handled_cleanly(monkeypatch, capsys):
    path = _write("@")
    try:
        rc = _invoke(monkeypatch, ["tokens", path])
    finally:
        os.unlink(path)
    out = capsys.readouterr().out
    assert rc == 1
    assert "Error:" in out
