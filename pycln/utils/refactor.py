"""
Pycln code refactoring utility.
"""
import ast
import os
from copy import copy
from pathlib import Path
from typing import List, Tuple, Union, Set
from functools import lru_cache

from . import cstu, astu, nodes, pathu, regexu
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
NOPYCLN = "nopycln"
NEW_LINE = "\n"


class Refactor:

    """Refactor the given source.

    >>> source = "source.py"
    >>> Refactor(
    ...     configs,  # Should be created on the main function.
    ...     reporter,  # Should be created on the main function.
    ...     source
    ... )
    >>> print("Easy!")

    :param source: a file path to handle.
    :param configs: `config.Config` instance.
    :param reporter: `report.Report` instance.
    """

    def __init__(self, source: Path, configs: Config, reporter: Report):
        self.configs = configs
        self.reporter = reporter
        self.source = source

        tree, self.original_lines = self.read_source()
        if tree and self.original_lines:

            self.source_stats, self.import_stats = self.analyze(tree)
            if self.source_stats and self.import_stats:

                pre_fixed_lines = self.refactor()
                if pre_fixed_lines != self.original_lines:
                    fixed_lines = astu.remove_useless_passes(pre_fixed_lines)
                    self.output(fixed_lines)
                else:
                    self.reporter.unchanged_file(self.source)

    def output(self, fixed_lines: List[str]) -> None:
        """Output the given `fixed_lines`.

        :param fixed_lines: the refactored source lines.
        """
        if self.configs.diff:
            self.reporter.colored_unified_diff(
                self.source, self.original_lines, fixed_lines
            )
        elif not self.configs.check:
            # Default.
            with open(self.source, "w") as sfile:
                sfile.writelines(fixed_lines)
        self.reporter.changed_file(self.source)

    def read_source(self) -> Union[Tuple[ast.Module, List[str]], Tuple[None, None]]:
        """Get `self.source` `ast.module` and source lines. `astu.get_file_ast` abstraction.

        :returns: tuple of source file AST (`ast.Module`) and source code lines.
        """
        tree, original_lines = None, None
        try:
            permissions = (
                (os.R_OK, os.W_OK)
                if not any([self.configs.check, self.configs.diff])
                else (os.R_OK,)
            )
            tree, original_lines, content = astu.get_file_ast(
                self.source, True, permissions
            )

            if regexu.skip_file(content):
                self.reporter.ignored_path(self.source, NOPYCLN)
                return None, None
        except (ReadPermissionError, WritePermissionError, UnparsableFile) as err:
            self.reporter.failure(err)
        return tree, original_lines

    def analyze(
        self,
        tree: ast.Module,
    ) -> Union[Tuple[astu.SourceStats, astu.ImportStats], Tuple[None, None]]:
        """Analyze the source code of `self.source`.

        :param tree: a parsed `ast.Module`.
        :returns: tuple of `astu.SourceStats` and `astu.ImportStats`.
        """
        source_stats, import_stats = None, None
        try:
            if astu.PY38_PLUS:
                analyzer = astu.SourceAnalyzer()
            else:
                analyzer = astu.SourceAnalyzer(self.original_lines)
            analyzer.visit(tree)
            source_stats, import_stats = analyzer.get_stats()
        except Exception as err:
            self.reporter.failure(err, self.source)
        return source_stats, import_stats

    def refactor(self) -> List[str]:
        """Remove all unused imports from `self.original_lines`.

        :returns: refactored source code lines.
        """
        fixed_lines = copy(self.original_lines)
        for type_ in self.import_stats:

            for node in type_:

                # Skip any import that has `# noqa` or `# nopycln: import` comment on it's `node.lineno`.
                if regexu.skip_import(fixed_lines[node.lineno - 1]):
                    self.reporter.ignored_import(self.source, node)
                    continue

                # Expand import '*' before checking.
                node, is_star_import = self.expand_import_star(node)
                if is_star_import is None:
                    continue

                has_changed = False
                used_names: Set[str] = set()
                for alias in node.names:
                    if self.should_removed(node, alias):
                        has_changed = True
                        if not is_star_import:
                            self.reporter.removed_import(self.source, node, alias)
                        continue
                    used_names.add(alias.name)

                if has_changed or not used_names:
                    # Return from module import '*' as before, if the --expand-star-imports has not specified.
                    if is_star_import:
                        star_alias = ast.alias(name=STAR, asname=None)
                        if node.names:
                            if not self.configs.expand_star_imports:
                                node.names = [star_alias]
                            else:
                                self.reporter.expanded_star(self.source, node)
                        elif not node.names:
                            self.reporter.removed_import(self.source, node, star_alias)

                    # Rebuild and replace the import without the unused parts.
                    if not is_star_import or self.configs.expand_star_imports:
                        import_stmnt = self.original_lines[
                            node.lineno - 1 : node.end_lineno
                        ]
                        rebuilt_import = cstu.rebuild_import(
                            EMPTY.join(import_stmnt), used_names
                        )
                        self.insert_import(rebuilt_import, fixed_lines, node)

        return fixed_lines

    def expand_import_star(
        self, node: Union[ast.Import, ast.ImportFrom, nodes.Import, nodes.ImportFrom]
    ) -> Tuple[
        Union[ast.Import, ast.ImportFrom, nodes.Import, nodes.ImportFrom],
        Union[bool, None],
    ]:
        """Expand import star statement, `astu.expand_import_star` abstraction.

        :param node: an node that has a '*' as `alias.name`.
        :returns: expanded '*' import or the original node and True if it's star import.
        """
        try:
            is_star_import = False
            if node.names[0].name == STAR:
                is_star_import = True
                node = astu.expand_import_star(node, self.source)
            return node, is_star_import
        except UnexpandableImportStar as err:
            self.reporter.failure(err)
            self.reporter.ignored_import(self.source, node, is_star_import=True)
            return node, None

    def should_removed(
        self, node: Union[ast.Import, ast.ImportFrom], alias: ast.alias
    ) -> bool:
        """Check if the alias should be removed or not.

        :param node: an `ast.Import` or `ast.ImportFrom`.
        :param alias: an `ast.alias` node.
        :returns: True if the alias should be removed else False.
        """
        real_name = node.module if hasattr(node, "level") else alias.name
        used_name = alias.asname if alias.asname else alias.name
        if (
            not self.has_used(used_name)
            and not real_name in pathu.IMPORTS_WITH_SIDE_EFFECTS
        ):
            if (
                self.configs.all_
                or real_name in pathu.get_standard_lib_names()
                or self.has_side_effects(alias.name, node)
                in (astu.HasSideEffects.NO, astu.HasSideEffects.NOT_MODULE)
            ):
                return True
        return False

    def has_used(self, name: str) -> bool:
        """Check if the given import name has used.

        :param name: a name to check.
        :returns: True if the name has used else False.
        """
        name = name.split(DOT) if DOT in name else name
        if isinstance(name, str):
            # Handle imports like (import os, from os import path).
            return any([name in self.source_stats.name_])
        else:
            # Handle imports like (import os.path, from os import path.join).
            return all([i in self.source_stats.name_ for i in name[:-1]]) and any(
                [name[-1] in set_ for set_ in self.source_stats]
            )

    @lru_cache()
    def has_side_effects(
        self, module_name: str, node: Union[ast.Import, ast.ImportFrom]
    ) -> astu.HasSideEffects:
        """Check if the given import file tree has side effects.

        :param module_name: `alias.name` to check.
        :param node: an `ast.Import` or `ast.ImportFrom` node.
        :returns: side effects status.
        """
        if hasattr(node, "level"):
            module_source = pathu.get_import_from_path(
                self.source, module_name, node.module, node.level
            )
        else:
            module_source = pathu.get_import_path(self.source, module_name)

        if not module_source:
            return astu.HasSideEffects.NOT_MODULE

        try:
            tree = astu.get_file_ast(module_source, permissions=(os.R_OK,))
        except (ReadPermissionError, UnparsableFile) as err:
            self.reporter.failure(err)
            return astu.HasSideEffects.NOT_KNOWN

        try:
            analyzer = astu.SideEffectsAnalyzer()
            analyzer.visit(tree)
            return analyzer.has_side_effects()
        except Exception as err:
            self.reporter.failure(err, self.source)
            return astu.HasSideEffects.NOT_KNOWN

    def insert_import(
        self,
        rebuilt_import: List[str],
        source_lines: List[str],
        old_node: Union[ast.Import, ast.ImportFrom, nodes.Import, nodes.ImportFrom],
    ) -> None:
        """Insert rebuilt import statement into `source_lines`.

        :param rebuilt_import: an import statement to insert.
        :param old_node: an unmodified node.
        :param source_lines: a list of source lines to modify.
        """
        # Insert the import statement.
        old_lineno = old_node.lineno - 1
        for line in rebuilt_import:
            source_lines[old_lineno] = line
            old_lineno += 1

        # Replace each removed line with EMPTY constant.
        new_len = len(rebuilt_import)
        old_len = old_node.end_lineno - old_node.lineno + 1
        lineno = old_node.lineno + new_len - 1
        for i in range(old_len - new_len):
            source_lines[lineno] = EMPTY
            lineno += 1
