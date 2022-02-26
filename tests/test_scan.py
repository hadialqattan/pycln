"""pycln/utils/scan.py tests."""
# pylint: disable=R0201,W0613
import ast
import sys
from importlib import import_module
from pathlib import Path
from typing import Optional
from unittest import mock

import pytest

from pycln.utils import _nodes, scan
from pycln.utils._exceptions import UnexpandableImportStar, UnparsableFile

from .utils import sysu

# Constants.
MOCK = "pycln.utils.scan.%s"
PY38_PLUS = sys.version_info >= (3, 8)
PY310_PLUS = sys.version_info >= (3, 10)


class TestDataclasses:

    """`scan.py` dataclasses test case."""

    def test_import_stats_iter(self):
        import_stats = scan.ImportStats({"import"}, {"from"})
        assert list(import_stats) == [{"import"}, {"from"}]

    def test_source_stats_iter(self):
        source_stats = scan.SourceStats({"name"}, {"attr"}, {"skip"})
        assert list(source_stats) == [{"name"}, {"attr"}]


class AnalyzerTestCase:

    """`scan.*Analyzer` test case."""

    def assert_set_equal_or_not(self, set_: set, expec_set: set):
        if expec_set:
            assert set_ == expec_set
        else:
            assert not set_

    def normalize_set(self, set_: set) -> set:
        # Remove any dunder name from the given set.
        return {i for i in set_ if not i.startswith("__")}


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
            assert not imports

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
            pytest.param([], sysu.Pass, id="with source lines"),
            pytest.param(None, sysu.Pass, id="without source lines"),
        ],
    )
    def test_init_py38_plus(self, source_lines, expec_error):
        # Test `__init__` dunder method for Python >=3.8.
        with pytest.raises(expec_error):
            scan.SourceAnalyzer(source_lines)
            raise sysu.Pass()

    @pytest.mark.skipif(PY38_PLUS, reason="Python <3.8 class usage.")
    @pytest.mark.parametrize(
        "source_lines, expec_error",
        [
            pytest.param([], sysu.Pass, id="with source lines"),
            pytest.param(None, ValueError, id="without source lines"),
        ],
    )
    def test_init_py37_minus(self, source_lines, expec_error):
        # Test `__init__` dunder method for Python <3.8.
        with pytest.raises(expec_error):
            scan.SourceAnalyzer(source_lines)
            raise sysu.Pass()

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
            pytest.param(
                ("def foo(bar: str):\n" "    pass\n"), {"str"}, id="normal types - arg"
            ),
            pytest.param(
                ("def foo() -> str :\n" "    pass\n"),
                {"str"},
                id="normal types - return",
            ),
            pytest.param(
                ("def foo(bar: str | int):\n" "    pass\n"),
                {"str", "int"},
                id="union types - arg",
                marks=pytest.mark.skipif(
                    not PY310_PLUS,
                    reason="This feature is only available in Python >=3.10.",
                ),
            ),
            pytest.param(
                ("def foo() -> str | int :\n" "    pass\n"),
                {"str", "int"},
                id="union types - return",
                marks=pytest.mark.skipif(
                    not PY310_PLUS,
                    reason="This feature is only available in Python >=3.10.",
                ),
            ),
        ],
    )
    def test_visit_Name(self, code, expec_names):
        analyzer = self._get_analyzer(code)
        source_stats, _ = analyzer.get_stats()
        self.assert_set_equal_or_not(source_stats.name_, expec_names)

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
        self.assert_set_equal_or_not(source_stats.attr_, expec_attrs)

    @pytest.mark.skipif(
        not PY310_PLUS, reason="Match/MatchAs nodes only available in Python >=3.10."
    )
    @pytest.mark.parametrize(
        "code, expec_names, expec_attrs",
        [
            pytest.param(
                (
                    "def foo():\n"
                    "    match x:\n"
                    "       case '':\n"
                    "           return ''\n"
                ),
                {"x"},
                set({}),
                id="subject",
            ),
            pytest.param(
                (
                    "def foo():\n"
                    "    match '':\n"
                    "       case x:\n"
                    "           return ''\n"
                ),
                {"x"},
                set({}),
                id="case name",
            ),
            pytest.param(
                (
                    "def foo():\n"
                    "    match '':\n"
                    "       case x | y:\n"
                    "           return ''\n"
                ),
                {"x", "y"},
                set({}),
                id="case name1 | name2",
            ),
            pytest.param(
                (
                    "def foo():\n"
                    "    match '':\n"
                    "       case x.i | y.j:\n"
                    "           return ''\n"
                ),
                {"x", "y"},
                {"i", "j"},
                id="case name1.attr | name2.attr",
            ),
            pytest.param(
                (
                    "def foo():\n"
                    "    match '':\n"
                    "       case (x, y):\n"
                    "           return ''\n"
                ),
                {"x", "y"},
                set({}),
                id="case (name1, name2)",
            ),
            pytest.param(
                (
                    "def foo():\n"
                    "    match '':\n"
                    "       case (x.i, y.j):\n"
                    "           return ''\n"
                ),
                {"x", "y"},
                {"i", "j"},
                id="case (name1.attr, name2.attr)",
            ),
            pytest.param(
                (
                    "def foo():\n"
                    "    match '':\n"
                    "       case Class():\n"
                    "           return ''\n"
                ),
                {"Class"},
                set({}),
                id="case-cls",
            ),
            pytest.param(
                (
                    "def foo():\n"
                    "    match '':\n"
                    "       case Class(x, y):\n"
                    "           return ''\n"
                ),
                {"Class", "x", "y"},
                set({}),
                id="case-cls(name1, name2)",
            ),
            pytest.param(
                (
                    "def foo():\n"
                    "    match '':\n"
                    "       case Class(x.i, y.j):\n"
                    "           return ''\n"
                ),
                {"Class", "x", "y"},
                {"j", "i"},
                id="case-cls(name1.attr, name2.attr)",
            ),
        ],
    )
    def test_visit_MatchAs(self, code, expec_names, expec_attrs):
        analyzer = self._get_analyzer(code)
        source_stats, _ = analyzer.get_stats()
        self.assert_set_equal_or_not(source_stats.name_, expec_names)
        self.assert_set_equal_or_not(source_stats.attr_, expec_attrs)

    @pytest.mark.parametrize(
        "code, expec_names, expec_attrs",
        [
            pytest.param(
                (
                    "from typing import cast\n"
                    "import foo, bar\n"
                    "baz = cast('foo', bar)\n"
                ),
                {"cast", "foo", "bar", "baz"},
                set(),
                id="cast name",
            ),
            pytest.param(
                (
                    "import typing\n"
                    "import foo, bar\n"
                    "baz = typing.cast('foo', bar)\n"
                ),
                {"typing", "foo", "bar", "baz"},
                {"cast"},
                id="typing.cast name",
            ),
            pytest.param(
                (
                    "from typing import cast\n"
                    "import foo.x, bar\n"
                    "baz = cast('foo.x', bar)\n"
                ),
                {"cast", "foo", "bar", "baz"},
                {"x"},
                id="cast attr-0",
            ),
            pytest.param(
                ("import typing\n" "import foo, bar\n" "baz = cast('foo.x', bar)\n"),
                {"cast", "foo", "bar", "baz"},
                {"x"},
                id="cast attr-1",
            ),
        ],
    )
    def test_visit_Call(self, code, expec_names, expec_attrs):
        analyzer = self._get_analyzer(code)
        source_stats, _ = analyzer.get_stats()
        self.assert_set_equal_or_not(source_stats.name_, expec_names)
        self.assert_set_equal_or_not(source_stats.attr_, expec_attrs)

    @pytest.mark.parametrize(
        "code, expec_names, expec_attrs",
        [
            pytest.param(
                ("from typing import List\n" "import foo\n" "baz = List['foo']\n"),
                {"List", "foo", "baz"},
                set(),
                id="str-name",
            ),
            pytest.param(
                ("from typing import List\n" "import foo.x\n" "baz = List['foo.x']\n"),
                {"List", "foo", "baz"},
                {"x"},
                id="str-attr",
            ),
            pytest.param(
                (
                    "from typing import Union\n"
                    "import foo, bar\n"
                    "baz = Union['foo', 'bar']\n"
                ),
                {"Union", "foo", "bar", "baz"},
                set(),
                id="tuple-name",
            ),
            pytest.param(
                (
                    "from typing import Union\n"
                    "import foo.x, bar.y\n"
                    "baz = Union['foo.x', 'bar.y']\n"
                ),
                {"Union", "foo", "bar", "baz"},
                {"x", "y"},
                id="tuple-attr",
            ),
            pytest.param(
                (
                    "from typing import Union\n"
                    "import bar.y\n"
                    "baz = Union['foo x', 'bar.y']\n"
                ),
                {"Union", "bar", "baz"},
                {"y"},
                id="literal with space (i41)",
            ),
        ],
    )
    def test_visit_Subscript(self, code, expec_names, expec_attrs):
        analyzer = self._get_analyzer(code)
        source_stats, _ = analyzer.get_stats()
        self.assert_set_equal_or_not(source_stats.name_, expec_names)
        self.assert_set_equal_or_not(source_stats.attr_, expec_attrs)

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
                "__all__ = ['x', 'y', 'z']",
                {"x", "y", "z"},
                {"__all__"},
                id="__all__ dunder overriding",
            ),
            pytest.param(
                "__all__ = ['x', 'y'] + ['i', 'j'] + ['z']",
                {"x", "y", "i", "j", "z"},
                {"__all__"},
                id="__all__ dunder overriding - concatenation",
            ),
        ],
    )
    @mock.patch(MOCK % "SourceAnalyzer.visit_Name")
    def test_visit_Assign(self, visit_Name, code, expec_names, expec_names_to_skip):
        analyzer = self._get_analyzer(code)
        source_stats, _ = analyzer.get_stats()
        self.assert_set_equal_or_not(source_stats.name_, expec_names)
        self.assert_set_equal_or_not(source_stats.names_to_skip, expec_names_to_skip)

    @pytest.mark.parametrize(
        "code, expec_names",
        [
            pytest.param(
                "__all__ += ['x', 'y', 'z']",
                {"x", "y", "z"},
                id="__all__ dunder overriding - aug assign",
            ),
            pytest.param(
                "__all__ += ['x', 'y'] + ['i', 'j'] + ['z']",
                {"x", "y", "i", "j", "z"},
                id="__all__ dunder overriding - aug assign & concatenation",
            ),
        ],
    )
    @mock.patch(MOCK % "SourceAnalyzer.visit_Name")
    def test_visit_AugAssign(self, visit_Name, code, expec_names):
        analyzer = self._get_analyzer(code)
        source_stats, _ = analyzer.get_stats()
        self.assert_set_equal_or_not(source_stats.name_, expec_names)

    @pytest.mark.parametrize(
        "code, expec_names",
        [
            pytest.param(
                "__all__.append('x', 'y', 'z')",
                {"x", "y", "z"},
                id="__all__ dunder overriding - append",
            ),
            pytest.param(
                "__all__.extend(['x', 'y', 'z'])",
                {"x", "y", "z"},
                id="__all__ dunder overriding - extend",
            ),
        ],
    )
    @mock.patch(MOCK % "SourceAnalyzer.visit_Name")
    def test_visit_Expr(self, visit_Name, code, expec_names):
        analyzer = self._get_analyzer(code)
        source_stats, _ = analyzer.get_stats()
        self.assert_set_equal_or_not(source_stats.name_, expec_names)

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
            pytest.param(
                "foo: \"List['str']\" = []\n", {"List", "str"}, id="nested-string"
            ),
            pytest.param("foobar: '' = 'x'\n", None, id="empty string annotation"),
            pytest.param("foobar = 'x'\n", None, id="no string annotation"),
        ],
    )
    @mock.patch(MOCK % "SourceAnalyzer.visit_Name")
    def test_visit_string_type_annotation(self, visit_Name, code, expec_names):
        analyzer = self._get_analyzer(code)
        source_stats, _ = analyzer.get_stats()
        self.assert_set_equal_or_not(source_stats.name_, expec_names)

    @pytest.mark.skipif(
        not PY38_PLUS,
        reason="This feature is only available in Python >=3.8.",
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
            pytest.param(
                "foo = []  # type: optional, defaults to '[]'\n",
                set({}),
                id="non-valid",
            ),
        ],
    )
    @mock.patch(MOCK % "SourceAnalyzer.visit_Name")
    def test_visit_type_comment(self, visit_Name, code, expec_names):
        analyzer = self._get_analyzer(code)
        source_stats, _ = analyzer.get_stats()
        self.assert_set_equal_or_not(source_stats.name_, expec_names)

    @pytest.mark.parametrize(
        "code, is_str_annotation, expec_names, expec_attrs",
        [
            pytest.param("x, y", False, {"x", "y"}, None, id="names, no-attr"),
            pytest.param("x.i, y.j", False, {"x", "y"}, {"i", "j"}, id="names, attrs"),
            pytest.param("'y'", True, {"y"}, None, id="const"),
            pytest.param("'y'", False, None, None, id="not const"),
            pytest.param("", False, None, None, id="no-names, no-attrs"),
        ],
    )
    def test_add_name_attr_const(
        self, code, is_str_annotation, expec_names, expec_attrs
    ):
        analyzer = scan.SourceAnalyzer([])
        analyzer._add_name_attr_const(ast.parse(code), is_str_annotation)
        source_stats, _ = analyzer.get_stats()
        self.assert_set_equal_or_not(source_stats.name_, expec_names)
        self.assert_set_equal_or_not(source_stats.attr_, expec_attrs)

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

    @pytest.mark.parametrize(
        "code, expec",
        [
            pytest.param(
                "__all__ = []\n",
                True,
                id="__all__ - assign",
            ),
            pytest.param(
                "__all__ += []\n",
                True,
                id="__all__ - aug-assign",
            ),
            pytest.param(
                "x = []\n",
                False,
                id="no __all__",
            ),
        ],
    )
    def test_has_all(self, code, expec):
        analyzer = self._get_analyzer(code)
        assert analyzer.has_all() == expec


