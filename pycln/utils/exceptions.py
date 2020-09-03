"""
Pycln exceptions utility.
"""
from typing import Union

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

    """Raises when the import `*` unexpandable."""

    def __init__(self, source: str, lineno: int, offset: int, msg: str):
        message = f"{source}:{lineno}:{offset} {self.__class__.__name__}: {msg}"
        super(UnexpandableImportStar, self).__init__(message)


class UnparsableFile(Exception):

    """Raises when the compiled source is invalid, or the source contains null bytes."""

    def __init__(
        self, source: str, exception: Union[SyntaxError, ValueError, UnicodeDecodeError]
    ):
        type_ = type(exception)

        if type_ not in {SyntaxError, ValueError, UnicodeDecodeError}:
            raise ValueError(
                f"UnparsableFile exception only takes SyntaxError, ValueError or UnicodeDecodeError as exception parameter but {type_!r} where given."
            )

        if type_ == SyntaxError:
            source = f"{source}:{exception.lineno}:{exception.offset}"
            postfix = SPACE + f"{exception.text.replace(NEW_LINE, EMPTY).lstrip()!r}"
        elif type_ == ValueError:
            postfix = EMPTY
        elif type_ == UnicodeDecodeError:
            encoding, object_ = exception.encoding, exception.object
            start, reason = exception.start, exception.reason
            setattr(
                exception,
                "msg",
                f"{encoding!r} codec can't decode {object_} in position {start}: {reason}",
            )
            postfix = EMPTY

        message = f"{source} {type_.__name__}: {exception.msg}{postfix}"
        super(UnparsableFile, self).__init__(message)


def rebuild_libcst_parser_syntax_error_message(
    source: str, err: "libcst.ParserSyntaxError"
) -> str:
    """Rebuild `LibCST.ParserSyntaxError` message.

    :param source: where the exception has occurred.
    :param err: instance of `LibCST.ParserSyntaxError`.
    :returns: rebuilt message.
    """
    location = f"{source}:{err.raw_line}:{err.raw_column}"
    postfix = SPACE + f"{err._lines[0].replace(NEW_LINE, EMPTY).lstrip()!r}"
    return f"{location} libcst.ParserSyntaxError: {err.message.rstrip(DOT)}:{postfix}"
