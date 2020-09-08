"""Pycln custom exceptions utility."""
from typing import Union

from .nodes import NodeLocation

# Constants.
DOT = "."
EMPTY = ""
SPACE = " "
NEW_LINE = "\n"


class BaseOSError(Exception):

    """Custom OSError."""

    def __init__(self, errno: int, strerror: str, filepath: str):
        message = f"{filepath} {strerror} [Errno {errno}]"
        super(BaseOSError, self).__init__(message)


class ReadPermissionError(BaseOSError):

    """Raises when the file does not have read permission."""


class WritePermissionError(BaseOSError):

    """Raises when the file does not have write permission."""


class UnexpandableImportStar(Exception):

    """Raises when the import `*` statement unexpandable."""

    def __init__(self, path: str, location: NodeLocation, msg: str):
        line, col = location.start.line, location.start.col
        message = f"{path}:{line}:{col} {self.__class__.__name__}: {msg}"
        super(UnexpandableImportStar, self).__init__(message)


class UnparsableFile(Exception):

    """Raises when the compiled source code is invalid, or the source code
    contains null bytes."""

    def __init__(
        self,
        path: str,
        err: Union[SyntaxError, ValueError, UnicodeDecodeError],
    ):
        postfix = EMPTY
        type_ = type(err)
        UnparsableFile._type_check(type_)

        if type_ == SyntaxError:
            if err.lineno:
                path = f"{path}:{err.lineno}:{err.offset}"
            if err.text:
                postfix = f"{SPACE}{err.text.replace(NEW_LINE, EMPTY).lstrip()!r}"

        elif type_ == UnicodeEncodeError:
            start, reason = err.start, err.reason
            encoding, object_ = err.encoding, err.object
            if len(object_) > 10:
                object_ = object_[:11] + (DOT * 3)
            msg = (
                f"{encoding!r} codec can't decode {object_}"
                + f" in position {start}: {reason}"
            )
            setattr(err, "msg", msg)

        message = f"{path} {type_.__name__}: {err.msg}{postfix}"
        super(UnparsableFile, self).__init__(message)

    @staticmethod
    def _type_check(type_: type) -> None:
        """Validate the given `exception` type.

        :param type_: err type.
        :raises ValueError: if `type_` not in allowed types.
        """
        allowed_types = {SyntaxError, ValueError, UnicodeDecodeError}
        if type_ not in allowed_types:
            raise ValueError(
                f"UnparsableFile exception only takes {allowed_types}"
                + f" as err parameter but {type_!r} where given."
            )


class UnsupportedCase(Exception):

    """Raises when unsupported import case detected."""

    def __init__(self, path: str, location: NodeLocation, msg: str):
        line, col = location.start.line, location.start.col
        cls_name = self.__class__.__name__
        message = f"{path}:{line}:{col} {cls_name}: {msg}"
        super(UnsupportedCase, self).__init__(message)


def libcst_parser_syntax_error_message(path: str, err) -> str:
    """Refactor `LibCST.ParserSyntaxError` message.

    :param path: where the exception has occurred.
    :param err: instance of `LibCST.ParserSyntaxError`.
    :returns: refactored message.
    """
    location = f"{path}:{err.raw_line}:{err.raw_column}"
    postfix = SPACE + f"{err._lines[0].replace(NEW_LINE, EMPTY).lstrip()!r}"
    return f"{location} libcst.ParserSyntaxError: {err.message.rstrip(DOT)}:{postfix}"
