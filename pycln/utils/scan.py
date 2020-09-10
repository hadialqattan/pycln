"""Pycln source code AST analysis utility."""
import ast
import os
import sys
from dataclasses import dataclass
from enum import Enum, unique
from functools import lru_cache, wraps
from importlib import import_module
from importlib.util import find_spec
from pathlib import Path
from typing import Any, Callable, List, Optional, Set, Tuple, TypeVar, Union, cast

from . import iou, nodes, pathu
from ._exceptions import ReadPermissionError, UnexpandableImportStar, UnparsableFile

# Constants.
PY38_PLUS = sys.version_info >= (3, 8)
IMPORT_EXCEPTIONS = {"ImportError", "ImportWarning", "ModuleNotFoundError"}
NAMES_TO_SKIP = {
    "__name__",
    "__doc__",
    "__package__",
    "__loader__",
    "__spec__",
    "__build_class__",
    "__import__",
    "__all__",
}
RIGHT_PAEENTHESIS = "("
LEFT_PARENTHESIS = ")"
D_UNDERSCORES = "__"
BACK_SLASH = "\\"
SEMICOLON = ";"
__ALL__ = "__all__"
EMPTY = ""
NAMES = "names"
STAR = "*"
ELTS = "elts"
DOT = "."
ID = "id"


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

    import_: Set[nodes.Import]
    from_: Set[nodes.ImportFrom]

    def __iter__(self):
        return iter([self.import_, self.from_])


@dataclass
class SourceStats:

    """Source code (`ast.Name`, `ast.Attribute`) statistics."""

    #: Included on `__iter__`.
    name_: Set[str]
    attr_: Set[str]

    #: Not included on `__iter__`.
    names_to_skip: Set[str]

    def __iter__(self):
        return iter([self.name_, self.attr_])


