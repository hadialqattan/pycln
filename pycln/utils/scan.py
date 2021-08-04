"""Pycln source code AST analysis utility."""
import ast
import os
import sys
from dataclasses import dataclass
from enum import Enum, unique
from functools import wraps
from pathlib import Path
from typing import Any, Callable, List, Optional, Set, Tuple, TypeVar, Union, cast

from . import _nodes, iou, pathu
from ._exceptions import ReadPermissionError, UnexpandableImportStar, UnparsableFile

# Constants.
PY38_PLUS = sys.version_info >= (3, 8)
PY39_PLUS = sys.version_info >= (3, 9)
IMPORT_EXCEPTIONS = {"ImportError", "ImportWarning", "ModuleNotFoundError"}
__ALL__ = "__all__"
NAMES_TO_SKIP = frozenset(
    {
        "__name__",
        "__doc__",
        "__package__",
        "__loader__",
        "__spec__",
        "__build_class__",
        "__import__",
        __ALL__,
    }
)
SUBSCRIPT_TYPE_VARIABLE = frozenset(
    {
        "AbstractSet",
        "AsyncContextManager",
        "AsyncGenerator",
        "AsyncIterable",
        "AsyncIterator",
        "Awaitable",
        "ByteString",
        "Callable",
        "ChainMap",
        "ClassVar",
        "Collection",
        "Container",
        "ContextManager",
        "Coroutine",
        "Counter",
        "DefaultDict",
        "Deque",
        "Dict",
        "FrozenSet",
        "Generator",
        "IO",
        "ItemsView",
        "Iterable",
        "Iterator",
        "KeysView",
        "List",
        "Mapping",
        "MappingView",
        "Match",
        "MutableMapping",
        "MutableSequence",
        "MutableSet",
        "Optional",
        "Pattern",
        "Reversible",
        "Sequence",
        "Set",
        "SupportsRound",
        "Tuple",
        "Type",
        "Union",
        "ValuesView",
        # Python >=3.7:
        "Literal",
        # Python >=3.8:
        "OrderedDict",
        # Python >=3.9:
        "tuple",
        "list",
        "dict",
        "set",
        "frozenset",
        "type",
    }
)

# Custom types.
FunctionT = TypeVar("FunctionT", bound=Callable[..., Any])
FunctionDefT = TypeVar(
    "FunctionDefT", bound=Union[ast.FunctionDef, ast.AsyncFunctionDef]
)


def recursive(func: FunctionT) -> FunctionT:
    """decorator to make `ast.NodeVisitor` work recursive.

    :param func: `ast.NodeVisitor.visit_*` function.
    """

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        func(self, *args, **kwargs)
        self.generic_visit(*args)

    return cast(FunctionT, wrapper)