class TestImportablesAnalyzer(AnalyzerTestCase):

    """`ImportablesAnalyzer` class tests."""

    def _assert_not_importables(self, not_importables: set, expec_not_importables: set):
        str_set = {(n.id if hasattr(n, "id") else n) for n in not_importables}
        assert str_set == expec_not_importables

    def _assert_importables_and_not(
        self, code: str, expec_importables: set, expec_not_importables=frozenset()
    ):
        analyzer = scan.ImportablesAnalyzer(Path(__file__))
        analyzer.visit(ast.parse(code))
        importables = analyzer.get_stats()
        if expec_importables:
            assert self.normalize_set(importables) == self.normalize_set(
                expec_importables
            )
        else:
            assert importables
        self._assert_not_importables(analyzer._not_importables, expec_not_importables)

    @pytest.mark.parametrize(
        "code, expec_importables",
        [
            pytest.param(
                ("x = 'y'\n" "__all__ = ['i', 'j', 'k']\n" "a = 'b'"),
                {"i", "j", "k"},
                id="__all__ dunder overriding",
            ),
            pytest.param(
                ("x = 'y'\n" "__all__ = ['x', 'y'] + ['i', 'j'] + ['z']\n" "a = 'b'"),
                {"x", "y", "i", "j", "z"},
                id="__all__ dunder overriding - concatenation",
            ),
        ],
    )
    def test_visit_Assign(self, code, expec_importables):
        self._assert_importables_and_not(code, expec_importables)

    @pytest.mark.parametrize(
        "code, expec_importables",
        [
            pytest.param(
                ("__all__ += ['i', 'j', 'k']\n" "x = 'y'"),
                {"i", "j", "k"},
                id="__all__ dunder overriding - aug assign",
            ),
            pytest.param(
                ("__all__ += ['x', 'y'] + ['i', 'j'] + ['z']\n" "a = 'b'"),
                {"x", "y", "i", "j", "z"},
                id="__all__ dunder overriding - aug assign and concatenation",
            ),
        ],
    )
    def test_visit_AugAssign(self, code, expec_importables):
        self._assert_importables_and_not(code, expec_importables)

    @pytest.mark.parametrize(
        "code, expec_importables",
        [
            pytest.param(
                ("x = 'y'\n" "__all__.append('x', 'y', 'z')"),
                {"x", "y", "z"},
                id="__all__ dunder overriding - append",
            ),
            pytest.param(
                ("x = 'y'\n" "__all__.extend(['x', 'y', 'z'])"),
                {"x", "y", "z"},
                id="__all__ dunder overriding - extend",
            ),
        ],
    )
    def test_visit_Expr(self, code, expec_importables):
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
                "from os import *\n",
                None,
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
        str_set = {call.func.id for call in not_side_effects}
        assert str_set == expec_not_side_effects

    def _assert_has_side_effects_and_not(
        self,
        code: str,
        expec_has_side_effects: scan.HasSideEffects,
        expec_not_side_effects=frozenset(),
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
                sysu.Pass,
                set(dir(import_module("ast"))),
                id="standard module",
            ),
            pytest.param(
                "from pycln import *\n",
                sysu.Pass,
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
        with pytest.raises(expec_err_type):
            node = ast.parse(code).body[0]
            expanded_node = scan.expand_import_star(node, Path(__file__))
            names = {(a.asname if a.asname else a.name) for a in expanded_node.names}
            assert self.normalize_set(names)
            raise sysu.Pass()

    @mock.patch(MOCK % "ImportablesAnalyzer.visit")
    def test_expand_import_star_stackoverflow(self, tree_visiting):
        tree_visiting.side_effect = RecursionError()
        with pytest.raises(UnexpandableImportStar):
            node = ast.parse("from pycln import *\n").body[0]
            scan.expand_import_star(node, Path(__file__))

    def _assert_ast_equal(
        self,
        code: str,
        mode: str,
        expec_err_type: Exception,
        type_comment: Optional[str] = None,
    ):
        with pytest.raises(expec_err_type):
            ast_tree = scan.parse_ast(code, mode=mode)
            assert ast_tree
            if type_comment:
                tc = ast_tree.body[0].type_comment  # type: ignore
                assert tc == type_comment
            raise sysu.Pass()

    @pytest.mark.skipif(not PY38_PLUS, reason="Python >=3.8 type comment support.")
    @pytest.mark.parametrize(
        "code, mode, expec_err_type, type_comment",
        [
            pytest.param(
                ("foo = 'bar'  # type: List[str]\n"),
                "exec",
                sysu.Pass,
                "List[str]",
                id="var type comment",
            ),
            pytest.param(
                ("def foo(bar):\n" "    # type: (str) -> List[str]\n" "    pass\n"),
                "exec",
                sysu.Pass,
                "(str) -> List[str]",
                id="function type comment",
            ),
            pytest.param(
                "List[str]", "eval", sysu.Pass, None, id="only var type comment"
            ),
            pytest.param(
                "(str) -> List[str]",
                "func_type",
                sysu.Pass,
                None,
                id="only function type comment",
            ),
            pytest.param("print()\n", "exec", sysu.Pass, None, id="normal code"),
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
            pytest.param(
                ("if x:\n" "    # type: x + y\n" "    x = 'y'\n"),
                "exec",
                UnparsableFile,
                None,
                id="indentation error",
            ),
        ],
    )
    def test_parse_ast_py38_plus(self, code, mode, expec_err_type, type_comment):
        self._assert_ast_equal(code, mode, expec_err_type, type_comment)

    @pytest.mark.skipif(PY38_PLUS, reason="No Python >=3.8 type comment support.")
    @pytest.mark.parametrize(
        "code, mode, expec_err_type",
        [
            pytest.param("print()\n", "exec", sysu.Pass, id="normal code"),
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
