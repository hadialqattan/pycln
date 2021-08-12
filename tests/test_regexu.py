"""pycln/utils/regexu.py tests."""
# pylint: disable=R0201,W0613
import re
from pathlib import Path

import pytest
from typer import Exit

from pycln import ISWIN
from pycln.utils import regexu

from . import CONFIG_DIR, DATA_DIR
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
            pytest.param(INCLUDE_REGEX, sysu.Pass, "", id="valid, regex: str"),
            pytest.param(
                COMPILED_INCLUDE_REGEX,
                sysu.Pass,
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
        with sysu.std_redirect(sysu.STD.ERR) as stderr:
            with pytest.raises(expec_err_type):
                regexu.safe_compile(regex, "include")
                raise sysu.Pass()
            assert stderr.getvalue() == expec_err

    @pytest.mark.parametrize(
        "path, expec_strpath",
        [
            pytest.param(
                Path(DATA_DIR / "paths" / "a.py"),
                f"{Path(DATA_DIR / 'paths' / 'a.py')}",
                id="path: file",
                marks=pytest.mark.skipif(
                    ISWIN, reason="Unix specific path normalization."
                ),
            ),
            pytest.param(
                Path(DATA_DIR / "paths"),
                f"{Path(DATA_DIR / 'paths')}/",
                id="path: directory",
                marks=pytest.mark.skipif(
                    ISWIN, reason="Unix specific path normalization."
                ),
            ),
            pytest.param(
                Path("C:/dir/child/a.py"),
                "C:/dir/child/a.py",
                id="path: file",
                marks=pytest.mark.skipif(
                    not ISWIN, reason="Windows specific path normalization."
                ),
            ),
            pytest.param(
                Path("C:/dir/child"),
                "C:/dir/child/",
                id="path: directory",
                marks=pytest.mark.skipif(
                    not ISWIN, reason="Windows specific path normalization."
                ),
            ),
        ],
    )
    def test_strpath(self, path, expec_strpath):
        assert regexu.strpath(path) == expec_strpath

    @pytest.mark.parametrize(
        "path, regex, expec",
        [
            pytest.param(
                Path("path/to/file00.py"),
                re.compile(r"file.*.py", re.IGNORECASE),
                True,
                id="path: file - true",
            ),
            pytest.param(
                Path("path/to/hi.py"),
                re.compile(r"file.*.py", re.IGNORECASE),
                False,
                id="path: file - false",
            ),
        ],
    )
    def test_is_included(self, path, regex, expec):
        assert regexu.is_included(path, regex) == expec

    @pytest.mark.parametrize(
        "path, regex, expec",
        [
            pytest.param(
                Path("path/to/file00.py"),
                re.compile(r"file.*.py", re.IGNORECASE),
                True,
                id="path: file - true",
            ),
            pytest.param(
                Path("path/to/hi.py"),
                re.compile(r"file.*.py", re.IGNORECASE),
                False,
                id="path: file - false",
            ),
            pytest.param(
                Path("path/to/directory00"),
                re.compile(r"directory.*/", re.IGNORECASE),
                True,
                id="path: directory - true",
            ),
            pytest.param(
                Path("path/to/root"),
                re.compile(r"directory.*/", re.IGNORECASE),
                False,
                id="path: directory - false",
            ),
            pytest.param(
                Path("path/to/directory00/file.py"),
                re.compile(r"directory.*/", re.IGNORECASE),
                True,
                id="path: directory/file.py - true",
            ),
            pytest.param(
                Path("path/to/root/file.py"),
                re.compile(r"directory.*/", re.IGNORECASE),
                False,
                id="path: directory/file.py - false",
            ),
        ],
    )
    def test_is_excluded(self, path, regex, expec):
        assert regexu.is_excluded(path, regex) == expec

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
