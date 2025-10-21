"""pycln/utils/refactor.py tests."""

# pylint: disable=R0201,W0613
import ast
from pathlib import Path
from unittest import mock

import pytest
from libcst import ParserSyntaxError

from pycln.utils import config, iou, refactor, report
from pycln.utils._exceptions import (
    InitFileDoesNotExistError,
    ReadPermissionError,
    UnexpandableImportStar,
    UnparsableFile,
    UnsupportedCase,
    WritePermissionError,
)
from pycln.utils._nodes import Import, ImportFrom, NodeLocation
from pycln.utils.scan import HasSideEffects, ImportStats, SourceStats

from .utils import sysu

# Constants.
MOCK = "pycln.utils.refactor.%s"


class TestPyPath:
    """`PyPath` class test case."""

    def test_is_subclass_of_pathlib_path(self):
        assert issubclass(refactor.PyPath, Path)

    @pytest.mark.parametrize(
        "path, expected_is_stub",
        [pytest.param("a.py", False), pytest.param("a.pyi", True)],
    )
    def test_is_stub_property(self, path, expected_is_stub):
        pypath = refactor.PyPath(path)
        assert pypath.is_stub == expected_is_stub


class TestRefactor:
    """`Refactor` methods test case."""

    def setup_method(self, method):
        self.configs = config.Config(paths=[Path("")], skip_imports=set({}))
        self.reporter = report.Report(self.configs)
        self.session_maker = refactor.Refactor(self.configs, self.reporter)

    @pytest.mark.parametrize(
        "source_lines, expec_lines",
        [
            pytest.param(
                [
                    "try:\n",
                    "    pass\n",
                    "except:\n",
                    "    import y\n",
                ],
                [
                    "try:\n",
                    "    pass\n",
                    "except:\n",
                    "    import y\n",
                ],
                id="useful",
            ),
            pytest.param(
                [
                    "try:\n",
                    "    import x\n",
                    "    pass\n",
                    "except:\n",
                    "    import y\n",
                ],
                [
                    "try:\n",
                    "    import x\n",
                    "except:\n",
                    "    import y\n",
                ],
                id="single-useless",
            ),
            pytest.param(
                [
                    "try:\n",
                    "    import x\n",
                    "    pass\n",
                    "    pass\n",
                    "    pass\n",
                    "    pass\n",
                    "    pass\n",
                    "    pass\n",
                    "    pass\n",
                    "except:\n",
                    "    import y\n",
                ],
                [
                    "try:\n",
                    "    import x\n",
                    "except:\n",
                    "    import y\n",
                ],
                id="multi-useless0",
            ),
            pytest.param(
                [
                    "try:\n",
                    "    pass\n",
                    "    pass\n",
                    "    pass\n",
                    "    pass\n",
                    "    pass\n",
                    "    pass\n",
                    "    pass\n",
                    "    pass\n",
                    "except:\n",
                    "    import y\n",
                ],
                [
                    "try:\n",
                    "    pass\n",
                    "except:\n",
                    "    import y\n",
                ],
                id="multi-useless1",
            ),
            pytest.param(
                [
                    "class Foo:\n",
                    "    '''docs'''\n",
                    "    pass\n",
                    "    pass\n",
                    "async def foo():\n",
                    "    '''docs'''\n",
                    "    pass\n",
                    "    pass\n",
                    "def foo():\n",
                    "    '''docs'''\n",
                    "    pass\n",
                    "    pass\n",
                ],
                [
                    "class Foo:\n",
                    "    '''docs'''\n",
                    "    pass\n",
                    "async def foo():\n",
                    "    '''docs'''\n",
                    "    pass\n",
                    "def foo():\n",
                    "    '''docs'''\n",
                    "    pass\n",
                ],
                id="useless with docstring",
            ),
            pytest.param(
                [
                    "x = i if i else y\n",
                ],
                [
                    "x = i if i else y\n",
                ],
                id="TypeError",
            ),
            pytest.param(
                [
                    "if True:\n",
                    "   pass\n",
                    "   pass\n",
                    "else:\n",
                    "   pass\n",
                    "   pass\n",
                ],
                [
                    "if True:\n",
                    "   pass\n",
                    "else:\n",
                    "   pass\n",
                ],
                id="orelse parent - else - useless",
            ),
            pytest.param(
                [
                    "if True:\n",
                    "   print()\n",
                    "   print()\n",
                    "else:\n",
                    "   pass\n",
                ],
                [
                    "if True:\n",
                    "   print()\n",
                    "   print()\n",
                    "else:\n",
                    "   pass\n",
                ],
                id="orelse parent - else - useful",
            ),
            pytest.param(
                [
                    "if True:\n",
                    "   print()\n",
                    "   pass\n",
                ],
                [
                    "if True:\n",
                    "   print()\n",
                ],
                id="orelse parent - no-else",
            ),
            pytest.param(
                [
                    "try:\n",
                    "   pass\n",
                    "finally:\n",
                    "   pass\n",
                    "   pass\n",
                ],
                [
                    "try:\n",
                    "   pass\n",
                    "finally:\n",
                    "   pass\n",
                ],
                id="finallybody parent",
            ),
            pytest.param(
                ["try:\n", "   x = 1\n", "   y = 2\n", "finally:\n", "   pass\n"],
                ["try:\n", "   x = 1\n", "   y = 2\n", "finally:\n", "   pass\n"],
                id="finallybody parent - useful",
            ),
            pytest.param(
                [
                    "try:\n",
                    "   x = 1\n",
                    "   y = 2\n",
                    "finally:\n",
                    "   pass\n",
                    "   pass\n",
                ],
                ["try:\n", "   x = 1\n", "   y = 2\n", "finally:\n", "   pass\n"],
                id="finallylbody parent - useless",
            ),
            pytest.param(
                [
                    "try:\n",
                    "   x = 1\n",
                    "   y = 2\n",
                    "except:\n",
                    "   x = 1\n",
                    "   y = 2\n",
                    "else:\n",
                    "   pass\n",
                    "finally:\n",
                    "   pass\n",
                ],
                [
                    "try:\n",
                    "   x = 1\n",
                    "   y = 2\n",
                    "except:\n",
                    "   x = 1\n",
                    "   y = 2\n",
                    "else:\n",
                    "   pass\n",
                    "finally:\n",
                    "   pass\n",
                ],
                id="both finallybody and orelse",
            ),
        ],
    )
    def test_remove_useless_passes(self, source_lines, expec_lines):
        fixed_code = refactor.Refactor.remove_useless_passes(source_lines)
        assert fixed_code == expec_lines

    @pytest.mark.parametrize(
        "path, read_stdin_raise, safe_read_raise, _code_session_raise",
        [
            pytest.param(Path("pseudopath"), None, None, None, id="no-err[file]"),
            pytest.param(iou.STDIN_FILE, None, None, None, id="no-err[stdin]"),
            pytest.param(
                Path("pseudopath"),
                None,
                ReadPermissionError(13, "", Path("")),
                None,
                id="ReadPermissionError[file]",
            ),
            pytest.param(
                Path("pseudopath"),
                None,
                WritePermissionError(13, "", Path("")),
                None,
                id="WritePermissionError[file]",
            ),
            pytest.param(
                Path("pseudopath"),
                None,
                None,
                UnparsableFile(Path(""), SyntaxError("")),
                id="UnparsableFile[code-session]",
            ),
            pytest.param(
                Path("DoesNotExistInitFile/__init__.py"),
                None,
                InitFileDoesNotExistError(2, "", Path("")),
                None,
                id="InitFileDoesNotExistError[file]",
            ),
        ],
    )
    @mock.patch(MOCK % "Refactor._output")
    @mock.patch(MOCK % "Refactor._code_session")
    @mock.patch(MOCK % "iou.safe_read")
    @mock.patch(MOCK % "iou.read_stdin")
    def test_session(
        self,
        read_stdin,
        safe_read,
        _code_session,
        _output,
        path,
        read_stdin_raise,
        safe_read_raise,
        _code_session_raise,
    ):
        safe_read.return_value = read_stdin.return_value = (
            "code...\ncode...\n",
            "utf-8",
            "\n",
        )
        safe_read.side_effect = safe_read_raise
        _code_session.return_value = "code...\ncode...\n"
        _code_session.side_effect = _code_session_raise
        self.session_maker.session(path)
        assert self.session_maker._path == Path("")

    @pytest.mark.parametrize(
        "skip_file_return, _analyze_return, expec_fixed_code",
        [
            pytest.param(True, None, "original.code", id="file skip"),
            pytest.param(False, None, "original.code", id="no stats"),
            pytest.param(False, ("s", "i"), "fixed.code", id="refactored"),
        ],
    )
    @mock.patch(MOCK % "Refactor._refactor")
    @mock.patch(MOCK % "Refactor._analyze")
    @mock.patch(MOCK % "scan.parse_ast")
    @mock.patch(MOCK % "regexu.skip_file")
    def test_code_session(
        self,
        skip_file,
        parse_ast,
        _analyze,
        _refactor,
        skip_file_return,
        _analyze_return,
        expec_fixed_code,
    ):
        skip_file.return_value = skip_file_return
        _analyze.return_value = _analyze_return
        _refactor.return_value = "fixed.code"
        with sysu.std_redirect(sysu.STD.ERR):
            fixed_code = self.session_maker._code_session("original.code")
            assert fixed_code == expec_fixed_code

    @pytest.mark.parametrize(
        "fixed_lines, original_lines, modes, expec_output",
        [
            pytest.param(
                ["code..\n"], ["code..\n"], ["verbose"], "looks good!", id="unchanged"
            ),
            pytest.param(
                ["fixed.code..\n"],
                ["original.code..\n"],
                ["check"],
                "🚀",
                id="changed-check",
            ),
            pytest.param(
                ["import x\n"],
                ["import x, y\n"],
                ["diff"],
                "-import x, y\n+import x\n",
                id="changed-diff",
            ),
            pytest.param(
                ["import x\n"],
                ["import x, y\n"],
                ["diff", "check"],
                "-import x, y\n+import x\n",
                id="changed-[diff & check]",
            ),
        ],
    )
    @mock.patch(MOCK % "Refactor.remove_useless_passes")
    def test_output(
        self, remove_useless_passes, fixed_lines, original_lines, modes, expec_output
    ):
        remove_useless_passes.return_value = fixed_lines
        for mode in modes:
            setattr(self.configs, mode, True)
        with sysu.std_redirect(sysu.STD.OUT) as stdout:
            self.session_maker._output(fixed_lines, original_lines, "utf-8", "\n")
            assert expec_output, "Expected output mustn't be empty str."
            assert expec_output in stdout.getvalue()

    @mock.patch(MOCK % "Refactor.remove_useless_passes")
    def test_output_write(self, remove_useless_passes):
        fixed_lines, original_lines = ["import x\n"], ["import x, y\n"]
        remove_useless_passes.return_value = fixed_lines
        with sysu.reopenable_temp_file("".join(original_lines)) as tmp_path:
            with open(tmp_path) as tmp:
                self.session_maker._path = tmp_path
                self.session_maker._output(fixed_lines, original_lines, "utf-8", "\n")
                assert tmp.readlines() == fixed_lines

    @pytest.mark.parametrize(
        "fixed_lines, original_lines, expec_output",
        [
            pytest.param(
                ["import x\n"], ["import x, y\n"], "import x\n", id="modified"
            ),
            pytest.param(
                ["import x, y\n"], ["import x, y\n"], "import x, y\n", id="not-modified"
            ),
        ],
    )
    @mock.patch(MOCK % "Refactor.remove_useless_passes")
    def test_output_stdin(
        self, remove_useless_passes, fixed_lines, original_lines, expec_output
    ):
        remove_useless_passes.return_value = fixed_lines
        setattr(self.configs, "silence", True)
        with sysu.std_redirect(sysu.STD.OUT) as stdout:
            self.session_maker._path = iou.STDIN_FILE
            self.session_maker._output(fixed_lines, original_lines, "utf-8", "\n")
            assert stdout.getvalue() == expec_output

    @pytest.mark.parametrize(
        (
            "disable_all_dunder_policy, get_stats_raise,"
            "has_all_return, is_init_file_return,"
            "expec_is_init_without_all, expec_val"
        ),
        [
            pytest.param(False, None, False, False, False, ("", ""), id="normal"),
            pytest.param(False, Exception(""), False, False, False, None, id="error"),
            pytest.param(
                False, None, False, True, True, ("", ""), id="__init__.py - no __all__"
            ),
            pytest.param(
                False, None, True, True, False, ("", ""), id="__init__.py - __all__"
            ),
            pytest.param(
                False,
                None,
                False,
                False,
                False,
                ("", ""),
                id="not __init__.py - no __all__",
            ),
            pytest.param(
                False,
                None,
                True,
                False,
                False,
                ("", ""),
                id="not __init__.py - __all__",
            ),
            pytest.param(
                True,
                None,
                False,
                True,
                False,
                ("", ""),
                id="__init__.py - no __all__ - policy disabled",
            ),
        ],
    )
    @mock.patch(MOCK % "regexu.is_init_file")
    @mock.patch(MOCK % "scan.SourceAnalyzer.has_all")
    @mock.patch(MOCK % "scan.SourceAnalyzer.get_stats")
    def test_analyze(
        self,
        get_stats,
        has_all,
        is_init_file,
        disable_all_dunder_policy,
        get_stats_raise,
        has_all_return,
        is_init_file_return,
        expec_is_init_without_all,
        expec_val,
    ):
        get_stats.return_value = ("", "")
        get_stats.side_effect = get_stats_raise
        has_all.return_value = has_all_return
        is_init_file.return_value = is_init_file_return

        setattr(self.configs, "disable_all_dunder_policy", disable_all_dunder_policy)

        with sysu.std_redirect(sysu.STD.ERR):
            val = self.session_maker._analyze(ast.parse(""))
            assert val == expec_val

        assert self.session_maker._is_init_without_all == expec_is_init_without_all

    @pytest.mark.parametrize(
        (
            "skip_import_return, _expand_import_star_return, _get_used_names_return,"
            "_transform_return, expand_stars, mode, original_lines, expec_fixed_lines"
        ),
        [
            pytest.param(
                False,
                (None, None),
                None,
                ["import x, y"],
                False,
                "not-matter",
                ["import *"],
                ["import *"],
                id="unexpandable star",
            ),
            pytest.param(
                False,
                (
                    Import(NodeLocation((1, 0), 1), [ast.alias(name="x", asname=None)]),
                    True,
                ),
                {"x", "y"},
                ["import x, y"],
                False,
                "not-matter",
                ["import *"],
                ["import *"],
                id="star, used, no -x",
            ),
            pytest.param(
                False,
                (
                    Import(NodeLocation((1, 0), 1), [ast.alias(name="x", asname=None)]),
                    True,
                ),
                {"x", "y"},
                ["import x, y"],
                True,
                "not-matter",
                ["import *"],
                ["import x, y"],
                id="star, used, -x",
            ),
            pytest.param(
                False,
                (
                    Import(NodeLocation((1, 0), 1), [ast.alias(name="x", asname=None)]),
                    True,
                ),
                set(),
                [""],
                False,
                "not-matter",
                ["import *"],
                [""],
                id="star, not used, x imported",
            ),
            pytest.param(
                False,
                (
                    Import(NodeLocation((1, 0), 1), []),
                    True,
                ),
                set(),
                [""],
                False,
                "not-matter",
                ["import *"],
                [""],
                id="star, not used, nothing's imported",
            ),
            pytest.param(
                False,
                (
                    Import(NodeLocation((1, 0), 1), [ast.alias(name="x", asname=None)]),
                    False,
                ),
                set("x"),
                None,
                False,
                "not-matter",
                ["import x"],
                ["import x"],
                id="all used, no -x",
            ),
            pytest.param(
                False,
                (
                    Import(NodeLocation((1, 0), 1), [ast.alias(name="x", asname=None)]),
                    True,
                ),
                set("x"),
                ["import x, y"],
                True,
                "not-matter",
                ["import x"],
                ["import x, y"],
                id="all used, -x",
            ),
            pytest.param(
                False,
                (
                    Import(NodeLocation((1, 0), 1), [ast.alias(name="x", asname=None)]),
                    False,
                ),
                set("x"),
                ["import x"],
                True,
                "check",
                ["import x, y"],
                ["import x, y\n_CHANGED_"],
                id="check",
            ),
        ],
    )
    @mock.patch(MOCK % "Refactor._transform")
    @mock.patch(MOCK % "Refactor._get_used_names")
    @mock.patch(MOCK % "Refactor._expand_import_star")
    @mock.patch(MOCK % "regexu.skip_import")
    def test_refactor(
        self,
        skip_import,
        _expand_import_star,
        _get_used_names,
        _transform,
        skip_import_return,
        _expand_import_star_return,
        _get_used_names_return,
        _transform_return,
        expand_stars,
        mode,
        original_lines,
        expec_fixed_lines,
    ):
        skip_import.return_value = skip_import_return
        _expand_import_star.return_value = _expand_import_star_return
        _get_used_names.return_value = _get_used_names_return
        _transform.return_value = _transform_return
        setattr(self.configs, "expand_stars", expand_stars)
        setattr(self.configs, mode, True)
        node = Import(NodeLocation((1, 0), 1), [ast.alias(name="x", asname=None)])
        self.session_maker._import_stats = ImportStats({node}, set())
        with sysu.std_redirect(sysu.STD.OUT):
            with sysu.std_redirect(sysu.STD.ERR):
                fixed_code = self.session_maker._refactor(original_lines)
                assert fixed_code == "".join(expec_fixed_lines)

    @pytest.mark.parametrize(
        ("endline_no, original_lines, expec_fixed_lines"),
        [
            pytest.param(
                1,
                ["import x # nopycln: import"],
                ["import x # nopycln: import"],
                id="nopycln - first line",
            ),
            pytest.param(
                3,
                ["import (\n", "    x\n", ") # nopycln: import"],
                ["import (\n", "    x\n", ") # nopycln: import"],
                id="nopycln - last line",
            ),
            pytest.param(
                1,
                ["import x # noqa"],
                ["import x # noqa"],
                id="noqa",
            ),
        ],
    )
    @mock.patch(MOCK % "Refactor._get_used_names")
    def test_refactor_skipping(
        self,
        _get_used_names,
        endline_no,
        original_lines,
        expec_fixed_lines,
    ):
        _get_used_names.return_value = set()
        setattr(self.configs, "expand_stars", False)
        node = Import(
            NodeLocation((1, 0), endline_no), [ast.alias(name="x", asname=None)]
        )
        self.session_maker._import_stats = ImportStats({node}, set())
        fixed_code = self.session_maker._refactor(original_lines)
        assert fixed_code == "".join(expec_fixed_lines)

    @pytest.mark.parametrize(
        (
            "_get_used_names_return, is_star_return,"
            "_is_init_without_all, is_undecidable"
        ),
        [
            pytest.param(None, None, False, False, id="all"),
            pytest.param(["node"], True, True, True, id="no-all - star - used"),
            pytest.param([], False, True, True, id="no-all - no-star - no-used"),
            pytest.param(["node"], False, True, False, id="no-all - no-star - used"),
        ],
    )
    @mock.patch(MOCK % "Refactor._expand_import_star")
    @mock.patch(MOCK % "Refactor._get_used_names")
    def test_refactor_init_without_all(
        self,
        _get_used_names,
        _expand_import_star,
        _get_used_names_return,  # we only care about the len.
        is_star_return,
        _is_init_without_all,
        is_undecidable,
    ):
        node = Import(NodeLocation((1, 0), 1), [ast.alias(name="x", asname=None)])
        _get_used_names.return_value = _get_used_names_return
        _expand_import_star.return_value = node, is_star_return
        self.session_maker._import_stats = ImportStats({node}, set())
        self.session_maker._is_init_without_all = _is_init_without_all

        with sysu.std_redirect(sysu.STD.ERR):
            self.session_maker._refactor(["import x"])  # Fake code

        if is_undecidable:
            assert self.session_maker.reporter._undecidable_case == 1
        else:
            assert not self.session_maker.reporter._undecidable_case

    @pytest.mark.parametrize(
        "_should_remove_return, node, is_star, _is_init_without_all, expec_names",
        [
            pytest.param(
                False,
                Import(
                    NodeLocation((1, 0), 1),
                    [
                        ast.alias(name="x", asname=None),
                        ast.alias(name="y", asname=None),
                    ],
                ),
                False,
                False,
                {"x", "y"},
                id="used",
            ),
            pytest.param(
                True,
                Import(
                    NodeLocation((1, 0), 1),
                    [
                        ast.alias(name="x", asname=None),
                        ast.alias(name="y", asname=None),
                    ],
                ),
                False,
                False,
                set(),
                id="not-used",
            ),
            pytest.param(
                True,
                Import(
                    NodeLocation((1, 0), 1),
                    [
                        ast.alias(name="x", asname=None),
                        ast.alias(name="y", asname=None),
                    ],
                ),
                True,
                False,
                set(),
                id="not-used, star",
            ),
            pytest.param(
                True,
                Import(
                    NodeLocation((1, 0), 1),
                    [
                        ast.alias(name="x", asname=None),
                        ast.alias(name="y", asname=None),
                    ],
                ),
                False,
                True,
                set(),
                id="unused | init-without-all",
            ),
        ],
    )
    @mock.patch(MOCK % "Refactor._should_remove")
    def test_get_used_names(
        self,
        _should_remove,
        _should_remove_return,
        node,
        is_star,
        _is_init_without_all,
        expec_names,
    ):
        _should_remove.return_value = _should_remove_return
        self.session_maker._is_init_without_all = _is_init_without_all
        with sysu.std_redirect(sysu.STD.OUT) as stdout:
            used_names = self.session_maker._get_used_names(node, is_star)
            assert used_names == expec_names

            if _is_init_without_all:
                assert stdout.getvalue() == ""

    @pytest.mark.parametrize(
        (
            "rebuild_import_return, rebuild_import_raise, "
            "location, original_lines, updated_lines"
        ),
        [
            pytest.param(
                "import x\n",
                None,
                NodeLocation((1, 0), 1),
                ["import x, i\n", "import y\n"],
                ["import x\n", "import y\n"],
                id="normal",
            ),
            pytest.param(
                "import x\n",
                UnsupportedCase(Path(""), NodeLocation((1, 0), 1), ""),
                NodeLocation((1, 0), 1),
                ["import x, i\n", "import y\n"],
                ["import x\n", "import y\n"],
                id="UnparsableFile",
            ),
            pytest.param(
                "import x\n",
                ParserSyntaxError("", lines=[""], raw_line=1, raw_column=0),
                NodeLocation((1, 0), 1),
                ["import x; import y\n"],
                ["import x; import y\n"],
                id="libcst.ParserSyntaxError",
            ),
        ],
    )
    @mock.patch(MOCK % "Refactor._insert")
    @mock.patch(MOCK % "transform.rebuild_import")
    def test_transform(
        self,
        rebuild_import,
        _insert,
        rebuild_import_return,
        rebuild_import_raise,
        location,
        original_lines,
        updated_lines,
    ):
        rebuild_import.side_effect = rebuild_import_raise
        rebuild_import.return_value = rebuild_import_return
        _insert.return_value = updated_lines
        with sysu.std_redirect(sysu.STD.ERR):
            fixed_lines = self.session_maker._transform(
                location, set(), original_lines, updated_lines
            )
            assert fixed_lines == updated_lines

    @pytest.mark.parametrize(
        "expand_import_star_raise, name, is_stub, expec_is_star",
        [
            pytest.param(None, "*", False, True, id="star"),
            pytest.param(None, "!*", False, False, id="not-star"),
            pytest.param(
                UnexpandableImportStar(Path(""), NodeLocation((1, 0), 1), ""),
                "*",
                False,
                None,
                id="not-star",
            ),
            pytest.param(None, "*", True, None, id="star-stub(pyi)"),
        ],
    )
    @mock.patch(MOCK % "scan.expand_import_star")
    def test_expand_import_star(
        self,
        expand_import_star,
        expand_import_star_raise,
        name,
        is_stub,
        expec_is_star,
    ):
        node = ImportFrom(NodeLocation((1, 0), 1), [ast.alias(name=name)], "xxx", 0)
        expand_import_star.return_value = node
        expand_import_star.side_effect = expand_import_star_raise
        if is_stub:
            self.session_maker._path = refactor.PyPath("stub.pyi")
        enode, is_star = self.session_maker._expand_import_star(node)
        assert (enode, is_star) == (node, expec_is_star)

    @pytest.mark.parametrize(
        "node, should_assert",
        [
            pytest.param(
                ImportFrom(NodeLocation((1, 0), 1), [ast.alias(name="*")], "x", 0),
                True,
                id="from x import *",
            ),
            pytest.param(
                ImportFrom(NodeLocation((1, 0), 1), [ast.alias(name="*")], None, 0),
                False,
                id="from . import * [pass]",
            ),
        ],
    )
    def test_expand_import_star_skip_imports(self, node, should_assert):
        #: Test the case where the module name is in the `skip_imports` set.
        with pytest.raises(sysu.Pass):
            self.configs.skip_imports = {"x"}
            enode, is_star = self.session_maker._expand_import_star(node)
            if should_assert:
                assert enode == node
                assert is_star is None
            raise sysu.Pass()

    @pytest.mark.parametrize(
        "_has_used_return, name, asname, expec_val",
        [
            pytest.param(True, "os.path.join", None, True, id="used"),
            pytest.param(False, "os.path.join", None, False, id="unused"),
            pytest.param(None, "os.path.join", "asname", False, id="as alias"),
            pytest.param(None, "os", None, False, id="single name"),
        ],
    )
    @mock.patch(MOCK % "Refactor._has_used")
    def test_is_partially_used(
        self, _has_used, _has_used_return, name, asname, expec_val
    ):
        _has_used.return_value = _has_used_return
        alias = ast.alias(name=name, asname=asname)
        val = self.session_maker._is_partially_used(alias, False)
        assert val == expec_val

    @pytest.mark.parametrize(
        "_has_used_return, _has_side_effects_return, all_, name, expec_val",
        [
            pytest.param(True, None, None, "not-matter", False, id="used"),
            pytest.param(False, None, None, "this", False, id="known side effects"),
            pytest.param(False, None, True, "not-matter", True, id="--all option"),
            pytest.param(False, None, False, "os", True, id="standard lib"),
            pytest.param(
                False,
                HasSideEffects.NO,
                False,
                "not-matter",
                True,
                id="no side-effects",
            ),
            pytest.param(
                False,
                HasSideEffects.YES,
                False,
                "not-matter",
                False,
                id="no all",
            ),
        ],
    )
    @mock.patch(MOCK % "Refactor._has_side_effects")
    @mock.patch(MOCK % "Refactor._has_used")
    def test_should_remove(
        self,
        _has_used,
        _has_side_effects,
        _has_used_return,
        _has_side_effects_return,
        all_,
        name,
        expec_val,
    ):
        _has_used.return_value = _has_used_return
        _has_side_effects.return_value = _has_side_effects_return
        setattr(self.configs, "all_", all_)
        alias = ast.alias(name=name, asname=None)
        node = Import(NodeLocation((1, 0), 1), [alias])
        val = self.session_maker._should_remove(node, alias, False)
        assert val == expec_val

    @pytest.mark.parametrize(
        "node, expec_should_remove",
        [
            pytest.param(
                Import(NodeLocation((1, 0), 1), [ast.alias(name="x", asname="x")]),
                False,
                id="x as x",
            ),
            pytest.param(
                Import(NodeLocation((1, 0), 1), [ast.alias(name="x", asname="y")]),
                True,
                id="x as y",
            ),
            pytest.param(
                Import(NodeLocation((1, 0), 1), [ast.alias(name="x", asname=None)]),
                True,
                id="no as",
            ),
        ],
    )
    @mock.patch(MOCK % "Refactor._has_side_effects")
    @mock.patch(MOCK % "Refactor._has_used")
    @mock.patch(MOCK % "PyPath.is_stub")
    def test_should_remove_skip_pep484(
        self, is_stub, _has_used, _has_side_effects, node, expec_should_remove
    ):
        #: Test PEP 484 - Redundant Module/Symbol Aliases rule for stub files:
        #:
        #: >>> import X as X  # exported (should be treated as used)
        #:
        #: More info: https://peps.python.org/pep-0484/#stub-files
        is_stub.return_value = True
        _has_used.return_value = False
        self.session_maker.configs.all_ = True
        val = self.session_maker._should_remove(node, node.names[0], False)
        assert val == expec_should_remove

    @pytest.mark.parametrize(
        "node, should_assert",
        [
            pytest.param(
                Import(NodeLocation((1, 0), 1), [ast.alias(name="x", asname="y")]),
                True,
                id="import",
            ),
            pytest.param(
                ImportFrom(
                    NodeLocation((1, 0), 1), [ast.alias(name="x", asname="y")], "x", 0
                ),
                True,
                id="import-from",
            ),
            pytest.param(
                ImportFrom(
                    NodeLocation((1, 0), 1), [ast.alias(name="x", asname="y")], None, 0
                ),
                False,
                id="from . import x [pass]",
            ),
        ],
    )
    def test_should_remove_skip_imports(self, node, should_assert):
        #: Test the case where the module name is in the `skip_imports` set.
        with pytest.raises(sysu.Pass):
            self.configs.skip_imports = {"x"}
            val = self.session_maker._should_remove(node, node.names[0], False)
            if should_assert:
                assert val is False
            raise sysu.Pass()

    @pytest.mark.parametrize(
        "name, is_star, expec_val",
        [
            pytest.param("x", False, True, id="used name"),
            pytest.param("y", False, False, id="not-used name"),
            pytest.param("x.i", False, True, id="used attr"),
            pytest.param("x.j", False, False, id="not-used attr"),
            pytest.param("x", True, True, id="used name, star"),
            pytest.param("__future__", True, False, id="skip name, star"),
        ],
    )
    def test_has_used(self, name, is_star, expec_val):
        self.session_maker._source_stats = SourceStats({"x"}, {"i"}, "__future__")
        val = self.session_maker._has_used(name, is_star)
        assert val == expec_val

    @pytest.mark.parametrize(
        (
            "get_import_return, safe_read_return, safe_read_raise,"
            "parse_ast_return, parse_ast_raise,"
            "has_side_effects_return, has_side_effects_raise,"
        ),
        [
            pytest.param(
                None,
                ("", "", ""),
                None,
                None,
                None,
                HasSideEffects.NOT_MODULE,
                None,
                id="no module path",
            ),
            pytest.param(
                Path(""),
                ("", "", ""),
                ReadPermissionError(13, "", Path("")),
                None,
                None,
                HasSideEffects.NOT_KNOWN,
                None,
                id="no read permission",
            ),
            pytest.param(
                Path(""),
                ("", "", ""),
                None,
                ast.Module(),
                UnparsableFile(Path(""), SyntaxError("")),
                HasSideEffects.NOT_KNOWN,
                None,
                id="Unparsable File",
            ),
            pytest.param(
                Path(""),
                ("", "", ""),
                None,
                ast.Module(),
                None,
                HasSideEffects.NOT_KNOWN,
                Exception("err"),
                id="generic err",
            ),
            pytest.param(
                Path(""),
                ("", "", ""),
                None,
                ast.Module(),
                None,
                HasSideEffects.YES,
                None,
                id="success",
            ),
        ],
    )
    @mock.patch(MOCK % "scan.SideEffectsAnalyzer.has_side_effects")
    @mock.patch(MOCK % "scan.SideEffectsAnalyzer.__init__")
    @mock.patch(MOCK % "scan.SideEffectsAnalyzer.visit")
    @mock.patch(MOCK % "scan.parse_ast")
    @mock.patch(MOCK % "iou.safe_read")
    @mock.patch(MOCK % "pathu.get_import_path")
    @mock.patch(MOCK % "pathu.get_import_from_path")
    def test_has_side_effects(
        self,
        get_import_from_path,
        get_import_path,
        safe_read,
        parse_ast,
        visit,
        init,
        has_side_effects,
        get_import_return,
        safe_read_return,
        safe_read_raise,
        parse_ast_return,
        parse_ast_raise,
        has_side_effects_return,
        has_side_effects_raise,
    ):
        init.return_value = None
        get_import_from_path.return_value = get_import_return
        get_import_path.return_value = get_import_return
        safe_read.return_value = safe_read_return
        safe_read.side_effect = safe_read_raise
        parse_ast.return_value = parse_ast_return
        parse_ast.side_effect = parse_ast_raise
        has_side_effects.return_value = has_side_effects_return
        has_side_effects.side_effect = has_side_effects_raise
        with sysu.std_redirect(sysu.STD.ERR):
            node = Import(NodeLocation((1, 0), 1), [])
            val = self.session_maker._has_side_effects("", node, cache={})
            assert val == has_side_effects_return

    @pytest.mark.parametrize(
        "rebuilt_import, updated_lines, location, expec_updated_lines",
        [
            pytest.param(
                ["import x\n"],
                [
                    "import z\n",
                    "import x, i\n",
                    "import y\n",
                ],
                NodeLocation((2, 0), 2),
                [
                    "import z\n",
                    "import x\n",
                    "import y\n",
                ],
                id="single:replace",
            ),
            pytest.param(
                "",
                [
                    "import z\n",
                    "import x, i\n",
                    "import y\n",
                ],
                NodeLocation((2, 0), 2),
                [
                    "import z\n",
                    "",
                    "import y\n",
                ],
                id="single:remove",
            ),
            pytest.param(
                [
                    "from xxx import (\n",
                    "    x\n",
                    ")\n",
                ],
                [
                    "import z\n",
                    "from xxx import (\n",
                    "    x, y\n",
                    ")\n",
                    "import y\n",
                ],
                NodeLocation((2, 0), 4),
                [
                    "import z\n",
                    "from xxx import (\n",
                    "    x\n",
                    ")\n",
                    "import y\n",
                ],
                id="multi:replace",
            ),
            pytest.param(
                [
                    "from xxx import (\n",
                    "    x\n",
                    ")\n",
                ],
                [
                    "import z\n",
                    "from xxx import (\n",
                    "    x,\n",
                    "    y\n",
                    ")\n",
                    "import y\n",
                ],
                NodeLocation((2, 0), 5),
                [
                    "import z\n",
                    "from xxx import (\n",
                    "    x\n",
                    ")\n",
                    "",
                    "import y\n",
                ],
                id="multi:remove:part",
            ),
            pytest.param(
                [""],
                [
                    "import z\n",
                    "from xxx import (\n",
                    "    x,\n",
                    "    y\n",
                    ")\n",
                    "import y\n",
                ],
                NodeLocation((2, 0), 5),
                [
                    "import z\n",
                    "",
                    "",
                    "",
                    "",
                    "import y\n",
                ],
                id="multi:remove:all",
            ),
            pytest.param(
                [
                    "from xxx import (\n",
                    "    x,\n",
                    "    y\n",
                    ")\n",
                ],
                [
                    "import z\n",
                    "from xxx import *\n",
                    "import y\n",
                ],
                NodeLocation((2, 0), 2),
                [
                    "import z\n",
                    "from xxx import (\n    x,\n    y\n)\n",
                    "import y\n",
                ],
                id="multi:add",
            ),
        ],
    )
    def test_insert(self, rebuilt_import, updated_lines, location, expec_updated_lines):
        fixed = refactor.Refactor._insert(rebuilt_import, updated_lines, location)
        print(repr(fixed))
        assert fixed == expec_updated_lines
