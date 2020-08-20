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


@dataclass
class Report:

    """
    Provide a Pycln report counters. Can be rendered with `str(report)`.
    """

    configs: config.Config

    def get_relpath(self, path: Path) -> Path:
        """
        Get relative path from the given absolute path.

        :param path: an absolute path.
        :returns: a relative path (relative to `self.configs.path`).
        """
        return os.path.relpath(path, self.configs.path)

    # Counters.
    __removed_imports: int = 0

    def removed_import(
        self,
        source: Path,
        node: Union[ast.Import, ast.ImportFrom],
        removed_alias: ast.alias,
    ) -> None:
        """
        Increment the counter for removed importes. Write a message to stdout.

        :param source: where the import has removed.
        :param node: remove import node.
        :param removed_alias: the removed `ast.alias` from the node.
        """
        if not any(self.configs.diff, self.configs.quiet, self.configs.silence):

            abc_node = copy(node)
            abc_node.names = [removed_alias]

            if isinstance(abc_node, ast.Import):
                statement = ast2s.rebuild_import(abc_node)

            elif isinstance(abc_node, ast.ImportFrom):
                statement = ast2s.rebuild_import_from(abc_node)

            location = ":".join(
                [self.get_relpath(source), abc_node.lineno, abc_node.col_offset]
            )
            removed = "has removed" if not self.configs.check else "whould be removed"

            typer.secho(f"{statement} {remove} from {location}", bold=False)
        self.__removed_imports += 1

    __changed_files: int = 0

    def changed_file(self, source: Path, removed_imports: int) -> None:
        """
        Increment the counter for changed files. Write a message to stdout.

        :param source: the changed file path.
        :param removed_imports: removed imports count.
        """
        if not any(self.configs.diff, self.configs.silence):
            s = "s" if removed_imports > 1 else ""
            typer.secho(
                f"{removed_imports} import{s} has removed from {self.get_relpath(source)}",
                bold=True,
            )

        self.__changed_files += 1

    __unchanged_files: int = 0

    def unchanged_file(self, source: Path) -> None:
        """
        Increment the counter for unchanged files. Write a message to stdout.

        :param source: the unchanged file path.
        """
        if any(self.configs.verbose, self.configs.diff):
            typer.secho(
                f"{self.get_relpath(source)} has no unused imports, good job!",
                bold=True,
            )
        self.__unchanged_files += 1

    __ignored_paths: int = 0

    def ignored_path(self, ignored_path: Path) -> None:
        """
        Increment the counter for ignored paths. Write a message to stderr.

        :param ignored_path: the ignored path.
        """
        if self.configs.verbose:
            typer.secho(
                f"{ignored_path} has ignored do to exclude and/or {'.gitignore'!r} patterns.",
                err=True,
            )
        self.__ignored_paths += 1

    __ignored_imports: int = 0

    def ignored_import(
        self, source: Path, node: Union[ast.Import, ast.ImportFrom]
    ) -> None:
        """
        Increment the counter for ignored imports. Write a message to stderr.

        :param source: where the import has ignored.
        :param node: the ignored import node.
        """
        if self.configs.verbose:
            if isinstance(node, ast.Import):
                statement = ast2s.rebuild_import(node)

            elif isinstance(node, ast.ImportFrom):
                statement = ast2s.rebuild_import_from(node)

                if isinstance(statement, list):
                    statement = statement[0].replace("\n", " ...")

            typer.secho(
                f"{statement} has ignored do to the '# noqa' comment.", err=True
            )
        self.__ignored_imports += 1

    __failures: int = 0

    def failure(self, message: str, source: Path = None) -> None:
        """
        Increment the counter for failures counter. Write a message to stderr.

        :param message: a failure message.
        :param source: where the failure has appeared.
        """
        if not self.configs.silence:
            if source:
                message = f"{self.get_relpath(source)} {message}"
            typer.secho(message, fg=typer.colors.RED, err=True)
        self.__failures += 1

    def __str__(self) -> str:
        """
        Render a counters report.
        """
        if any(self.configs.check, self.configs.diff):
            removed_imports = "would be removed"
            changed_files = "would be changed"
            unchanged_files = "would be left unchanged"
        else:
            removed_imports = "has removed"
            changed_files = "has changed"
            unchanged_files = "left unchanged"
        failures = "has failed to clean"

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

        if self.configs.verbose:
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

        return ", ".join(report) + "."
