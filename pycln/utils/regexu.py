"""Pycln regex utility."""
import os
import re
import tokenize
from pathlib import Path
from typing import List, Pattern

import typer
from pathspec import PathSpec
from pathspec.patterns import GitWildMatchPattern

# Constants.
INCLUDE = "include"
EXCLUDE = "exclude"
GITIGNORE = ".gitignore"
SKIP_FILE_REGEX = r"# *(nopycln *: *file).*"
SKIP_IMPORT_REGEX = r"# *((noqa *:*)|(nopycln *: *import)).*"
INCLUDE_REGEX = r".*\.py$"
EXCLUDE_REGEX = (
    r"(\.eggs|\.git|\.hg|\.mypy_cache|__pycache__|\.nox|"
    + r"\.tox|\.venv|\.svn|buck-out|build|dist)/"
)


def safe_compile(pattern: str, type_: str) -> Pattern[str]:
    """Safely compile [--include, --exclude] options regex.

    :param pattern: an str regex to be complied.
    :param type_: 'include' OR 'exclude'.
    :returns: complied regex.
    """
    try:
        if isinstance(pattern, str):
            compiled: Pattern[str] = re.compile(pattern, re.IGNORECASE)
            return compiled
        return pattern  # type: ignore
    except re.error as err:
        typer.secho(
            f"Invalid regular expression for {type_} given: {pattern!r} ⛔",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(1) from err


def is_included(name: str, regex: Pattern[str]) -> bool:
    """Check if the file/directory name match include pattern.

    :param name: file/directory name to check.
    :param regex: include regex pattern.
    :returns: True if the name match else False.
    """
    return bool(regex.fullmatch(name))


def is_excluded(name: str, regex: Pattern[str]) -> bool:
    """Check if the file/directory name match exclude pattern.

    :param name: file/directory name to check.
    :param regex: exclude regex pattern.
    :returns: True if the name match else False.
    """
    return bool(regex.fullmatch(name))


def get_gitignore(root: Path, no_gitignore: bool = False) -> PathSpec:
    """Return a PathSpec matching gitignore content, if present.

    :param root: root path to search for `.gitignore`.
    :param no_gitignore: `config.no_gitignore` value (default=False).
    :returns: PathSpec matching gitignore content, if present.
    """
    lines: List[str] = []
    if not no_gitignore:
        path = os.path.join(root, GITIGNORE)
        if os.path.isfile(path):
            if os.access(path, os.R_OK):
                with tokenize.open(path) as ignore_file:
                    lines = ignore_file.readlines()
    return PathSpec.from_lines(GitWildMatchPattern, lines)


def skip_import(line: str) -> bool:
    """Check if the lines has `# noqa` or `# nopycln: import` to skip.

    :param line: a line to check.
    :returns: True if it matches else False.
    """
    return bool(re.search(SKIP_IMPORT_REGEX, line, re.IGNORECASE))


def skip_file(src_code: str) -> bool:
    """Check if the src_code code has `nopycln: file` comment to skip.

    :param src_code: string source code to check.
    :returns: True if it matches else False.
    """
    return bool(re.search(SKIP_FILE_REGEX, src_code, re.IGNORECASE))
