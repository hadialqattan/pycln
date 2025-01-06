"""pycln/utils/transform.py tests."""

# pylint: disable=R0201,W0613
from pathlib import Path
from typing import Union
from unittest import mock

import libcst as cst
import pytest

from pycln.utils import transform
from pycln.utils._exceptions import UnsupportedCase
from pycln.utils._nodes import NodeLocation

from .utils import sysu

# Constants.
MOCK = "pycln.utils.transform.%s"


class TestImportTransformer:
    """`ImportTransformer` methods test case."""

    def _assert_import_equal(
        self, impt_stmnt: str, endlineno: int, used_names: set, expec_impt: str
    ):
        location = NodeLocation((1, 0), endlineno)
        transformer = transform.ImportTransformer(used_names, location)
        cst_tree = cst.parse_module(impt_stmnt)
        assert cst_tree.visit(transformer).code == expec_impt

    @pytest.mark.parametrize(
        "used_names, location, expec_err",
        [
            pytest.param(
                {"x", "y", "z"},
                NodeLocation((1, 4), 0),
                sysu.Pass,
                id="pass used_names",
            ),
            pytest.param(set(), None, ValueError, id="pass no used_names"),
        ],
    )
    def test_init(self, used_names, location, expec_err):
        with pytest.raises(expec_err):
            transform.ImportTransformer(used_names, location)
            raise sysu.Pass()

    @pytest.mark.parametrize(
        "impt_stmnt, endlineno, used_names, expec_impt",
        [
            pytest.param(
                "import x, y, z",
                1,
                ("x", "y", "z"),
                "import x, y, z",
                id="single, no-unused",
            ),
            pytest.param(
                "import x, y, z",
                1,
                ("x", "z"),
                "import x, z",
                id="single, some-unused",
            ),
            pytest.param(
                "import xx as x, yy as y, zz as z",
                1,
                ("xx", "yy", "zz"),
                "import xx as x, yy as y, zz as z",
                id="single, no-unused, as",
            ),
            pytest.param(
                "import xx as x, yy as y, zz as z",
                1,
                ("xx", "zz"),
                "import xx as x, zz as z",
                id="single, some-unused, as",
            ),
            pytest.param(
                ("import \\\n" "    x, y, z"),
                2,
                ("x", "y", "z"),
                ("import \\\n" "    x, y, z"),
                id="multi, no-unused",
            ),
            pytest.param(
                ("import \\\n" "    x, y, z"),
                2,
                ("x", "z"),
                ("import \\\n" "    x, z"),
                id="multi, some-unused",
            ),
            pytest.param(
                ("import \\\n" "    xx as x, yy as y, zz as z"),
                2,
                ("xx", "yy", "zz"),
                ("import \\\n" "    xx as x, yy as y, zz as z"),
                id="multi, no-unused, as",
            ),
            pytest.param(
                ("import \\\n" "    xx as x, yy as y, zz as z"),
                2,
                ("xx", "zz"),
                ("import \\\n" "    xx as x, zz as z"),
                id="multi, some-unused, as",
            ),
        ],
    )
    def test_leave_Import(self, impt_stmnt, endlineno, used_names, expec_impt):
        #: `leave_Import` returns `refactor_import`.
        #: so if there's a bug, please debug `refactor_import`.
        self._assert_import_equal(impt_stmnt, endlineno, used_names, expec_impt)

    @pytest.mark.parametrize(
        "impt_stmnt, endlineno, used_names, expec_impt",
        [
            pytest.param(
                "from x import *",
                1,
                ("x", "y", "z"),
                "from x import x, y, z",
                id="single, star",
            ),
            pytest.param(
                "from x import *",
                1,
                ("x", "y", "z", "i", "j"),
                (
                    "from x import (\n"
                    "    x,\n"
                    "    y,\n"
                    "    z,\n"
                    "    i,\n"
                    "    j\n"
                    ")"
                ),
                id="multi, star",
            ),
            pytest.param(
                "from x import *",
                1,
                ("x", "y", "z", "i", "j.j"),
                ("from x import (\n" "    x,\n" "    y,\n" "    z,\n" "    i\n" ")"),
                id="multi, star, names collision",
            ),
            pytest.param(
                "from xxx import x, y, z",
                1,
                ("x", "y", "z"),
                "from xxx import x, y, z",
                id="single, no-unused",
            ),
            pytest.param(
                "from xxx import x, y, z",
                1,
                ("x", "z"),
                "from xxx import x, z",
                id="single, some-unused",
            ),
            pytest.param(
                "from xxx import (x, y, z)",
                1,
                ("x", "y", "z"),
                "from xxx import (x, y, z)",
                id="single, parentheses, no-end-comma, no-unused",
            ),
            pytest.param(
                "from xxx import (x, y, z)",
                1,
                ("x", "z"),
                "from xxx import (x, z)",
                id="single, parentheses, no-end-comma, some-unused",
            ),
            pytest.param(
                "from xxx import (x, y, z)",
                1,
                ("x", "y", "z"),
                "from xxx import (x, y, z)",
                id="single, parentheses, end-comma, no-unused",
            ),
            pytest.param(
                "from xxx import (x, y, z,)",
                1,
                ("x", "z"),
                "from xxx import (x, z,)",
                id="single, parentheses, nend-comma, some-unused",
            ),
            pytest.param(
                "from xxx import xx as x, yy as y, zz as z",
                1,
                ("xx", "yy", "zz"),
                "from xxx import xx as x, yy as y, zz as z",
                id="single, no-unused, as",
            ),
            pytest.param(
                "from xxx import xx as x, yy as y, zz as z",
                1,
                ("xx", "zz"),
                "from xxx import xx as x, zz as z",
                id="single, some-unused, as",
            ),
            pytest.param(
                ("from xxx import x,\\\n" "    y, \\\n" "    z"),
                3,
                ("x", "y", "z"),
                ("from xxx import x,\\\n" "    y, \\\n" "    z"),
                id="multi, slash, no-unused",
            ),
            pytest.param(
                ("from xxx import x,\\\n" "    y, \\\n" "    z"),
                3,
                ("x", "z"),
                ("from xxx import x,\\\n" "    z"),
                id="multi, slash, some-unused",
            ),
            pytest.param(
                ("from xxx import x,\\\n" "    y, z"),
                2,
                ("x", "z"),
                ("from xxx import x,\\\n" "    z"),
                id="multi, slash, double, some-unused",
            ),
            pytest.param(
                ("from xxx import xx as x,\\\n" "    yy as y, \\\n" "    zz as z"),
                3,
                ("xx", "yy", "zz"),
                ("from xxx import xx as x,\\\n" "    yy as y, \\\n" "    zz as z"),
                id="multi, slash, no-unused, as",
            ),
            pytest.param(
                ("from xxx import xx as x,\\\n" "    yy as y, \\\n" "    zz as z"),
                3,
                ("xx", "zz"),
                ("from xxx import xx as x,\\\n" "    zz as z"),
                id="multi, slash, some-unused, as",
            ),
            pytest.param(
                ("from xxx import xx as x,\\\n" "    yy as y, zz as z"),
                2,
                ("xx", "zz"),
                ("from xxx import xx as x,\\\n" "    zz as z"),
                id="multi, slash, double, some-unused, as",
            ),
            pytest.param(
                ("from xxx import (\n" "    x,\n" "    y,\n" "    z\n" ")"),
                5,
                ("x", "y", "z"),
                ("from xxx import (\n" "    x,\n" "    y,\n" "    z\n" ")"),
                id="multi, parentheses, no-end-comma, no-unused",
            ),
            pytest.param(
                ("from xxx import (\n" "    x,\n" "    y,\n" "    z,\n" ")"),
                5,
                ("x", "y", "z"),
                ("from xxx import (\n" "    x,\n" "    y,\n" "    z,\n" ")"),
                id="multi, parentheses, end-comma, no-unused",
            ),
            pytest.param(
                ("from xxx import (\n" "    x,\n" "    y,\n" "    z\n" ")"),
                5,
                ("x", "z"),
                ("from xxx import (\n" "    x,\n" "    z\n" ")"),
                id="multi, parentheses, no-end-comma, some-unused",
            ),
            pytest.param(
                ("from xxx import (\n" "    x,\n" "    y,\n" "    z,\n" ")"),
                5,
                ("x", "z"),
                ("from xxx import (\n" "    x,\n" "    z,\n" ")"),
                id="multi, parentheses, end-comma, some-unused",
            ),
            pytest.param(
                ("from xxx import (\n" "    x,\n" "    y, z\n" ")"),
                4,
                ("x", "z"),
                ("from xxx import (\n" "    x,\n" "    z\n" ")"),
                id="multi, parentheses, double, no-end-comma, some-unused",
            ),
            pytest.param(
                ("from xxx import (\n" "    x,\n" "    y, z,\n" ")"),
                4,
                ("x", "z"),
                ("from xxx import (\n" "    x,\n" "    z,\n" ")"),
                id="multi, parentheses, double, end-comma, some-unused",
            ),
            pytest.param(
                (
                    "from xxx import (\n"
                    "    xx as x,\n"
                    "    yy as y,\n"
                    "    zz as z\n"
                    ")"
                ),
                5,
                ("xx", "yy", "zz"),
                (
                    "from xxx import (\n"
                    "    xx as x,\n"
                    "    yy as y,\n"
                    "    zz as z\n"
                    ")"
                ),
                id="multi, parentheses, no-end-comma, no-unused, as",
            ),
            pytest.param(
                (
                    "from xxx import (\n"
                    "    xx as x,\n"
                    "    yy as y,\n"
                    "    zz as z,\n"
                    ")"
                ),
                5,
                ("xx", "yy", "zz"),
                (
                    "from xxx import (\n"
                    "    xx as x,\n"
                    "    yy as y,\n"
                    "    zz as z,\n"
                    ")"
                ),
                id="multi, parentheses, end-comma, no-unused, as",
            ),
            pytest.param(
                (
                    "from xxx import (\n"
                    "    xx as x,\n"
                    "    yy as y,\n"
                    "    zz as z\n"
                    ")"
                ),
                5,
                ("xx", "zz"),
                ("from xxx import (\n" "    xx as x,\n" "    zz as z\n" ")"),
                id="multi, parentheses, no-end-comma, some-unused, as",
            ),
            pytest.param(
                (
                    "from xxx import (\n"
                    "    xx as x,\n"
                    "    yy as y,\n"
                    "    zz as z,\n"
                    ")"
                ),
                5,
                ("xx", "zz"),
                ("from xxx import (\n" "    xx as x,\n" "    zz as z,\n" ")"),
                id="multi, parentheses, end-comma, some-unused, as",
            ),
            pytest.param(
                ("from xxx import (\n" "    xx as x,\n" "    yy as y, zz as z\n" ")"),
                4,
                ("xx", "zz"),
                ("from xxx import (\n" "    xx as x,\n" "    zz as z\n" ")"),
                id="multi, parentheses, double, no-end-comma, some-unused, as",
            ),
            pytest.param(
                ("from xxx import (\n" "    xx as x,\n" "    yy as y, zz as z,\n" ")"),
                4,
                ("xx", "zz"),
                ("from xxx import (\n" "    xx as x,\n" "    zz as z,\n" ")"),
                id="multi, parentheses, double, end-comma, some-unused, as",
            ),
            pytest.param(
                ("from xxx import (x,\n" "    y,\n" "    z,)"),
                3,
                ("x", "z"),
                ("from xxx import (x,\n" "    z,)"),
                id="multi, parentheses(no-new-lines), end-comma, some-unused",
            ),
        ],
    )
    def test_leave_ImportFrom(self, impt_stmnt, endlineno, used_names, expec_impt):
        #: `leave_ImportFrom` returns:
        #:      - `refactor_import_star` when * import passed.
        #:      - otherwise `refactor_import`.
        #: Debug `refactor_import_star` or `refactor_import`.
        self._assert_import_equal(impt_stmnt, endlineno, used_names, expec_impt)

    @pytest.mark.parametrize("name", ["x", "x.y", "x.y.z"])
    @mock.patch(MOCK % "ImportTransformer.__init__")
    def test_get_alias_name(self, init, name):
        init.return_value = None

        def get_name_node(name: str) -> Union[cst.Name, cst.Attribute]:
            # Inverse `_get_alias_name`.
            if "." not in name:
                return cst.Name(name)
            names = name.split(".")
            value = get_name_node(".".join(names[:-1]))
            attr = get_name_node(names[-1])
            return cst.Attribute(value=value, attr=attr)

        node = get_name_node(name)
        transformer = transform.ImportTransformer(None, None)
        assert transformer._get_alias_name(node) == name

    @pytest.mark.parametrize("indent", [" " * 0, " " * 2, " " * 4, " " * 8])
    @mock.patch(MOCK % "ImportTransformer.__init__")
    def test_multiline_parenthesized_whitespace(self, init, indent):
        init.return_value = None
        transformer = transform.ImportTransformer(None, None)
        mpw = transformer._multiline_parenthesized_whitespace(indent)
        assert mpw.last_line.value == indent

    @pytest.mark.parametrize("indent", [" " * 0, " " * 2, " " * 4, " " * 8])
    @mock.patch(MOCK % "ImportTransformer.__init__")
    def test_multiline_alias(self, init, indent):
        init.return_value = None
        transformer = transform.ImportTransformer(None, None)
        transformer._indentation = indent
        alias = transformer._multiline_alias(cst.ImportAlias(name=cst.Name("x")))
        assert alias.comma.whitespace_after.last_line.value == indent + " " * 4

    @pytest.mark.parametrize("indent", [" " * 0, " " * 2, " " * 4, " " * 8])
    @mock.patch(MOCK % "ImportTransformer.__init__")
    def test_multiline_lpar(self, init, indent):
        init.return_value = None
        transformer = transform.ImportTransformer(None, None)
        transformer._indentation = indent
        lpar = transformer._multiline_lpar()
        assert lpar.whitespace_after.last_line.value == indent + " " * 4

    @pytest.mark.parametrize("indent", [" " * 0, " " * 2, " " * 4, " " * 8])
    @mock.patch(MOCK % "ImportTransformer.__init__")
    def test_multiline_rpar(self, init, indent):
        init.return_value = None
        transformer = transform.ImportTransformer(None, None)
        transformer._indentation = indent
        rpar = transformer._multiline_rpar()
        assert rpar.whitespace_before.last_line.value == indent

    @pytest.mark.parametrize(
        "code, endlineno, ismultiline",
        [
            pytest.param("import x, y, z", 1, False, id="single, import"),
            pytest.param(("import \\\n" "    x, y, z"), 2, True, id="multi, import"),
            pytest.param(
                "from xxx import (x, y, z,)", 1, False, id="single, from, parentheses"
            ),
            pytest.param(
                ("from xxx import (\n" "    x,\n" "    y,\n" "    z,\n" ")"),
                5,
                True,
                id="multi, from, parentheses",
            ),
            pytest.param(
                ("from xxx import (\n" "    x,\n" "    y,\n" "    z,)"),
                4,
                True,
                id="multi, from, parentheses, distorted-end",
            ),
            pytest.param(
                ("from xxx import x,\\\n" "    y,\\\n" "    z"),
                3,
                True,
                id="multi, from, slash",
            ),
        ],
    )
    def test_stylize(self, code, endlineno, ismultiline):
        location = NodeLocation((1, 0), endlineno)
        node = cst.parse_module(code).body[0].body[0]
        transformer = transform.ImportTransformer({""}, location)
        new_node = transformer._stylize(node, node.names, False)
        if getattr(new_node, "rpar", None) and ismultiline:
            assert new_node.rpar != node.rpar
            assert new_node.lpar != node.lpar
        assert new_node.names[-1].comma == cst.MaybeSentinel.DEFAULT


