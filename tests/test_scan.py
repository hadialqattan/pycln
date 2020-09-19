"""pycln/utils/scan.py  tests."""
import ast
import sys
from importlib import import_module
from pathlib import Path
from typing import Optional

import pytest
from pytest_mock import mock

from pycln.utils import _nodes, scan
from pycln.utils._exceptions import UnexpandableImportStar, UnparsableFile

# Constants.
PY38_PLUS = sys.version_info >= (3, 8)


class TestDataclasses:

    """`scan.py` dataclasses test case."""

    def test_import_stats_iter(self):
        import_stats = scan.ImportStats({"import"}, {"from"})
        assert [i for i in import_stats] == [{"import"}, {"from"}]

    def test_source_stats_iter(self):
        source_stats = scan.SourceStats({"name"}, {"attr"}, {"skip"})
        assert [i for i in source_stats] == [{"name"}, {"attr"}]


class AnalyzerTestCase:

    """`scan.*Analyzer` test case."""

    def _assert_set_equal_or_not(self, set_: set, expec_set: set):
        if expec_set:
            assert set_ == expec_set
        else:
            assert not set_

    def _normalize_set(self, set_: set) -> set:
        # Remove any dunder name from the given set.
        return set([i for i in set_ if not i.startswith("__")])


class TestSourceAnalyzer(AnalyzerTestCase):

    """`SourceAnalyzer` class tests."""

    def _get_analyzer(self, source_code: str):
        analyzer = scan.SourceAnalyzer(source_code.splitlines(True))
        if PY38_PLUS:
            ast_tree = ast.parse(source_code, type_comments=True)
        else:
            ast_tree = ast.parse(source_code)
        analyzer.visit(ast_tree)
        return analyzer

    def _assert_name_equal_or_not(self, imports: list, expec_name: str):
        if expec_name:
            assert imports
            assert imports[0].names[0].name == expec_name
        else:
            not imports

    def _get_import(self, import_stmnt: str, expec_end_lineno: Optional[int]) -> tuple:
        ast_impt = ast.parse(import_stmnt).body[0]
        if expec_end_lineno:
            end_lineno = expec_end_lineno
        else:
            end_lineno = ast_impt.end_lineno
        start = (ast_impt.lineno, ast_impt.col_offset)
        location = _nodes.NodeLocation(start, end_lineno)
        return ast_impt, location

    def _assert_import_equal_py38(
        self,
        analyzer: scan.SourceAnalyzer,
        import_stmnt: str,
        expec_end_lineno: Optional[int] = None,
    ):
        ast_impt, location = self._get_import(import_stmnt, expec_end_lineno)
        py38_node = analyzer._get_py38_import_node(ast_impt)
        assert py38_node == _nodes.Import(location, ast_impt.names)

    def _assert_import_from_equal_py38(
        self,
        analyzer: scan.SourceAnalyzer,
        import_stmnt: str,
        expec_end_lineno: Optional[int] = None,
    ):
        ast_impt, location = self._get_import(import_stmnt, expec_end_lineno)
        py38_node = analyzer._get_py38_import_from_node(ast_impt)
        assert py38_node == _nodes.ImportFrom(
            location, ast_impt.names, ast_impt.module, ast_impt.level
        )

    @pytest.mark.skipif(not PY38_PLUS, reason="Python >=3.8 class usage.")
    @pytest.mark.parametrize(
        "source_lines, expec_error",
        [
            pytest.param([], None, id="with source lines"),
            pytest.param(None, None, id="without source lines"),
        ],
    )
    def test_init_py38_plus(self, source_lines, expec_error):
        # Test `__init__` dunder method for Python >=3.8.
        err_type = None
        try:
            scan.SourceAnalyzer(source_lines)
        except ValueError as err:
            err_type = type(err)
        assert err_type == expec_error

    @pytest.mark.skipif(PY38_PLUS, reason="Python <3.8 class usage.")
    @pytest.mark.parametrize(
        "source_lines, expec_error",
        [
            pytest.param([], None, id="with source lines"),
            pytest.param(None, ValueError, id="without source lines"),
        ],
    )
    def test_init_py37_minus(self, source_lines, expec_error):
        # Test `__init__` dunder method for Python <3.8.
        err_type = None
        try:
            scan.SourceAnalyzer(source_lines)
        except ValueError as err:
            err_type = type(err)
        assert err_type == expec_error

    @pytest.mark.parametrize(
        "code, expec_name",
        [pytest.param(("import x\n" "print()\n"), "x", id="single name")],
    )
    def test_visit_Import(self, code, expec_name):
        analyzer = self._get_analyzer(code)
        _, import_stats = analyzer.get_stats()
        self._assert_name_equal_or_not(list(import_stats.import_), expec_name)

    @pytest.mark.parametrize(
        "code, expec_module_name",
        [
            pytest.param(
                ("from x import y\n" "print()\n"),
                ("x", "y"),
                id="normal module name",
            ),
            pytest.param(
                ("from __dunder__ import y\n" "print()\n"),
                None,
                id="skip dunder module name",
            ),
        ],
    )
    def test_visit_ImportFrom(self, code, expec_module_name):
        analyzer = self._get_analyzer(code)
        _, import_stats = analyzer.get_stats()
        imports = list(import_stats.from_)
        if expec_module_name:
            assert imports
            node = imports[0]
            assert (node.module, node.names[0].name) == expec_module_name
        else:
            assert not imports

    @pytest.mark.parametrize(
        "code, expec_names",
        [
            pytest.param(
                ("x, y, z\n" "import r\n"), {"x", "y", "z"}, id="normal names"
            ),
            pytest.param("import x\n", None, id="no names"),
        ],
    )
    def test_visit_Name(self, code, expec_names):
        analyzer = self._get_analyzer(code)
        source_stats, _ = analyzer.get_stats()
        self._assert_set_equal_or_not(source_stats.name_, expec_names)

    @pytest.mark.parametrize(
        "code, expec_attrs",
        [
            pytest.param(
                ("i.x, j.y, m.z\n" "import k.r\n"),
                {"x", "y", "z"},
                id="normal attrs",
            ),
            pytest.param("import k.r\n", None, id="no attrs"),
        ],
    )
    def test_visit_Attribute(self, code, expec_attrs):
        analyzer = self._get_analyzer(code)
        source_stats, _ = analyzer.get_stats()
        self._assert_set_equal_or_not(source_stats.attr_, expec_attrs)

    @pytest.mark.parametrize(
        "code, expec_name",
        [
            pytest.param(
                (
                    "try:\n"
                    "    import x\n"
                    "except ModuleNotFoundError:\n"
                    "    pass\n"
                ),
                "x",
                id="try : ModuleNotFoundError",
            ),
            pytest.param(
                ("try:\n" "    import x\n" "except ImportError:\n" "    pass\n"),
                "x",
                id="try : ImportError",
            ),
            pytest.param(
                ("try:\n" "    import x\n" "except ImportWarning:\n" "    pass\n"),
                "x",
                id="try : ImportWarning",
            ),
            pytest.param(
                (
                    "try:\n"
                    "    import x\n"
                    "except ("
                    "ImportWarning, "
                    "ImportError, "
                    "ModuleNotFoundError"
                    "):\n"
                    "    pass\n"
                ),
                "x",
                id="All supported errors",
            ),
            pytest.param(
                ("try:\n" "    pass\n" "except ImportError:\n" "    import x\n"),
                "x",
                id="except : ImportError",
            ),
            pytest.param(
                (
                    "try:\n"
                    "    pass\n"
                    "except ImportError:\n"
                    "    pass\n"
                    "else:\n"
                    "    import x\n"
                ),
                "x",
                id="else : ImportError",
            ),
            pytest.param(
                (
                    "try:\n"
                    "    pass\n"
                    "except ImportError:\n"
                    "    pass\n"
                    "else:\n"
                    "    pass\n"
                    "finally:\n"
                    "    import x"
                ),
                None,
                id="finally : ImportError",
            ),
        ],
    )
    def test_visit_Try(self, code, expec_name):
        analyzer = self._get_analyzer(code)
        self._assert_name_equal_or_not(list(analyzer._imports_to_skip), expec_name)

    @pytest.mark.parametrize(
        "code, expec_names, expec_names_to_skip",
        [
            pytest.param(
                (
                    "x = 'y'\n"
                    "__name__ = x; __doc__ = x; __package__ = x; __loader__ = x\n"
                    "__spec__ = x; __build_class__ = x; __import__ = x; __all__ = x\n"
                ),
                None,
                scan.NAMES_TO_SKIP,
                id="names to skip",
            ),
            pytest.param(
                "__all__ = ['x', 'y', 'z']\n",
                {"x", "y", "z"},
                {"__all__"},
                id="__all__ dunder overriding",
            ),
        ],
    )
    @mock.patch("pycln.utils.scan.SourceAnalyzer.visit_Name")
    def test_visit_Assign(self, visit_Name, code, expec_names, expec_names_to_skip):
        analyzer = self._get_analyzer(code)
        source_stats, _ = analyzer.get_stats()
        self._assert_set_equal_or_not(source_stats.name_, expec_names)
        self._assert_set_equal_or_not(source_stats.names_to_skip, expec_names_to_skip)

    @pytest.mark.parametrize(
        "code, expec_names",
        [
            pytest.param("foo: 'List[str]' = []\n", {"List", "str"}, id="assign"),
            pytest.param(
                ("def foo(bar: 'List[str]'):\n" "    pass\n"),
                {"List", "str"},
                id="arg",
            ),
            pytest.param(
                ("def foo() -> 'Tuple[int]':\n" "    pass\n"),
                {"Tuple", "int"},
                id="function",
            ),
            pytest.param(
                ("async def foo() -> 'Tuple[int]':\n" "    pass\n"),
                {"Tuple", "int"},
                id="async-function",
            ),
            pytest.param("foobar: '' = 'x'\n", None, id="empty string annotation"),
            pytest.param("foobar = 'x'\n", None, id="no string annotation"),
        ],
    )
    @mock.patch("pycln.utils.scan.SourceAnalyzer.visit_Name")
    def test_visit_string_type_annotation(self, visit_Name, code, expec_names):
        analyzer = self._get_analyzer(code)
        source_stats, _ = analyzer.get_stats()
        self._assert_set_equal_or_not(source_stats.name_, expec_names)

    @pytest.mark.skipif(
        not PY38_PLUS,
        reason="This feature is only available for Python >=3.8.",
    )
    @pytest.mark.parametrize(
        "code, expec_names",
        [
            pytest.param("foo = []  # type: List[str]\n", {"List", "str"}, id="assign"),
            pytest.param(
                ("def foo(\n" "bar  # type: List[str]\n" "):\n" "    pass\n"),
                {"List", "str"},
                id="arg",
            ),
            pytest.param(
                (
                    "def foo(bar):\n"
                    "    # type: (List[str]) -> Tuple[int]\n"
                    "    pass\n"
                ),
                {"List", "str", "Tuple", "int"},
                id="function",
            ),
            pytest.param(
                (
                    "async def foo(bar):\n"
                    "    # type: (List[str]) -> Tuple[int]\n"
                    "    pass\n"
                ),
                {"List", "str", "Tuple", "int"},
                id="async-function",
            ),
            pytest.param("foobar = 'x'\n", None, id="no type comment"),
        ],
    )
    @mock.patch("pycln.utils.scan.SourceAnalyzer.visit_Name")
    def test_visit_type_comment(self, visit_Name, code, expec_names):
        analyzer = self._get_analyzer(code)
        source_stats, _ = analyzer.get_stats()
        self._assert_set_equal_or_not(source_stats.name_, expec_names)

    @pytest.mark.parametrize(
        "code, expec_names, expec_attrs",
        [
            pytest.param("x, y", {"x", "y"}, None, id="names, no-attr"),
            pytest.param("x.i, y.j", {"x", "y"}, {"i", "j"}, id="names, attrs"),
            pytest.param("", None, None, id="no-names, no-attrs"),
        ],
    )
    def test_add_name_attr(self, code, expec_names, expec_attrs):
        analyzer = scan.SourceAnalyzer([])
        analyzer._add_name_attr(ast.parse(code))
        source_stats, _ = analyzer.get_stats()
        self._assert_set_equal_or_not(source_stats.name_, expec_names)
        self._assert_set_equal_or_not(source_stats.attr_, expec_attrs)

    @pytest.mark.skipif(not PY38_PLUS, reason="Test Python >=3.8 ast nodes.")
    @pytest.mark.parametrize(
        "code",
        [
            pytest.param("import x\n", id="single line"),
            pytest.param(("import \\\n" "    x\n"), id="multi line"),
        ],
    )
    def test_get_py38_import_node_py38_plus(self, code):
        analyzer = scan.SourceAnalyzer()
        self._assert_import_equal_py38(analyzer, code)

    @pytest.mark.skipif(PY38_PLUS, reason="Test Python <3.8 ast nodes.")
    @pytest.mark.parametrize(
        "code, expec_end_lineno",
        [
            pytest.param("import x\n", 1, id="single line"),
            pytest.param(("import \\\n" "    x\n"), 2, id="multi line"),
        ],
    )
    def test_get_py38_import_node_py37_minus(self, code, expec_end_lineno):
        analyzer = scan.SourceAnalyzer(code.splitlines(True))
        self._assert_import_equal_py38(analyzer, code, expec_end_lineno)

    @pytest.mark.skipif(not PY38_PLUS, reason="Test Python >=3.8 ast nodes.")
    @pytest.mark.parametrize(
        "code",
        [
            pytest.param("from x import y\n", id="single line"),
            pytest.param(
                ("from x import y, \\\n" "    z\n"), id="multi line, backslash"
            ),
            pytest.param(
                ("from x import (\n" "    y\n" ")\n"),
                id="multi line, parentheses",
            ),
        ],
    )
    def test_get_py38_import_from_node_py38_plus(self, code):
        analyzer = scan.SourceAnalyzer()
        self._assert_import_from_equal_py38(analyzer, code)

    @pytest.mark.skipif(PY38_PLUS, reason="Test Python <3.8 ast nodes.")
    @pytest.mark.parametrize(
        "code, expec_end_lineno",
        [
            pytest.param("from x import y\n", 1, id="single line"),
            pytest.param(
                ("from x import y, \\\n" "    z\n"),
                2,
                id="multi line, backslash",
            ),
            pytest.param(
                ("from x import (\n" "    y\n" ")\n"),
                3,
                id="multi line, parentheses",
            ),
        ],
    )
    def test_get_py38_import_from_node_py37_minus(self, code, expec_end_lineno):
        analyzer = scan.SourceAnalyzer(code.splitlines(True))
        self._assert_import_from_equal_py38(analyzer, code, expec_end_lineno)

    @pytest.mark.skipif(
        PY38_PLUS, reason="Required to determine end_lineno for Python <3.8."
    )
    @pytest.mark.parametrize(
        "line, expec",
        [
            pytest.param("from x import (\n", True, id="parentheses"),
            pytest.param("from x import y \\\n", False, id="backslash"),
            pytest.param("from x import y\n", None, id="single line"),
        ],
    )
    def test_is_parentheses(self, line, expec):
        assert scan.SourceAnalyzer._is_parentheses(line) == expec

    @pytest.mark.skipif(
        PY38_PLUS, reason="Required to determine end_lineno for Python <3.8."
    )
    @pytest.mark.parametrize(
        "code, lineno, is_parentheses, expec_end_lineno",
        [
            pytest.param(
                ("from x import (\n" "    y,\n" "    z,\n" ")\n" "print()\n"),
                1,
                True,
                4,
                id="parentheses",
            ),
            pytest.param(
                ("from x import y \\\n" "    z" "print()\n"),
                1,
                False,
                2,
                id="backslash",
            ),
        ],
    )
    def test_get_end_lineno(self, code, lineno, is_parentheses, expec_end_lineno):
        analyzer = scan.SourceAnalyzer(code.splitlines(True))
        end_lineno = analyzer._get_end_lineno(lineno, is_parentheses)
        assert end_lineno == expec_end_lineno


