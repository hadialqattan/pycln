"""pycln/utils/refactor.py tests."""
import tempfile
from pathlib import Path

import pytest
from pytest_mock import mock

from pycln.utils import config, refactor, report
from pycln.utils._exceptions import (
    ReadPermissionError,
    UnparsableFile,
    WritePermissionError,
)

from .utils import sysu

# Constants.
MOCK = "pycln.utils.refactor.%s"


class TestRefactor:

    """`Refactor` methods test case."""

    def setup_method(self, method):
        self.configs = config.Config(Path(""))
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
                    "def foo():\n",
                    "    '''docs'''\n",
                    "    pass\n",
                ],
                [
                    "def foo():\n",
                    "    '''docs'''\n",
                ],
                id="useless with docs",
            ),
        ],
    )
    def test_remove_useless_passes(self, source_lines, expec_lines):
        fixed_code = refactor.Refactor.remove_useless_passes(source_lines)
        assert fixed_code == expec_lines

    @pytest.mark.parametrize(
        "safe_read_raise, _code_session_raise",
        [
            pytest.param(None, None, id="without errors"),
            pytest.param(
                ReadPermissionError(13, "", Path("")), None, id="ReadPermissionError"
            ),
            pytest.param(
                WritePermissionError(13, "", Path("")), None, id="WritePermissionError"
            ),
            pytest.param(
                None, UnparsableFile(Path(""), SyntaxError("")), id="UnparsableFile"
            ),
        ],
    )
    @mock.patch(MOCK % "Refactor._output")
    @mock.patch(MOCK % "Refactor._code_session")
    @mock.patch(MOCK % "iou.safe_read")
    def test_session(
        self, safe_read, _code_session, _output, safe_read_raise, _code_session_raise
    ):
        safe_read.return_value = ("code...\ncode...\n", "utf-8")
        safe_read.side_effect = safe_read_raise
        _code_session.return_value = "code...\ncode...\n"
        _code_session.side_effect = _code_session_raise
        self.session_maker.session(Path("modified"))
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
        "fixed_lines, original_lines, mode, expec_output",
        [
            pytest.param(
                ["code..\n"], ["code..\n"], "verbose", "looks good!", id="unchanged"
            ),
            pytest.param(
                ["fixed.code..\n"],
                ["original.code..\n"],
                "check",
                "🚀",
                id="changed-check",
            ),
            pytest.param(
                ["import x\n"],
                ["import x, y\n"],
                "diff",
                "-import x, y\n+import x\n",
                id="changed-diff",
            ),
            pytest.param(
                ["import x\n"],
                ["import x, y\n"],
                "diff",
                "-import x, y\n+import x\n",
                id="changed-diff",
            ),
        ],
    )
    @mock.patch(MOCK % "Refactor.remove_useless_passes")
    def test_output(self, x, fixed_lines, original_lines, mode, expec_output):
        x.return_value = fixed_lines
        setattr(self.configs, mode, True)
        with sysu.std_redirect(sysu.STD.OUT) as stdout:
            self.session_maker._output(fixed_lines, original_lines, "utf-8")
            assert expec_output in stdout.getvalue()

    @mock.patch(MOCK % "Refactor.remove_useless_passes")
    def test_output_write(self, x):
        fixed_lines, original_lines = ["import x\n"], ["import x, y\n"]
        x.return_value = fixed_lines
        with tempfile.NamedTemporaryFile(mode="w+", suffix=".py") as tmp:
            tmp.writelines(original_lines)
            tmp.seek(0)
            self.session_maker._path = Path(tmp.name)
            self.session_maker._output(fixed_lines, original_lines, "utf-8")
            tmp.seek(0)
            assert tmp.readlines() == fixed_lines
