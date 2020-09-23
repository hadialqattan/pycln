"""Pycln custom exceptions utility."""
from pathlib import Path
from typing import Union

from ._nodes import NodeLocation


class BaseOSError(Exception):

    """Custom OSError."""

    def __init__(self, errno: int, strerror: str, filepath: Path):
        message = f"{filepath} {strerror} [Errno {errno}]"
        super().__init__(message)


class ReadPermissionError(BaseOSError):

    """Raises when the file does not have read permission."""


class WritePermissionError(BaseOSError):

    """Raises when the file does not have write permission."""


class UnexpandableImportStar(Exception):

    """Raises when the import `*` statement unexpandable."""

    def __init__(self, path: Path, location: NodeLocation, msg: str):
        line, col = location.start.line, location.start.col
        message = f"{path}:{line}:{col} {self.__class__.__name__}: {msg}"
        super().__init__(message)


class UnparsableFile(Exception):

    """Raises when the compiled source code is invalid, or the source code
    contains null bytes."""

    def __init__(
        self,
        path: Path,
        err: Union[SyntaxError, IndentationError, ValueError],
    ):
        location = str(path)
        postfix = ""
        type_ = type(err)
        UnparsableFile._type_check(type_)

        if type_ in {SyntaxError, IndentationError}:
            lineno, col, text = err.lineno, err.offset, err.text  # type: ignore
            if lineno:
                location = f"{path}:{lineno}:{col}"
            if text:
                text = text.replace("\n", "").lstrip()
                postfix = f" {text!r}"

        elif type_ == ValueError:
            setattr(err, "msg", str(err))

        msg = err.msg  # type: ignore
        message = f"{location} {type_.__name__}: {msg}{postfix}"
        super().__init__(message)

    @staticmethod
    def _type_check(type_: type) -> None:
        """Validate the given `exception` type.

        :param type_: err type.
        :raises ValueError: if `type_` not in allowed types.
        """
        allowed_types = {SyntaxError, IndentationError, ValueError}
        if type_ not in allowed_types:
            raise ValueError(  # pragma: nocover
                f"UnparsableFile exception only takes {allowed_types}"
                + f" as err parameter but {type_!r} where given."
            )


class UnsupportedCase(Exception):

    """Raises when unsupported import case detected."""

    def __init__(self, path: Path, location: NodeLocation, msg: str):
        line, col = location.start.line, location.start.col
        cls_name = self.__class__.__name__
        message = f"{path}:{line}:{col} {cls_name}: {msg}"
        super().__init__(message)


def libcst_parser_syntax_error_message(path: Path, err) -> str:
    """Refactor `LibCST.ParserSyntaxError` message.

    :param path: where the exception has occurred.
    :param err: instance of `LibCST.ParserSyntaxError`.
    :returns: refactored message.
    """
    location = f"{path}:{err.raw_line}:{err.raw_column}"
    line = err._lines[0].replace("\n", "").lstrip()
    postfix = f" {line!r}"
    return f"{location} libcst.ParserSyntaxError: {err.message.rstrip('.')}:{postfix}"
