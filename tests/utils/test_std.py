"""Test `tests/utils/std.py`."""
import sys

import pytest

from . import std


class TestSTD:

    """`std.py` functions test case."""

    @pytest.mark.parametrize(
        "std_type",
        [
            pytest.param(std.STD.OUT, id="stdout"),
            pytest.param(std.STD.ERR, id="stderr"),
        ],
    )
    def test_redirect(self, std_type):
        with std.redirect(std_type) as std_stream:
            out = "Test std stream.\n"
            if std_type is std.STD.OUT:
                print(out, end="", file=sys.stdout)
            else:
                print(out, end="", file=sys.stderr)
            assert std_stream.getvalue() == out