class TestImportablesAnalyzer(AnalyzerTestCase):

    """`ImportablesAnalyzer` class tests."""

    def _assert_not_importables(self, not_importables: set, expec_not_importables: set):
        str_set = set([(n.id if hasattr(n, "id") else n) for n in not_importables])
        assert str_set == expec_not_importables

    def _assert_importables_and_not(
        self, code: str, expec_importables: set, expec_not_importables=set()
    ):
        analyzer = scan.ImportablesAnalyzer(Path(__file__))
        analyzer.visit(ast.parse(code))
        assert self._normalize_set(analyzer.get_stats()) == self._normalize_set(
            expec_importables
        )
        self._assert_not_importables(analyzer._not_importables, expec_not_importables)

    @pytest.mark.parametrize(
        "module_name, level, expec_names",
        [
            pytest.param("time", 0, set(dir(import_module("time"))), id="standard lib"),
            pytest.param(
                "typer", 0, set(dir(import_module("typer"))), id="third party"
            ),
            pytest.param("not-exists", 0, None, id="not exists"),
        ],
    )
    def test_handle_c_libs_importables(self, module_name, level, expec_names):
        try:
            importables = scan.ImportablesAnalyzer.handle_c_libs_importables(
                module_name, level
            )
            self._assert_set_equal_or_not(importables, expec_names)
        except ModuleNotFoundError:
            assert module_name == "not-exists"

    @pytest.mark.parametrize(
        "code, expec_importables",
        [
            pytest.param(
                ("x = 'y'\n" "__all__ = ['i', 'j', 'k']"),
                {"i", "j", "k"},
                id="__all__ dunder overriding",
            )
        ],
    )
    def test_visit_Assign(self, code, expec_importables):
        self._assert_importables_and_not(code, expec_importables)

    @pytest.mark.parametrize(
        "code, expec_importables",
        [
            pytest.param(
                ("import x\n" "import y as z"),
                {"x", "z"},
                id="normal imports",
            )
        ],
    )
    def test_visit_Import(self, code, expec_importables):
        self._assert_importables_and_not(code, expec_importables)

    @pytest.mark.parametrize(
        "code, expec_importables",
        [
            pytest.param(
                ("from i import x\n" "from j import y as z"),
                {"x", "z"},
                id="normal imports",
            ),
            pytest.param(
                "from time import *\n",
                set(dir(import_module("time"))),
                id="standard star import",
            ),
            pytest.param(
                "from pycln import *\n",
                set(dir(import_module("pycln")) + ["cli"]),
                id="local star import",
            ),
        ],
    )
    def test_visit_ImportFrom(self, code, expec_importables):
        self._assert_importables_and_not(code, expec_importables)

    @pytest.mark.parametrize(
        "code, expec_importables, expec_not_importables",
        [
            pytest.param(
                ("def foo():\n" "    bar = 'x'\n"),
                {"foo"},
                {"bar"},
                id="function",
            ),
            pytest.param(
                ("async def foo():\n" "    bar = 'x'\n"),
                {"foo"},
                {"bar"},
                id="async-function",
            ),
        ],
    )
    def test_visit_FunctionDef(self, code, expec_importables, expec_not_importables):
        self._assert_importables_and_not(code, expec_importables, expec_not_importables)

    @pytest.mark.parametrize(
        "code, expec_importables, expec_not_importables",
        [
            pytest.param(
                ("class Foo:\n" "    bar = 'x'\n" "    def foo():\n" "        pass\n"),
                {"Foo"},
                {"bar", "foo"},
                id="class",
            )
        ],
    )
    def test_visit_ClassDef(self, code, expec_importables, expec_not_importables):
        self._assert_importables_and_not(code, expec_importables, expec_not_importables)

    @pytest.mark.parametrize(
        "code, expec_importables",
        [pytest.param("x, y, z = 'x', 'y', 'z'", {"x", "y", "z"}, id="normal names")],
    )
    def test_visit_Name(self, code, expec_importables):
        self._assert_importables_and_not(code, expec_importables)

    @pytest.mark.parametrize(
        "code, expec_not_importables",
        [
            pytest.param(
                ("def foo():\n" "    bar = 'x'\n"),
                {"bar"},
                id="function, name",
            ),
            pytest.param(
                ("async def foo():\n" "    bar = 'x'\n"),
                {"bar"},
                id="async function, name",
            ),
            pytest.param(
                ("def foo():\n" "    def bar():\n" "        pass\n"),
                {"bar"},
                id="function, function",
            ),
            pytest.param(
                ("class Foo:\n" "    bar = 'x'\n"),
                {"bar"},
                id="class, name",
            ),
            pytest.param(
                ("class Foo:\n" "    def bar():\n" "        pass\n"),
                {"bar"},
                id="class, function",
            ),
            pytest.param(
                ("class Foo:\n" "    class Bar:\n" "        pass\n"),
                {"Bar"},
                id="class, class",
            ),
        ],
    )
    def test_compute_not_importables(self, code, expec_not_importables):
        analyzer = scan.ImportablesAnalyzer(Path(""))
        analyzer._compute_not_importables(ast.parse(code).body[0])
        self._assert_not_importables(analyzer._not_importables, expec_not_importables)


