"""Test `tests/utils/sysu.py`."""
# pylint: disable=R0201,W0613
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

    def test_reopenable_temp_file(self):
        with sysu.reopenable_temp_file("CODE") as tmp_path:
            assert tmp_path.is_file()
            with open(tmp_path) as tmp:
                assert tmp.read() == "CODE"
        assert not tmp_path.is_file()