class SourceAnalyzer(ast.NodeVisitor):

    """AST source code analyzer.

    >>> import ast
    >>> source = "source.py"
    >>> with open(source, "r") as sourcef:
    >>>     source_lines = sourcef.readlines()
    >>>     tree = ast.parse("".join(source_lines))
    >>> analyzer = SourceAnalyzer(source_lines)
    >>> analyzer.visit(tree)
    >>> source_stats, import_stats = analyzer.get_stats()

    :param source_lines: source code as string lines,
        required only when Python < 3.8.
    :raises ValueError: when Python < 3.8 and no source code lines provided.
    """

    def __init__(self, source_lines: Optional[List[str]] = None, *args, **kwargs):
        super(SourceAnalyzer, self).__init__(*args, **kwargs)
        if not PY38_PLUS and source_lines is None:
            # Bad class usage.
            raise ValueError("Please provide source lines for Python < 3.8.")
        self._lines = source_lines
        self._import_stats = ImportStats(set(), set())
        self._imports_to_skip: Set[Union[nodes.Import, nodes.ImportFrom]] = set()
        self._source_stats = SourceStats(set(), set(), set())

    @recursive
    def visit_Import(self, node: ast.Import):
        if node not in self._imports_to_skip:
            py38_node = self._get_py38_import_node(node)
            self._import_stats.import_.add(py38_node)

    @recursive
    def visit_ImportFrom(self, node: ast.ImportFrom):
        if node not in self._imports_to_skip:
            py38_node = self._get_py38_import_from_node(node)
            if not str(py38_node.module).startswith(D_UNDERSCORES):
                self._import_stats.from_.add(py38_node)

    @recursive
    def visit_Name(self, node: ast.Name):
        self._source_stats.name_.add(node.id)

    @recursive
    def visit_Attribute(self, node: ast.Name):
        self._source_stats.attr_.add(node.attr)

    @recursive
    def visit_Try(self, node: ast.Try):
        """Support any try/except block that has import error(s).

        Add any import that placed on try/except block that has import error
        to `self._imports_to_skip`.

        exp:- two of these imports would not be used and should not be removed:
            >>> try:
            >>>     import foo2
            >>> except ModuleNotFoundError:
            >>>     import foo3
            >>> else:
            >>>     import foo38

        supported exceptions (`IMPORT_EXCEPTIONS`):
            - ModuleNotFoundError
            - ImportError.
            - ImportWarning.

        supported blocks:
            - try.
            - except.
            - else.
        """
        is_skip_case = False

        def add_imports_to_skip(body: ast.List) -> None:
            """Add all try/except/else blocks body import children to
            `self._imports_to_skip`.

            :param body: ast.List to iterate over.
            """
            for child in body:
                if hasattr(child, NAMES):
                    self._imports_to_skip.add(child)

        for handler in node.handlers:
            if hasattr(handler.type, ELTS):
                for name in handler.type.elts:
                    if hasattr(name, ID) and name.id in IMPORT_EXCEPTIONS:
                        is_skip_case = True
                        break
            elif hasattr(handler.type, ID):
                if handler.type.id in IMPORT_EXCEPTIONS:
                    is_skip_case = True
            if is_skip_case:
                add_imports_to_skip(handler.body)

        if is_skip_case:
            for body in (node.body, node.orelse):
                add_imports_to_skip(body)

    @recursive
    def visit_AnnAssign(self, node: ast.AnnAssign):
        """Support string type annotations.

        exp:- this code has no unused imports:
            >>> from typing import List
            >>> foo: "List[str]" = []
        """
        self._visit_string_type_annotation(node)

    @recursive
    def visit_arg(self, node: ast.arg):
        """Support arg string type annotations.

        exp:- this code has no unused imports:
            >>> from typing import Tuple
            >>> def foo(bar: "Tuple[str, int]"):
                    pass
        """
        self._visit_string_type_annotation(node)

    @recursive
    def visit_FunctionDef(self, node: Union[ast.FunctionDef, ast.AsyncFunctionDef]):
        # Support Python > 3.8 type comments.
        if PY38_PLUS:
            self._visit_type_comment(node)

    # Support `ast.AsyncFunctionDef`.
    visit_AsyncFunctionDef = visit_FunctionDef

    @recursive
    def visit_Assign(self, node: ast.Assign):
        # Support Python > 3.8 type comments.
        if PY38_PLUS:
            self._visit_type_comment(node)
        # These names will be skipped on import `*` case.
        if getattr(node.targets[0], ID, None) in NAMES_TO_SKIP:
            self._source_stats.names_to_skip.add(node.targets[0].id)
        # Support `__all__` dunder overriding case
        if getattr(node.targets[0], ID, None) == __ALL__:
            if isinstance(node.value, (ast.List, ast.Tuple, ast.Set)):
                for constant in node.value.elts:
                    if PY38_PLUS:
                        if isinstance(constant.value, str):
                            self._source_stats.name_.add(constant.value)
                    else:
                        if isinstance(constant.s, str):
                            self._source_stats.name_.add(constant.s)

    def _visit_type_comment(self, node: Union[ast.Assign, ast.FunctionDef]) -> None:
        """Support Python > 3.8 type comments.

        This feature is only available for python > 3.8.
        PEP 526 -- Syntax for Variable Annotations.
        For more information:
            - https://www.python.org/dev/peps/pep-0526/
            - https://docs.python.org/3.8/library/ast.html#ast.parse
        """
        if node.type_comment:
            if isinstance(node, ast.Assign):
                mode = "eval"
            else:
                mode = "func_type"
            tree = parse_ast(node.type_comment, EMPTY, mode)
            self._add_name_attr(tree)

    def _visit_string_type_annotation(self, node: Union[ast.AnnAssign, ast.arg]):
        """Support string type annotations.

        exp:- this code has no unused imports:
            >>> from typing import List, Tuple
            >>> foo: "List[str]" = []
            >>> def foobar(bar: "Tuple[str, int]"):
            ...     pass
        """
        if isinstance(node.annotation, (ast.Constant, ast.Str)):
            if PY38_PLUS:
                value = node.annotation.value
            else:
                value = node.annotation.s
            tree = parse_ast(value, EMPTY, mode="eval")
            self._add_name_attr(tree)

    def _add_name_attr(self, tree: ast.Module):
        """Add any `node` `ast.Name` or `ast.Attribute` child to
        `self._source_stats`."""
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                self._source_stats.name_.add(node.id)
            elif isinstance(node, ast.Attribute):
                self._source_stats.attr_.add(node.attr)

    def _get_py38_import_node(self, node: ast.Import) -> nodes.Import:
        """Convert any Python < 3.8 `ast.Import` to `nodes.Import` in order to
        support `end_lineno`.

        :param node: an `ast.Import` node.
        :returns: a `nodes.Import` node.
        """
        if PY38_PLUS:
            end_lineno = node.end_lineno
        else:
            line = self._lines[node.lineno - 1]
            multiline = self._is_parentheses(line) is not None
            end_lineno = node.lineno + (1 if multiline else 0)
        start = nodes.NodePosition(node.lineno, node.col_offset)
        end = nodes.NodePosition(end_lineno)
        location = nodes.NodeLocation(start, end)
        return nodes.Import(location=location, names=node.names)

    def _get_py38_import_from_node(self, node: ast.ImportFrom) -> nodes.ImportFrom:
        """Convert any Python < 3.8 `ast.ImportFrom` to `nodes.ImportFrom` in
        order to support `end_lineno`.

        :param node: an `ast.ImportFrom` node.
        :returns: a `nodes.ImportFrom` node.
        """
        if PY38_PLUS:
            end_lineno = node.end_lineno
        else:
            line = self._lines[node.lineno - 1]
            is_parentheses = self._is_parentheses(line)
            multiline = is_parentheses is not None
            end_lineno = (
                node.lineno
                if not multiline
                else self._get_end_lineno(node.lineno, is_parentheses)
            )
        start = nodes.NodePosition(node.lineno, node.col_offset)
        end = nodes.NodePosition(end_lineno)
        location = nodes.NodeLocation(start, end)
        return nodes.ImportFrom(
            location=location,
            names=node.names,
            module=node.module,
            level=node.level,
        )

    def _is_parentheses(self, import_from_line: str) -> Optional[bool]:
        """Return importFrom multi-line type.

        :param import_from_line: importFrom statement str line.
        :returns: importFrom type ('(' => True), ('\\' => False), else None.
        """
        if RIGHT_PAEENTHESIS in import_from_line:
            return True
        elif BACK_SLASH in import_from_line:
            return False
        else:
            return None

    def _get_end_lineno(self, lineno: int, is_parentheses: bool) -> int:
        """Get `ast.ImportFrom` end lineno of the given lineno.

        :param lineno: `ast.ImportFrom.lineno`.
        :param is_parentheses: is the multiline notations are parentheses.
        :returns: end_lineno.
        """
        lines_len = len(self._lines)
        for end_lineno in range(lineno, lines_len):
            if is_parentheses:
                if LEFT_PARENTHESIS in self._lines[end_lineno]:
                    return end_lineno + 1
            else:
                if BACK_SLASH not in self._lines[end_lineno]:
                    return end_lineno + 1

    def get_stats(self) -> Tuple[ImportStats, SourceStats]:
        """Get source analyzer results.

        :returns: tuple of `ImportStats` and `SourceStats`.
        """
        return self._source_stats, self._import_stats


