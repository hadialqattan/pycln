"""pycln `__init__.py`/`pyproject.toml` metadata tests."""

# pylint: disable=R0201,W0613
import sys
import tokenize
from os import getenv
from pathlib import Path

import pytest
import requests
import tomlkit
from semver import VersionInfo
from typer import Exit

from pycln import VENDOR_PATH, __doc__, __name__, __version__, version_callback

from .utils import sysu

# Constants.
PYPROJECT_PATH = Path(__file__).parent.parent.joinpath("pyproject.toml")
with tokenize.open(PYPROJECT_PATH) as toml_f:
    PYCLN_METADATA = tomlkit.parse(toml_f.read())["tool"]["poetry"]  # type: ignore

PYCLN_PYPI_JSON_URL = f"https://pypi.org/pypi/{__name__}/json"
PYCLN_PYPI_URL = f"https://pypi.org/project/{__name__}/"


class TestMetadata:
    """`__init__.py`/`pyproject.toml` test case."""

    def test_vendor_path(self):
        assert VENDOR_PATH.is_dir()
        assert str(VENDOR_PATH) in sys.path

    def test_pyproject_path(self):
        assert PYPROJECT_PATH.is_file()
        assert str(PYPROJECT_PATH).endswith("pyproject.toml")

    def test_doc(self):
        assert isinstance(__doc__, str)
        assert len(__doc__) > 30, "Too short description!"
        assert len(__doc__) <= 100, "Too long description!"
        assert __doc__ == PYCLN_METADATA["description"]

    def test_name(self):
        assert isinstance(__name__, str)
        assert __name__ == PYCLN_METADATA["name"] == "pycln"

    def test_validate_semver(self):
        # It follows strictly the 2.0.0 version of the SemVer scheme.
        # For more information: https://semver.org/spec/v2.0.0.html
        assert isinstance(__version__, str)
        assert VersionInfo.isvalid(__version__), (
            "Invalid semantic-version."
            "For more information: https://semver.org/spec/v2.0.0.html"
        )
        assert __version__ == PYCLN_METADATA["version"]

    @pytest.mark.skipif(
        getenv("CI", "false") != "true" or not VersionInfo.isvalid(__version__),
        reason="Invalid semantic-version.",
    )
    def test_compare_semver(self):
        # It follows strictly the 2.0.0 version of the SemVer scheme.
        # For more information: https://semver.org/spec/v2.0.0.html
        pycln_json = requests.get(PYCLN_PYPI_JSON_URL, timeout=5)
        latest_version = pycln_json.json()["info"]["version"]
        current_version = VersionInfo.parse(__version__)
        assert current_version.compare(latest_version) > -1, (
            f"Current version ({current_version}) can't be less than the "
            f"latest released ({PYCLN_PYPI_URL}) version ({latest_version})!"
        )

    @pytest.mark.parametrize(
        "value, expec_err, expec_exit_code",
        [
            pytest.param(True, Exit, 0, id="value=True"),
            pytest.param(False, sysu.Pass, None, id="value=False"),
        ],
    )
    def test_version_callback(self, value, expec_err, expec_exit_code):
        with sysu.std_redirect(sysu.STD.OUT) as stream:
            with pytest.raises(expec_err):
                version_callback(value)
                raise sysu.Pass()
            stdout = stream.getvalue()
            if expec_err is Exit:
                assert __version__ in stdout
            else:
                assert not stdout
