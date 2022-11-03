import io
import os
import sys
import tokenize
from pathlib import Path

import tomlkit
import typer

#: Add vendor directory to module search path
VENDOR_PATH = Path(__file__).parent.parent.joinpath("vendor")
sys.path.append(str(VENDOR_PATH))


#: Fixes `UnicodeEncodeError` in non-utf8 terminals.
#: For more info: https://github.com/hadialqattan/pycln/issues/54
UTF8 = "utf-8"
if "pytest" not in sys.modules:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=UTF8)  # pragma: nocover
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding=UTF8)  # pragma: nocover

ISWIN = os.name == "nt"
PYPROJECT_PATH = Path(__file__).parent.parent.joinpath("pyproject.toml")

with tokenize.open(PYPROJECT_PATH) as toml_f:
    pycln = tomlkit.parse(toml_f.read())["tool"]["poetry"]  # type: ignore[index]

__name__ = str(pycln["name"])  # type: ignore[index]
__doc__ = str(pycln["description"])  # type: ignore[index]
__version__ = pycln["version"]  # type: ignore[index]


def version_callback(value: bool):
    """Show the version and exit with 0."""
    if value:
        typer.echo(f"{__name__}, version {__version__}")
        raise typer.Exit(0)
