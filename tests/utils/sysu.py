"""System hacks utility."""

import os
import sys
from collections.abc import Generator
from contextlib import contextmanager
from enum import Enum, unique
from io import StringIO
from pathlib import Path
from tempfile import NamedTemporaryFile


@unique
class STD(Enum):
    """STD TYPES."""

    OUT = 0
    ERR = 1


@contextmanager
def std_redirect(type_: STD) -> Generator:
    """Redirect stdout/err to a variable.

    :param type_: `STD.OUT` or `STD.ERR`.
    :returns: Generator of `StringIO` represents `sys.stdout/stderr`.
    """
    std_capture = StringIO()
    if type_ is STD.OUT:
        default_std = sys.stdout
        sys.stdout = std_capture
    else:
        default_std = sys.stderr
        sys.stderr = std_capture
    yield std_capture
    if type_ is STD.OUT:
        sys.stdout = default_std
    else:
        sys.stderr = default_std


@contextmanager
def hide_sys_argv():
    """Hide `sys.argv`"""
    sys_argv = sys.argv.copy()
    sys.argv.clear()
    yield
    sys.argv = sys_argv


@contextmanager
def reopenable_temp_file(content: str) -> Generator:
    """Reopenable tempfile to support writing/reading to/from the opened
    tempfile (requiered for Windows OS).

    For more information: https://bit.ly/3cr0Qkl

    :param content: string content to write.
    :yields: tempfile path.
    """
    try:
        with NamedTemporaryFile(
            mode="w", suffix=".py", encoding="utf-8", delete=False
        ) as tmp:
            tmp_path = Path(tmp.name)
            tmp.write(content)
        yield tmp_path
    finally:
        os.unlink(tmp_path)


class Pass(Exception):
    """Raises to pass some tests."""
