import io
import os
import sys
from pathlib import Path

import toml
import typer

#: Fixes `UnicodeEncodeError` in non-utf8 terminals.
#: For more info: https://github.com/hadialqattan/pycln/issues/54
UTF8 = "utf-8"
if "pytest" not in sys.modules:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=UTF8)  # pragma: nocover
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding=UTF8)  # pragma: nocover

ISWIN = os.name == "nt"
PYPROJECT_PATH = Path(__file__).parent.parent.joinpath("pyproject.toml")
pycln = toml.load(PYPROJECT_PATH)["tool"]["poetry"]

__name__ = pycln["name"]
__version__ = pycln["version"]
__doc__ = pycln["description"]


def version_callback(value: bool):
    """Show the version and exit with 0."""
    if value:
        typer.echo(f"{__name__}, version {__version__}")
        raise typer.Exit(0)
