import io
import os
import sys
from importlib.metadata import metadata
from pathlib import Path

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

pycln = metadata("pycln")
__name__ = str(pycln["Name"])
__doc__ = str(pycln["Summary"])
__version__ = str(pycln["Version"])


def version_callback(value: bool):
    """Show the version and exit with 0."""
    if value:
        typer.echo(f"{__name__}, version {__version__}")
        raise typer.Exit(0)
