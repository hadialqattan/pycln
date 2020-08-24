"""
Pycln code refactoring utility.
"""
import ast
import os
from copy import copy
from pathlib import Path
from typing import Generator, List, Union

import typer

from . import ast2source as ast2s, astu, pathu, regexu
from .config import Config
from .exceptions import (
    ReadPermissionError,
    UnexpandableImportStar,
    UnparsableFile,
    WritePermissionError,
)
from .report import Report

# Constants.
DOT = "."
STAR = "*"
EMPTY = ""
SPACE = " "
NEW_LINE = "\n"


class Refactor:

    """Refactor `pathu.yield_sources` codes."""

    def __init__(self, configs: Config, reporter: Report, sources: Generator):
        self.configs = configs
        self.reporter = reporter

        self.import_analyzer = astu.ImportAnalyzer()
        self.source_analyzer = astu.SourceAnalyzer()
        self.side_effects_analyzer = astu.SideEffectsAnalyzer()

        self.source_lines = []
        self.source_stats = astu.SourceStats(set(), set())
        self.import_stats = astu.ImportStats(set(), set())

        for source in sources:
            self.analyze(source)
            new_source_lines = astu.remove_useless_passes(self.refactor(source))
            self.output(source, new_source_lines)

    def output(self, source: Path, new_source_lines: List[str]) -> None:
        """Output the given source lines.

        :param source: a path to output the source lines.
        :param new_source_lines: the refactored source lines.
        """
        if new_source_lines != self.source_lines:
            if self.configs.diff:
                source = self.reporter.get_relpath(source)
                self.reporter.colored_unified_diff(
                    source, self.source_lines, new_source_lines
                )
            elif not self.configs.check:
                # Default.
                with open(source, "w") as sfile:
                    sfile.writelines(new_source_lines)
            self.reporter.changed_file(source)
        else:
            self.reporter.unchanged_file(source)

    def analyze(self, source: Path) -> None:
        """Analyze the source code of the given source.

        :param source: a source to analyze.
        """
        try:
            permissions = (
                (os.R_OK, os.W_OK)
                if not any([self.configs.check, self.configs.diff])
                else (os.R_OK,)
            )
            tree, self.source_lines = astu.get_file_ast(source, True, permissions)
        except (ReadPermissionError, UnparsableFile, WritePermissionError) as err:
            self.reporter.failure(err)
            return None

        try:
            # Analyze file imports.
            self.import_analyzer.visit(tree)
            self.import_stats = self.import_analyzer.get_stats()
            self.import_analyzer.reset_stats()

            # Analyze file source code.
            self.source_analyzer.visit(tree)
            self.source_stats = self.source_analyzer.get_stats()
            self.source_analyzer.reset_stats()
        except Exception as err:
            self.reporter.failure(err, source)

    def refactor(self, source: Path) -> List[str]:
        """Refactor currect `self.source_lines`.

        :param source: a source where `self.source_lines` belogns to.
        :returns: refactored lines.
        """
        new_source_lines = copy(self.source_lines)

        for type_ in self.import_stats:

            for node in type_:

                # Skip any import that has `# noqa` comment on it's `node.lineno`.
                if regexu.has_noqa(new_source_lines[node.lineno - 1]):
                    self.reporter.ignored_import(source, node)
                    continue

                # Expand import '*' before checking.
                is_star_import = False
                if isinstance(node, ast.ImportFrom):
                    if node.names[0].name == STAR:
                        try:
                            is_star_import = True
                            node = astu.expand_import_star(node, source)
                        except UnexpandableImportStar as err:
                            self.reporter.failure(err)
                            self.reporter.ignored_import(
                                source, node, is_star_import=True
                            )
                            continue

                # Shallow copy only the importat parts.
                clean_node = copy(node)
                clean_node.names = copy(node.names)

                has_used = True

                for alias in node.names:
                    # Get the actual name.
                    name = alias.asname if alias.asname else alias.name

                    if self.should_remove(source, node, alias):
                        has_used = False
                        clean_node.names.remove(alias)
                        if not is_star_import:
                            self.reporter.removed_import(source, node, alias)

                if not has_used:

                    # Return from module import '*' as before, if the --expand-star-imports not specified.
                    if (
                        clean_node.names
                        and is_star_import
                        and not self.configs.expand_star_imports
                    ):
                        clean_node.names = [ast.alias(name=STAR, asname=None)]
                    elif is_star_import and not clean_node.names:
                        self.reporter.removed_import(
                            source, node, ast.alias(name=STAR, asname=None)
                        )

                    # Rebuild and replace the import without the unused parts.
                    if isinstance(node, ast.Import):
                        rebuilt_import = ast2s.rebuild_import(clean_node)
                        self.insert_import(rebuilt_import, node, new_source_lines)
                    else:
                        is_parentheses = ast2s.is_parentheses(
                            self.source_lines[node.lineno - 1]
                        )
                        rebuilt_import = ast2s.rebuild_import_from(
                            clean_node, is_parentheses
                        )
                        self.insert_import_from(rebuilt_import, node, new_source_lines)

        return new_source_lines

    def should_remove(
        self, source: Path, node: Union[ast.Import, ast.ImportFrom], alias: ast.alias
    ):
        """Check if the alias should be removed or not.

        :param source: where the node has imported.
        :param node: an `ast.Import` or `ast.ImportFrom`.
        :param alias: an `ast.alias` node.
        :returns: True if the alias should be removed else False.
        """
        real_name = alias.name if isinstance(node, ast.Import) else node.module
        used_name = alias.asname if alias.asname else alias.name
        return not any(
            [self.has_used(used_name), real_name in pathu.IMPORTS_WITH_SIDE_EFFECTS]
        ) and any(
            [
                self.configs.all_,
                any(
                    [
                        real_name in pathu.get_standard_lib_names(),
                        self.has_side_effects(source, real_name, node)
                        is astu.HasSideEffects.NO,
                    ]
                ),
            ]
        )

    def has_used(self, name: str) -> bool:
        """Check if the given import name has used.

        :param name: a name to check.
        :returns: True if the name has used else False.
        """
        name = namee.split(DOT) if DOT in name else name
        if isinstance(name, str):
            # Handle imports like (import os, from os import path).
            return any([name in self.source_stats.name_])
        else:
            # Handle imports like (import os.path, from os import path.join).
            return all([i in self.source_stats.name_ for i in name[:-1]]) and any(
                [name[-1] in set_ for set_ in self.source_stats]
            )

    def has_side_effects(
        self, source: Path, module_name: str, node: Union[ast.Import, ast.ImportFrom]
    ) -> astu.HasSideEffects:
        """Check if the given import file tree has side effects.

        :param source: where node has imported.
        :param module_name: `alias.name` to check.
        :param node: an `ast.Import` or `ast.ImportFrom` node.
        :returns: side effects status.
        """
        if isinstance(node, ast.Import):
            pathu.get_import_path(source, module_name)
        elif isinstance(node, ast.ImportFrom):
            pathu.get_import_from_path(source, module_name, node.module, node.level)

        try:
            tree = astu.get_file_ast(source, permissions=(os.R_OK,))
        except (ReadPermissionError, UnparsableFile) as err:
            self.reporter.failure(err)
            return astu.HasSideEffects.NOT_KNOWN

        try:
            self.side_effects_analyzer.visit(tree)
            has_side_effects = self.side_effects_analyzer.has_side_effects()
            # Reset fot the next usage.
            self.side_effects_analyzer.reset()
            return has_side_effects
        except Exception as err:
            self.reporter.failure(err, source)
            return astu.HasSideEffects.NOT_KNOWN

    def insert_import(
        self,
        rebuilt_import: Union[str, None],
        old_node: ast.Import,
        source_lines: List[str],
    ) -> List[int]:
        """Insert rebuilt import statement into current source lines.

        :param rebuilt_import: an import statement to insert.
        :param old_node: an `ast.Import` object.
        :param source_lines: a list of source lines to modify.
        """
        source_lines[old_node.lineno - 1] = rebuilt_import
        # Replace each removed line with EMPTY constant.
        if old_node.end_lineno - old_node.lineno:
            source_lines[old_node.lineno] = EMPTY

    def insert_import_from(
        self,
        rebuilt_import_from: Union[str, list, None],
        old_node: ast.ImportFrom,
        source_lines: List[str],
    ) -> List[int]:
        """Insert rebuilt importFrom statement into current source lines.

        :param rebuilt_import_from: an importFrom statement to insert.
        :param old_node: an `ast.ImportFrom` object.
        :param source_lines: a list of source lines to modify.
        """
        old_lineno = old_node.lineno - 1

        if isinstance(rebuilt_import_from, str):
            # Insert the single-line importFrom statement.
            new_len = 1
            source_lines[old_lineno] = rebuilt_import_from

        elif isinstance(rebuilt_import_from, list):
            # Insert the multi-line importFrom statement.
            new_len = len(rebuilt_import_from)
            for line in rebuilt_import_from:
                source_lines[old_lineno] = line
                old_lineno += 1

        else:
            new_len = 0

        # Replace each removed line with EMPTY constant.
        lineno = old_node.lineno + new_len - 1
        old_len = old_node.end_lineno - old_node.lineno + 1
        for i in range(old_len - new_len):
            source_lines[lineno] = EMPTY
            lineno += 1