class ImportablesAnalyzer(ast.NodeVisitor):

    """Get set of all importable names from given `ast.Module`.

    >>> import ast
    >>> source = "source.py"
    >>> with open(source, "r") as sourcef:
    >>>     tree = ast.parse(sourcef.read())
    >>> analyzer = ImportablesAnalyzer(source)
    >>> analyzer.visit(tree)
    >>> importable_names = analyzer.get_stats()

    :param path: a file path that belongs to the given `ast.Module`.
    """

    @staticmethod
    @lru_cache()
    def handle_c_libs_importables(module_name: str, level: int) -> Set[str]:
        """Handle libs written in C or built-in CPython.

        :param module_name: `nodes/ast.ImportFrom.module`.
        :param level: `nodes/ast.ImportFrom.level`.
        :returns: set of importables.
        :raises ModuleNotFoundError: when we can't find the spec of the `module_name`
            and/or can't create the module.
        """
        dots = DOT * level if level else None
        spec = find_spec(module_name, dots)

        if spec:
            # Module `__init__.py`.
            module = spec.loader.create_module(spec)
            if module:
                return set(dir(module))

            # File `foo.py`.
            module = import_module(module_name)
            if module:
                return set(dir(module))

        raise ModuleNotFoundError(name=module_name)

    def __init__(self, path: Path, *args, **kwargs):
        super(ImportablesAnalyzer, self).__init__(*args, **kwargs)
        self._not_importables: Set[ast.Name] = set()
        self._importables: Set[str] = set()
        self._has_all = False
        self._path = path

    @recursive
    def visit_Assign(self, node: ast.Assign):
        # Support `__all__` dunder overriding case.
        if getattr(node.targets[0], ID, None) == __ALL__:
            if isinstance(node.value, (ast.List, ast.Tuple, ast.Set)):
                self._has_all = True
                self._importables.clear()
                for constant in node.value.elts:
                    if PY38_PLUS:
                        if isinstance(constant.value, str):
                            self._importables.add(constant.value)
                    else:
                        if isinstance(constant.s, str):
                            self._importables.add(constant.s)

    @recursive
    def visit_Import(self, node: ast.Import):
        # Analyze each import statement.
        for alias in node.names:
            name = alias.asname if alias.asname else alias.name
            self._importables.add(name)

    @recursive
    def visit_ImportFrom(self, node: ast.ImportFrom):
        # Analyze each importFrom statement.
        try:
            if node.names[0].name == STAR:
                # Expand import star if possible.
                node = expand_import_star(node, self._path)
            for alias in node.names:
                name = alias.asname if alias.asname else alias.name
                self._importables.add(name)
        except UnexpandableImportStar:
            # * We shouldn't do anything because it's not importable.
            pass

    @recursive
    def visit_FunctionDef(self, node: ast.FunctionDef):
        # Add function name as importable name.
        self._importables.add(node.name)

        # Compute function not-importables.
        for node_ in ast.iter_child_nodes(node):

            if isinstance(node_, ast.Assign):

                for target in node_.targets:
                    self._not_importables.add(target)

    @recursive
    def visit_ClassDef(self, node: ast.ClassDef):
        # Add class name as importable name.
        self._importables.add(node.name)

        # Compute class not-importables.
        for node_ in ast.iter_child_nodes(node):

            if isinstance(node_, ast.Assign):

                for target in node_.targets:
                    self._not_importables.add(target)

    @recursive
    def visit_Name(self, node: ast.Name):
        if isinstance(node.ctx, ast.Store):
            # Except not-importables.
            if node not in self._not_importables:
                self._importables.add(node.id)

    def get_stats(self) -> Set[str]:
        return self._importables

    def generic_visit(self, node):
        """Called if no explicit visitor function exists for a node
        (override)."""
        # Continue visiting if only if `__all__` has not overridden.
        if not self._has_all:
            for field, value in ast.iter_fields(node):
                if isinstance(value, list):
                    for item in value:
                        if isinstance(item, ast.AST):
                            self.visit(item)
                elif isinstance(value, ast.AST):
                    self.visit(value)


