"""
Pycln AST utility.
"""
import ast
import os
import sys
from dataclasses import dataclass
from enum import Enum, unique
from functools import wraps, lru_cache
from importlib.util import find_spec
from pathlib import Path
from typing import Any, Callable, List, Optional, Set, Tuple, TypeVar, Union, cast

from _ast import AST

from . import ast2source as ast2s, nodes, pathu
from .exceptions import (
    ReadPermissionError,
    UnexpandableImportStar,
    UnparsableFile,
    WritePermissionError,
)

# Constants.
PY38_PLUS = sys.version_info >= (3, 8)
LEFT_PARENTHESIS = ")"
BACK_SLASH = "\\"
EMPTY = ""
STAR = "*"
DOT = "."

# Custom types.
Function = TypeVar("Function", bound=Callable[..., Any])


def recursive(func: Function) -> Function:
    """decorator to make `ast.NodeVisitor` work recursive.
    
    :param func: `ast.NodeVisitor.visit_*` function.
    """

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        func(self, *args, **kwargs)
        self.generic_visit(*args)

    return cast(Function, wrapper)


@dataclass
class ImportStats:

    """Import statements statistics."""

    import_: Set[Union[ast.Import, nodes.Import]]
    from_: Set[Union[ast.ImportFrom, nodes.ImportFrom]]

    def __iter__(self):
        return iter([self.import_, self.from_])


@dataclass
class SourceStats:

    """Source code (`ast.Name` & `ast.Attribute`) statistics."""

    name_: Set[str]
    attr_: Set[str]

    def __iter__(self):
        return iter([self.name_, self.attr_])


class SourceAnalyzer(ast.NodeVisitor):

    """AST source code analyzer.

    Python >= 3.8:
        >>> import ast
        >>> source = "source.py"
        >>> with open(source, "r") as sourcef:
        >>>     tree = ast.parse(sourcef.read())
        >>> analyzer = SourceAnalyzer()
        >>> analyzer.visit(tree)
        >>> source_stats, import_stats = analyzer.get_stats()
    
    Python < 3.8:
        >>> import ast
        >>> source = "source.py"
        >>> with open(source, "r") as sourcef:
        >>>     source_lines = sourcef.readlines()
        >>>     tree = ast.parse("".join(source_lines))
        >>> analyzer = SourceAnalyzer(source_lines)
        >>> analyzer.visit(tree)
        >>> source_stats, import_stats = analyzer.get_stats()

    :param source_lines: source code as string lines, required only when Python < 3.8.
    :raises ValueError: when Python < 3.8 and no source code lines provided.
    """

    def __init__(self, source_lines: Optional[List[str]] = None, *args, **kwargs):
        super(SourceAnalyzer, self).__init__(*args, **kwargs)

        if not any([PY38_PLUS, source_lines]):
            # Bad class usage.
            raise ValueError("Please provide source lines for Python < 3.8.")
        else:
            self.__lines = source_lines

        self.__import_stats = ImportStats(set(), set())
        self.__source_stats = SourceStats(set(), set())

    @recursive
    def visit_Import(self, node: ast.Import):
        py38_node = self.__get_py38_node(node)
        self.__import_stats.import_.add(py38_node)

    @recursive
    def visit_ImportFrom(self, node: ast.ImportFrom):
        py38_node = self.__get_py38_node(node)
        self.__import_stats.import_.add(py38_node)

    @recursive
    def visit_Name(self, node: ast.Name):
        self.__source_stats.name_.add(node.id)

    @recursive
    def visit_Attribute(self, node: ast.Name):
        self.__source_stats.attr_.add(node.attr)

    def __get_py38_node(
        self, node: Union[ast.Import, ast.ImportFrom]
    ) -> Union[nodes.Import, nodes.ImportFrom]:
        """Convert any Python < 3.8 `ast.Import` or `ast.ImportFrom`
        to `nodes.Import` or `nodes.ImportFrom` to support `end_lineno`.

        :param node: an `ast.Import` or `ast.ImportFrom` node.
        :returns: a `nodes.Import` or `nodes.ImportFrom` node.
        """
        if PY38_PLUS:
            return node

        import_line = self.__lines[node.lineno - 1]

        if isinstance(node, ast.Import):
            multiline = BACK_SLASH in import_line
            py38_node = nodes.Import(
                lineno=node.lineno,
                col_offset=node.col_offset,
                end_lineno=node.lineno + (1 if multiline else 0),
                names=node.names,
            )
        else:
            is_parentheses = ast2s.is_parentheses(import_line)
            multiline = is_parentheses is not None
            end_lineno = (
                node.lineno
                if not multiline
                else self.__get_end_lineno(node.lineno, is_parentheses)
            )
            py38_node = nodes.ImportFrom(
                lineno=node.lineno,
                col_offset=node.col_offset,
                end_lineno=end_lineno,
                names=node.names,
                module=node.module,
                level=node.level,
            )
        return py38_node

    def __get_end_lineno(self, lineno: int, is_parentheses: bool):
        """Get `ast.ImportFrom` end lineno of the given lineno.

        :param lineno: `ast.ImportFrom.lineno`.
        :param is_parentheses: is the multiline notations are parentheses.
        :returns: end_lineno.
        """
        lines_len = len(self.__lines)
        for end_lineno in range(lineno, lines_len):
            if is_parentheses:
                if LEFT_PARENTHESIS in self.__lines[end_lineno]:
                    return end_lineno + 1
            else:
                if BACK_SLASH not in self.__lines[end_lineno]:
                    return end_lineno + 1

    def get_stats(self) -> Tuple[ImportStats, SourceStats]:
        """Get source analyzer results.

        :returns: tuple of `ImportStats` and `SourceStats`.
        """
        return self.__source_stats, self.__import_stats


