"""
Pycln config utility.
"""
from dataclasses import dataclass
from pathlib import Path
from typing import Pattern

import typer

from . import regexu

# Constants.
EMPTY = ""


@dataclass
class Config:

    """Pycln configs dataclass."""

    def __post_init__(self):
        self.check_path()
        self.include: Pattern[str] = regexu.safe_compile(self.include, regexu.INCLUDE)
        self.exclude: Pattern[str] = regexu.safe_compile(self.exclude, regexu.EXCLUDE)

    path: Path
    include: str = regexu.INCLUDE_REGEX
    exclude: str = regexu.EXCLUDE_REGEX
    all_: bool = False
    check: bool = False
    diff: bool = False
    verbose: bool = False
    quiet: bool = False
    silence: bool = False
    expand_star_imports: bool = False
    no_gitignore: bool = False

    def check_path(self) -> None:
        """Validate `self.path`."""
        if not self.path:
            typer.secho(
                "No Path provided. Nothing to do 😴",
                bold=True,
                err=True,
            )
            raise typer.Exit(1)

        if not self.path.is_dir():
            typer.secho(
                f"'{self.path}' is not a directory. Maybe it does not exist 😅",
                bold=True,
                err=True,
            )
            raise typer.Exit(1)
