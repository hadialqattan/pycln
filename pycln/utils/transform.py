"""
Pycln CST utility.
"""
from typing import List, Set, Union, Optional
from pathlib import Path

import libcst as cst

from .nodes import NodeLocation
from ._exceptions import UnsupportedCase

# Constants.
DOT = "."
PASS = "pass"
EMPTY = ""
SPACE = " "
SPACE4 = SPACE * 4
NEW_LINE = "\n"
SEMICOLON = ";"
RIGHT_PAEENTHESIS = ")"


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
        self._indentation = SPACE * location.start.col

    def _multiline_parenthesized_whitespace(self, indent: str) -> cst.ParenthesizedWhitespace:
        """Get multiline parenthesized white space.

        :param indent: indentation of the last line.
        :returns: multiline `cst.ParenthesizedWhitespace`
        """
        return cst.ParenthesizedWhitespace(
            indent=True,
            last_line=cst.SimpleWhitespace(value=indent),
        )

    def _multiline_alias(self, alias: cst.ImportAlias) -> cst.ImportAlias:
        """Convert the given `alias` to multiline `alias`.

        :param alias: `cst.ImportAlias` to correct.
        :returns: multiline `cst.ImportAlias`.
        """
        return cst.ImportAlias(
            name=alias.name,
            asname=alias.asname,
            comma=cst.Comma(
                whitespace_after=self._multiline_parenthesized_whitespace()
            ),
        )

    def _multiline_lpar(self) -> cst.LeftParen:
        """Get multiline `lpar`.

        :returns: multiline `cst.LeftParen`.
        """
        return cst.LeftParen(
            whitespace_after=self._multiline_parenthesized_whitespace(self._indentation + SPACE4)
        )

    def _multiline_rpar(self) -> cst.RightParen:
        """Get multiline `rpar`.

        :returns: multiline `cst.RightParen`.
        """
        return cst.RightParen(
            whitespace_before=self._multiline_parenthesized_whitespace(self._indentation)
        )

    def _get_alias_name(
        self, node: Optional[Union[cst.Name, cst.Attribute]], name: str = ""
    ) -> str:
        """Recursion function that calculates `node` string dotted name.

        :param node: `cst.Name` or `cst.Attribute`.
        :returns: dotted name.
        """
        if isinstance(node, cst.Name):
            name += node.value
            return name
        return self._get_alias_name(node.value) + DOT + node.attr.value

    def _stylize(
        self,
        node: Union[cst.Import, cst.ImportFrom],
        used_aliases: List[cst.ImportAlias],
        force_multiline: bool = False,
    ) -> Union[cst.Import, cst.ImportFrom]:
        """Preserving `node` style.

        :param node: `cst.Import` or `cst.ImportFrom` to stylize.
        :param used_aliases: list of `cst.ImportAlias`.
        :param force_multiline: make the node multiline.
        :returns: stylized node.
        """
        # Remove the comma from the last name.
        used_aliases[-1] = used_aliases[-1].with_changes(
            comma=cst.MaybeSentinel.DEFAULT
        )
        node = node.with_changes(names=used_aliases)
        # Preserving multiline nodes style.
        if isinstance(node, cst.ImportFrom):
            start, end = self._location.start.line, self._location.end.line
            if force_multiline or (node.rpar and start != end):
                rpar, lpar = self._multiline_rpar(), self._multiline_lpar()
                node = node.with_changes(rpar=rpar, lpar=lpar)
        return node

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
            if DOT in name:
                continue

            # Initialy create a single line alias.
            cst_alias = cst.ImportAlias(
                name=cst.Name(name),
                comma=cst.Comma(whitespace_after=cst.SimpleWhitespace(SPACE)),
            )

            # Convert the single line alias to multiline
            # if there're more than 3 used names.
            if is_multiline:
                cst_alias = self._multiline_alias(cst_alias)

            used_aliases.append(cst_alias)

        return self._stylize(updated_node, used_aliases, is_multiline)

    def refactor_import(
        self, updated_node: Union[cst.Import, cst.ImportFrom]
    ) -> Union[cst.Import, cst.ImportFrom]:
        """Remove unused imports from the given `updated_node`.

        :param updated_node: `cst.Import` or `cst.ImportFrom` node to refactor.
        :returns: refactored node, or `cst.RemovalSentianel` if there's no used aliases.
        """
        # Normal import.
        used_aliases: List[cst.ImportAlias] = []
        for alias in updated_node.names:
            if self._get_alias_name(alias.name) in self._used_names:
                used_aliases.append(alias)
        return self._stylize(updated_node, used_aliases)

    def leave_Import(
        self, original_node: cst.Import, updated_node: cst.Import
    ) -> Union[cst.Import]:
        return self.refactor_import(updated_node)

    def leave_ImportFrom(
        self, original_node: cst.ImportFrom, updated_node: cst.ImportFrom
    ) -> Union[cst.ImportFrom]:
        if isinstance(updated_node.names, cst.ImportStar):
            return self.refactor_import_star(updated_node)
        else:
            return self.refactor_import(updated_node)


def rebuild_import(
    import_stmnt: str,
    used_names: Set[str],
    path: Union[Path, str],
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
    if SEMICOLON in import_stmnt:
        msg = "import statements separated with ';'."
        raise UnsupportedCase(path, location, msg)

    # Remove `import_stmnt` indentation/last-NEW_LINE.
    stripped_stmnt = import_stmnt.lstrip(SPACE).rstrip(NEW_LINE)
    indentation = SPACE * location.start.col

    # Remove unused aliases.
    fixed_lines: List[str] = []
    if used_names:
        transformer = ImportTransformer(used_names, location)
        cst_tree = cst.parse_module(stripped_stmnt)  # May raise cst.ParserSyntaxError.
        fixed_lines = cst_tree.visit(transformer).code.splitlines(keepends=True)

    # Replace each removed import with a pass statement.
    if not fixed_lines:
        return [f"{indentation}{PASS}{NEW_LINE}" if indentation else EMPTY]

    # Reinsert the removed indentation.
    fixed_lines[0] = indentation + fixed_lines[0]

    # Reinsert the removed `NEW_LINE`.
    fixed_lines[-1] = fixed_lines[-1] + NEW_LINE

    return fixed_lines