class ImportablesAnalyzer(ast.NodeVisitor):

    """Get set of all importable names from given `ast.Module`.

    >>> import ast
    >>> source = "source.py"
    >>> with open(source, "r") as sourcef:
    >>>     tree = ast.parse(sourcef.read())
    >>> analyzer = ImportablesAnalyzer(source)
    >>> analyzer.visit(tree)
    >>> importable_names = analyzer.get_stats()

    :param source: a file path that belongs to the given `ast.Module`.
    """

    @staticmethod
    @lru_cache()
    def handle_c_libs_importables(module_name: str, level: int) -> Set[str]:
        """
        Handle libs written in C or built-in CPython.

        :param module_name: `ast.ImportFrom.module`.
        :param level: `ast.ImportFrom.level`.
        :returns: set of importables.
        :raises ModuleNotFoundError: when we can't find the spec of the module and/or can't create the module.
        """
        level_dots = DOT * level
        spec = find_spec(module_name, level_dots if level_dots else None)

        if spec:
            module = spec.loader.create_module(spec)

            if module:
                return set(dir(module))

        raise ModuleNotFoundError(name=module_name)

    def __init__(self, source: Path, *args, **kwargs):
        super(ImportablesAnalyzer, self).__init__(*args, **kwargs)
        self.__not_importables: Set[ast.Name] = set()
        self.__stats: Set[str] = set()
        self.__source = source

    @recursive
    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            name = alias.asname if alias.asname else alias.name
            self.__stats.add(name)

    @recursive
    def visit_ImportFrom(self, node: ast.ImportFrom):
        try:
            if node.names[0].name == STAR:
                # Expand import star if possible.
                node = expand_import_star(node, self.__source)
            for alias in node.names:
                name = alias.asname if alias.asname else alias.name
                self.__stats.add(name)
        except UnexpandableImportStar:
            # * We shouldn't do anything because it's not importable.
            pass

    @recursive
    def visit_FunctionDef(self, node: ast.FunctionDef):
        # Add function name as importable name.
        self.__stats.add(node.name)

        # Compute function not-importables.
        for node_ in ast.iter_child_nodes(node):

            if isinstance(node_, ast.Assign):

                for target in node_.targets:
                    self.__not_importables.add(target)

    @recursive
    def visit_ClassDef(self, node: ast.ClassDef):
        # Add class name as importable name.
        self.__stats.add(node.name)

        # Compute class not-importables.
        for node_ in ast.iter_child_nodes(node):

            if isinstance(node_, ast.Assign):

                for target in node_.targets:
                    self.__not_importables.add(target)

    @recursive
    def visit_Name(self, node: ast.Name):
        if isinstance(node.ctx, ast.Store):
            # Except not-importables.
            if node not in self.__not_importables:
                self.__stats.add(node.id)

    def get_stats(self) -> Set[str]:
        return self.__stats


@unique
class HasSideEffects(Enum):
    YES = 1
    MAYBE = 0.5
    NO = 0
    NOT_MODULE = -1

    # Just in case an exception has raised
    # while parsing a file.
    NOT_KNOWN = -2


