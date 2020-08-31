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
LEFT_PARENTHESIS = ")"
RIGHT_PARENTHESIS = "("


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
    if RIGHT_PARENTHESIS in import_from_line:
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
    if len(node.names) < 1:
        return f"{indentation}{PASS}{NEW_LINE}" if indentation else EMPTY

    names_line = get_import_names(node.names)
    return f"{indentation}{IMPORT}{SPACE}{names_line}{NEW_LINE}"


def rebuild_import_from(
    node: ast.ImportFrom, is_parentheses: Union[bool, None], old_names_count: int
) -> Union[str, list]:
    """
    Rebuild importFrom statement from `ast.ImportFrom` node.

    :param node: `ast.ImportFrom` node to rebuild as importFrom.
    :param is_parentheses: multiline importFrom type. keep None if neither.
    :param old_names_count: unmodified node names count.
    :returns: single-line => str, multi-line => list.
    """
    indentation = SPACE * node.col_offset
    inner_indentation = indentation + (SPACE * 4)
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

        # Compute the actual lines count.
        lines_count -= 2 if is_parentheses else 0

        # Compute the avrage of the old node names per line.
        old_avg = old_names_count // lines_count
        old_remainder = old_names_count - (old_avg * lines_count)
        
        delta = old_names_count - names_len

        for i in range(delta):
            
            if delta < 1:
                break
            
            if old_remainder > 0:
                old_remainder -= 1
                delta -= 1
                continue
            
            if delta >= old_avg:
                delta -= old_avg
                lines_count -= 1

        # Compute the avrage names per line.
        avg = names_len // lines_count
        remainder = names_len - (avg * lines_count)

        print(old_avg, old_remainder, delta, avg, remainder)

        # Compute multiline ImportFrom lines.
        names_list, i = [], 0
        for line in range(lines_count):

            avg += 1 if remainder > 0 else 0
            remainder -= 1

            # Create the line.
            names_line = get_import_names(node.names[i:avg])
            print(names_line, i, avg)
            names_list.append(
                inner_indentation
                + names_line
                + (COMMA_BS if not is_parentheses else COMMA)
                + NEW_LINE
            )

            # Compute the real avrage names per line.
            i = avg
            avg += avg
            names_len -= 1
            if not names_len:
                break


        # Return the rebuilt multiline ImportFrom based on the type.
        if is_parentheses:
            return [
                f"{base}{SPACE}{RIGHT_PARENTHESIS}{NEW_LINE}",
                *names_list[0:-1],
                names_list[-1].rstrip(COMMA + NEW_LINE) + NEW_LINE,
                f"{LEFT_PARENTHESIS}{NEW_LINE}",
            ]
        else:
            return [
                f"{base}{SPACE}{names_list[0].replace(indentation, EMPTY)}",
                *names_list[0:-1],
                names_list[-1].rstrip(COMMA_BS + NEW_LINE) + NEW_LINE,
            ]
    else:
        # Compute the single line ImportFrom.
        names_line = get_import_names(node.names)
        return f"{base}{SPACE}{names_line}{NEW_LINE}"
