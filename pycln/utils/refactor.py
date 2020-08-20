"""
Pycln code refactoring utility.
"""
import ast
from pathlib import Path
from copy import copy
from typing import List, Union

from . import astu, regexu, pathu, ast2source as ast2s
from .config import Config
from .report import Report


class Refactor:

    """
    Refactor `configs.sources` codes.
    """

    def __init__(self, configs: Config, reporter: Report):
        self.configs: Config = configs
        self.reporter: Report = reporter

        self.import_analyzer = astu.ImportAnalyzer()
        self.source_analyzer = astu.SourceAnalyzer()
        self.side_effects_analyzer = astu.SideEffectsAnalyzer()

        for path in self.configs.ignored_paths:
            self.reporter.ignored_path(path)

        self.source_lines = []
        self.source_stats = astu.SourceStats(set(), set())
        self.import_stats = astu.ImportStats(set(), set())
        for source in self.configs.sources:
            self.analyze(source)
            new_source_lines = astu.remove_useless_passes(self.refactor(source))

    def analyze(self, source: Path) -> None:
        """
        Analyze the source code of the given source.

        :param source: a source to analyze.
        """
        try:
            tree, self.source_lines = astu.get_file_ast(source, True)
        except PermissionError as err:
            self.reporter.failure(err)
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
            self.reporter.failure(err, source)

    def refactor(self, source: Path) -> List[str]:
        """
        Refactor currect `self.source_lines`.

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
                    if node.names[0].name == "*":
                        is_star_import = True
                        node = astu.expand_import_star(node, source)
                
                # Shallow copy only the importat parts.
                clean_node = copy(node)
                clean_node.names = copy(node.names)

                has_used = True

                for alias in node.names:
                    # Get the actual name.
                    name = alias.asname if alias.asname else alias.name
                    
                    if not all(self.has_used(name), name in pathu.IMPORTS_WITH_SIDE_EFFECTS, self.has_side_effects(source, name)):
                        has_used = False
                        clean_node.names.remove(alias)

                if not has_used:
                    
                    # Return from module import '*' as before, if the --expand-star-imports not specified.
                    if clean_node.names and not self.configs.expand_star_imports:
                        clean_node.names = [ast.alias(name="*", asname=None)]

                    # Rebuild and replace the import without the unused parts.
                    if isinstance(node, ast.Import):
                        rebuilt_import = ast2s.rebuild_import(clean_node)
                        self.insert_import(rebuilt_import, node)
                    else:
                        is_parentheses = ast2s.is_parentheses(self.source_lines[node.lineno - 1])
                        rebuilt_import_from = ast2s.rebuild_import_from(clean_node, is_parentheses)
                        self.insert_import_from(rebuilt_import_from, node)

        # The new_source_lines has None values for each removed line.
        # Filter it later before rewrite/output it.
        return new_source_lines

    def has_used(self, name: str) -> bool:
        """
        Check if the given import name has used.

        :param name: a name to check.
        :returns: True if the name has used else False.
        """
        name = namee.split(".") if "." in name else name
        if isinstance(str):
            # Handle imports like (import os, from os import path).
            return any([name in self.source_stats.name_])
        else:
            # Handle imports like (import os.path, from os import path.join).
            return all(
                [i in self.source_stats.name_ for i in name[:-1]]
            ) and any([name[-1] in set_ for set_ in self.source_stats])

    def has_side_effects(self, tree: ast.Module) -> astu.HasSideEffects:
        """
        Check if the given import file tree has side effects.

        :param tree: import file tree.
        :returns: side effects status.
        """
        raise NotImplementedError

    def insert_import(
        self, rebuilt_import: Union[str, None], old_node: ast.Import
    ) -> None:
        """
        Insert rebuilt import statement into current source lines.

        :param rebuilt_import: an import statement to insert.
        :param old_node: an `ast.Import` object.
        """
        self.source_lines[old_node.lineno - 1] = rebuilt_import
        # Replace each removed line with None.
        if old_node.end_lineno - old_node.lineno:
            self.source_lines[old_node.lineno] = None

    def insert_import_from(
        self, rebuilt_import_from: Union[str, list, None], old_node: ast.ImportFrom
    ) -> None:
        """
        Insert rebuilt importFrom statement into current source lines.

        :param rebuilt_import_from: an importFrom statement to insert.
        :param old_node: an `ast.ImportFrom` object.
        """
        old_lineno = old_lineno - 1

        if isinstance(rebuilt_import_from, str):
            # Insert the single-line importFrom statement.
            new_len = 1
            self.source_lines[old_lineno] = rebuilt_import_from

        elif isinstance(rebuilt_import_from, list):
            # Insert the multi-line importFrom statement.
            new_len = len(rebuilt_import_from)
            for line in rebuilt_import_from:
                self.source_lines[old_lineno] = line
                old_lineno += 1

        else:
            new_len = 0

        # Replace each removed line with None.
        lineno = old_node.lineno + new_len - 1
        old_len = old_node.end_lineno - old_node.lineno + 1
        for i in range(old_len - new_len):
            self.source_lines[lineno] = None
            lineno += 1
