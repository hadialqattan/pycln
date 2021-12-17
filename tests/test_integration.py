"""Integration tests."""
# pylint: disable=R0201,W0613
import pytest
from typer.testing import CliRunner

from pycln import cli

from . import DATA_DIR

# Constants.
INTEGRATION_DATA_DIR = DATA_DIR.joinpath("integration")


class TestIntegration:
    def _assert_code_in(self, expec_out, *args, expec_exit_code=0):
        results = self.cli.invoke(cli.app, args)
        for snippet in expec_out:
            assert snippet in results.stdout

        assert results.exit_code == expec_exit_code

    def _create_file(self, path, contents):
        filepath = INTEGRATION_DATA_DIR.joinpath(path)
        with filepath.open("w") as f:
            f.write(contents)

    def _check_file_contents(self, path, contents):
        filepath = INTEGRATION_DATA_DIR.joinpath(path)
        with filepath.open("r") as f:
            assert f.read() == contents

    def setup_method(self, method):
        self.cli = CliRunner()

    def teardown_method(self, method):
        """Delete all created python files in INTEGRATION_DATA_DIR."""
        for py_file in [
            py_file
            for py_file in INTEGRATION_DATA_DIR.glob("*.py")
            if py_file.is_file()
        ]:
            py_file.unlink()

    @pytest.mark.parametrize(
        ("expec_out, args, expec_init, expec_exit_code"),
        [
            pytest.param(
                # We're told an import has been removed
                ["'from y import *' was removed! 🔮", "1 import was removed"],
                [],
                # And the file has changed
                "from x import *\n",
                0,
                id="default",
            ),
            pytest.param(
                ["'from y import *' would be removed! 🔮", "1 import would be removed"],
                ["--check"],
                "from x import *\nfrom y import *",
                1,
                id="check",
            ),
            pytest.param(
                # We're told two imports have been removed
                [
                    "'from x import *' was removed! 🔮",
                    "'from y import *' was removed! 🔮",
                    "2 imports were removed",
                ],
                ["--all"],
                # And both have been removed
                "",
                0,
                id="all",
            ),
            pytest.param(
                [
                    "'from x import *' would be removed! 🔮",
                    "'from y import *' would be removed! 🔮",
                    "2 imports would be removed",
                ],
                ["--all", "--check"],
                "from x import *\nfrom y import *",
                1,
                id="all, check",
            ),
        ],
    )
    def test_non_regression_star_imports(
        self, expec_out, args, expec_init, expec_exit_code
    ):
        """See https://github.com/hadialqattan/pycln/issues/91."""
        self._create_file("__init__.py", "from x import *\nfrom y import *")
        self._create_file("x.py", "CONSTANT = 1")
        self._create_file("y.py", '"""Purposefully left blank"""')

        args = [str(INTEGRATION_DATA_DIR)] + args
        self._assert_code_in(expec_out, *args, expec_exit_code=expec_exit_code)

        self._check_file_contents("__init__.py", expec_init)
        # x.py and y.py don't change
        self._check_file_contents("x.py", "CONSTANT = 1")
        self._check_file_contents("y.py", '"""Purposefully left blank"""')
