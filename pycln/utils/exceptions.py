"""
Pycln exceptions utility.
"""
from typing import Union

# Constants.
EMPTY = ""
SPACE = " "
NEW_LINE = "\n"


class BaseOSError(Exception):

    """Custom OSError."""

    def __init__(self, errno: int, strerror: str, filepath: str):
        message = f"{filepath} {strerror} [Errno {errno}]"
        super(BaseOSError, self).__init__(message)


class ReadPermissionError(BaseOSError):

    """Raised when the file does not have read permission."""


class WritePermissionError(BaseOSError):

    """Raised when the file does not have write permission."""


class UnexpandableImportStar(Exception):

    """Raised when the import `*` unexpandable."""

    def __init__(self, source: str, lineno: int, offset: int, msg: str):
        message = f"{source}:{lineno}:{offset} {self.__class__.__name__}: {msg}"
        super(UnexpandableImportStar, self).__init__(message)


class UnparsableFile(Exception):

    """Raised when the compiled source is invalid, or the source contains null bytes."""

    def __init__(self, source: str, exception: Union[SyntaxError, ValueError]):
        type_ = type(exception)

        if type_ not in (SyntaxError, ValueError):
            raise ValueError(
                f"UnparsableFile exception only takes SyntaxError or ValueError as exception parameter but {type_!r} where given."
            )

        source = (
            f"{source}:{exception.lineno}:{exception.offset}"
            if type_ == SyntaxError
            else source
        )
        postfix = (
            (SPACE + f"{exception.text.replace(NEW_LINE, EMPTY).lstrip()!r}")
            if type_ == SyntaxError
            else EMPTY
        )

        message = f"{source} {type_.__name__}: {exception.msg}{postfix}"
        super(UnparsableFile, self).__init__(message)
