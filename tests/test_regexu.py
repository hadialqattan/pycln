"""pycln/utils/regexu.py unit tests."""
import re
from pathlib import Path

import pytest
from typer import Exit

from pycln.utils import regexu

from . import CONFIG_DIR
from .utils import std

# Constants.
INCLUDE_REGEX = r".*_util.py$"
COMPILED_INCLUDE_REGEX = re.compile(INCLUDE_REGEX, re.IGNORECASE)
EXCLUDE_REGEX = r".*_test.py$"
COMPILED_EXCLUDE_REGEX = re.compile(EXCLUDE_REGEX, re.IGNORECASE)


class TestRegexU:

    """`regexu.py` functions test case."""

    @pytest.mark.parametrize("regex", [INCLUDE_REGEX, COMPILED_INCLUDE_REGEX])
    def test_safe_compile_valid_regex(self, regex):
        # Test `safe_compile` function.
        compiled_regex = regexu.safe_compile(regex, "include")
        assert compiled_regex == COMPILED_INCLUDE_REGEX

    def test_safe_compile_invalid_regex(self):
        # Test `safe_comile` function.
        regex = r"**invalid**"
        expected_err = f"Invalid regular expression for include given: {regex!r} ⛔\n"
        with std.redirect(std.STD.ERR) as stderr:
            try:
                regexu.safe_compile(regex, "include")
            except Exit:
                err_type = Exit
            err_msg = stderr.getvalue()
        assert err_type == Exit
        assert err_msg == expected_err

    @pytest.mark.parametrize(
        "type_, name, regex, expec",
        [
            ("included", "pycln_util.py", COMPILED_INCLUDE_REGEX, True),
            ("excluded", "pycln_test.py", COMPILED_EXCLUDE_REGEX, True),
            ("included", "main.py", COMPILED_INCLUDE_REGEX, False),
            ("excluded", "cli.py", COMPILED_EXCLUDE_REGEX, False),
        ],
    )
    def test_is_(self, type_, name, regex, expec):
        # Test `is_included` and `is_excluded` functions.
        assert getattr(regexu, f"is_{type_}")(name, regex) == expec

    @pytest.mark.parametrize(
        "root, no_gitignore, expec",
        [
            (CONFIG_DIR, False, True),
            (Path("NotExists"), False, False),
            (Path("NoMatter"), True, False),
        ],
    )
    def test_get_gitignore(self, root, no_gitignore, expec):
        # Test `get_gitignore` function.
        gitignore = regexu.get_gitignore(root, no_gitignore)
        assert gitignore.match_file("test.ignore") == expec
        assert gitignore.match_file("test_ignore/") == expec

    @pytest.mark.parametrize(
        "line, expec",
        [
            ("import os  # nopycln: import", True),
            ("import sys  # noqa", True),
            ("import time", False),
        ],
    )
    def test_skip_import(self, line, expec):
        # Test `skip_import` function.
        assert regexu.skip_import(line) == expec

    @pytest.mark.parametrize(
        "src_code, expec",
        [("#" + " nopycln: file\n source code...", True), ("source code...", False)],
    )
    def test_skip_file(self, src_code, expec):
        # Test `skip_file` function.
        assert regexu.skip_file(src_code) == expec
