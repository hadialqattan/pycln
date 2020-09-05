"""
Pycln CST utility.
"""
from typing import List, Set, Union, Tuple

import libcst as cst

from .exceptions import UnsupportedCase

# Constants.
DOT = "."
PASS = "pass"
EMPTY = ""
SPACE = " "
NEW_LINE = "\n"
SEMICOLON = ";"
RIGHT_PAEENTHESIS = ")"


class ImportTransformer(cst.CSTTransformer):

    """Import statements transformer.

    :param used_names: set of all used names to keep.
    :param indentation: gap before the statement.
    :param multiline: is it a multi line statement.
    """

    def __init__(self, used_names: Set[str], indentation: str, multiline: bool):
        self.__used_names = used_names
        self.__indentation = indentation
        self.__multiline = multiline

    def __get_multiline_alias(self, alias: cst.ImportAlias) -> cst.ImportAlias:
        """Convert the given `alias` to multiline `alias`.

        :param alias: `cst.ImportAlias` to correct.
        :returns: multiline `cst.ImportAlias`.
        """
        return cst.ImportAlias(
            name=alias.name,
            asname=alias.asname,
            comma=cst.Comma(
                whitespace_after=cst.ParenthesizedWhitespace(
                    indent=True,
                    last_line=cst.SimpleWhitespace(
                        value=self.__indentation + (SPACE * 4),
                    ),
                ),
            ),
        )

    def __get_multiline_lpar(self) -> cst.LeftParen:
        """Get multiline `lpar`.

        :returns: multiline `cst.LeftParen`.
        """
        return cst.LeftParen(
            whitespace_after=cst.ParenthesizedWhitespace(
                last_line=cst.SimpleWhitespace(
                    value=self.__indentation + (SPACE * 4),
                ),
            )
        )

    def __get_multiline_rpar(
        self, rpar: cst.RightParen, force: bool = False
    ) -> cst.RightParen:
        """Convert the given `rpar` to multiline `rpar`.

        :param rpar: `cst.RightParen` to correct.
        :param force: force convert.
        :returns: multiline `cst.RightParen`.
        """
        if not self.__multiline and not force:
            return rpar
        return cst.RightParen(
            whitespace_before=cst.ParenthesizedWhitespace(
                indent=True,
                last_line=cst.SimpleWhitespace(
                    value=self.__indentation,
                ),
            )
        )

    def refactor_import_star(self, updated_node: cst.ImportFrom) -> cst.ImportFrom:
        """Add used import aliases to import star.

        :param updated_node: `cst.ImportFrom` node to refactor.
        :returns: refactored node.
        """
        if not self.__used_names:
            return cst.RemoveFromParent()

        multiline = len(self.__used_names) > 3
        used_aliases: List[cst.ImportAlias] = []
        for name in self.__used_names:
            if DOT in name:
                continue
            cst_alias = cst.ImportAlias(
                name=cst.Name(name),
                comma=cst.Comma(whitespace_after=cst.SimpleWhitespace(SPACE)),
            )
            if multiline:
                cst_alias = self.__get_multiline_alias(cst_alias)
            used_aliases.append(cst_alias)
        used_aliases[-1] = used_aliases[-1].with_changes(
            comma=cst.MaybeSentinel.DEFAULT
        )
        updated_node = updated_node.with_changes(names=used_aliases)
        if multiline:
            rpar = self.__get_multiline_rpar(updated_node.rpar, True)
            lpar = self.__get_multiline_lpar()
            updated_node = updated_node.with_changes(rpar=rpar, lpar=lpar)
        return updated_node

    def refactor_import(
        self, updated_node: Union[cst.Import, cst.ImportFrom]
    ) -> Union[cst.Import, cst.ImportFrom, cst.RemovalSentinel]:
        """Remove unused imports from the given `updated_node`.

        :param updated_node: `cst.Import` or `cst.ImportFrom` node to refactor.
        :returns: refactored node, or `cst.RemovalSentianel` if there's no used aliases.
        """
        if not self.__used_names:
            return cst.RemoveFromParent()
        # Normal import.
        used_aliases: List[cst.ImportAlias] = []
        for alias in updated_node.names:
            print(alias.name.value)
            if alias.name.value in self.__used_names:
                used_aliases.append(alias)
        used_aliases[-1] = used_aliases[-1].with_changes(
            comma=cst.MaybeSentinel.DEFAULT
        )
        rpar = self.__get_multiline_rpar(updated_node.rpar)
        return updated_node.with_changes(names=used_aliases, rpar=rpar)

    def leave_Import(
        self, original_node: cst.Import, updated_node: cst.Import
    ) -> Union[cst.Import, cst.RemovalSentinel]:
        return self.refactor_import(updated_node)

    def leave_ImportFrom(
        self, original_node: cst.ImportFrom, updated_node: cst.ImportFrom
    ) -> Union[cst.ImportFrom, cst.RemovalSentinel]:
        if isinstance(updated_node.names, cst.ImportStar):
            return self.refactor_import_star(updated_node)
        else:
            return self.refactor_import(updated_node)


def rebuild_import(
    import_stmnt: str,
    used_names: Set[str],
    source: str,
    location: Tuple[int, int],
) -> List[str]:
    """Rebuild the given `import_stmnt` based on `used_names` using `LibCST`.

    :param import_stmnt: source code of the import statement.
    :param used_names: set of all used names to keep.
    :param source: where `import_stats` has imported.
    :param location: tuple of `node.lineno` and `node.col_offset`.
    :returns: fixed import statement source code as list of lines.
    :raises cst.ParserSyntaxError: in some rare cases.
    :raises UnsupportedCase: in some rare cases.
    """
    if SEMICOLON in import_stmnt:
        msg = "import statements separated with ';'."
        raise UnsupportedCase(source, location, msg)

    # Remove `import_stmnt` indentation.
    stripped_stmnt = import_stmnt.lstrip(SPACE)
    indentation = SPACE * location[-1]
    multiline = stripped_stmnt.count(NEW_LINE) > 1

    # Remove unused aliases.
    import_transformer = ImportTransformer(used_names, indentation, multiline)
    import_tree = cst.parse_module(stripped_stmnt)  # May raise cst.ParserSyntaxError.
    fixed_import = import_tree.visit(import_transformer).code.splitlines(keepends=True)

    # Replace each removed import with a pass statement.
    if not fixed_import:
        return [f"{indentation}{PASS}{NEW_LINE}" if indentation else EMPTY]
    # Reinsert the removed indentation.
    fixed_import[0] = indentation + fixed_import[0]
    return fixed_import