@unique
class HasSideEffects(Enum):
    YES = 1
    MAYBE = 0.5
    NO = 0
    NOT_MODULE = -1

    #: Just in case an exception has raised
    #: while parsing a file.
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
        self._not_side_effect: Set[ast.Call] = set()
        self._has_side_effects = HasSideEffects.NO

    @recursive
    def visit_FunctionDef(self, node: ast.FunctionDef):
        # Mark any call inside a function as not-side-effect.
        for node_ in ast.iter_child_nodes(node):
            if isinstance(node_, ast.Expr):
                if isinstance(node_.value, ast.Call):
                    self._not_side_effect.add(node_.value)

    @recursive
    def visit_ClassDef(self, node: ast.ClassDef):
        # Mark any call inside a class as not-side-effect.
        for node_ in ast.iter_child_nodes(node):
            if isinstance(node_, ast.Expr):
                if isinstance(node_.value, ast.Call):
                    self._not_side_effect.add(node_.value)

    @recursive
    def visit_Call(self, node: ast.Call):
        if node not in self._not_side_effect:
            self._has_side_effects = HasSideEffects.YES

    @recursive
    def visit_Import(self, node: ast.Import):
        self._has_side_effects = self._check_names(node.names)

    @recursive
    def visit_ImportFrom(self, node: ast.ImportFrom):
        packages = node.module.split(DOT) if node.module else []
        packages_aliases = [ast.alias(name=name, asname=None) for name in packages]
        self._has_side_effects = self._check_names(packages_aliases)
        if self._has_side_effects is HasSideEffects.NO:
            self._has_side_effects = self._check_names(node.names)

    def _check_names(self, names: List[ast.alias]) -> HasSideEffects:
        """Check if imported names has side effects or not.

        :param names: list of imported names.
        :returns: `HasSideEffects` value.
        """
        for alias in names:

            # All standard lib modules doesn't has side effects
            # except `pathu.IMPORTS_WITH_SIDE_EFFECTS`.
            if alias.name in pathu.get_standard_lib_names():
                continue

            # Known side effects.
            if alias.name in pathu.IMPORTS_WITH_SIDE_EFFECTS:
                return HasSideEffects.YES

            # [Here instead of doing that, we can make the analyzer
            # works recursively inside each not known import.
            return HasSideEffects.MAYBE
            # I choosed this way because it's almost %100 we will end
            # with a file that has side effects :-) ].

        return HasSideEffects.NO

    def has_side_effects(self) -> HasSideEffects:
        return self._has_side_effects

    def generic_visit(self, node):
        """Called if no explicit visitor function exists for a node
        (override)."""
        # Continue visiting if only if there's no know side effects.
        if self._has_side_effects is HasSideEffects.NO:
            for field, value in ast.iter_fields(node):
                if isinstance(value, list):
                    for item in value:
                        if isinstance(item, ast.AST):
                            self.visit(item)
                elif isinstance(value, ast.AST):
                    self.visit(value)