@dataclass
class ImportStats:

    """Import statements statistics."""

    import_: Set[_nodes.Import]
    from_: Set[_nodes.ImportFrom]

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

    def __init__(self, source_lines: Optional[List[str]] = None):
        if not PY38_PLUS and source_lines is None:
            # Bad class usage.
            raise ValueError("Please provide source lines for Python < 3.8.")
        self._lines = source_lines
        self._import_stats = ImportStats(set(), set())
        self._imports_to_skip: Set[Union[_nodes.Import, _nodes.ImportFrom]] = set()
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
            if not str(py38_node.module).startswith("__"):
                self._import_stats.from_.add(py38_node)

    @recursive
    def visit_Name(self, node: ast.Name):
        self._source_stats.name_.add(node.id)

    @recursive
    def visit_Attribute(self, node: ast.Attribute):
        self._source_stats.attr_.add(node.attr)

    @recursive
    def visit_Call(self, node: ast.Call):
        #: Support casting case.
        #: >>> from typing import cast
        #: >>> import xxx, yyy
        #: >>> zzz = cast("xxx", yyy)
        #: Issue: https://github.com/hadialqattan/pycln/issues/26
        func = node.func
        if getattr(func, "id", "") == "cast" or (
            getattr(func, "attr", "") == "cast"
            and getattr(func.value, "id", "") == "typing"  # type: ignore
        ):
            self._parse_string(node.args[0])  # type: ignore

    @recursive
    def visit_Subscript(self, node: ast.Subscript) -> None:
        #: Support semi string type hints.
        #: >>> from ast import Import
        #: >>> from typing import List
        #: >>> def foo(bar: List["Import"]):
        #: >>>     pass
        #: Issue: https://github.com/hadialqattan/pycln/issues/32
        value = getattr(node, "value", "")
        if getattr(value, "id", "") in SUBSCRIPT_TYPE_VARIABLE or (
            hasattr(value, "value") and getattr(value.value, "id", "") == "typing"
        ):
            if PY39_PLUS:
                s_val = node.slice  # type: ignore
            else:
                s_val = node.slice.value  # type: ignore
            for elt in getattr(s_val, "elts", ()) or (s_val,):
                try:
                    self._parse_string(elt)  # type: ignore
                except UnparsableFile:
                    #: Ignore errors when parsing Literal
                    #: that are not valid identifiers.
                    #:
                    #: >>> from typing import Literal
                    #: >>> L: Literal[" "] = " "
                    #:
                    #: Issue: https://github.com/hadialqattan/pycln/issues/41
                    pass

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

        def add_imports_to_skip(body: List[ast.stmt]) -> None:
            """Add all try/except/else blocks body import children to
            `self._imports_to_skip`.

            :param body: ast.List to iterate over.
            """
            for child in body:
                if hasattr(child, "names"):
                    self._imports_to_skip.add(child)  # type: ignore

        for handler in node.handlers:
            if hasattr(handler.type, "elts"):
                for name in getattr(handler.type, "elts", []):
                    if hasattr(name, "id") and name.id in IMPORT_EXCEPTIONS:
                        is_skip_case = True
                        break
            elif hasattr(handler.type, "id"):
                if getattr(handler.type, "id", "") in IMPORT_EXCEPTIONS:
                    is_skip_case = True
            if is_skip_case:
                add_imports_to_skip(handler.body)

        if is_skip_case:
            for body in (node.body, node.orelse):
                add_imports_to_skip(body)

    @recursive
    def visit_AnnAssign(self, node: ast.AnnAssign):
        #: Support string type annotations.
        #: >>> from typing import List
        #: >>> foo: "List[str]" = []
        self._visit_string_type_annotation(node)

    @recursive
    def visit_arg(self, node: ast.arg):
        # Support Python ^3.8 type comments.
        self._visit_type_comment(node)
        #: Support arg string type annotations.
        #: >>> from typing import Tuple
        #: >>> def foo(bar: "Tuple[str, int]"):
        #: ...     pass
        self._visit_string_type_annotation(node)

    @recursive
    def visit_FunctionDef(self, node: FunctionDefT):
        # Support Python ^3.8 type comments.
        self._visit_type_comment(node)
        #: Support string type annotations.
        #: >>> from typing import List
        #: >>> def foo() -> 'List[str]':
        #: >>>     pass
        self._visit_string_type_annotation(node)

    # Support `ast.AsyncFunctionDef`.
    visit_AsyncFunctionDef = visit_FunctionDef

    @recursive
    def visit_Assign(self, node: ast.Assign):
        # Support Python ^3.8 type comments.
        self._visit_type_comment(node)
        id_ = getattr(node.targets[0], "id", None)
        # These names will be skipped on import `*` case.
        if id_ in NAMES_TO_SKIP:
            self._source_stats.names_to_skip.add(id_)
        # Support `__all__` dunder overriding cases.
        if id_ == __ALL__:
            if isinstance(node.value, (ast.List, ast.Tuple, ast.Set)):
                #: Support normal `__all__` dunder overriding:
                #:
                #: >>> import x, y, z
                #: >>>
                #: >>> __all__ = ["x", "y", "z"]
                self._add_list_names(node.value.elts)
            elif isinstance(node.value, ast.BinOp):
                #: Support `__all__` dunder overriding with
                #: add (`+`) binary operator (concatenation):
                #:
                #: >>> import x, y, z, i, j
                #: >>>
                #: >>> __all__ = ["x"] + ["y", "z"] + ["i", "j"]
                #:
                #: Issue: https://github.com/hadialqattan/pycln/issues/28
                self._add_concatenated_list_names(node.value)

    @recursive
    def visit_AugAssign(self, node: ast.AugAssign):
        id_ = getattr(node.target, "id", None)
        # Support `__all__` with `+=` operator case.
        if id_ == __ALL__:
            if isinstance(node.value, (ast.List, ast.Tuple, ast.Set)):
                #: Support `__all__` dunder overriding with
                #: only `+=` operator:
                #:
                #: >>> import x, y, z
                #: >>>
                #: >>> __all__ += ["x", "y", "z"]
                self._add_list_names(node.value.elts)
            elif isinstance(node.value, ast.BinOp):
                #: Support `__all__` dunder overriding with
                #: both `+=` and `+` operators:
                #:
                #: >>> import x, y, z
                #: >>>
                #: >>> __all__ += ["x", "y"] + ["z"]
                self._add_concatenated_list_names(node.value)

    @recursive
    def visit_Expr(self, node: ast.Expr):
        #: Support `__all__` dunder overriding with
        #: `append` and `extend` operations:
        #:
        #: >>> import x, y, z
        #: >>>
        #: >>> __all__ = ["x"]
        #: >>> __all__.append("y")
        #: >>> __all__.extend(["z"])
        #:
        #: Issue: https://github.com/hadialqattan/pycln/issues/29
        node_value = node.value
        if (
            isinstance(node_value, ast.Call)
            and isinstance(node_value.func, ast.Attribute)
            and isinstance(node_value.func.value, ast.Name)
            and node_value.func.value.id == __ALL__
        ):
            func_attr = node_value.func.attr
            if func_attr == "append":
                self._add_list_names(node_value.args)
            elif func_attr == "extend":
                for arg in node_value.args:
                    if isinstance(arg, ast.List):
                        self._add_list_names(arg.elts)

    def _visit_string_type_annotation(
        self, node: Union[ast.AnnAssign, ast.arg, FunctionDefT]
    ) -> None:
        # Support string type annotations.
        if isinstance(node, (ast.AnnAssign, ast.arg)):
            annotation = node.annotation
        else:
            annotation = node.returns
        self._parse_string(annotation)  # type: ignore

    def _visit_type_comment(
        self, node: Union[ast.Assign, ast.arg, FunctionDefT]
    ) -> None:
        #: Support Python ^3.8 type comments.
        #:
        #: This feature is only available for Python ^3.8.
        #: PEP 526 -- Syntax for Variable Annotations.
        #: For more information:
        #:     - https://www.python.org/dev/peps/pep-0526/
        #:     - https://docs.python.org/3.8/library/ast.html#ast.parse
        type_comment = getattr(node, "type_comment", None)
        if type_comment:
            if isinstance(node, (ast.Assign, ast.arg)):
                mode = "eval"
            else:
                mode = "func_type"
            try:
                tree = parse_ast(type_comment, mode=mode)
                self._add_name_attr(tree)
            except UnparsableFile:
                #: Ignore errors when it's not a valid type comment.
                #:
                #: Sometimes we find nodes (comments)
                #: satisfy PIP-526 type comment rules, but they're not valid.
                #:
                #: Issue: https://github.com/hadialqattan/pycln/issues/58
                pass

    def _parse_string(self, node: Union[ast.Constant, ast.Str]) -> None:
        # Parse string names/attrs.
        if isinstance(node, (ast.Constant, ast.Str)):
            val = getattr(node, "value", "") or getattr(node, "s", "")
            if val and isinstance(val, str):
                tree = parse_ast(val, mode="eval")
                self._add_name_attr(tree)

    def _add_concatenated_list_names(self, node: ast.BinOp) -> None:
        #: Safely add `["x", "y"] + ["i", "j"]`
        #: `const/str` names to `self._source_stats.name_`.
        if isinstance(node.right, (ast.List, ast.Tuple, ast.Set)):
            self._add_list_names(node.right.elts)
        if isinstance(node.left, (ast.List, ast.Tuple, ast.Set)):
            self._add_list_names(node.left.elts)
        elif isinstance(node.left, ast.BinOp):
            self._add_concatenated_list_names(node.left)

    def _add_list_names(self, node: List[ast.expr]) -> None:
        # Safely add list `const/str` names to `self._source_stats.name_`.
        for item in node:
            if isinstance(item, (ast.Constant, ast.Str)):
                key = "s" if hasattr(item, "s") else "value"
                value = getattr(item, key, "")
                if value and isinstance(value, str):
                    self._source_stats.name_.add(value)

    def _add_name_attr(self, tree: ast.AST):
        # Add any `ast.Name` or `ast.Attribute`
        # child to `self._source_stats`.
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                self._source_stats.name_.add(node.id)
            elif isinstance(node, ast.Attribute):
                self._source_stats.attr_.add(node.attr)

    def _get_py38_import_node(self, node: ast.Import) -> _nodes.Import:
        # Convert any Python < 3.8 `ast.Import`
        # to `_nodes.Import` in order to support `end_lineno`.
        if hasattr(node, "end_lineno"):
            end_lineno = node.end_lineno
        else:
            line = self._lines[node.lineno - 1]
            multiline = SourceAnalyzer._is_parentheses(line) is not None
            end_lineno = node.lineno + (1 if multiline else 0)
        location = _nodes.NodeLocation((node.lineno, node.col_offset), end_lineno)
        return _nodes.Import(location=location, names=node.names)

    def _get_py38_import_from_node(self, node: ast.ImportFrom) -> _nodes.ImportFrom:
        # Convert any Python < 3.8 `ast.ImportFrom`
        # to `_nodes.ImportFrom` in order to support `end_lineno`.
        if hasattr(node, "end_lineno"):
            end_lineno = node.end_lineno
        else:
            line = self._lines[node.lineno - 1]
            is_parentheses = SourceAnalyzer._is_parentheses(line)
            multiline = is_parentheses is not None
            end_lineno = (
                node.lineno
                if not multiline
                else self._get_end_lineno(node.lineno, is_parentheses)
            )
        location = _nodes.NodeLocation((node.lineno, node.col_offset), end_lineno)
        return _nodes.ImportFrom(
            location=location,
            names=node.names,
            module=node.module,
            level=node.level,
        )

    @staticmethod
    def _is_parentheses(import_from_line: str) -> Optional[bool]:
        # Return importFrom multi-line type.
        # ('(' => True), ('\\' => False) else None.
        if "(" in import_from_line:
            return True
        elif "\\" in import_from_line:
            return False
        else:
            return None

    def _get_end_lineno(self, lineno: int, is_parentheses: bool) -> int:
        # Get `ast.ImportFrom` `end_lineno` of the given `lineno`.
        lines_len = len(self._lines)
        for end_lineno in range(lineno, lines_len):
            if is_parentheses:
                if ")" in self._lines[end_lineno]:
                    end_lineno += 1
                    break
            else:
                if "\\" not in self._lines[end_lineno]:
                    end_lineno += 1
                    break
        return end_lineno

    def get_stats(self) -> Tuple[SourceStats, ImportStats]:
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

    def __init__(self, path: Path):
        self._not_importables: Set[Union[ast.Name, str]] = set()
        self._importables: Set[str] = set()
        self._has_all = False
        self._path = path

    @recursive
    def visit_Assign(self, node: ast.Assign):
        id_ = getattr(node.targets[0], "id", None)
        # Support `__all__` dunder overriding cases.
        if id_ == __ALL__:
            self._has_all = True
            self._importables.clear()
            if isinstance(node.value, (ast.List, ast.Tuple, ast.Set)):
                #: Support normal `__all__` dunder overriding:
                #:
                #: >>> import x, y, z
                #: >>>
                #: >>> __all__ = ["x", "y", "z"]
                self._add_list_names(node.value.elts)
            elif isinstance(node.value, ast.BinOp):
                #: Support `__all__` dunder overriding with
                #: add (`+`) binary operator (concatenation):
                #:
                #: >>> import x, y, z, i, j
                #: >>>
                #: >>> __all__ = ["x"] + ["y", "z"] + ["i", "j"]
                #:
                #: Issue: https://github.com/hadialqattan/pycln/issues/28
                self._add_concatenated_list_names(node.value)

    @recursive
    def visit_AugAssign(self, node: ast.AugAssign):
        id_ = getattr(node.target, "id", None)
        # Support `__all__` with `+=` operator case.
        if id_ == __ALL__:
            self._has_all = True
            if isinstance(node.value, (ast.List, ast.Tuple, ast.Set)):
                #: Support `__all__` dunder overriding with
                #: only `+=` operator:
                #:
                #: >>> import x, y, z
                #: >>>
                #: >>> __all__ += ["x", "y", "z"]
                self._add_list_names(node.value.elts)
            elif isinstance(node.value, ast.BinOp):
                #: Support `__all__` dunder overriding with
                #: both `+=` and `+` operators:
                #:
                #: >>> import x, y, z
                #: >>>
                #: >>> __all__ += ["x", "y"] + ["z"]
                self._add_concatenated_list_names(node.value)

    @recursive
    def visit_Expr(self, node: ast.Expr):
        #: Support `__all__` dunder overriding with
        #: `append` and `extend` operations:
        #:
        #: >>> import x, y, z
        #: >>>
        #: >>> __all__ = ["x"]
        #: >>> __all__.append("y")
        #: >>> __all__.extend(["z"])
        #:
        #: Issue: https://github.com/hadialqattan/pycln/issues/29
        node_value = node.value
        if (
            isinstance(node_value, ast.Call)
            and isinstance(node_value.func, ast.Attribute)
            and isinstance(node_value.func.value, ast.Name)
            and node_value.func.value.id == __ALL__
        ):
            func_attr = node_value.func.attr
            if func_attr == "append":
                self._add_list_names(node_value.args)
            elif func_attr == "extend":
                for arg in node_value.args:
                    if isinstance(arg, ast.List):
                        self._add_list_names(arg.elts)

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
            if node.names[0].name == "*":
                # Expand import star if possible.
                node = cast(ast.ImportFrom, expand_import_star(node, self._path))
            for alias in node.names:
                name = alias.asname if alias.asname else alias.name
                self._importables.add(name)
        except UnexpandableImportStar:  # pragma: no cover
            # * We shouldn't do anything because it's not importable.
            pass  # pragma: no cover

    @recursive
    def visit_FunctionDef(self, node: FunctionDefT):
        # Add function name as importable name.
        if node.name not in self._not_importables:
            self._importables.add(node.name)
        self._compute_not_importables(node)

    # Support `ast.AsyncFunctionDef`.
    visit_AsyncFunctionDef = visit_FunctionDef

    @recursive
    def visit_ClassDef(self, node: ast.ClassDef):
        # Add class name as importable name.
        if node.name not in self._not_importables:
            self._importables.add(node.name)
        self._compute_not_importables(node)

    @recursive
    def visit_Name(self, node: ast.Name):
        if isinstance(node.ctx, ast.Store):
            # Except not-importables.
            if node not in self._not_importables:
                self._importables.add(node.id)

    def _add_concatenated_list_names(self, node: ast.BinOp) -> None:
        #: Safely add `["x", "y"] + ["i", "j"]`
        #: `const/str` names to `self._importables`.
        if isinstance(node.right, (ast.List, ast.Tuple, ast.Set)):
            self._add_list_names(node.right.elts)
        if isinstance(node.left, (ast.List, ast.Tuple, ast.Set)):
            self._add_list_names(node.left.elts)
        elif isinstance(node.left, ast.BinOp):
            self._add_concatenated_list_names(node.left)

    def _add_list_names(self, node: List[ast.expr]) -> None:
        # Safely add list `const/str` names to `self._importables`.
        for item in node:
            if isinstance(item, (ast.Constant, ast.Str)):
                key = "s" if hasattr(item, "s") else "value"
                value = getattr(item, key, "")
                if value and isinstance(value, str):
                    self._importables.add(value)

    def _compute_not_importables(self, node: Union[FunctionDefT, ast.ClassDef]):
        # Compute class/function not-importables.
        for node_ in ast.iter_child_nodes(node):

            if isinstance(node_, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                self._not_importables.add(cast(str, node_.name))

            if isinstance(node_, ast.Assign):
                for target in node_.targets:
                    self._not_importables.add(cast(ast.Name, target))

    def get_stats(self) -> Set[str]:
        if self._path.name == "__init__.py":
            for path in os.listdir(self._path.parent):
                file_path = self._path.parent.joinpath(path)
                if file_path.is_dir() or path.endswith(".py"):
                    self._importables.add(path.split(".")[0])
        return self._importables

    def generic_visit(self, node):
        """Called if no explicit visitor function exists for a node
        (override)."""
        # Continue visiting if only if `__all__` has not overridden.
        if (not self._has_all) or isinstance(node, ast.AugAssign):
            for _, value in ast.iter_fields(node):
                if isinstance(value, list):
                    for item in value:
                        if isinstance(item, ast.AST):
                            self.visit(item)
                elif isinstance(value, ast.AST):
                    self.visit(value)


@unique
class HasSideEffects(Enum):
    """SideEffects values."""

    YES = 1
    MAYBE = 0.5
    NO = 0

    #: Some names aren't modules.
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

    def __init__(self):
        self._not_side_effects: Set[ast.Call] = set()
        self._has_side_effects = HasSideEffects.NO

    @recursive
    def visit_FunctionDef(self, node: FunctionDefT):
        # Mark any call inside a function as not-side-effect.
        self._compute_not_side_effects(node)

    # Support `ast.AsyncFunctionDef`.
    visit_AsyncFunctionDef = visit_FunctionDef

    @recursive
    def visit_ClassDef(self, node: ast.ClassDef):
        # Mark any call inside a class as not-side-effect.
        self._compute_not_side_effects(node)

    def _compute_not_side_effects(
        self, node: Union[ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef]
    ) -> None:
        # Mark any call inside the given `node` as not-side-effect.
        for node_ in ast.iter_child_nodes(node):
            if isinstance(node_, ast.Expr):
                if isinstance(node_.value, ast.Call):
                    self._not_side_effects.add(node_.value)

    @recursive
    def visit_Call(self, node: ast.Call):
        if node not in self._not_side_effects:
            self._has_side_effects = HasSideEffects.YES

    @recursive
    def visit_Import(self, node: ast.Import):
        self._has_side_effects = SideEffectsAnalyzer._check_names(node.names)

    @recursive
    def visit_ImportFrom(self, node: ast.ImportFrom):
        packages = node.module.split(".") if node.module else []
        packages_aliases = [ast.alias(name=name, asname=None) for name in packages]
        self._has_side_effects = SideEffectsAnalyzer._check_names(packages_aliases)
        if self._has_side_effects is HasSideEffects.NO:
            self._has_side_effects = SideEffectsAnalyzer._check_names(node.names)

    @staticmethod
    def _check_names(names: List[ast.alias]) -> HasSideEffects:
        # Check if imported names has side effects or not.
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
            for _, value in ast.iter_fields(node):
                if isinstance(value, list):
                    for item in value:
                        if isinstance(item, ast.AST):
                            self.visit(item)
                elif isinstance(value, ast.AST):
                    self.visit(value)


def expand_import_star(
    node: Union[ast.ImportFrom, _nodes.ImportFrom], path: Path
) -> Union[ast.ImportFrom, _nodes.ImportFrom]:
    """Expand import star statement, replace the `*` with a list of ast.alias.

    :param node: `_nodes/ast.ImportFrom` node that has a '*' as `alias.name`.
    :param path: where the node has imported.
    :returns: expanded `_nodes/ast.ImportFrom` (same input node type).
    :raises UnexpandableImportStar: when `ReadPermissionError`,
        `UnparsableFile` or `ModuleNotFoundError` raised.
    """
    mpath = pathu.get_import_from_path(path, "*", node.module, node.level)

    importables: Set[str] = set()

    try:
        if mpath:
            content, _, _ = iou.safe_read(mpath, permissions=(os.R_OK,))
            tree = parse_ast(content, mpath)

            analyzer = ImportablesAnalyzer(mpath)
            analyzer.visit(tree)
            importables = analyzer.get_stats()
        else:
            name = ("." * node.level) + (node.module if node.module else "")
            raise ModuleNotFoundError(name=name)
    except (ReadPermissionError, UnparsableFile, ModuleNotFoundError) as err:
        msg = (
            err
            if not isinstance(err, ModuleNotFoundError)
            else f"{err.name!r} module not found or it's a C wrapped module!"
        )
        if hasattr(node, "location"):
            location = node.location  # type: ignore # pragma: nocover.
        else:
            location = _nodes.NodeLocation(
                (node.lineno, node.col_offset), 0  # type: ignore
            )
        raise UnexpandableImportStar(path, location, str(msg)) from err

    # Create `ast.alias` for each name.
    node.names.clear()
    for name in importables:
        node.names.append(ast.alias(name=name, asname=None))

    return node


def parse_ast(source_code: str, path: Path = Path(""), mode: str = "exec") -> ast.AST:
    """Parse the given `source_code` AST.

    :param source_code: python source code.
    :param path: `source_code` file path.
    :param mode: `ast.parse` mode.
    :returns: `ast.AST` (source code AST).
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
    except (SyntaxError, IndentationError, ValueError) as err:
        raise UnparsableFile(path, err) from err
