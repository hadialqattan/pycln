"""
Pycln report utility.
"""
import ast
import os
from copy import copy
from dataclasses import dataclass
from difflib import unified_diff
from pathlib import Path
from typing import List, Union

import typer

from . import config, nodes

# Constants.
AT = "@"
AS = "as"
DOT = "."
STAR = "*"
DASH = "-"
PLUS = "+"
FROM = "from"
EMPTY = ""
SPACE = " "
COMMA = ","
COLUMN = ":"
IMPORT = "import"
COMMA_SP = ", "
NEW_LINE = "\n"
DOT_FSLSH = "./"


@dataclass
class Report:

    """Provide a Pycln report counters. Can be rendered with `str(report)`."""

    configs: config.Config

    def get_relpath(self, path: Path) -> Path:
        """Get relative path from the given absolute path.

        :param path: an absolute path.
        :returns: a relative path (relative to `self.configs.path`).
        """
        rel_path = os.path.join(
            self.configs.path, os.path.relpath(path, self.configs.path)
        )
        return (
            os.path.join(DOT_FSLSH, rel_path)
            if not rel_path.startswith(DOT)
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
    ) -> None:
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

    def colored_unified_diff(
        self, source: str, original_lines: List[str], fixed_lines: List[str]
    ) -> None:
        """Writeout colored and normalized diff.

        :param source: a file path.
        :param original_lines: original source code lines.
        :param fixed_lines: fixed source code lines.
        """
        fixed_lines = [line for line in fixed_lines if line != EMPTY]
        diff_gen = unified_diff(
            original_lines,
            fixed_lines,
            fromfile=f"original/ {source}",
            tofile=f"fixed/ {source}",
            n=3,
            lineterm=NEW_LINE,
        )
        diff_str = EMPTY
        for line in diff_gen:
            if line.startswith(DASH):
                line = typer.style(line, fg=typer.colors.RED)
            elif line.startswith(PLUS):
                line = typer.style(line, fg=typer.colors.GREEN)
            elif line.startswith(AT):
                line = typer.style(line, fg=typer.colors.CYAN)
            diff_str += line
        diff_str = diff_str.rstrip(NEW_LINE + SPACE) + NEW_LINE
        typer.echo(diff_str)

    def rebuild_report_import(
        self,
        node: Union[ast.Import, ast.ImportFrom, nodes.Import, nodes.ImportFrom],
        alias: ast.alias,
    ) -> str:
        str_alias = (
            f"{alias.name}{SPACE}{AS}{SPACE}{alias.asname}"
            if alias.asname
            else alias.name
        )
        str_import = (
            f"{FROM}{SPACE}{node.module}{SPACE}{IMPORT}"
            if hasattr(node, "level")
            else f"{IMPORT}{SPACE}"
        )
        return f"{str_import}{SPACE}{str_alias}"

    # Counters.
    __removed_imports: int = 0

    def removed_import(
        self,
        source: Path,
        node: Union[ast.Import, ast.ImportFrom, nodes.Import, nodes.ImportFrom],
        removed_alias: ast.alias,
    ) -> None:
        """Increment the counter for removed importes. Write a message to stdout.

        :param source: where the import has removed.
        :param node: removed import node.
        :param removed_alias: the removed `ast.alias` from the node.
        """
        if not any([self.configs.diff, self.configs.quiet, self.configs.silence]):

            statement = self.rebuild_report_import(node, removed_alias)
            location = COLUMN.join(
                [
                    self.get_relpath(source),
                    str(node.lineno),
                    str(node.col_offset),
                ]
            )
            removed = "has removed" if not self.configs.check else "whould be removed"
            self.secho(
                f"{location} {statement!r} {removed}! 🔮", bold=False, isedit=True
            )

        self.__removed_imports += 1
        self.__file_removed_imports += 1 if self.__file_removed_imports != -1 else 2

    __expanded_stars: int = 0

    def expanded_star(
        self, source: Path, node: Union[ast.ImportFrom, nodes.ImportFrom]
    ) -> None:
        """Increment the counter for expanded stars. Write a message to stdout.

        :param source: where the import has expanded.
        :param node: the expanded node.
        """
        if not any([self.configs.diff, self.configs.quiet, self.configs.silence]):
            statement = self.rebuild_report_import(
                node, ast.alias(name=STAR, asname=None)
            )
            location = COLUMN.join(
                [
                    self.get_relpath(source),
                    str(node.lineno),
                    str(node.col_offset),
                ]
            )
            expanded = (
                "has expanded" if not self.configs.check else "whould be expanded"
            )
            self.secho(
                f"{location} {statement!r} {expanded}! 🔗", bold=False, isedit=True
            )

        self.__expanded_stars += 1
        self.__file_expanded_stars += 1 if self.__file_expanded_stars != -1 else 2

    __changed_files: int = 0
    __file_removed_imports: int = 0
    __file_expanded_stars: int = 0

    def changed_file(self, source: Path) -> None:
        """Increment the counter for changed files. Write a message to stdout.

        :param source: the changed file path.
        """
        if not any([self.configs.diff, self.configs.silence]) and (
            self.__file_removed_imports > 0 or self.__file_expanded_stars > 0
        ):
            file_report: List[str] = []

            if self.__file_removed_imports > 0:
                removed = (
                    "has removed" if not self.configs.check else "whould be removed"
                )
                rs = "s" if self.__file_removed_imports > 1 else ""
                file_report.append(
                    f"{self.__file_removed_imports} import{rs} {removed}"
                )

            if self.__file_expanded_stars > 0:
                expanded = (
                    "has expanded" if not self.configs.check else "whould be expanded"
                )
                es = "s" if self.__file_expanded_stars > 1 else ""
                file_report.append(
                    f"{self.__file_expanded_stars} import{es} {expanded}"
                )

            str_file_report = COMMA_SP.join(file_report)
            self.secho(
                f"{self.get_relpath(source)} {str_file_report}! 🚀",
                bold=True,
                isedit=True,
            )

        self.__changed_files += 1
        self.__file_removed_imports = 0
        self.__file_expanded_stars = 0

    __unchanged_files: int = 0

    def unchanged_file(self, source: Path) -> None:
        """Increment the counter for unchanged files. Write a message to stdout.

        :param source: the unchanged file path.
        """
        if self.configs.verbose and self.__file_removed_imports != -1:
            self.secho(
                f"{self.get_relpath(source)} looks good! ✨", bold=False, issuccess=True
            )
        self.__unchanged_files += 1

    __ignored_paths: int = 0

    def ignored_path(self, ignored_path: Path, type_: str) -> None:
        """Increment the counter for ignored paths. Write a message to stderr.

        :param ignored_path: the ignored path.
        :param type_: ignore type, `exclude` or `include` or `gitignore` or `nopycln`.
        """
        if self.configs.verbose:
            if type_ == "exclude":
                type_ = "matches the --exclude regex"
            elif type_ == "gitignore":
                type_ = "matches the .gitignore patterns"
            elif type_ == "include":
                type_ = "does not match the --include regex"
            else:
                sharp = "#"  # To avoid skiping this file.
                type_ = f"do to `{sharp} nopycln: file` comment"
            self.secho(
                f"{self.get_relpath(ignored_path)} has ignored: {type_}! ⚠️",
                bold=False,
                err=True,
                iswarning=True,
            )
        self.__ignored_paths += 1

    __ignored_imports: int = 0

    def ignored_import(
        self,
        source: Path,
        node: Union[ast.Import, ast.ImportFrom, nodes.Import, nodes.ImportFrom],
        is_star_import: bool = False,
    ) -> None:
        """Increment the counter for ignored imports. Write a message to stderr.

        :param source: where the import has ignored.
        :param node: the ignored import node.
        :param is_star_import: set to true if it's a '*' import.
        """
        if self.configs.verbose:
            statement = self.rebuild_report_import(node, node.names[0]) + (DOT * 3)
            location = f"{self.get_relpath(source)}:{node.lineno}:{node.col_offset}"
            reason = (
                "`# noqa` or `# nopycln: import`"
                if not is_star_import
                else f"cannot expand the {STAR!r}"
            )
            self.secho(
                f"{location} {statement!r} has ignored: {reason}! ⚠️",
                bold=False,
                err=True,
                iswarning=True,
            )
        self.__ignored_imports += 1

    __failures: int = 0

    def failure(self, message: str, source: Path = None) -> None:
        """Increment the counter for failures counter. Write a message to stderr.

        :param message: a failure message.
        :param source: where the failure has appeared.
        """
        if not self.configs.silence:
            message = (
                f"{self.get_relpath(source)} {message} ⛔" if source else f"{message} ⛔"
            )
            self.secho(message, bold=False, err=True, iserror=True)
        self.__failures += 1

        if self.__file_removed_imports == 0:
            self.__file_removed_imports = -1

    @property
    def exit_code(self) -> int:
        """Return an exit code.

        :returns: an exit code (0, 1, 250).
        """
        # According to http://tldp.org/LDP/abs/html/exitcodes.html
        # exit codes 1 - 2, 126 - 165, and 255 have special meanings,
        # and should therefore be avoided for user-specified exit parameters
        if self.__failures:
            # Internal error.
            return 250
        if self.__changed_files and self.configs.check:
            # File(s) should be refactord.
            return 1
        # Everything is fine.
        return 0

    @property
    def report_prefix(self) -> str:
        """Return the correct prefix.

        :returns: NEW_LINE or EMPTY.
        """
        return (
            NEW_LINE
            if any(
                [
                    self.__changed_files,
                    all(
                        [
                            self.configs.verbose,
                            any([self.__ignored_paths, self.__ignored_imports]),
                        ]
                    ),
                    all(
                        [
                            any(
                                [
                                    self.__failures,
                                    self.__removed_imports,
                                    self.__expanded_stars,
                                ]
                            ),
                            not self.configs.quiet,
                        ]
                    ),
                ]
            )
            else EMPTY
        )

    def __str__(self) -> str:
        """Render a counters report. can renders using `str(object)`

        :returns: full counters report.
        """
        if not any([self.__changed_files, self.__unchanged_files, self.__failures]):
            typer.secho(
                (NEW_LINE if self.configs.verbose and self.__ignored_paths else EMPTY)
                + "No Python files are present to be cleaned. Nothing to do 😴",
                bold=True,
                err=True,
            )
            raise typer.Exit(1)

        if any([self.configs.check, self.configs.diff]):
            removed_imports = "would be removed"
            expanded_stars = "would be expanded"
            changed_files = "would be changed"
            unchanged_files = "would be left unchanged"
        else:
            removed_imports = "has removed"
            expanded_stars = "has expanded"
            changed_files = "has changed"
            unchanged_files = "left unchanged"
        failures = "has failed to be cleaned"

        report = []

        if self.__removed_imports:
            s = "s" if self.__removed_imports > 1 else EMPTY
            report.append(
                typer.style(
                    f"{self.__removed_imports} import{s} {removed_imports}", bold=True
                )
            )

        if self.__expanded_stars:
            s = "s" if self.__expanded_stars > 1 else EMPTY
            report.append(
                typer.style(
                    f"{self.__expanded_stars} import{s} {expanded_stars}", bold=True
                )
            )

        if self.__changed_files:
            s = "s" if self.__changed_files > 1 else EMPTY
            report.append(
                typer.style(
                    f"{self.__changed_files} file{s} {changed_files}", bold=True
                )
            )

        if self.__unchanged_files:
            s = "s" if self.__unchanged_files > 1 else EMPTY
            report.append(
                typer.style(
                    f"{self.__unchanged_files} file{s} {unchanged_files}", bold=False
                )
            )

        if self.__failures:
            s = "s" if self.__failures > 1 else EMPTY
            report.append(
                typer.style(f"{self.__failures} file{s} {failures}", bold=False)
            )

        if self.configs.verbose:
            ignored_imports = "has ignored"
            ignored_paths = "has ignored"

            if self.__ignored_imports:
                s = "s" if self.__ignored_imports > 1 else EMPTY
                report.append(
                    typer.style(
                        f"{self.__ignored_imports} import{s} {ignored_imports}",
                        bold=False,
                    )
                )

            if self.__ignored_paths:
                s = "s" if self.__ignored_paths > 1 else EMPTY
                report.append(
                    typer.style(
                        f"{self.__ignored_paths} path{s} {ignored_paths}", bold=False
                    )
                )

        done_msg = typer.style(
            (
                (
                    "All done! 💪 😎"
                    if self.__removed_imports or self.__expanded_stars
                    else "Looks good! ✨ 🍰 ✨"
                )
                if not self.__failures
                else f"Oh no, there {'are errors' if self.__failures > 1 else 'is an error'}! 💔 ☹️"
            )
            + NEW_LINE,
            bold=True,
        )
        return self.report_prefix + done_msg + COMMA_SP.join(report) + DOT
