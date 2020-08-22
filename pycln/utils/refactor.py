"""
Pycln code refactoring utility.
"""
import ast
import os
from pathlib import Path
from copy import copy
from typing import List, Union
from difflib import unified_diff

import typer

from . import astu, regexu, pathu, ast2source as ast2s
from .config import configs
from .report import reporter

# Constants.
DOT = "."
STAR = "*"
EMPTY = ""
NEW_LINE = "\n"


class Refactor:

    """Refactor `configs.sources` codes."""

    def __init__(self):
        self.import_analyzer = astu.ImportAnalyzer()
        self.source_analyzer = astu.SourceAnalyzer()
        self.side_effects_analyzer = astu.SideEffectsAnalyzer()

        for type_ in configs.ignored_paths:
            for path in configs.ignored_paths[type_]:
                reporter.ignored_path(path, type_)

        self.source_lines = []
        self.source_stats = astu.SourceStats(set(), set())
        self.import_stats = astu.ImportStats(set(), set())
        for source in configs.sources:
            self.analyze(source)
            new_source_lines = astu.remove_useless_passes(self.refactor(source))
            self.output(source, new_source_lines)

    def output(self, source: Path, new_source_lines: List[str]) -> None:
        """Output the given source lines.

        :param source: a path to output the source lines.
        :param new_source_lines: the refactored source lines.
        """
        if new_source_lines != self.source_lines:
            if configs.diff:
                source = reporter.get_relpath(source)
                diff_gen = unified_diff(
                    self.source_lines,
                    new_source_lines,
                    fromfile=f"original/ {source}",
                    tofile=f"fixed/ {source}",
                    n=3,
                    lineterm=NEW_LINE,
                )
                typer.echo(EMPTY.join([line for line in diff_gen]))
            elif not configs.check:
                # Default.
                with open(source, "w") as sfile:
                    sfile.writelines(new_source_lines)
            reporter.changed_file(source)
        else:
            reporter.unchanged_file(source)

    def analyze(self, source: Path) -> None:
        """Analyze the source code of the given source.

        :param source: a source to analyze.
        """
        try:
            tree, self.source_lines = astu.get_file_ast(source, True)
        except PermissionError as err:
            reporter.failure(err)
            return None

        try:
            # Visit.
            self.import_analyzer.visit(tree)
            self.source_analyzer.visit(tree)

            # Get stats.
            self.import_stats = self.import_analyzer.get_stats()
            self.source_stats = self.source_analyzer.get_stats()

            # Reset for the next source.
            self.import_analyzer.reset_stats()
            self.source_analyzer.reset_stats()
        except Exception as err:
            reporter.failure(err, source)

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
                    reporter.ignored_import(source, node)
                    continue

                # Expand import '*' before checking.
                is_star_import = False
                if isinstance(node, ast.ImportFrom):
                    if node.names[0].name == STAR:
                        is_star_import = True
                        node = astu.expand_import_star(node, source)

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
                        reporter.removed_import(source, node, alias)

                if not has_used:

                    # Return from module import '*' as before, if the --expand-star-imports not specified.
                    if (
                        clean_node.names
                        and is_star_import
                        and not configs.expand_star_imports
                    ):
                        clean_node.names = [ast.alias(name=STAR, asname=None)]

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
                configs.all_,
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
        except PermissionError as err:
            reporter.failure(err)
            return astu.HasSideEffects.NOT_KNOWN

        try:
            self.side_effects_analyzer.visit(tree)
            has_side_effects = self.side_effects_analyzer.has_side_effects()
            # Reset fot the next usage.
            self.side_effects_analyzer.reset()
            return has_side_effects
        except Exception as err:
            reporter.failure(err, source)
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