class TestSideEffectsAnalyzer:

    """`SideEffectsAnalyzer` class tests."""

    def _assert_not_side_effects(
        self, not_side_effects: set, expec_not_side_effects: set
    ):
        str_set = set([call.func.id for call in not_side_effects])
        assert str_set == expec_not_side_effects

    def _assert_has_side_effects_and_not(
        self,
        code: str,
        expec_has_side_effects: scan.HasSideEffects,
        expec_not_side_effects=set(),
    ):
        analyzer = scan.SideEffectsAnalyzer()
        analyzer.visit(ast.parse(code))
        assert analyzer.has_side_effects() is expec_has_side_effects
        self._assert_not_side_effects(
            analyzer._not_side_effects, expec_not_side_effects
        )

    @pytest.mark.parametrize(
        "code, expec_has_side_effects, expec_not_side_effects",
        [
            pytest.param(
                ("def foo():\n" "    print()\n"),
                scan.HasSideEffects.NO,
                {"print"},
                id="call inside a function",
            ),
            pytest.param(
                ("async def foo():\n" "    print()\n"),
                scan.HasSideEffects.NO,
                {"print"},
                id="call inside a async-function",
            ),
        ],
    )
    def test_visit_FunctionDef(
        self, code, expec_has_side_effects, expec_not_side_effects
    ):
        self._assert_has_side_effects_and_not(
            code, expec_has_side_effects, expec_not_side_effects
        )

    @pytest.mark.parametrize(
        "code, expec_has_side_effects, expec_not_side_effects",
        [
            pytest.param(
                ("class Foo:\n" "    print()\n"),
                scan.HasSideEffects.NO,
                {"print"},
                id="call inside a class",
            )
        ],
    )
    def test_visit_ClassDef(self, code, expec_has_side_effects, expec_not_side_effects):
        self._assert_has_side_effects_and_not(
            code, expec_has_side_effects, expec_not_side_effects
        )

    @pytest.mark.parametrize(
        "code, expec_not_side_effects",
        [
            pytest.param(("def foo():\n" "    bar()\n"), {"bar"}, id="function"),
            pytest.param(
                ("async def foo():\n" "    bar()\n"),
                {"bar"},
                id="async-function",
            ),
            pytest.param(("class Foo:\n" "    bar()\n"), {"bar"}, id="class"),
        ],
    )
    def test_compute_not_side_effects(self, code, expec_not_side_effects):
        analyzer = scan.SideEffectsAnalyzer()
        analyzer._compute_not_side_effects(ast.parse(code).body[0])
        self._assert_not_side_effects(
            analyzer._not_side_effects, expec_not_side_effects
        )

    @pytest.mark.parametrize(
        "code, expec_has_side_effects",
        [
            pytest.param(
                "print()\n",
                scan.HasSideEffects.YES,
                id="normal call",
            )
        ],
    )
    def test_visit_Call(self, code, expec_has_side_effects):
        self._assert_has_side_effects_and_not(code, expec_has_side_effects)

    @pytest.mark.parametrize(
        "code, expec_has_side_effects",
        [
            pytest.param(
                "import time, os\n",
                scan.HasSideEffects.NO,
                id="known standard modules",
            ),
            pytest.param(
                "import antigravity\n",
                scan.HasSideEffects.YES,
                id="known imports with side effects",
            ),
            pytest.param(
                "import unknown\n",
                scan.HasSideEffects.MAYBE,
                id="unknown imports (third party)",
            ),
        ],
    )
    def test_visit_Import(self, code, expec_has_side_effects):
        self._assert_has_side_effects_and_not(code, expec_has_side_effects)

    @pytest.mark.parametrize(
        "code, expec_has_side_effects",
        [
            pytest.param(
                "from time.time import time\n",
                scan.HasSideEffects.NO,
                id="known standard modules",
            ),
            pytest.param(
                "from antigravity import time\n",
                scan.HasSideEffects.YES,
                id="known imports with side effects ~> on from",
            ),
            pytest.param(
                "from time import antigravity\n",
                scan.HasSideEffects.YES,
                id="known imports with side effects ~> on import",
            ),
            pytest.param(
                "from unknown import time\n",
                scan.HasSideEffects.MAYBE,
                id="unknown imports (third party) -> on from",
            ),
            pytest.param(
                "from time import unknown\n",
                scan.HasSideEffects.MAYBE,
                id="unknown imports (third party) -> on import",
            ),
        ],
    )
    def test_visit_ImportFrom(self, code, expec_has_side_effects):
        self._assert_has_side_effects_and_not(code, expec_has_side_effects)

    @pytest.mark.parametrize(
        "names, expec_has_side_effects",
        [
            pytest.param(
                ("time", "os", "sys"),
                scan.HasSideEffects.NO,
                id="known standard modules",
            ),
            pytest.param(
                ("antigravity", "this", "rlcompleter"),
                scan.HasSideEffects.YES,
                id="known imports with side effects",
            ),
            pytest.param(
                ("unknows", "x", "y"),
                scan.HasSideEffects.MAYBE,
                id="unknown imports (third party)",
            ),
        ],
    )
    def test_check_names(self, names, expec_has_side_effects):
        aliases = [ast.alias(name=n, asname=None) for n in names]
        analyzer = scan.SideEffectsAnalyzer()
        assert analyzer._check_names(aliases) is expec_has_side_effects


