"""pycln/utils/report.py tests."""
# pylint: disable=R0201,W0613
import ast
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

import pytest
from typer import Exit

from pycln.utils import config, report
from pycln.utils._nodes import Import, ImportFrom, NodeLocation

from .utils import sysu


class TestReport:

    """`Report` methods test case."""

    def setup_method(self, method):
        self.configs = config.Config(paths=[Path("")], skip_imports=set({}))
        self.reporter = report.Report(self.configs)
        # Needed for some tests.
        self.alias = ast.alias(name="x", asname=None)
        self.impt = ImportFrom(NodeLocation((1, 0), 1), [self.alias], "xx", 1)

    def test_get_location(self):
        path, location = Path("file_path"), NodeLocation((2, 0), 4)
        str_location = report.Report.get_location(path, location)
        assert str_location == "file_path:2:0"

    @pytest.mark.parametrize(
        "type_", ["isedit", "issuccess", "iswarning", "iserror", ""]
    )
    def test_secho(self, type_):
        err = sysu.Pass if type_ else ValueError
        with pytest.raises(err):
            if type_ in {"iswarning", "iserror"}:
                std = sysu.STD.ERR
            else:
                std = sysu.STD.OUT
            with sysu.std_redirect(std) as stream:
                kwargs = {type_: True} if type_ else {}
                report.Report.secho("msg", bold=False, **kwargs)
                assert "msg" in stream.getvalue()
            raise sysu.Pass()

    def test_colored_unified_diff(self):
        original_lines = ["import x, y\n", "print()"]
        fixed_lines = ["import x\n", "print()"]
        with sysu.std_redirect(sysu.STD.OUT) as stdout:
            report.Report.colored_unified_diff(
                Path("file_path"), original_lines, fixed_lines
            )
            assert stdout.getvalue() == (
                "--- original/ file_path\n"
                "+++ fixed/ file_path\n"
                "@@ -1,2 +1,2 @@\n"
                "-import x, y\n"
                "+import x\n"
                " print()\n"
                "\n"
            )

    def test_output_stdin_to_stdout(self):
        fixed_lines = ["import x\n", "print()"]
        with sysu.std_redirect(sysu.STD.OUT) as stdout:
            report.Report.output_stdin_to_stdout(fixed_lines)
            assert stdout.getvalue() == ("import x\n" "print()")

    @pytest.mark.parametrize(
        "node, alias, expec_imp_stmnt",
        [
            pytest.param(
                Import(None, None),
                ast.alias(name="x", asname=None),
                "import x",
                id="import, name",
            ),
            pytest.param(
                Import(None, None),
                ast.alias(name="xx", asname="x"),
                "import xx as x",
                id="import, asname",
            ),
            pytest.param(
                ImportFrom(None, None, "xxx", 0),
                ast.alias(name="x", asname=None),
                "from xxx import x",
                id="from, name",
            ),
            pytest.param(
                ImportFrom(None, None, "xxx", 0),
                ast.alias(name="xx", asname="x"),
                "from xxx import xx as x",
                id="from, asname",
            ),
            pytest.param(
                ImportFrom(None, None, "r", 1),
                ast.alias(name="x", asname=None),
                "from .r import x",
                id="from, relative, module",
            ),
            pytest.param(
                ImportFrom(None, None, None, 2),
                ast.alias(name="x", asname=None),
                "from .. import x",
                id="from, relative, no-module",
            ),
        ],
    )
    def test_rebuild_report_import(self, node, alias, expec_imp_stmnt):
        imp_stmnt = report.Report.rebuild_report_import(node, alias)
        assert imp_stmnt == expec_imp_stmnt

    @pytest.mark.parametrize(
        "mode, is_out",
        [
            ("default", True),
            ("check", True),
            ("diff", False),
            ("verbose", True),
            ("quiet", False),
            ("silence", False),
        ],
    )
    def test_removed_import(self, mode, is_out):
        setattr(self.configs, mode, True)
        with sysu.std_redirect(sysu.STD.OUT) as stdout:
            self.reporter.removed_import(Path(""), self.impt, self.alias)
            assert bool(stdout.getvalue()) == is_out
            assert self.reporter._removed_imports == 1
            assert self.reporter._file_removed_imports == 1

    @pytest.mark.parametrize(
        "mode, is_out",
        [
            ("default", True),
            ("check", True),
            ("diff", False),
            ("verbose", True),
            ("quiet", False),
            ("silence", False),
        ],
    )
    def test_expanded_star(self, mode, is_out):
        setattr(self.configs, mode, True)
        with sysu.std_redirect(sysu.STD.OUT) as stdout:
            self.reporter.expanded_star(Path(""), self.impt)
            assert bool(stdout.getvalue()) == is_out
            assert self.reporter._expanded_stars == 1
            assert self.reporter._file_expanded_stars == 1

    @contextmanager
    def assert_file_counters_reseted(self) -> Generator:
        file_counters = ("_file_removed_imports", "_file_expanded_stars")
        for counter in file_counters:
            setattr(self.reporter, counter, 10)
        yield
        for counter in file_counters:
            assert getattr(self.reporter, counter) == 0

    @pytest.mark.parametrize(
        "mode, is_out",
        [
            ("default", True),
            ("check", True),
            ("diff", False),
            ("verbose", True),
            ("quiet", True),
            ("silence", False),
        ],
    )
    def test_changed_file(self, mode, is_out):
        setattr(self.configs, mode, True)
        with sysu.std_redirect(sysu.STD.OUT) as stdout:
            with self.assert_file_counters_reseted():
                self.reporter.changed_file(Path(""))
                assert bool(stdout.getvalue()) == is_out
                assert self.reporter._changed_files == 1

    @pytest.mark.parametrize(
        "mode, is_out",
        [
            ("default", False),
            ("check", False),
            ("diff", False),
            ("verbose", True),
            ("quiet", False),
            ("silence", False),
        ],
    )
    def test_unchanged_file(self, mode, is_out):
        setattr(self.configs, mode, True)
        with sysu.std_redirect(sysu.STD.OUT) as stdout:
            with self.assert_file_counters_reseted():
                self.reporter.unchanged_file(Path(""))
                assert bool(stdout.getvalue()) == is_out
                assert self.reporter._unchanged_files == 1

    @pytest.mark.parametrize(
        "mode, is_err",
        [
            ("default", False),
            ("check", False),
            ("diff", False),
            ("verbose", True),
            ("quiet", False),
            ("silence", False),
        ],
    )
    def test_ignored_path(self, mode, is_err):
        setattr(self.configs, mode, True)
        with sysu.std_redirect(sysu.STD.ERR) as stderr:
            self.reporter.ignored_path(Path(""), None)
            assert bool(stderr.getvalue()) == is_err
            assert self.reporter._ignored_paths == 1

    @pytest.mark.parametrize(
        "mode, is_err",
        [
            ("default", False),
            ("check", False),
            ("diff", False),
            ("verbose", True),
            ("quiet", False),
            ("silence", False),
        ],
    )
    def test_ignored_import(self, mode, is_err):
        setattr(self.configs, mode, True)
        with sysu.std_redirect(sysu.STD.ERR) as stderr:
            self.reporter.ignored_import(Path(""), self.impt, False)
            assert bool(stderr.getvalue()) == is_err
            assert self.reporter._ignored_imports == 1

    @pytest.mark.parametrize(
        "mode, is_err",
        [
            ("default", True),
            ("check", True),
            ("diff", True),
            ("verbose", True),
            ("quiet", True),
            ("silence", False),
        ],
    )
    def test_failure(self, mode, is_err):
        setattr(self.configs, mode, True)
        with sysu.std_redirect(sysu.STD.ERR) as stderr:
            self.reporter.failure("", Path(""))
            assert bool(stderr.getvalue()) == is_err
            assert self.reporter._failures == 1

    @pytest.mark.parametrize(
        "mode, is_err",
        [
            ("default", True),
            ("check", True),
            ("diff", True),
            ("verbose", True),
            ("quiet", True),
            ("silence", False),
        ],
    )
    def test_init_without_all_warning(self, mode, is_err):
        setattr(self.configs, mode, True)
        with sysu.std_redirect(sysu.STD.ERR) as stderr:
            self.reporter.init_without_all_warning(Path(""))
            assert bool(stderr.getvalue()) == is_err
            assert self.reporter._undecidable_case == 1

    @pytest.mark.parametrize(
        "_failures, _changed_files, check, expec_code",
        [
            pytest.param(1, None, True, 250, id="internal error (check)"),
            pytest.param(1, None, False, 1, id="internal error (not-check)"),
            pytest.param(0, 1, True, 1, id="changed (check)"),
            pytest.param(0, 0, False, 0, id="changed (not-check)"),
            pytest.param(0, 0, False, 0, id="looks good"),
        ],
    )
    def test_exit_code(self, _failures, _changed_files, check, expec_code):
        self.reporter._failures = _failures
        self.reporter._changed_files = _changed_files
        self.configs.check = check
        assert self.reporter.exit_code == expec_code

    @pytest.mark.parametrize(
        "counters, mode, output_mode, err, is_out, expec_in_out",
        [
            pytest.param(
                (0, 0, 0, 0, 0, 0, 0, 0),
                "not-matter",
                "silence",
                sysu.Pass,
                False,
                "",
                id="silence",
            ),
            pytest.param(
                (0, 0, 0, 0, 0, 0, 0, 0),
                "not-matter",
                "not-matter",
                Exit,
                None,
                None,
                id="no-file",
            ),
            pytest.param(
                (1, 0, 1, 0, 0, 0, 0, 0),
                "check",
                "default",
                sysu.Pass,
                True,
                ["1 import would be removed", "1 file would be changed"],
                id="check",
            ),
            pytest.param(
                (1, 0, 1, 0, 0, 0, 0, 0),
                "diff",
                "default",
                sysu.Pass,
                True,
                ["1 import would be removed", "1 file would be changed"],
                id="diff",
            ),
            pytest.param(
                (1, 0, 1, 0, 0, 0, 0, 0),
                "default",
                "default",
                sysu.Pass,
                True,
                ["1 import was removed", "1 file was changed"],
                id="default",
            ),
            pytest.param(
                (1, 1, 1, 1, 0, 0, 1, 1),
                "default",
                "verbose",
                sysu.Pass,
                True,
                [
                    "1 import was removed",
                    "1 import was expanded",
                    "1 file was changed",
                    "1 file left unchanged",
                    "1 import was ignored",
                    "1 path was ignored",
                ],
                id="verbose, ignored",
            ),
            pytest.param(
                (2, 3, 4, 5, 0, 0, 3, 2),
                "default",
                "verbose",
                sysu.Pass,
                True,
                [
                    "2 imports were removed",
                    "3 imports were expanded",
                    "4 files were changed",
                    "5 files left unchanged",
                    "3 imports were ignored",
                    "2 paths were ignored",
                ],
                id="verbose, ignored, plural",
            ),
            pytest.param(
                (1, 1, 1, 1, 0, 0, 0, 0),
                "default",
                "default",
                sysu.Pass,
                True,
                "All done!",
                id="normal",
            ),
            pytest.param(
                (0, 0, 0, 1, 0, 0, 0, 0),
                "default",
                "default",
                sysu.Pass,
                True,
                "Looks good!",
                id="no-changes",
            ),
            pytest.param(
                (1, 1, 1, 1, 1, 1, 1, 1),
                "default",
                "default",
                sysu.Pass,
                True,
                "Oh no, there was an error!",
                id="failure",
            ),
            pytest.param(
                (1, 1, 1, 1, 0, 1, 1, 1),
                "default",
                "default",
                sysu.Pass,
                True,
                "Wait a minute, there was an undecidable case!",
                id="undecidable case",
            ),
        ],
    )
    def test_str_dunder(self, counters, mode, output_mode, err, is_out, expec_in_out):
        counters_order = (
            "_removed_imports",
            "_expanded_stars",
            "_changed_files",
            "_unchanged_files",
            "_failures",
            "_undecidable_case",
            "_ignored_imports",
            "_ignored_paths",
        )
        for name, val in zip(counters_order, counters):
            setattr(self.reporter, name, val)
        for mod in (mode, output_mode):
            setattr(self.configs, mod, True)
        with pytest.raises(err):
            with sysu.std_redirect(sysu.STD.OUT):
                str_report = str(self.reporter)
            raise sysu.Pass()
        if err is sysu.Pass:
            assert bool(str_report) == is_out
            if isinstance(expec_in_out, list):
                for snippet in expec_in_out:
                    assert snippet in str_report
            else:
                assert expec_in_out in str_report
