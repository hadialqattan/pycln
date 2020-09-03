"""
Pycln CST utility.
"""
from typing import List, Set, Union
from pathlib import Path

import libcst as cst

from .exceptions import UnparsableFile

# Constants.
DOT = "."
PASS = "pass"
EMPTY = ""
SPACE = " "
NEW_LINE = "\n"
SEMICOLON = ";"


class ImportTransformer(cst.CSTTransformer):

    """Import statements transformer.

    :param used_names: set of all used names to keep.
    """

    def __init__(self, used_names: Set[str]):
        self.__used_names = used_names

    def refactor_import(
        self, updated_node: Union[cst.Import, cst.ImportFrom]
    ) -> Union[cst.Import, cst.ImportFrom, cst.RemovalSentinel]:
        """Remove unused imports from the given `updated_node`.

        :param updated_node: `cst.Import` or `cst.ImportFrom` node to refactor.
        :returns: refactored node, or `cst.RemovalSentianel` if there's no used aliases.
        """
        used_aliases: List[cst.ImportAlias] = []
        if isinstance(updated_node.names, cst.ImportStar):
            # Star import.
            for name in self.__used_names:
                if DOT in name:
                    continue
                cst_alias = cst.ImportAlias(
                    name=cst.Name(value=name),
                    comma=cst.Comma(whitespace_after=cst.SimpleWhitespace(SPACE)),
                )
                used_aliases.append(cst_alias)
        else:
            # Normal import.
            for alias in updated_node.names:
                if alias.name.value in self.__used_names:
                    used_aliases.append(alias)
        if not used_aliases:
            return cst.RemoveFromParent()
        else:
            used_aliases[-1] = used_aliases[-1].with_changes(
                comma=cst.MaybeSentinel.DEFAULT
            )
            return updated_node.with_changes(names=used_aliases)

    def leave_Import(
        self, original_node: cst.Import, updated_node: cst.Import
    ) -> Union[cst.Import, cst.RemovalSentinel]:
        return self.refactor_import(updated_node)

    def leave_ImportFrom(
        self, original_node: cst.ImportFrom, updated_node: cst.ImportFrom
    ) -> Union[cst.ImportFrom, cst.RemovalSentinel]:
        return self.refactor_import(updated_node)


def rebuild_import(import_stmnt: str, used_names: Set[str]) -> List[str]:
    """Rebuild the given `import_stmnt` based on `used_names` using `LibCST`.

    :param import_stmnt: source code of the import statement.
    :param used_names: set of all used names to keep.
    :returns: fixed import statement source code as list of lines.
    :raises cst.ParserSyntaxError: in some rare cases.
    """
    # Remove `import_stmnt` indentation/end new_line.
    stripped_stmnt = import_stmnt.lstrip(SPACE).rstrip(NEW_LINE)
    indentation = SPACE * (len(import_stmnt) - (len(stripped_stmnt) + 1))
    stripped_stmnt = stripped_stmnt.rstrip(SEMICOLON + SPACE)

    # Remove unused aliases.
    import_transformer = ImportTransformer(used_names)
    import_tree = cst.parse_module(stripped_stmnt)  # May raise cst.ParserSyntaxError.
    fixed_import = import_tree.visit(import_transformer).code.splitlines(keepends=True)

    # Replace each removed import with a pass statement.
    if not fixed_import:
        return [f"{indentation}{PASS}{NEW_LINE}" if indentation else EMPTY]

    # Reinsert the removed indentation/end new_line.
    fixed_import[0] = indentation + fixed_import[0]
    # Fix any missing new line.
    for i in (0, -1):
        if not fixed_import[i].endswith(NEW_LINE):
            fixed_import[i] += NEW_LINE

    return fixed_import
