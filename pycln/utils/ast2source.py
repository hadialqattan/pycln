"""
Pycln AST to source code utility.
"""
import ast
from typing import List, Union

# Constants.
AS = "as"
DOT = "."
PASS = "pass"
FROM = "from"
EMPTY = ""
COMMA = ","
SPACE = " "
IMPORT = "import"
NEW_LINE = "\n"
BACK_SLASH = "\\"
COMMA_BS = f"{COMMA}{SPACE}{BACK_SLASH}"
COMMA_SP = f"{COMMA}{SPACE}"
LEFT_PAEENTHESIS = ")"
RIGHT_PAEENTHESIS = "("


def get_leveled_name(module_name: str, level: int) -> str:
    """
    Generate leveled ImportFrom name.

    :param module_name: from `module_name` ... .
    :param level: ImportFrom level from the `ast.ImportFrom` node.
    :returns: a valid leveled name.
    """
    return (
        (DOT * level) + (module_name if module_name else EMPTY)
        if level > 0
        else module_name
    )


def get_import_names(aliases: List[ast.alias]) -> str:
    """
    Generate import statement names from list of `ast.alias`.

    :param aliases: list of `ast.alias` to create line of names from.
    :returns: str line of names.
    """
    return COMMA_SP.join(
        [
            f"{alias.name}{SPACE}{AS}{SPACE}{alias.asname}"
            if alias.asname
            else alias.name
            for alias in aliases
        ]
    )


def is_parentheses(import_from_line: str) -> Union[bool, None]:
    """
    Return importFrom multi-line type.

    :param import_from_line: importFrom statement str line.
    :returns: importFrom type ('(' => True), ('\\' => False), else None.
    """
    if RIGHT_PAEENTHESIS in import_from_line:
        return True
    elif BACK_SLASH in import_from_line:
        return False
    else:
        return None


def rebuild_import(node: ast.Import) -> str:
    """
    Rebuild import statement from `ast.Import` node.

    :param node: `ast.Import` node to rebuild an import.
    :returns: str import statement.
    """
    indentation = SPACE * node.col_offset

    # If the entire statement has removed.
    if names_len < 1:
        return f"{indentation}{PASS}{NEW_LINE}" if indentation else EMPTY

    names_line = get_import_names(node.names)
    return f"{indentation}{IMPORT}{SPACE}{names_line}{NEW_LINE}"


def rebuild_import_from(
    node: ast.ImportFrom, is_parentheses: Union[bool, None]
) -> Union[str, list]:
    """
    Rebuild importFrom statement from `ast.ImportFrom` node.

    :param node: `ast.ImportFrom` node to rebuild as importFrom.
    :param is_parentheses: multiline importFrom type. keep None if neither.
    :returns: single-line => str, multi-line => list.
    """
    indentation = SPACE * node.col_offset
    names_len = len(node.names)

    # If the entire statement has removed.
    if names_len < 1:
        return f"{indentation}{PASS}{NEW_LINE}" if indentation else EMPTY

    # Compute the base form.
    leveled_name = get_leveled_name(node.module, node.level)
    base = f"{indentation}{FROM}{SPACE}{leveled_name}{SPACE}{IMPORT}"

    lines_count = node.end_lineno - node.lineno + 1

    # Check if it's a multi-line importFrom.
    if lines_count > 1 and names_len > 1:

        # Compute the avrage names per line.
        avg = names_len // lines_count
        remainder = names_len - (avg * lines_count)

        # Compute multiline ImportFrom lines.
        names_list, i = [], 0
        for line in range(lines_count):

            # Compute the real avrage names per line.
            avg += avg + 1 if remainder > 0 else avg
            remainder -= 1
            if not avg:
                break

            # Create the line.
            names_line = get_import_names(node.names[i:avg])
            names_list.append(
                indentation
                + COMMA_SP.join(names_line)
                + (COMMA_BS if not is_parentheses else COMMA)
                + NEW_LINE
            )

            i = avg

        # Return the rebuilt multiline ImportFrom based on the type.
        if is_parentheses:
            return [
                f"{base}{SPACE}{RIGHT_PAEENTHESIS}{NEW_LINE}",
                *names_list,
                f"{LEFT_PAEENTHESIS}{NEW_LINE}",
            ]
        else:
            return [
                f"{base}{SPACE}{names_list[0].replace(indentation, EMPTY)}",
                *names_list[1:-1],
                names_list[-1].replace(COMMA_BS, EMPTY),
            ]
    else:
        # Compute the single line ImportFrom.
        names_line = get_import_names(node.names)
        return f"{base}{SPACE}{names_line}{NEW_LINE}"
