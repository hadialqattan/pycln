"""Test `tests/utils/std.py`."""
import sys

from . import std


class TestSTD:
    def test_redirect_stdout(self):
        # Test `redirect` function.
        with std.redirect(std.STD.OUT) as stdout:
            out = "Test stdout.\n"
            print(out, end="", file=sys.stdout)
            assert stdout.getvalue() == out

    def test_redirect_stderr(self):
        # Test `redirect` function.
        with std.redirect(std.STD.ERR) as stderr:
            err = "Test stderr.\n"
            print(err, end="", file=sys.stderr)
            assert stderr.getvalue() == err
