import toml
import typer

pycln = toml.load("./pyproject.toml")["tool"]["poetry"]

__name__ = pycln["name"]
__version__ = pycln["version"]
__doc__ = pycln["description"]


def version_callback(value: bool):
    if value:
        typer.echo(f"{__name__}, version {__version__}")
        raise typer.Exit(0)