class TestTransformFunctions:
    """`transform.py` functions test case."""

    @pytest.mark.parametrize(
        (
            "import_stmnt, col_offset, used_names,"
            "expec_fixed_code, expec_fixed_lines, expec_err"
        ),
        [
            pytest.param(
                "import x, y, z",
                0,
                True,
                "import x, z",
                ["import x, z\n"],
                sysu.Pass,
                id="modified",
            ),
            pytest.param(
                "    import x, y, z",
                4,
                False,
                "",
                ["    pass\n"],
                sysu.Pass,
                id="removed, 4-indentation",
            ),
            pytest.param(
                "import x, y, z",
                0,
                False,
                "",
                [""],
                sysu.Pass,
                id="removed, no-indentation",
            ),
            pytest.param(
                "import x; import y",
                0,
                False,
                "",
                [""],
                UnsupportedCase,
                id="not supported case, ';'",
            ),
            pytest.param(
                "if True: import x",
                0,
                False,
                "",
                [""],
                UnsupportedCase,
                id="not supported case, ':'",
            ),
            pytest.param(
                "import x  # comment: with colon",
                0,
                False,
                "",
                [""],
                sysu.Pass,
                id="comment-colon, UnsupportedCase(false positive)",
            ),
            pytest.param(
                "import x  # comment; with semicolon",
                0,
                False,
                "",
                [""],
                sysu.Pass,
                id="comment-semicolon, UnsupportedCase(false positive)",
            ),
        ],
    )
    @mock.patch(MOCK % "ImportTransformer.__init__")
    @mock.patch(MOCK % "cst.parse_module")
    def test_rebuild_import(
        self,
        parse_module,
        init,
        import_stmnt,
        col_offset,
        used_names,
        expec_fixed_code,
        expec_fixed_lines,
        expec_err,
    ):
        with pytest.raises(expec_err):
            init.return_value = None
            parse_module.return_value.visit.return_value.code = expec_fixed_code
            fixed_lines = transform.rebuild_import(
                import_stmnt,
                used_names,
                Path(__file__),
                NodeLocation((1, col_offset), 0),
            )
            assert fixed_lines == expec_fixed_lines
            raise sysu.Pass()

    @pytest.mark.xfail(raises=cst.ParserSyntaxError)
    @mock.patch(MOCK % "ImportTransformer.__init__")
    def test_rebuild_import_invalid_syntax(self, init):
        init.return_value = None
        transform.rebuild_import(
            "@invalid_syntax",
            {""},
            Path(__file__),
            NodeLocation((1, 0), 0),
        )
