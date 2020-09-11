"""Pycln code refactoring utility."""
import ast
import os
from copy import copy
from functools import lru_cache
from importlib import import_module
from pathlib import Path
from typing import List, Optional, Set, Tuple, Union

from . import iou, pathu, regexu, scan
from ._exceptions import (
    ReadPermissionError,
    UnexpandableImportStar,
    UnparsableFile,
    UnsupportedCase,
    WritePermissionError,
    libcst_parser_syntax_error_message,
)
from .config import Config
from .nodes import Import, ImportFrom
from .report import Report


class LazyLibCSTLoader:

    """`transform.py` takes about '0.3s' to be loaded because of LibCST,
    therefore I've created this class to load it only if necessary."""

    def __init__(self):
        self._module = None

    def __getattr__(self, name):
        if self._module is None:
            self._module = import_module(".transform", "pycln.utils")
        return getattr(self._module, name)


transform = LazyLibCSTLoader()

# Constants.
DOT = "."
STAR = "*"
CODE = "code"
EMPTY = ""
SPACE = " "
NOPYCLN = "nopycln"
NEW_LINE = "\n"
SEMICOLON = ";"
CHANGE_MARK = "\n_CHANGED_"


class Refactor:

    """Refactor the given source.

    >>> refactor = Refactor(
    ...     configs,  # Should be created on the main function.
    ...     reporter,  # Should be created on the main function.
    ... )
    >>> file_path = "./source.py"
    >>> refactor.session(file_path)

    :param configs: `config.Config` instance.
    :param reporter: `report.Report` instance.
    """

    def __init__(self, configs: Config, reporter: Report):
        self.configs = configs
        self.reporter = reporter
        # Resetables.
        self._import_stats = None
        self._source_stats = None
        self._path = None

    def _reset(self) -> None:
        self._import_stats = None
        self._source_stats = None
        self._path = None

    @staticmethod
    def remove_useless_passes(source_lines: List[str]) -> List[str]:
        """Remove any useless `pass`.

        :param source_lines: source code lines.
        :returns: clean source code lines.
        """
        tree = ast.parse(EMPTY.join(source_lines))
        for parent in ast.walk(tree):
            try:
                if parent.__dict__.get("body", None):
                    body_len = len(parent.body)
                else:
                    continue
            except TypeError:
                continue
            for child in ast.iter_child_nodes(parent):
                if isinstance(child, ast.Pass):
                    if body_len > 1:
                        body_len -= 1
                        source_lines[child.lineno - 1] = EMPTY
        return EMPTY.join(source_lines).splitlines(True)

    def session(self, path: Union[Path, str]) -> None:
        """Refactoring session.

        Refactor the given `path` source code.

        :param path: `.py` file to refactor.
        """
        self._path = path
        try:
            # Safly read the file.
            permissions = (os.R_OK,)
            if not self.configs.check and not self.configs.diff:
                permissions = (os.R_OK, os.W_OK)
            content, encoding = iou.safe_read(self._path, permissions)

            # Refactor and output the `content`.
            fixed_lines = self._code_session(content).splitlines(True)
            self._output(fixed_lines, content.splitlines(True), encoding)
        except (
            ReadPermissionError,
            WritePermissionError,
            UnparsableFile,
        ) as err:
            self.reporter.failure(err)
        finally:
            self._reset()

    def _code_session(self, source_code: str) -> str:
        """Refactor the given `source_code`.

        :param source_code: python source code.
        :returns: fixed source code.
        """
        # Skip any file that has `# nopycln: file`.
        if regexu.skip_file(source_code):
            self.reporter.ignored_path(self._path, NOPYCLN)
            return source_code

        # Parse and analyze the `source_code` AST.
        tree = scan.parse_ast(source_code, self._path)
        original_lines = source_code.splitlines(True)
        stats = self._analyze(tree, original_lines)
        if not stats:
            return source_code
        self._source_stats, self._import_stats = stats

        # Refactor the `source_code`.
        return self._refactor(original_lines)

    def _output(
        self, fixed_lines: List[str], original_lines: List[str], encoding: str
    ) -> None:
        """Output the given `fixed_lines`.

        :param fixed_lines: the refactored source lines.
        :param original_lines: unmodified source lines.
        :param encoding: file encoding.
        """
        if fixed_lines == original_lines:
            self.reporter.unchanged_file(self._path)
        else:
            self.reporter.changed_file(self._path)
            if not self.configs.check:
                fixed_lines = Refactor.remove_useless_passes(fixed_lines)
                if self.configs.diff:
                    self.reporter.colored_unified_diff(
                        self._path, original_lines, fixed_lines
                    )
                else:
                    iou.safe_write(self._path, fixed_lines, encoding)

    def _analyze(
        self, tree: ast.Module, original_lines: List[str]
    ) -> Optional[Tuple[scan.SourceStats, scan.ImportStats]]:
        """Analyze the given `tree`.

        :param tree: a parsed `ast.Module`.
        :param original_lines: code lines requiered for Python < 3.8.
        :returns: tuple of `ImportStats`, `SourceStats` and set of names to skip.
        """
        try:
            analyzer = scan.SourceAnalyzer(original_lines)
            analyzer.visit(tree)
            source_stats, import_stats = analyzer.get_stats()
            return source_stats, import_stats
        except Exception as err:
            self.reporter.failure(err, self._path)

    def _refactor(self, original_lines: List[str]) -> str:
        """Remove all unused imports from given `original_lines`.

        :param original_lines: unmodified lines.
        :reutrns: fixed source code.
        """
        fixed_lines = copy(original_lines)
        for type_ in self._import_stats:

            for node in type_:

                # Skip any import that has `# noqa` or `# nopycln: import` comment.
                lineno = node.location.start.line - 1
                if regexu.skip_import(fixed_lines[lineno]):
                    self.reporter.ignored_import(self._path, node)
                    continue

                # Expand any import '*' before checking.
                node, is_star = self._expand_import_star(node)
                if is_star is None:
                    continue

                # Get set of used names.
                used_names = self._get_used_names(node, is_star)

                # Depends on `--expand-stars, -x` option.
                if is_star:
                    if used_names:
                        if self.configs.expand_stars:
                            self.reporter.expanded_star(self._path, node)
                        else:
                            continue
                    else:
                        star_alias = ast.alias(name=STAR, asname=None)
                        self.reporter.removed_import(self._path, node, star_alias)

                # No alias has removed/added.
                if len(used_names) == len(node.names):
                    if not self.configs.expand_stars:
                        continue

                # Depends on `--check, -c` option.
                if self.configs.check:
                    fixed_lines.append(CHANGE_MARK)
                    continue

                # Default and `--diff, -d` option.
                fixed_lines = self._transform(
                    node, used_names, original_lines, fixed_lines
                )

        return EMPTY.join(fixed_lines)

    def _get_used_names(
        self, node: Union[Import, ImportFrom], is_star: bool
    ) -> Set[str]:
        """Get set of used names base on given `node` and `self._source_stats`.

        :param node: import node to names check.
        :parma is_star: is '*' import node.
        :returns: set of used names.
        """
        used_names: Set[str] = set()
        for alias in node.names:
            if self._should_remove(node, alias, is_star):
                if not is_star:
                    self.reporter.removed_import(self._path, node, alias)
                continue
            used_names.add(alias.name)
        return used_names

    def _transform(
        self,
        node: Union[Import, ImportFrom],
        used_names: Set[str],
        original_lines: List[str],
        updated_lines: List[str],
    ) -> List[str]:
        """Rebuild and replace the import without any unused part.

        :param node: an import statement node.
        :param used_names: set of all used names.
        :param original_lines: file original code lines.
        :param updated_lines: code lines to modify.
        :returns: modified source lines (fixed lines).
        """
        try:
            try:
                lineno = node.location.start.line - 1
                end_lineno = node.location.end.line
                import_stmnt = EMPTY.join(original_lines[lineno:end_lineno])
                rebuilt_import = transform.rebuild_import(
                    import_stmnt,
                    used_names,
                    self._path,
                    node.location,
                )
                updated_lines = self._insert(rebuilt_import, updated_lines, node)
            except UnsupportedCase as msg:
                self.reporter.failure(msg)
        except transform.cst.ParserSyntaxError as err:
            msg = libcst_parser_syntax_error_message(self._path, err)
            self.reporter.failure(msg)
        return updated_lines

    def _expand_import_star(
        self, node: ImportFrom
    ) -> Tuple[ast.ImportFrom, Optional[bool]]:
        """Expand import star statement, `scan.expand_import_star` abstraction.

        :param node: `ImportFrom` that has a '*' as `alias.name`.
        :returns: expanded '*' import or the original node and True if it's star import.
        """
        try:
            is_star = False
            if node.names[0].name == STAR:
                is_star = True
                node = scan.expand_import_star(node, self._path)
            return node, is_star
        except UnexpandableImportStar as err:
            self.reporter.failure(err)
            self.reporter.ignored_import(self._path, node, is_star=True)
            return node, None

    def _should_remove(
        self, node: Union[Import, ImportFrom], alias: ast.alias, is_star: bool
    ) -> bool:
        """Check if the alias should be removed or not.

        :param node: an `Import` or `ImportFrom`.
        :param alias: an `ast.alias` node.
        :param is_star: is it a '*' import.
        :returns: True if the alias should be removed else False.
        """
        real_name = node.module if isinstance(node, ImportFrom) else alias.name
        used_name = alias.asname if alias.asname else alias.name
        if (
            not self._has_used(used_name, is_star)
            and real_name not in pathu.IMPORTS_WITH_SIDE_EFFECTS
        ):
            if (
                self.configs.all_
                or real_name in pathu.get_standard_lib_names()
                or self._has_side_effects(alias.name, node)
                in (scan.HasSideEffects.NO, scan.HasSideEffects.NOT_MODULE)
            ):
                return True
        return False

    def _has_used(self, name: str, is_star: bool) -> bool:
        """Check if the given import name has used.

        :param name: a name to check.
        :param is_star: is it a '*' import.
        :returns: True if the name has used else False.
        """
        name = name.split(DOT) if DOT in name else name
        if isinstance(name, str):
            if is_star and name in self._source_stats.names_to_skip:
                return False
            # Handle imports like (import os, from os import path).
            return name in self._source_stats.name_
        else:
            # Handle imports like (import os.path, from os import path.join).
            return self._has_used(name[0], is_star) and all(
                [name in self._source_stats.attr_ for name in name[1:]]
            )

    @lru_cache()
    def _has_side_effects(
        self, module: str, node: Union[Import, ImportFrom]
    ) -> scan.HasSideEffects:
        """Check if the given import file tree has side effects.

        :param module: `alias.name` to check.
        :param node: an `ast.Import` or `ast.ImportFrom` node.
        :returns: side effects status.
        """
        if isinstance(node, ImportFrom):
            module_source = pathu.get_import_from_path(
                self._path, module, node.module, node.level
            )
        else:
            module_source = pathu.get_import_path(self._path, module)

        if not module_source:
            return scan.HasSideEffects.NOT_MODULE

        try:
            code, _ = iou.safe_read(module_source, permissions=(os.R_OK,))
            tree = scan.parse_ast(code, module_source)
        except (ReadPermissionError, UnparsableFile) as err:
            self.reporter.failure(err)
            return scan.HasSideEffects.NOT_KNOWN

        try:
            analyzer = scan.SideEffectsAnalyzer()
            analyzer.visit(tree)
            return analyzer.has_side_effects()
        except Exception as err:
            self.reporter.failure(err, self._path)
            return scan.HasSideEffects.NOT_KNOWN

    def _insert(
        self,
        rebuilt_import: List[str],
        updated_lines: List[str],
        node: Union[Import, ImportFrom],
    ) -> List[str]:
        """Insert (replace) rebuilt import statement into `updated_lines`.

        :param rebuilt_import: an import statement ot insert.
        :param updated_lines: a list of source lines to modify.
        :param node: unmodified node.
        :returns: fixed list of lines.
        """
        # Shollow copy.
        fixed_lines = updated_lines.copy()

        # Determine old-new import delta.
        new_len = len(rebuilt_import)
        old_len = len(node.location)
        delta = old_len - new_len
        if rebuilt_import[0] == EMPTY:
            delta += 1

        # Insert the rebuilt import statement.
        index = node.location.start.line - 1
        for i in range(new_len):
            if old_len == 1 and i != (new_len - 3):
                line = EMPTY.join(rebuilt_import[i:])
                fixed_lines[index] = line
                break
            else:
                fixed_lines[index] = rebuilt_import[i]
            index += 1
            old_len -= 1

        # Replace each removed line with `EMPTY`.
        if delta > 0:
            for i in range(delta):
                fixed_lines[index] = EMPTY
                index += 1

        return fixed_lines
