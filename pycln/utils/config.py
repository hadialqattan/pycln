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

    """
    Pycln configs dataclass.
    """

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
    ignored_paths: FrozenSet[Path] = frozenset()

    def compute_sources(self) -> FrozenSet[Path]:
        """
        Compute sources to handle.
        """
        # Compute `.gitignore`.
        gitignore = regexu.get_gitignore(self.path if not self.no_gitignore else EMPTY)

        # Compute list of sources.
        sources = []
        ignored_paths = []
        walk = pathu.walk(self.path, self.include, self.exclude, gitignore)
        for root, _, files, ignored in walk:
            sources.extend(map(partial(os.path.join, root), files))
            ignored_paths.extend(map(partial(os.path.join, root), ignored_paths))

        if not sources:
            typer.secho(
                "No Python files are present to be cleaned. Nothing to do 😴",
                fg=typer.colors.BRIGHT_WHITE,
                bold=True,
                err=True,
            )
            raise typer.Exit()

        self.sources = frozenset(sources)
        self.ignored_paths = frozenset(ignored_paths)

    def check_path(self):
        """
        Validate `self.path`.
        """
        if not self.path:
            typer.secho(
                "No Path provided. Nothing to do 😴",
                fg=typer.colors.BRIGHT_WHITE,
                bold=True,
                err=True,
            )
            raise typer.Exit()

        if not self.path.is_dir():
            typer.secho(
                f"'{self.path}' is not a directory. Maybe it does not exist 😅",
                fg=typer.colors.BRIGHT_WHITE,
                bold=True,
                err=True,
            )
            raise typer.Exit()
