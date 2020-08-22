"""
Pycln config utility.
"""
import os
from dataclasses import dataclass
from functools import partial
from pathlib import Path
from typing import FrozenSet, Pattern

import typer

from . import pathu, regexu

# Constants.
EMPTY = ""


@dataclass
class Config:

    """Pycln configs dataclass."""

    def __post_init__(self):
        self.check_path()
        self.include: Pattern[str] = regexu.safe_compile(self.include, regexu.INCLUDE)
        self.exclude: Pattern[str] = regexu.safe_compile(self.exclude, regexu.EXCLUDE)
        self.compute_sources()

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

    # This will be computed.
    sources: FrozenSet[Path] = frozenset()

    def compute_sources(self) -> None:
        """Compute sources to handle them."""
        # Compute `.gitignore`.
        gitignore = regexu.get_gitignore(self.path if not self.no_gitignore else EMPTY)

        # Compute list of sources.
        sources = []
        walk = pathu.walk(self.path, self.include, self.exclude, gitignore)
        for root, _, files in walk:
            sources.extend(map(partial(os.path.join, root), files))

        if not sources:
            typer.secho(
                "No Python files are present to be cleaned. Nothing to do 😴",
                bold=True,
                err=True,
            )
            raise typer.Exit()

        self.sources = frozenset(sources)

    def check_path(self) -> None:
        """Validate `self.path`."""
        if not self.path:
            typer.secho(
                "No Path provided. Nothing to do 😴", bold=True, err=True,
            )
            raise typer.Exit(1)

        if not self.path.is_dir():
            typer.secho(
                f"'{self.path}' is not a directory. Maybe it does not exist 😅",
                bold=True,
                err=True,
            )
            raise typer.Exit(1)


# To avoid reiniting or passing.
# this should be changed at the `main` function.
configs: Config = None
