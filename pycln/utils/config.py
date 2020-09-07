"""
Pycln configuration management utility.
"""
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Pattern, Union

import typer

from . import regexu

# Constants.
EMPTY = ""
DOT_FSLSH = "./"
DDOT_FSLSH = "../"


@dataclass
class Config:

    """Pycln configs dataclass."""

    def __post_init__(self):
        self._check_path()
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
    expand_stars: bool = False
    no_gitignore: bool = False

    def _check_path(self) -> None:
        """Validate `self.path`."""
        if not self.path:
            typer.secho(
                "No Path provided. Nothing to do 😴",
                bold=True,
                err=True,
            )
            raise typer.Exit(1)

        if not (self.path.is_dir() or self.path.is_file()):
            typer.secho(
                f"'{self.path}' is not a directory or a file. Maybe it does not exist 😅",
                bold=True,
                err=True,
            )
            raise typer.Exit(1)

    def get_relpath(self, path: Union[Path, str]) -> Path:
        """Get relative path from the given `path`.

        :param path: an absolute path.
        :returns: a relative path (relative to `self.configs.path`).
        """
        relpath, conf_path = Path(path), self.configs.path

        if not relpath.is_file():
            os_relpath = os.path.relpath(relpath, conf_path)
            relpath = os.path.join(conf_path, os_relpath)

        if not str(relpath).startswith((DOT_FSLSH, DDOT_FSLSH)):
            relpath = (DOT_FSLSH, relpath)
        return Path(relpath)
