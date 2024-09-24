"""Pycln file IO utility."""
import io
import os
import sys
import tokenize
from pathlib import Path
from typing import List, Tuple

from ._exceptions import (
    InitFileDoesNotExistError,
    ReadPermissionError,
    UnparsableFile,
    WritePermissionError,
)

# Constants.
STDIN_FILE = Path("STDIN")
STDIN_NOTATION = Path("-")
FORM_FEED_CHAR = "\x0c"
CRLF = "\r\n"
LF = "\n"
__INIT__ = "__init__.py"

# Types
FileContent = str
Encoding = str
NewLine = str


def read_stdin() -> Tuple[FileContent, Encoding, NewLine]:
    """Read the content of STDIN with encoding and new line type detection.

    :returns: decoded source code, file encoding, and a newline.
    :raises UnparsableFile: If both a BOM and a cookie are present, but disagree.
        or some rare characters presented.
    """
    try:
        source_code_buf = io.BytesIO(sys.stdin.buffer.read())
        encoding, lines = tokenize.detect_encoding(source_code_buf.readline)
        if not lines:
            return "", encoding, LF

        newline = CRLF if CRLF.encode() == lines[0][-2:] else LF
        source_code_buf.seek(0)
        with io.TextIOWrapper(source_code_buf, encoding) as wrapper:
            source_code = wrapper.read()

        if FORM_FEED_CHAR in source_code:
            raise ValueError(
                "Pycln can not handle a file containing a form feed character (\\f)"
            )
        return source_code, encoding, newline
    except (SyntaxError, ValueError) as err:
        raise UnparsableFile(STDIN_FILE, err) from err


def safe_read(
    path: Path, permissions: tuple = (os.R_OK, os.W_OK)
) -> Tuple[FileContent, Encoding, NewLine]:
    """Read file content with encoding and new line type detection.

    :param path: `.py` file path.
    :returns: decoded source code, file encoding, and a newline.
    :raises ReadPermissionError: when `os.R_OK` in permissions
        and the source does not have read permission.
    :raises WritePermissionError: when `os.W_OK` in permissions
        and the source does not have write permission.
    :raises UnparsableFile: If both a BOM and a cookie are present, but disagree.
        or some rare characters presented.
    :raises InitFileDoesNotExistError: when `path` is a path to a non-existing
        `__init__.py` file.
    """
    # Check for a non-existing `__init__.py` file case.
    if str(path).endswith(__INIT__) and not path.exists():
        raise InitFileDoesNotExistError(2, "`__init__.py` file does not exist", path)

    # Check these permissions before openinig the file.
    for permission in permissions:
        if not os.access(path, permission):
            if permission is os.R_OK:
                raise ReadPermissionError(13, "Permission denied [READ]", path)
            elif permission is os.W_OK:
                raise WritePermissionError(13, "Permission denied [WRITE]", path)
    try:
        with tokenize.open(path) as stream:
            source_code = stream.read()
            encoding = stream.encoding
        if FORM_FEED_CHAR in source_code:
            raise ValueError(
                "Pycln can not handle a file containing a form feed character (\\f)"
            )
        with open(path, "rb") as f:
            newline = CRLF if CRLF.encode() == f.readline()[-2:] else LF
        return source_code, encoding, newline
    except (SyntaxError, ValueError) as err:
        raise UnparsableFile(path, err) from err


def safe_write(path: Path, fixed_lines: List[str], encoding: str, newline: str) -> None:
    """Write file content based on given `encoding`.

    :param path: `.py` file path.
    :param encoding: file encoding.
    :param fixed_lines: fixed source code lines.
    :param newline: output file's newline (CRFL | FL).
    :raises WritePermissionError: when `os.W_OK` in permissions
        and the source does not have write permission.
    """
    if not os.access(path, os.W_OK):
        raise WritePermissionError(13, "Permission denied [WRITE]", path)

    fixed_lines_newline = newline
    if fixed_lines:
        fixed_lines_newline = CRLF if CRLF == fixed_lines[0][-2:] else LF

    with open(path, mode="w", encoding=encoding, newline="") as destination:
        for line in fixed_lines:
            destination.write(line.replace(fixed_lines_newline, newline))
