"""Pycln CST transforming utility."""
from pathlib import Path
from typing import List, Optional, Set, TypeVar, Union, cast

import libcst as cst

from ._exceptions import UnsupportedCase
from ._nodes import NodeLocation

# Constants.
SPACE4 = " " * 4

# Custom types.
ImportT = TypeVar("ImportT", bound=Union[cst.Import, cst.ImportFrom])


class ImportTransformer(cst.CSTTransformer):

    """Import statements transformer.

    :param used_names: set of all used names to keep.
    :param location: `NodeLocation`.
    """

    def __init__(self, used_names: Set[str], location: NodeLocation):
        if not used_names:
            # Bad class usage.
            raise ValueError("'used_names' parameter can't be empty set.")
        self._used_names = used_names
        self._location = location
        self._indentation = " " * location.start.col

    def refactor_import_star(self, updated_node: cst.ImportFrom) -> cst.ImportFrom:
        """Add used import aliases to import star.

        :param updated_node: `cst.ImportFrom` node to refactor.
        :returns: refactored node.
        """
        is_multiline = len(self._used_names) > 3
        used_aliases: List[cst.ImportAlias] = []
        for name in self._used_names:

            # Skip any dotted name in order
            # to avoid names collision.
            if "." in name:
                continue

            # Initialy create a single line alias.
            cst_alias = cst.ImportAlias(
                name=cst.Name(name),
                comma=cst.Comma(whitespace_after=cst.SimpleWhitespace(" ")),
            )

            # Convert the single line alias to multiline
            # if there're more than 3 used names.
            if is_multiline:
                cst_alias = self._multiline_alias(cst_alias)

            used_aliases.append(cst_alias)

        return self._stylize(updated_node, used_aliases, is_multiline)

    def refactor_import(self, updated_node: ImportT) -> ImportT:
        """Remove unused imports from the given `updated_node`.

        :param updated_node: `cst.Import` or `cst.ImportFrom` node to refactor.
        :returns: refactored node.
        """
        used_aliases: List[cst.ImportAlias] = []
        for alias in updated_node.names:  # type: ignore
            if self._get_alias_name(alias.name) in self._used_names:
                used_aliases.append(alias)
        return self._stylize(updated_node, used_aliases)

    def leave_Import(  # pylint: disable=W0613
        self, original_node: cst.Import, updated_node: cst.Import
    ) -> Union[cst.Import]:
        return self.refactor_import(updated_node)

    def leave_ImportFrom(  # pylint: disable=W0613
        self, original_node: cst.ImportFrom, updated_node: cst.ImportFrom
    ) -> Union[cst.ImportFrom]:
        if isinstance(updated_node.names, cst.ImportStar):
            return self.refactor_import_star(updated_node)
        else:
            return self.refactor_import(updated_node)

    def _get_alias_name(
        self, node: Optional[Union[cst.Name, cst.Attribute]], name=""
    ) -> str:
        # Recursion function that calculates `node` string dotted name.
        if isinstance(node, cst.Name):
            name += node.value
            return name
        return self._get_alias_name(node.value) + "." + node.attr.value  # type: ignore

    @staticmethod
    def _multiline_parenthesized_whitespace(indent: str) -> cst.ParenthesizedWhitespace:
        # Return multiline parenthesized white space.
        return cst.ParenthesizedWhitespace(
            indent=True,
            last_line=cst.SimpleWhitespace(value=indent),
        )

    def _multiline_alias(self, alias: cst.ImportAlias) -> cst.ImportAlias:
        # Convert the given `alias` to multiline `alias`.
        return cst.ImportAlias(
            name=alias.name,
            asname=alias.asname,
            comma=cst.Comma(
                whitespace_after=ImportTransformer._multiline_parenthesized_whitespace(
                    self._indentation + SPACE4
                )
            ),
        )

    def _multiline_lpar(self) -> cst.LeftParen:
        # Return multiline `cst.LeftParen`.
        return cst.LeftParen(
            whitespace_after=ImportTransformer._multiline_parenthesized_whitespace(
                self._indentation + SPACE4
            )
        )

    def _multiline_rpar(self) -> cst.RightParen:
        # Return multiline `cst.RightParen`.
        return cst.RightParen(
            whitespace_before=ImportTransformer._multiline_parenthesized_whitespace(
                self._indentation
            )
        )

    def _stylize(
        self,
        node: ImportT,
        used_aliases: List[cst.ImportAlias],
        force_multiline: bool = False,
    ) -> ImportT:
        # (Preserving `node` style).
        # Remove the comma from the last name.
        used_aliases[-1] = used_aliases[-1].with_changes(
            comma=cst.MaybeSentinel.DEFAULT
        )
        node = cast(ImportT, node.with_changes(names=used_aliases))
        # Preserving multiline nodes style.
        if isinstance(node, cst.ImportFrom):
            if force_multiline or (node.rpar and len(self._location) != 1):
                rpar, lpar = self._multiline_rpar(), self._multiline_lpar()
                node = cast(ImportT, node.with_changes(rpar=rpar, lpar=lpar))
        return node


def rebuild_import(
    import_stmnt: str,
    used_names: Set[str],
    path: Path,
    location: NodeLocation,
) -> List[str]:
    """Rebuild the given `import_stmnt` based on `used_names` using `LibCST`.

    :param import_stmnt: source code of the import statement.
    :param used_names: set of all used names to keep.
    :param path: where `import_stats` has imported.
    :param location: `NodeLocation`.
    :returns: fixed import statement source code as list of lines.
    :raises cst.ParserSyntaxError: in some rare cases.
    :raises UnsupportedCase: in some rare cases.
    """
    if ";" in import_stmnt:
        msg = "import statements separated with ';'."
        raise UnsupportedCase(path, location, msg)

    # Remove `import_stmnt` indentation/last-"\n".
    stripped_stmnt = import_stmnt.lstrip(" ").rstrip("\n")
    indentation = " " * location.start.col

    # Remove unused aliases.
    fixed_lines: List[str] = []
    if used_names:
        transformer = ImportTransformer(used_names, location)
        cst_tree = cst.parse_module(stripped_stmnt)  # May raise cst.ParserSyntaxError.
        fixed_lines = cst_tree.visit(transformer).code.splitlines(keepends=True)

    if not fixed_lines:
        # Replace the removed import with a pass statement.
        fixed_lines = [f"{indentation}pass\n" if indentation else ""]
    else:
        # Reinsert the removed indentation.
        fixed_lines[0] = indentation + fixed_lines[0]

        # Reinsert the removed `"\n"`.
        fixed_lines[-1] = fixed_lines[-1] + "\n"

    return fixed_lines
