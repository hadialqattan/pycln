"""pycln/utils/pathu.py tests."""
# pylint: disable=R0201,W0613
import re
import sys
from pathlib import Path
from unittest import mock

import pytest
from pathspec import PathSpec

from pycln import ISWIN
from pycln.utils import pathu, regexu
from pycln.utils.report import Report

from . import DATA_DIR

# Constants.
MOCK = "pycln.utils.pathu.%s"
REPORT_MOCK = "pycln.utils.report.%s"

if ISWIN:
    PYVER = "Lib"
else:
    PYVER = f"python{sys.version_info[0]}.{sys.version_info[1]}"


LRU_CACHED_FUNCS = frozenset(
    {
        "get_standard_lib_paths",
        "get_standard_lib_names",
        "get_third_party_lib_paths",
        "get_local_import_path",
        "get_local_import_from_path",
        "get_import_path",
        "get_import_from_path",
    }
)


class TestPathu:

    """`pathu.py` functions test case."""

    @pytest.fixture(autouse=True)
    def clear_all_lru_cache(self):
        for func_name in LRU_CACHED_FUNCS:
            getattr(pathu, func_name).cache_clear()
        yield

    @pytest.mark.parametrize(
        "path, include, exclude, extend_exclude, gitignore, expec",
        [
            pytest.param(
                Path(DATA_DIR / "paths" / "dir"),
                re.compile(r".*\.py$"),
                re.compile(r"(.*s\.py|git/)$"),
                re.compile(regexu.EMPTY_REGEX),
                PathSpec.from_lines("gitwildmatch", ["*u.py", "utils/"]),
                {
                    "x.py",
                    "y.py",
                    "z.py",
                },
                id="path: directory",
            ),
            pytest.param(
                Path(DATA_DIR / "paths"),
                re.compile(r".*\.py$"),
                re.compile(r"paths/"),
                re.compile(regexu.EMPTY_REGEX),
                PathSpec.from_lines("gitwildmatch", []),
                set(),
                id="path: directory - excluded",
            ),
            pytest.param(
                Path(DATA_DIR / "paths"),
                re.compile(r".*\.py$"),
                re.compile(regexu.EMPTY_REGEX),
                re.compile(r"paths/"),
                PathSpec.from_lines("gitwildmatch", []),
                set(),
                id="path: directory - extend-excluded",
            ),
            pytest.param(
                Path(DATA_DIR / "paths" / "dir"),
                re.compile(r".*\.py$"),
                re.compile(r"paths/"),
                re.compile(regexu.EMPTY_REGEX),
                PathSpec.from_lines("gitwildmatch", []),
                set(),
                id="path: nested-directory - excluded",
            ),
            pytest.param(
                Path(DATA_DIR / "paths" / "a.py"),
                re.compile(r".*\.py$"),
                re.compile(regexu.EMPTY_REGEX),
                re.compile(regexu.EMPTY_REGEX),
                PathSpec.from_lines("gitwildmatch", []),
                {"a.py"},
                id="path: file",
            ),
            pytest.param(
                Path(DATA_DIR / "paths" / "a.py"),
                re.compile(r".*\.py$"),
                re.compile(regexu.EMPTY_REGEX),
                re.compile(regexu.EMPTY_REGEX),
                PathSpec.from_lines("gitwildmatch", ["a.py"]),
                set(),
                id="path: file - ignored",
            ),
            pytest.param(
                Path(DATA_DIR / "paths" / "b.c"),
                re.compile(r".*\.py$"),
                re.compile(regexu.EMPTY_REGEX),
                re.compile(regexu.EMPTY_REGEX),
                PathSpec.from_lines("gitwildmatch", []),
                set(),
                id="path: non-py-file",
            ),
        ],
    )
    @mock.patch(REPORT_MOCK % "Report.ignored_path")
    def test_yield_sources(
        self, ignored_path, path, include, exclude, extend_exclude, gitignore, expec
    ):
        sources = pathu.yield_sources(
            path, include, exclude, extend_exclude, gitignore, Report(None)
        )
        sources = list(sources)
        if sources and expec:
            for source in sources:
                assert source.parts[-1] in expec
        else:
            assert sources == list(expec)

    @mock.patch(REPORT_MOCK % "Report.ignored_path")
    def test_nested_gitignore(self, ignored_path):
        path = Path(DATA_DIR / "nested_gitignore_tests")
        include = regexu.safe_compile(regexu.INCLUDE_REGEX, regexu.INCLUDE)
        exclude = regexu.safe_compile(regexu.EXCLUDE_REGEX, regexu.EXCLUDE)
        extend_exclude = regexu.safe_compile(regexu.EMPTY_REGEX, regexu.EXCLUDE)
        gitignore = regexu.get_gitignore(path)
        sources = pathu.yield_sources(
            path, include, exclude, extend_exclude, gitignore, Report(None)
        )
        expected = [
            Path(path / "x.py"),
            Path(path / "root/b.py"),
            Path(path / "root/c.py"),
            Path(path / "root/child/c.py"),
        ]
        assert sorted(list(sources)) == sorted(expected)

    def test_get_standard_lib_paths(self):
        standard_paths = pathu.get_standard_lib_paths()
        dirs = {path.parts[-2] for path in standard_paths}
        if ISWIN:
            expected_dirs = {pathu.LIB_DYNLOAD}
        else:
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
        #: `DATA_DIR/site-packages/custom.pth` file contains
        #: `DATA_DIR/site-packages/custom/path/1` custom path.
        data_site: Path = DATA_DIR / "site-packages"
        sys.path.append(str(data_site))
        pathu.get_third_party_lib_paths.cache_clear()
        third_paths, pth_paths = pathu.get_third_party_lib_paths()
        dirs = {path.parts[-2] for path in third_paths}
        for dir_ in dirs:
            assert dir_ in {"site-packages", "dist-packages"}

        assert data_site / "custom/path/1" in pth_paths
        assert data_site / "custom/path/2" not in pth_paths, "A commented path"

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
        "module, expec_path_num",
        [
            pytest.param("hi", "1", id="exists[1]"),
            pytest.param("hello", "2", id="exists[2]"),
            pytest.param("not-exists", "", id="not-exists"),
        ],
    )
    def test_get_local_import_pth_path(self, module: str, expec_path_num: str):
        custom_pth = DATA_DIR / "site-packages/custom/path"
        custom_pth1 = custom_pth / "1"
        custom_pth2 = custom_pth / "2"
        pth_paths = {custom_pth1, custom_pth2}
        path = pathu.get_local_import_pth_path(pth_paths, module)
        if expec_path_num:
            if expec_path_num == "1":
                assert path == custom_pth1 / f"{module}.py"
            else:
                assert path == custom_pth2 / f"{module}.py"
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
                "*",
                ".",
                1,
                Path("pycln/tests/__init__.py"),
                id="from . import *",
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
            pytest.param("utils", None, 1, None, id="non-package"),
        ],
    )
    def test_get_local_import_from_path(self, module, package, level, expec_path):
        path = pathu.get_local_import_from_path(Path(__file__), module, package, level)
        if expec_path:
            assert path.parts[-3:] == expec_path.parts
        else:
            assert path is None

    @pytest.mark.parametrize(
        "module, package, expec_path",
        [
            pytest.param("hi", "hi", "hi.py", id="exists[file]"),
            pytest.param("hi2", "world", "world/hi2.py", id="exists[module]"),
            pytest.param("not", "exists", "", id="not-exists"),
        ],
    )
    def test_get_local_import_from_pth_path(
        self, module: str, package: str, expec_path: str
    ):
        custom_pth = DATA_DIR / "site-packages/custom/path"
        custom_pth1 = custom_pth / "1"
        custom_pth2 = custom_pth / "2"
        pth_paths = {custom_pth1, custom_pth2}
        path = pathu.get_local_import_from_pth_path(pth_paths, module, package, 0)
        if expec_path:
            assert path == custom_pth1 / expec_path
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
            pytest.param(
                [
                    #: This represents this case:
                    #:
                    #: >>> from . import *
                    #:
                    #: while the file is not in a package.
                ],
                None,
                None,
                id="not exists - no module",
            ),
        ],
    )
    def test_get_module_path(self, paths, module, expec_path):
        path = pathu.get_module_path(paths, module)
        assert path == expec_path

    @pytest.mark.parametrize(
        "module, expec_path",
        [
            pytest.param("pycln", "pycln/__init__.py", id="import module : local"),
            pytest.param(
                "test_pathu",
                "tests/test_pathu.py",
                id="import file : local",
            ),
            pytest.param(
                "distutils",
                "distutils/__init__.py",
                id="import module : standard",
            ),
            pytest.param(
                "typer",
                "typer/__init__.py",
                id="import module : third party",
            ),
            pytest.param(
                "hi",
                "custom/path/1/hi.py",
                id="import file : local third party (.pth)",
            ),
            pytest.param("not-exists", None, id="not exists"),
        ],
    )
    def test_get_import_path(self, module, expec_path):
        pathu.get_import_path.cache_clear()
        # Add the path containing `custom.pth` file.
        sys.path.append(str(DATA_DIR / "site-packages"))
        path = pathu.get_import_path(Path(__file__), module)
        if expec_path:
            assert str(path).endswith(expec_path)
        else:
            assert path is None

    @pytest.mark.parametrize(
        "module, package, level, expec_path",
        [
            pytest.param(
                "utils",
                "pycln",
                2,
                "utils/__init__.py",
                id="from ..package import module : local",
            ),
            pytest.param(
                "*",
                "pycln",
                2,
                "pycln/__init__.py",
                id="from ..package import * : local",
            ),
            pytest.param(
                "sysu",
                "utils",
                1,
                "utils/sysu.py",
                id="from .package import file : local",
            ),
            pytest.param(
                "*",
                "test_pathu",
                1,
                "tests/test_pathu.py",
                id="from .file import * : local",
            ),
            pytest.param(
                "AST",
                "ast",
                0,
                f"{PYVER}/ast.py",
                id="from package import file : standard",
            ),
            pytest.param(
                "*",
                "distutils",
                0,
                "distutils/__init__.py",
                id="from package import * : standard",
            ),
            pytest.param(
                "colors",
                "typer",
                0,
                "typer/__init__.py",
                id="from package import file : third party",
            ),
            pytest.param(
                "*",
                "typer",
                0,
                "typer/__init__.py",
                id="from package import * : third party",
            ),
            pytest.param(
                "hi",
                "hi",
                0,
                "custom/path/1/hi.py",
                id="from file import func : local third party (.pth)",
            ),
            pytest.param("not-exists", "", 0, None, id="not exists"),
        ],
    )
    def test_get_import_from_path(self, module, package, level, expec_path):
        pathu.get_import_from_path.cache_clear()
        # Add the path containing `custom.pth` file.
        sys.path.append(str(DATA_DIR / "site-packages"))
        path = pathu.get_import_from_path(Path(__file__), module, package, level)
        if expec_path:
            assert str(path).endswith(expec_path)
        else:
            assert path is None
