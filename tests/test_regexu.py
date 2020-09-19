"""pycln/utils/regexu.py tests."""
import re
from pathlib import Path

import pytest
from typer import Exit

from pycln.utils import regexu

from . import CONFIG_DIR
from .utils import sysu

# Constants.
INCLUDE_REGEX = r".*_util.py$"
COMPILED_INCLUDE_REGEX = re.compile(INCLUDE_REGEX, re.IGNORECASE)
EXCLUDE_REGEX = r".*_test.py$"
COMPILED_EXCLUDE_REGEX = re.compile(EXCLUDE_REGEX, re.IGNORECASE)


class TestRegexU:

    """`regexu.py` functions test case."""

    @pytest.mark.parametrize(
        "regex, expec_err_type, expec_err",
        [
            pytest.param(INCLUDE_REGEX, None, "", id="valid, regex: str"),
            pytest.param(
                COMPILED_INCLUDE_REGEX,
                None,
                "",
                id="valid, regex: Pattern[str]",
            ),
            pytest.param(
                r"**invalid**",
                Exit,
                "Invalid regular expression for include given: '**invalid**' ⛔\n",
                id="invalid: regex: str",
            ),
        ],
    )
    def test_safe_compile(self, regex, expec_err_type, expec_err):
        err_type, err_msg = None, ""
        with sysu.std_redirect(sysu.STD.ERR) as stderr:
            try:
                regexu.safe_compile(regex, "include")
            except Exit:
                err_type = Exit
            err_msg = stderr.getvalue()
        assert err_type == expec_err_type
        assert err_msg == expec_err

    @pytest.mark.parametrize(
        "type_, name, regex, expec",
        [
            pytest.param(
                "included",
                "pycln_util.py",
                COMPILED_INCLUDE_REGEX,
                True,
                id="include -> True",
            ),
            pytest.param(
                "excluded",
                "pycln_test.py",
                COMPILED_EXCLUDE_REGEX,
                True,
                id="exclude -> True",
            ),
            pytest.param(
                "included",
                "main.py",
                COMPILED_INCLUDE_REGEX,
                False,
                id="include -> False",
            ),
            pytest.param(
                "excluded",
                "cli.py",
                COMPILED_EXCLUDE_REGEX,
                False,
                id="exclude -> False",
            ),
        ],
    )
    def test_is_(self, type_, name, regex, expec):
        # Test `is_included` and `is_excluded` functions.
        assert getattr(regexu, f"is_{type_}")(name, regex) == expec

    @pytest.mark.parametrize(
        "root, no_gitignore, expec",
        [
            pytest.param(CONFIG_DIR, False, True, id="valid path"),
            pytest.param(Path("NotExists"), False, False, id="not exists path"),
            pytest.param(Path("NoMatter"), True, False, id="no gitignore"),
        ],
    )
    def test_get_gitignore(self, root, no_gitignore, expec):
        gitignore = regexu.get_gitignore(root, no_gitignore)
        assert gitignore.match_file("test.ignore") == expec
        assert gitignore.match_file("test_ignore/") == expec

    @pytest.mark.parametrize(
        "line, expec",
        [
            pytest.param("import os  # nopycln: import", True, id="nopycln: import"),
            pytest.param("import sys  # noqa", True, id="noqa"),
            pytest.param("import time", False, id="no comment"),
        ],
    )
    def test_skip_import(self, line, expec):
        assert regexu.skip_import(line) == expec

    @pytest.mark.parametrize(
        "src_code, expec",
        [
            pytest.param(
                "#" + " nopycln: file\n source code...",
                True,
                id="nopycln: file",
            ),
            pytest.param("source code...", False, id="no comment"),
        ],
    )
    def test_skip_file(self, src_code, expec):
        assert regexu.skip_file(src_code) == expec
