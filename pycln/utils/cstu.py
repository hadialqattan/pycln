"""
Pycln CST utility.
"""
from typing import Union, List, Set

from libcst import (
    Import,
    ImportFrom,
    ImportAlias,
    ImportStar,
    RemoveFromParent,
    RemovalSentinel,
    CSTTransformer,
    parse_module,
    MaybeSentinel,
    SimpleWhitespace,
    Name,
    Comma,
)

# Constants.
PASS = "pass"
EMPTY = ""
SPACE = " "
NEW_LINE = "\n"


class ImportTransformer(CSTTransformer):

    """Import statements transformer.

    :param used_names: set of all used names to keep.
    """

    def __init__(self, used_names: Set[str]):
        self.__used_names = used_names

    def refactor_import(
        self, updated_node: Union[Import, ImportFrom]
    ) -> Union[Import, ImportFrom, RemovalSentinel]:
        """Remove unused imports from the given `updated_node`.

        :param updated_node: `Import` or `ImportFrom` node to refactor.
        :returns: refactored node, or `RemovalSentianel` if there's no used aliases.
        """
        used_aliases: List[ImportAlias] = []
        if isinstance(updated_node.names, ImportStar):
            # Star import.
            for name in self.__used_names:
                cst_alias = ImportAlias(
                    name=Name(value=name),
                    comma=Comma(whitespace_after=SimpleWhitespace(SPACE)),
                )
                used_aliases.append(cst_alias)
        else:
            # Normal import.
            for alias in updated_node.names:
                if alias.name.value in self.__used_names:
                    used_aliases.append(alias)
        if not used_aliases:
            return RemoveFromParent()
        else:
            used_aliases[-1] = used_aliases[-1].with_changes(
                comma=MaybeSentinel.DEFAULT
            )
            return updated_node.with_changes(names=used_aliases)

    def leave_Import(
        self, original_node: Import, updated_node: Import
    ) -> Union[Import, RemovalSentinel]:
        return self.refactor_import(updated_node)

    def leave_ImportFrom(
        self, original_node: ImportFrom, updated_node: ImportFrom
    ) -> Union[ImportFrom, RemovalSentinel]:
        return self.refactor_import(updated_node)


def rebuild_import(import_stmnt: str, used_names: Set[str]) -> List[str]:
    """Rebuild the given `import_stmnt` based on `used_names` using `LibCST`.

    :param import_stmnt: source code of the import statement.
    :param used_names: set of all used names to keep.
    :returns: fixed import statement source code as list of lines.
    """
    # Remove `import_stmnt` indentation/end new_line.
    stripped_stmnt = import_stmnt.lstrip(SPACE).rstrip(NEW_LINE)
    indentation = SPACE * (len(import_stmnt) - (len(stripped_stmnt) + 1))

    # Remove unused aliases.
    import_transformer = ImportTransformer(used_names)
    import_tree = parse_module(stripped_stmnt)
    fixed_import = import_tree.visit(import_transformer).code.splitlines(keepends=True)

    # Replace each removed import with a pass statement.
    if not fixed_import:
        return f"{indentation}{PASS}{NEW_LINE}" if indentation else EMPTY

    # Reinsert the removed indentation/end new_line.
    fixed_import[0] = indentation + fixed_import[0] + NEW_LINE
    return fixed_import
