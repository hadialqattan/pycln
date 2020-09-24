"""pycln/utils/pathu.py tests."""
import re
import sys
from pathlib import Path

import pytest
from pathspec import PathSpec
from pytest_mock import mock

from pycln.utils import pathu
from pycln.utils.report import Report

from . import CONFIG_DIR

# Constants.
MOCK = "pycln.utils.report.%s"
PYVER = f"python{sys.version_info[0]}.{sys.version_info[1]}"


class TestPathu:

    """`pathu.py` functions test case."""

    @pytest.mark.parametrize(
        "path, include, exclude, gitignore, expec",
        [
            pytest.param(
                Path(__file__).parent.parent,
                re.compile(r"test_.*\.py$"),
                re.compile(r"(.*_re.*\.py|.git/|pycln/)$"),
                PathSpec.from_lines("gitwildmatch", ["*u.py", "utils/"]),
                {
                    "test_main.py",
                    "test_scan.py",
                    "test_config.py",
                    "test_metadata.py",
                    "test_transform.py",
                    "test_nodes.py",
                    "test_cli.py",
                },
                id="path: directory",
            ),
            pytest.param(
                Path(__file__),
                re.compile(r".*\.py$"),
                re.compile(r""),
                PathSpec.from_lines("gitwildmatch", []),
                {"test_pathu.py"},
                id="path: file",
            ),
            pytest.param(
                CONFIG_DIR.joinpath("setup.cfg"),
                re.compile(r".*\.py$"),
                re.compile(r""),
                PathSpec.from_lines("gitwildmatch", []),
                {},
                id="path: non-py-file",
            ),
        ],
    )
    @mock.patch(MOCK % "Report.ignored_path")
    def test_yield_sources(
        self, ignored_path, path, include, exclude, gitignore, expec
    ):
        sources = pathu.yield_sources(path, include, exclude, gitignore, Report(None))
        for source in sources:
            assert source.parts[-1] in expec

    def test_get_standard_lib_paths(self):
        standard_paths = pathu.get_standard_lib_paths()
        dirs = {path.parts[-2] for path in standard_paths}
        expected_dirs = {PYVER, pathu.LIB_DYNLOAD}
        assert dirs == expected_dirs
        assert len(standard_paths) > 180

    def test_get_standard_lib_names(self):
        standard_names = pathu.get_standard_lib_names()
        # Test some random standard lib names.
        for name in {"ast", "unittest", "pathlib"}:
            assert name in standard_names
        # Imports with side effects shouldn't included.
        for name in pathu.IMPORTS_WITH_SIDE_EFFECTS:
            assert name not in standard_names
        # Expected bin imports should included.
        for name in pathu.BIN_IMPORTS:
            assert name in standard_names
        assert len(standard_names) > 180

    def test_get_third_party_lib_paths(self):
        third_paths = pathu.get_third_party_lib_paths()
        dirs = {path.parts[-2] for path in third_paths}
        expected_dirs = {"site-packages", "dist-packages"}
        assert dirs == expected_dirs
        assert len(third_paths) > 2

    @pytest.mark.parametrize(
        "module, expec_path",
        [
            pytest.param(
                "pycln", Path("pycln/__init__.py"), id="import module : lvl -2"
            ),
            pytest.param(
                "utils", Path("utils/__init__.py"), id="import module : lvl +1"
            ),
            pytest.param(
                "test_pathu",
                Path("tests/test_pathu.py"),
                id="import file : lvl 0",
            ),
            pytest.param("not-exists", None, id="not exists"),
        ],
    )
    def test_get_local_import_path(self, module, expec_path):
        path = pathu.get_local_import_path(Path(__file__), module)
        if expec_path:
            assert path.parts[-2:] == expec_path.parts
        else:
            assert path is None

    @pytest.mark.parametrize(
        "module, package, level, expec_path",
        [
            pytest.param(
                "utils",
                "pycln",
                2,
                Path("pycln/utils/__init__.py"),
                id="from ..package import module",
            ),
            pytest.param(
                "utils",
                "",
                1,
                Path("tests/utils/__init__.py"),
                id="from . import module",
            ),
            pytest.param(
                "*",
                "pycln",
                2,
                Path("pycln/pycln/__init__.py"),
                id="from ..package import *",
            ),
            pytest.param(
                "sysu",
                "utils",
                1,
                Path("tests/utils/sysu.py"),
                id="from .package import file",
            ),
            pytest.param(
                "*",
                "test_pathu",
                1,
                Path("pycln/tests/test_pathu.py"),
                id="from .file import *",
            ),
            pytest.param("not-exists", "", 1, None, id="not exists"),
        ],
    )
    def test_get_local_import_from_path(self, module, package, level, expec_path):
        path = pathu.get_local_import_from_path(Path(__file__), module, package, level)
        if expec_path:
            assert path.parts[-3:] == expec_path.parts
        else:
            assert path is None

    @pytest.mark.parametrize(
        "paths, module, expec_path",
        [
            pytest.param(
                [
                    Path("pycln/pycln/utils/pathu.py"),
                    Path("pycln/tests/utils/sysu.py"),
                ],
                "sysu",
                Path("pycln/tests/utils/sysu.py"),
                id="module",
            ),
            pytest.param(
                [
                    Path("pycln/pycln/utils/pathu.py"),
                    Path("pycln/tests/utils"),
                ],
                "utils.sysu",
                Path("pycln/tests/utils/__init__.py"),
                id="package.module",
            ),
            pytest.param(
                [
                    Path("pycln/pycln/setup.py"),
                    Path("pycln/tests/utils/temp.py"),
                ],
                "std",
                None,
                id="not exists",
            ),
        ],
    )
    def test_get_module_path(self, paths, module, expec_path):
        path = pathu.get_module_path(paths, module)
        assert path == expec_path

    @pytest.mark.parametrize(
        "module, expec_path",
        [
            pytest.param(
                "pycln", Path("pycln/__init__.py"), id="import module : local"
            ),
            pytest.param(
                "test_pathu",
                Path("tests/test_pathu.py"),
                id="import file : local",
            ),
            pytest.param(
                "distutils",
                Path("distutils/__init__.py"),
                id="import module : standard",
            ),
            pytest.param(
                "typer",
                Path("typer/__init__.py"),
                id="import module : third party",
            ),
            pytest.param("not-exists", None, id="not exists"),
        ],
    )
    def test_get_import_path(self, module, expec_path):
        path = pathu.get_import_path(Path(__file__), module)
        if expec_path:
            assert path.parts[-2:] == expec_path.parts
        else:
            assert path is None

    @pytest.mark.parametrize(
        "module, package, level, expec_path",
        [
            pytest.param(
                "utils",
                "pycln",
                2,
                Path("utils/__init__.py"),
                id="from ..package import module : local",
            ),
            pytest.param(
                "*",
                "pycln",
                2,
                Path("pycln/__init__.py"),
                id="from ..package import * : local",
            ),
            pytest.param(
                "sysu",
                "utils",
                1,
                Path("utils/sysu.py"),
                id="from .package import file : local",
            ),
            pytest.param(
                "*",
                "test_pathu",
                1,
                Path("tests/test_pathu.py"),
                id="from .file import * : local",
            ),
            pytest.param(
                "AST",
                "ast",
                0,
                Path(f"{PYVER}/ast.py"),
                id="from package import file : standard",
            ),
            pytest.param(
                "*",
                "distutils",
                0,
                Path("distutils/__init__.py"),
                id="from package import * : standard",
            ),
            pytest.param(
                "colors",
                "typer",
                0,
                Path("typer/__init__.py"),
                id="from package import file : third party",
            ),
            pytest.param(
                "*",
                "typer",
                0,
                Path("typer/__init__.py"),
                id="from package import * : third party",
            ),
            pytest.param("not-exists", "", 0, None, id="not exists"),
        ],
    )
    def test_get_import_from_path(self, module, package, level, expec_path):
        if not expec_path:
            print()
        path = pathu.get_import_from_path(Path(__file__), module, package, level)
        if expec_path:
            assert path.parts[-2:] == expec_path.parts
        else:
            assert path is None
