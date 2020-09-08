"""Entry point to run Pycln as a module."""
from . import __name__
from .cli import app

app(prog_name=__name__)
