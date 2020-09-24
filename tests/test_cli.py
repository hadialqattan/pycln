"""pycln/utils/cli.py tests."""
import tempfile
from pathlib import Path

import pytest
from typer.testing import CliRunner

from pycln import __doc__, __version__, cli

# Constants.
CONFIG_FILE = Path(__file__).parent.joinpath(Path("config/setup.cfg"))


class TestCli:

    """some `cli.py` tests."""

    def _assert_code_in(self, expec_out, expec_err, *args):
        results = self.cli.invoke(cli.app, args)
        if expec_out:
            assert expec_out in results.stdout
        if expec_err:
            assert expec_err in results.stderr
        assert results.exit_code == 0

    def setup_method(self, method):
        # results = self.cli.invoke(cli.app, args...)
        self.cli = CliRunner()

    @pytest.mark.parametrize("flag", ["-h", "--help"])
    def test_help(self, flag):
        self._assert_code_in(__doc__, None, flag)

    def test_version(self):
        self._assert_code_in(__version__, None, "--version")

    @pytest.mark.parametrize(
        "expec_out, args, expec_change",
        [
            pytest.param("1 import has removed", ["--all"], True, id="default"),
            pytest.param(
                "1 import would be removed", ["--all", "--check"], False, id="check"
            ),
            pytest.param("1 file left unchanged", [], False, id="side effects"),
            pytest.param(
                "import x\n",
                ["--config", str(CONFIG_FILE)],
                False,
                id="config-file, diff",
            ),
        ],
    )
    def test_integrations(self, expec_out, args, expec_change):
        with tempfile.NamedTemporaryFile(mode="w+", suffix=".py") as tmp:
            tmp.write("import x, y\n" "x\n")
            tmp.seek(0)
            args = [tmp.name] + args
            self._assert_code_in(expec_out, None, *args)
            tmp.seek(0)
            if expec_change:
                assert tmp.read() == ("import x\n" "x\n")
            else:
                assert tmp.read() == ("import x, y\n" "x\n")
