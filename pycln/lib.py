from os import *
from time import *


try:
    import try_import
except (ModuleNotFoundError, ImportError):
    import except_import
else:
    import else_import
finally:
    import finally_import


try:
    import dataclasses
except (ModuleNotFoundError, ImportError):
    pass

try:
    pass
except:
    pass

__all__ = ["path", "sleep", "Hello"]  # type: (str, str, str)


def function(a, b):
    # type: (str, int, str) -> str
    """
    R_OK
    W_OK
    path
    sleep
    abort
    abs
    altsep
    add_dll_directory
    chown
    chmod
    chroot
    """
    pass