def expand_import_star(
    node: Union[ast.ImportFrom, nodes.ImportFrom], path: Path
) -> Union[ast.ImportFrom, nodes.ImportFrom]:
    """Expand import star statement, replace the `*` with a list of ast.alias.

    :param node: `nodes/ast.ImportFrom` node that has a '*' as `alias.name`.
    :param path: where the node has imported.
    :returns: expanded `nodes/ast.ImportFrom` (same input node type).
    :raises UnexpandableImportStar: when `ReadPermissionError`,
        `UnparsableFile` or `ModuleNotFoundError` raised.
    """
    mpath = pathu.get_import_from_path(path, STAR, node.module, node.level)

    importables: Set[str] = set()

    try:
        if mpath:
            content, _ = iou.safe_read(mpath, permissions=(os.R_OK,))
            tree = parse_ast(content, mpath)

            analyzer = ImportablesAnalyzer(mpath)
            analyzer.visit(tree)
            importables = analyzer.get_stats()
        else:
            importables = ImportablesAnalyzer.handle_c_libs_importables(
                node.module, node.level
            )
    except (ReadPermissionError, UnparsableFile, ModuleNotFoundError) as err:
        msg = (
            err
            if not isinstance(err, ModuleNotFoundError)
            else f"{err.name!r} module not found!"
        )
        if hasattr(node, "location"):
            location = node.location
        else:
            start = nodes.NodePosition(node.lineno, node.col_offset)
            end = nodes.NodePosition(node.end_lineno)
            location = nodes.NodeLocation(start, end)
        raise UnexpandableImportStar(path, location, msg)

    # Create `ast.alias` for each name.
    node.names.clear()
    for name in importables:
        node.names.append(ast.alias(name=name, asname=None))

    return node


def parse_ast(
    source_code: str, path: Union[Path, str], mode: str = "exec"
) -> ast.Module:
    """Parse the given `source_code` AST.

    :param source_code: python source code.
    :param path: `source_code` file path.
    :param mode: `ast.parse` mode.
    :returns: `ast.Module` (source code AST).
    :raises UnparsableFile: if the compiled source is invalid,
        or the source contains null bytes.
    """
    try:
        if PY38_PLUS:
            # Include type_comments when Python >=3.8.
            # For more information https://www.python.org/dev/peps/pep-0526/ .
            tree = ast.parse(source_code, mode=mode, type_comments=True)
        else:
            tree = ast.parse(source_code, mode=mode)
        return tree
    except (SyntaxError, ValueError, UnicodeError) as err:
        raise UnparsableFile(path, err)
