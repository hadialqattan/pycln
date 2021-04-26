"""pycln/utils/cli.py tests."""
# pylint: disable=R0201,W0613
import pytest
from typer.testing import CliRunner

from pycln import __doc__, __version__, cli

from . import CONFIG_DIR
from .utils.sysu import reopenable_temp_file

# Constants.
CONFIG_FILE = CONFIG_DIR.joinpath("setup.cfg")


class TestCli:

    """some `cli.py` tests."""

    def _assert_code_in(self, expec_out, *args, expec_exit_code=0):
        results = self.cli.invoke(cli.app, args)
        if expec_out:
            assert expec_out in results.stdout
        assert results.exit_code == expec_exit_code

    def setup_method(self, method):
        # results = self.cli.invoke(cli.app, args...)
        self.cli = CliRunner()

    @pytest.mark.parametrize("flag", ["-h", "--help"])
    def test_help(self, flag):
        self._assert_code_in(__doc__, flag)

    def test_version(self):
        self._assert_code_in(__version__, "--version")

    @pytest.mark.parametrize(
        "expec_out, args, expec_change, expec_exit_code",
        [
            pytest.param("1 import has removed", ["--all"], True, 0, id="default"),
            pytest.param("1 file left unchanged", [], False, 0, id="side effects"),
            pytest.param(
                "1 import would be removed", ["--all", "--check"], False, 1, id="check"
            ),
            pytest.param(
                "import x\n",
                ["--config", str(CONFIG_FILE)],
                False,
                0,
                id="config-file, diff",
            ),
        ],
    )
    def test_integrations(self, expec_out, args, expec_change, expec_exit_code):
        content = "import x, y\nx\n"
        with reopenable_temp_file(content) as tmp_path:
            with open(tmp_path) as tmp:
                args = [str(tmp_path)] + args
                self._assert_code_in(expec_out, *args, expec_exit_code=expec_exit_code)
                if expec_change:
                    assert tmp.read() == content.replace(", y", "")
                else:
                    assert tmp.read() == content
