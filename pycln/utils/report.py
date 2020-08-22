"""
Pycln report utility.
"""
from dataclasses import dataclass
from typing import Union
from pathlib import Path
from copy import copy
import ast
import os

import typer

from . import config, ast2source as ast2s
from .config import configs

# Constants.
DOT = "."
EMPTY = ""
SPACE = " "
COLUMN = ":"
COMMA_SP = ", "
NEW_LINE = "\n"
DOT_FSLSH = "./"


@dataclass
class Report:

    """Provide a Pycln report counters. Can be rendered with `str(report)`."""

    def get_relpath(self, path: Path) -> Path:
        """Get relative path from the given absolute path.

        :param path: an absolute path.
        :returns: a relative path (relative to `configs.path`).
        """
        rel_path = os.path.join(
            configs.path, os.path.relpath(path, configs.path)
        )
        return (
            os.path.join(DOT_FSLSH, rel_path)
            if not rel_path.startswith(DOT_FSLSH)
            else rel_path
        )

    def secho(
        self,
        message: str,
        bold: bool,
        err: bool = False,
        isedit: bool = False,
        issuccess: bool = False,
        iswarning: bool = False,
        iserror: bool = False,
    ) -> str:
        """Print a colored message.

        :param message: a string message.
        :param bold: is if a bold message.
        :param err: redirect to stderr instead of stdout.
        :param isedit: is it an edit message.
        :param issuccess: is it a success message.
        :param iswarning: is it a warning message.
        :param iserror: is it an error message.
        """
        if isedit:
            color = typer.colors.BRIGHT_BLUE
        elif issuccess:
            color = typer.colors.BRIGHT_GREEN
        elif iswarning:
            color = typer.colors.BRIGHT_YELLOW
        elif iserror:
            color = typer.colors.BRIGHT_RED
        else:
            color = typer.colors.RESET
        # Print the colored message
        typer.echo(
            typer.style(SPACE, bg=color) + SPACE + typer.style(message, bold=bold),
            err=err,
        )

    # Counters.
    __removed_imports: int = 0

    def removed_import(
        self,
        source: Path,
        node: Union[ast.Import, ast.ImportFrom],
        removed_alias: ast.alias,
    ) -> None:
        """Increment the counter for removed importes. Write a message to stdout.

        :param source: where the import has removed.
        :param node: remove import node.
        :param removed_alias: the removed `ast.alias` from the node.
        """
        if not any([configs.diff, configs.quiet, configs.silence]):

            abc_node = copy(node)
            abc_node.names = [removed_alias]

            if isinstance(abc_node, ast.Import):
                statement = ast2s.rebuild_import(abc_node)

            elif isinstance(abc_node, ast.ImportFrom):
                statement = ast2s.rebuild_import_from(abc_node, None)

            statement = statement.replace(NEW_LINE, EMPTY).lstrip(SPACE)
            location = COLUMN.join(
                [
                    self.get_relpath(source),
                    str(abc_node.lineno),
                    str(abc_node.col_offset),
                ]
            )
            removed = "has removed" if not configs.check else "whould be removed"
            self.secho(
                f"{location} {statement!r} {removed}! 🔮", bold=False, isedit=True
            )

        self.__removed_imports += 1
        self.__file_removed_imports += 1

    __changed_files: int = 0
    __file_removed_imports: int = 0

    def changed_file(self, source: Path) -> None:
        """Increment the counter for changed files. Write a message to stdout.

        :param source: the changed file path.
        """
        if not any([configs.diff, configs.silence]):
            removed = "has removed" if not configs.check else "whould be removed"
            s = "s" if self.__file_removed_imports > 1 else ""
            self.secho(
                f"{self.get_relpath(source)} {self.__file_removed_imports} import{s} {removed}! 🚀",
                bold=True,
                isedit=True,
            )

        self.__changed_files += 1
        self.__file_removed_imports = 0

    __unchanged_files: int = 0

    def unchanged_file(self, source: Path) -> None:
        """Increment the counter for unchanged files. Write a message to stdout.

        :param source: the unchanged file path.
        """
        if any([configs.verbose, configs.diff]):
            self.secho(
                f"{self.get_relpath(source)} looks good! ✨", bold=False, issuccess=True
            )
        self.__unchanged_files += 1

    __ignored_paths: int = 0

    def ignored_path(self, ignored_path: Path, type_: str) -> None:
        """Increment the counter for ignored paths. Write a message to stderr.

        :param ignored_path: the ignored path.
        :param type_: ignore type, `exclude` or `enclude` or `gitignore`.
        """
        if configs.verbose:
            if type_ == "exclude":
                type_ = "matches the --exclude regex"
            elif type_ == "gitignore":
                type_ = "matches the .gitignore patterns"
            else:
                type_ = "does not match the --include regex"
            self.secho(
                f"{self.get_relpath(ignored_path)} has ignored: {type_}! ⚠️",
                bold=False,
                err=True,
                iswarning=True,
            )
        self.__ignored_paths += 1

    __ignored_imports: int = 0

    def ignored_import(
        self, source: Path, node: Union[ast.Import, ast.ImportFrom]
    ) -> None:
        """Increment the counter for ignored imports. Write a message to stderr.

        :param source: where the import has ignored.
        :param node: the ignored import node.
        """
        if configs.verbose:
            if isinstance(node, ast.Import):
                statement = ast2s.rebuild_import(node)

            elif isinstance(node, ast.ImportFrom):
                statement = ast2s.rebuild_import_from(node, None).replace(
                    NEW_LINE, EMPTY
                )

                if isinstance(statement, list):
                    statement = statement[0] + f" {DOT*3}"
            self.secho(
                f"{statement} has ignored! ⚠️", bold=False, err=True, iswarning=True
            )
        self.__ignored_imports += 1

    __failures: int = 0

    def failure(self, message: str, source: Path = None) -> None:
        """Increment the counter for failures counter. Write a message to stderr.

        :param message: a failure message.
        :param source: where the failure has appeared.
        """
        if not configs.silence:
            message = (
                f"{self.get_relpath(source)} {message} ⛔" if source else f"{message} ⛔"
            )
            self.secho(message, bold=False, err=True, iserror=True)
        self.__failures += 1

    @property
    def exit_code(self) -> int:
        """Return an exit code."""
        # According to http://tldp.org/LDP/abs/html/exitcodes.html
        # exit codes 1 - 2, 126 - 165, and 255 have special meanings,
        # and should therefore be avoided for user-specified exit parameters
        if self.__failures:
            # Internal error.
            return 250
        if self.__changed_files and configs.check:
            # File(s) should be refactord.
            return 1
        # Everything is fine.
        return 0

    def __str__(self) -> str:
        """Render a counters report. can renders using `str(object)`"""
        if any([configs.check, configs.diff]):
            removed_imports = "would be removed"
            changed_files = "would be changed"
            unchanged_files = "would be left unchanged"
        else:
            removed_imports = "has removed"
            changed_files = "has changed"
            unchanged_files = "left unchanged"
        failures = "has failed to be cleaned"

        report = []

        if self.__removed_imports:
            s = "s" if self.__removed_imports > 1 else ""
            report.append(
                typer.style(
                    f"{self.__removed_imports} import{s} {removed_imports}", bold=True
                )
            )

        if self.__changed_files:
            s = "s" if self.__changed_files > 1 else ""
            report.append(
                typer.style(
                    f"{self.__changed_files} file{s} {changed_files}", bold=True
                )
            )

        if self.__unchanged_files:
            s = "s" if self.__unchanged_files > 1 else ""
            report.append(
                typer.style(
                    f"{self.__unchanged_files} file{s} {unchanged_files}", bold=False
                )
            )

        if self.__failures:
            s = "s" if self.__failures > 1 else ""
            report.append(
                typer.style(f"{self.__failures} file{s} {failures}", bold=False)
            )

        if configs.verbose:
            ignored_imports = "has ignored"
            ignored_paths = "has ignored"

            if self.__ignored_imports:
                s = "s" if self.__ignored_imports > 1 else ""
                report.append(
                    typer.style(
                        f"{self.__ignored_imports} import{s} {ignored_imports}",
                        bold=False,
                    )
                )

            if self.__ignored_paths:
                s = "s" if self.__ignored_paths > 1 else ""
                report.append(
                    typer.style(
                        f"{self.__ignored_paths} path{s} {ignored_paths}", bold=False
                    )
                )

        prefix = (
            NEW_LINE
            if report
            and any([configs.verbose, self.__removed_imports, self.__failures])
            else EMPTY
        )
        done_msg = typer.style(
            (
                ("All done! 💪 😎" if self.__removed_imports else "Looks good! ✨ 🍰 ✨")
                if not self.__failures
                else f"Oh no, there {'are errors' if self.__failures > 1 else 'is an error'}! 💔 ☹️"
            )
            + NEW_LINE,
            bold=True,
        )
        return prefix + done_msg + COMMA_SP.join(report) + DOT


# To avoid reiniting or passing.
# this should be changed at the `main` function.
reporter: Report = None