class SideEffectsAnalyzer(ast.NodeVisitor):

    """Check if the given `ast.Module` has side effects or not.

    >>> import ast
    >>> source = "source.py"
    >>> with open(source, "r") as sourcef:
    >>>     tree = ast.parse(sourcef.read())
    >>> analyzer = SideEffectsAnalyzer()
    >>> analyzer.visit(tree)
    >>> has_side_effects = analyzer.has_side_effects()
    """

    def __init__(self, *args, **kwargs):
        super(SideEffectsAnalyzer, self).__init__(*args, **kwargs)
        self.__not_side_effect: Set[ast.Call] = set()
        self.__has_side_effects = HasSideEffects.NO

    @recursive
    def visit_FunctionDef(self, node: ast.FunctionDef):
        # Mark any call inside a function as not-side-effect.
        for node_ in ast.iter_child_nodes(node):
            if isinstance(node_, ast.Expr):
                if isinstance(node_.value, ast.Call):
                    self.__not_side_effect.add(node_.value)

    @recursive
    def visit_ClassDef(self, node: ast.ClassDef):
        # Mark any call inside a class as not-side-effect.
        for node_ in ast.iter_child_nodes(node):
            if isinstance(node_, ast.Expr):
                if isinstance(node_.value, ast.Call):
                    self.__not_side_effect.add(node_.value)

    @recursive
    def visit_Call(self, node: ast.Call):
        if node not in self.__not_side_effect:
            self.__has_side_effects = HasSideEffects.YES

    @recursive
    def visit_Import(self, node: ast.Import):
        for alias in node.names:

            if alias.name in pathu.get_standard_lib_names():
                continue

            if alias.name in pathu.IMPORTS_WITH_SIDE_EFFECTS:
                self.__has_side_effects = HasSideEffects.YES
                break

            # [Here instead of doing that, we can make the analyzer
            # works recursively inside each not known import.
            self.__has_side_effects = HasSideEffects.MAYBE
            # I choosed this way because it's almost %100 we will end
            # with a file that has side effects :-) ].

    @recursive
    def visit_ImportFrom(self, node: ast.ImportFrom):
        for alias in node.names:

            if alias.name in pathu.get_standard_lib_names():
                continue

            if alias.name in pathu.IMPORTS_WITH_SIDE_EFFECTS:
                self.__has_side_effects = HasSideEffects.YES
                break

            # [Here instead of doing that, we can make the analyzer
            # works recursively inside each not known import.
            self.__has_side_effects = HasSideEffects.MAYBE
            # I choosed this way because it's almost %100 we will end
            # with a file that has side effects :-) ].

    def has_side_effects(self) -> HasSideEffects:
        return self.__has_side_effects

    def generic_visit(self, node):
        """Called if no explicit visitor function exists for a node (override)."""
        # Continue visiting if only if there's no know side effects.
        if self.__has_side_effects is HasSideEffects.NO:
            for field, value in ast.iter_fields(node):
                if isinstance(value, list):
                    for item in value:
                        if isinstance(item, AST):
                            self.visit(item)
                elif isinstance(value, AST):
                    self.visit(value)


def expand_import_star(node: ast.ImportFrom, source: Path) -> ast.ImportFrom:
    """Expand import star statement, replace the `*` with a list of ast.alias.
    
    :param node: an `ast.ImportFrom` node that has a '*' as `alias.name`.
    :param source: where the node has imported.
    :returns: expanded `ast.ImportFrom`.
    :raises UnexpandableImportStar: when `ReadPermissionError` or `UnparsableFile` or `ModuleNotFoundError` raised.
    """
    module_path = pathu.get_import_from_path(source, STAR, node.module, node.level)

    importables: Set[str] = set()

    try:
        if module_path:
            tree = get_file_ast(module_path, permissions=(os.R_OK,))

            analyzer = ImportablesAnalyzer(source)
            analyzer.visit(tree)
            importables = analyzer.get_stats()

        else:
            importables = ImportablesAnalyzer.handle_c_libs_importables(
                node.module, node.level
            )
    except (ReadPermissionError, UnparsableFile, ModuleNotFoundError) as err:
        msg = err if not isinstance(err, ModuleNotFoundError) else "module not found!"
        raise UnexpandableImportStar(source, node.lineno, node.col_offset, msg)

    # Create `ast.alias` for each name.
    node.names.clear()
    for name in importables:
        node.names.append(ast.alias(name=name, asname=None))

    return node


def remove_useless_passes(source_lines: List[str]) -> List[str]:
    """Remove any useless `pass`.

    :param source_lines: source code lines to check.
    :returns: clean source lines.
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

    return source_lines


def get_file_ast(
    source: Path, get_codes: bool = False, permissions: tuple = (os.R_OK, os.W_OK)
) -> Union[ast.Module, Tuple[ast.Module, List[str]]]:
    """Parse source file AST.

    :param source: source to read.
    :param get_codes: if true the source file lines and the source code will be returned.
    :param permissions: tuple of permissions to check, supported permissions (os.R_OK, os.W_OK).
    :returns: source file AST (`ast.Module`). Also source code lines if get_lines.
    :raises ReadPermissionError: when `os.R_OK` in permissions and the source does not have read permission.
    :raises WritePermissionError: when `os.W_OK` in permissions and the source does not have write permission.
    :raises UnparsableFile: if the compiled source is invalid, or the source contains null bytes.
    """
    # Check these permissions before openinig the file.
    for permission in permissions:
        if not os.access(source, permission):
            if permission is os.R_OK:
                raise ReadPermissionError(13, "Permission denied [READ]", source)
            elif permission is os.W_OK:
                raise WritePermissionError(13, "Permission denied [WRITE]", source)

    with open(source, "r") as sfile:
        lines = sfile.readlines() if get_codes else []
        content = EMPTY.join(lines) if get_codes else sfile.read()

    try:
        if PY38_PLUS:
            # Include type_comments when Python >=3.8.
            # For more information https://www.python.org/dev/peps/pep-0526/ .
            tree = ast.parse(content, type_comments=True)
        else:
            tree = ast.parse(content)
    except (SyntaxError, ValueError) as exception:
        raise UnparsableFile(source, exception)

    return (tree, lines, content) if get_codes else tree