class TestScanFunctions(AnalyzerTestCase):

    """`scan.py` functions test case."""

    @pytest.mark.parametrize(
        "code, expec_err_type, some_expec_importables",
        [
            pytest.param(
                "from ast import *\n",
                None,
                set(dir(import_module("ast"))),
                id="standard module",
            ),
            pytest.param(
                "from time import *\n",
                None,
                set(dir(import_module("time"))),
                id="cpython embedded module",
            ),
            pytest.param(
                "from pycln import *\n",
                None,
                set(dir(import_module("pycln")) + ["cli"]),
                id="local module",
            ),
            pytest.param(
                "from unimportable import *\n",
                UnexpandableImportStar,
                None,
                id="module not found",
            ),
        ],
    )
    def test_expand_import_star(self, code, expec_err_type, some_expec_importables):
        err_type = None
        try:
            node = ast.parse(code).body[0]
            expanded_node = scan.expand_import_star(node, Path(__file__))
            names = set(
                [(a.asname if a.asname else a.name) for a in expanded_node.names]
            )
            assert self._normalize_set(names).issuperset(
                self._normalize_set(some_expec_importables)
            )
        except UnexpandableImportStar:
            err_type = UnexpandableImportStar
        assert err_type == expec_err_type

    def _assert_ast_equal(
        self,
        code: str,
        mode: str,
        expec_err_type: Exception,
        type_comment: Optional[str] = None,
    ):
        err_type = None
        try:
            ast_tree = scan.parse_ast(code, mode=mode)
            assert ast_tree
            if type_comment:
                tc = ast_tree.body[0].type_comment  # type: ignore
                assert tc == type_comment
        except UnparsableFile:
            err_type = UnparsableFile
        assert err_type == expec_err_type

    @pytest.mark.skipif(not PY38_PLUS, reason="Python >=3.8 type comment support.")
    @pytest.mark.parametrize(
        "code, mode, expec_err_type, type_comment",
        [
            pytest.param(
                ("foo = 'bar'  # type: List[str]\n"),
                "exec",
                None,
                "List[str]",
                id="var type comment",
            ),
            pytest.param(
                ("def foo(bar):\n" "    # type: (str) -> List[str]\n" "    pass\n"),
                "exec",
                None,
                "(str) -> List[str]",
                id="function type comment",
            ),
            pytest.param("List[str]", "eval", None, None, id="only var type comment"),
            pytest.param(
                "(str) -> List[str]",
                "func_type",
                None,
                None,
                id="only function type comment",
            ),
            pytest.param("print()\n", "exec", None, None, id="normal code"),
            pytest.param(
                "@print(SyntaxError)\n",
                "exec",
                UnparsableFile,
                None,
                id="syntax error",
            ),
            pytest.param(
                b"\x00print('Hello')",
                "exec",
                UnparsableFile,
                None,
                id="contain null bytes",
            ),
        ],
    )
    def test_parse_ast_py38_plus(self, code, mode, expec_err_type, type_comment):
        self._assert_ast_equal(code, mode, expec_err_type, type_comment)

    @pytest.mark.skipif(PY38_PLUS, reason="No Python >=3.8 type comment support.")
    @pytest.mark.parametrize(
        "code, mode, expec_err_type",
        [
            pytest.param("print()\n", "exec", None, id="normal code"),
            pytest.param(
                "@print(SyntaxError)\n",
                "exec",
                UnparsableFile,
                id="syntax error",
            ),
            pytest.param(
                b"\x00print('Hello')",
                "exec",
                UnparsableFile,
                id="contain null bytes",
            ),
        ],
    )
    def test_parse_ast_py37_minus(self, code, mode, expec_err_type):
        self._assert_ast_equal(code, mode, expec_err_type)
