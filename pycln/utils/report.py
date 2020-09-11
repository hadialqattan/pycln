"""Pycln report utility."""
import ast
from dataclasses import dataclass
from difflib import unified_diff
from pathlib import Path
from typing import List, Optional, Union

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


@dataclass
class Report:

    """Provide a Pycln report counters.

    Can be rendered with `str(report)`.
    """

    #: Configured instance.
    configs: config.Config

    @staticmethod
    def get_location(path: Path, location: nodes.NodeLocation) -> str:
        """Create full location from `path` and node location.

        :param path: file path.
        :param location: `nodes.NodeLocation`.
        :returns: full location.
        """
        start = location.start
        line, col = str(start.line), str(start.col)
        return COLUMN.join([str(path), line, col])

    @staticmethod
    def secho(
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

    @staticmethod
    def colored_unified_diff(
        path: Path,
        original_lines: List[str],
        fixed_lines: List[str],
    ) -> None:
        """Writeout colored and normalized diff.

        :param path: a file path.
        :param original_lines: original path code lines.
        :param fixed_lines: fixed path code lines.
        """
        diff_gen = unified_diff(
            original_lines,
            fixed_lines,
            fromfile=f"original/ {path}",
            tofile=f"fixed/ {path}",
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

    @staticmethod
    def rebuild_report_import(
        node: Union[nodes.Import, nodes.ImportFrom],
        alias: ast.alias,
    ) -> str:
        """Rebuild import statement from AST for reporting purposes.

        :param node: import node.
        :param alias: `ast.alias` node.
        """
        str_alias = (
            f"{alias.name}{SPACE}{AS}{SPACE}{alias.asname}"
            if alias.asname
            else alias.name
        )
        str_import = (
            f"{FROM}{SPACE}{node.relative_name}{SPACE}{IMPORT}"
            if isinstance(node, nodes.ImportFrom)
            else IMPORT
        )
        return f"{str_import}{SPACE}{str_alias}"

    #: Total removed import statements counter.
    _removed_imports: int = 0

    def removed_import(
        self,
        path: Path,
        node: Union[nodes.Import, nodes.ImportFrom],
        removed_alias: ast.alias,
    ) -> None:
        """Increment `self._removed_imports`. Write a message to stdout.

        :param path: where the import has removed.
        :param node: removed import node.
        :param removed_alias: the removed `ast.alias` from the node.
        """
        if not any([self.configs.diff, self.configs.quiet, self.configs.silence]):
            location = Report.get_location(path, node.location)
            statement = Report.rebuild_report_import(node, removed_alias)
            removed = "whould be removed" if self.configs.check else "has removed"
            Report.secho(
                f"{location} {statement!r} {removed}! 🔮",
                bold=False,
                isedit=True,
            )

        self._removed_imports += 1
        self._file_removed_imports += 1 if self._file_removed_imports != -1 else 2

    #: Total expanded import statements counter.
    _expanded_stars: int = 0

    def expanded_star(self, path: Path, node: nodes.ImportFrom) -> None:
        """Increment `self._expanded_stars`. Write a message to stdout.

        :param path: where the import has expanded.
        :param node: the expanded node.
        """
        if not any([self.configs.diff, self.configs.quiet, self.configs.silence]):
            location = Report.get_location(path, node.location)
            star_alias = ast.alias(name=STAR, asname=None)
            statement = Report.rebuild_report_import(node, star_alias)
            expanded = "whould be expanded" if self.configs.check else "has expanded"
            Report.secho(
                f"{location} {statement!r} {expanded}! 🔗",
                bold=False,
                isedit=True,
            )

        self._expanded_stars += 1
        self._file_expanded_stars += 1 if self._file_expanded_stars != -1 else 2

    #: Total changed files counter.
    _changed_files: int = 0

    #: These counters will be reseted for each file.
    _file_removed_imports: int = 0
    _file_expanded_stars: int = 0

    def changed_file(self, path: Path) -> None:
        """Increment `self._changed_files`. Write a message to stdout.

        :param path: the changed file path.
        """
        if not any([self.configs.diff, self.configs.silence]):
            file_report: List[str] = []

            if self._file_removed_imports > 0:
                removed = "whould be removed" if self.configs.check else "has removed"
                s = "s" if self._file_removed_imports > 1 else ""
                file_report.append(f"{self._file_removed_imports} import{s} {removed}")

            if self._file_expanded_stars > 0:
                expanded = (
                    "whould be expanded" if self.configs.check else "has expanded"
                )
                s = "s" if self._file_expanded_stars > 1 else ""
                file_report.append(f"{self._file_expanded_stars} import{s} {expanded}")

            str_file_report = COMMA_SP.join(file_report)
            Report.secho(f"{path} {str_file_report}! 🚀", bold=True, isedit=True)

        self._changed_files += 1
        self._file_removed_imports = 0
        self._file_expanded_stars = 0

    #: Total unchanged files counter.
    _unchanged_files: int = 0

    def unchanged_file(self, path: Path) -> None:
        """Increment `self._unchanged_files`. Write a message to stdout.

        :param path: the unchanged file path.
        """
        if self.configs.verbose and self._file_removed_imports != -1:
            Report.secho(f"{path} looks good! ✨", bold=False, issuccess=True)

        self._unchanged_files += 1
        self._file_removed_imports = 0
        self._file_expanded_stars = 0

    #: Total ignored paths counter.
    _ignored_paths: int = 0

    def ignored_path(self, ignored_path: Path, type_: str) -> None:
        """Increment `self._ignored_paths`. Write a message to stderr.

        :param ignored_path: the ignored path.
        :param type_: ignore type (`exclude`, `include`, `gitignore` or `nopycln`).
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
            Report.secho(
                f"{ignored_path} has ignored: {type_}! ⚠️",
                bold=False,
                err=True,
                iswarning=True,
            )

        self._ignored_paths += 1

    #: Total ignored import statements counter.
    _ignored_imports: int = 0

    def ignored_import(
        self,
        path: Path,
        node: Union[nodes.Import, nodes.ImportFrom],
        is_star: bool = False,
    ) -> None:
        """Increment `self._ignored_imports`. Write a message to stderr.

        :param path: where the import has ignored.
        :param node: the ignored import node.
        :param is_star: set to true if it's a '*' import.
        """
        if self.configs.verbose:
            location = Report.get_location(path, node.location)
            statement = Report.rebuild_report_import(node, node.names[0]) + (DOT * 3)
            reason = (
                "`# noqa` or `# nopycln: import`"
                if not is_star
                else f"cannot expand the {STAR!r}"
            )
            Report.secho(
                f"{location} {statement!r} has ignored: {reason}! ⚠️",
                bold=False,
                err=True,
                iswarning=True,
            )
        self._ignored_imports += 1

    #: Total number of failures.
    _failures: int = 0

    def failure(self, msg: str, path: Optional[Path] = None) -> None:
        """Increment `self._failures`. Write a msg to stderr.

        :param msg: a failure msg.
        :param path: where the failure has appeared.
        """
        if not self.configs.silence:
            message = f"{path} {msg} ⛔" if path else f"{msg} ⛔"
            Report.secho(message, bold=False, err=True, iserror=True)
        if self._file_removed_imports == 0:
            self._file_removed_imports = -1
        self._failures += 1

    @property
    def exit_code(self) -> int:
        """Return an exit code.

        :returns: an exit code (0, 1, 250).
        """
        # According to http://tldp.org/LDP/abs/html/exitcodes.html
        # exit codes 1 - 2, 126 - 165, and 255 have special meanings,
        # and should therefore be avoided for user-specified exit parameters
        if self._failures:
            # Internal error.
            return 250
        if self._changed_files and self.configs.check:
            # File(s) should be refactord.
            return 1
        # Everything is fine.
        return 0

    @property
    def report_prefix(self) -> str:
        """Return the correct prefix.

        :returns: `NEW_LINE` or `EMPTY`.
        """
        return (
            NEW_LINE
            if any(
                [
                    self._changed_files,
                    all(
                        [
                            self.configs.verbose,
                            any([self._ignored_paths, self._ignored_imports]),
                        ]
                    ),
                    all(
                        [
                            any(
                                [
                                    self._failures,
                                    self._removed_imports,
                                    self._expanded_stars,
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
        """Render a colored report of the current state.

        Use `typer.unstyle` to remove colors.

        :returns: a colored report of the current state.
        """
        if self.configs.silence:
            return EMPTY

        if not any([self._changed_files, self._unchanged_files, self._failures]):
            typer.secho(
                (NEW_LINE if self.configs.verbose and self._ignored_paths else EMPTY)
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

        if self._removed_imports:
            s = "s" if self._removed_imports > 1 else EMPTY
            report.append(
                typer.style(
                    f"{self._removed_imports} import{s} {removed_imports}",
                    bold=True,
                )
            )

        if self._expanded_stars:
            s = "s" if self._expanded_stars > 1 else EMPTY
            report.append(
                typer.style(
                    f"{self._expanded_stars} import{s} {expanded_stars}",
                    bold=True,
                )
            )

        if self._changed_files:
            s = "s" if self._changed_files > 1 else EMPTY
            report.append(
                typer.style(
                    f"{self._changed_files} file{s} {changed_files}",
                    bold=True,
                )
            )

        if self._unchanged_files:
            s = "s" if self._unchanged_files > 1 else EMPTY
            report.append(
                typer.style(
                    f"{self._unchanged_files} file{s} {unchanged_files}",
                    bold=False,
                )
            )

        if self._failures:
            s = "s" if self._failures > 1 else EMPTY
            report.append(
                typer.style(f"{self._failures} file{s} {failures}", bold=False)
            )

        if self.configs.verbose:
            ignored_imports = "has ignored"
            ignored_paths = "has ignored"

            if self._ignored_imports:
                s = "s" if self._ignored_imports > 1 else EMPTY
                report.append(
                    typer.style(
                        f"{self._ignored_imports} import{s} {ignored_imports}",
                        bold=False,
                    )
                )

            if self._ignored_paths:
                s = "s" if self._ignored_paths > 1 else EMPTY
                report.append(
                    typer.style(
                        f"{self._ignored_paths} path{s} {ignored_paths}",
                        bold=False,
                    )
                )

        if not self._failures:
            if self._removed_imports or self._expanded_stars:
                done_msg = "All done! 💪 😎"
            else:
                done_msg = "Looks good! ✨ 🍰 ✨"
        else:
            s = "are errors" if self._failures > 1 else "is an error"
            done_msg = f"Oh no, there {s}! 💔 ☹️"

        sdone_msg = typer.style(done_msg + NEW_LINE, bold=True)
        return self.report_prefix + sdone_msg + COMMA_SP.join(report) + DOT + NEW_LINE
