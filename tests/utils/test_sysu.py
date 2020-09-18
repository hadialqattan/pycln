"""Test `tests/utils/sysu.py`."""
import sys

import pytest

from . import sysu


class TestSTD:

    """`sysu.py` functions test case."""

    @pytest.mark.parametrize(
        "std_type",
        [
            pytest.param(sysu.STD.OUT, id="stdout"),
            pytest.param(sysu.STD.ERR, id="stderr"),
        ],
    )
    def test_std_redirect(self, std_type):
        with sysu.std_redirect(std_type) as std_stream:
            out = "Test std stream.\n"
            if std_type is sysu.STD.OUT:
                print(out, end="", file=sys.stdout)
            else:
                print(out, end="", file=sys.stderr)
            assert std_stream.getvalue() == out

    def test_hide_sys_argv(self):
        original_argv = sys.argv.copy()
        sys.argv = ["test", "argv"]
        with sysu.hide_sys_argv():
            assert sys.argv == []
        assert sys.argv == ["test", "argv"]
        sys.argv = original_argv
