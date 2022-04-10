"""A modified version of some functions of `site.py`.

---

No upstream.

The original source code has been copied from the following commit:
    https://github.com/python/cpython/blob/4827483f47906fecee6b5d9097df2a69a293a85c/Lib/site.py

---

This was created to parse `.pth` files without executing any arbitrary code even if it starts with `import`.

---

All functions have been copied without any modification except `addpackage`.

---

Only relevant functions have been added to this file.
"""
import os
import sys


def makepath(*paths):
    dir = os.path.join(*paths)
    try:
        dir = os.path.abspath(dir)
    except OSError:
        pass
    return dir  #, os.path.normcase(dir)


def addpackage(sitedir, name):  #, known_paths):
    """Process a .pth file within the site-packages directory:

    For each line in the file, combine it with sitedir to a path and
    yield it.
    """
    fullname = os.path.join(sitedir, name)
    try:
        # f = io.TextIOWrapper(io.open_code(fullname))
        # change to the following code to make it compatible with Python3.6:
        f = open(fullname, "r")
    except OSError:
        return
    with f:
        for n, line in enumerate(f):
            if line.startswith("#"):
                continue
            if line.strip() == "":
                continue
            try:
                if line.startswith(("import ", "import\t")):
                    continue
                line = line.rstrip()
                dir = makepath(sitedir, line)
                if os.path.exists(dir):
                    yield dir
            except Exception:
                print(f"Error processing line {n + 1:d} of {fullname}:\n", file=sys.stderr)
                import traceback

                for record in traceback.format_exception(*sys.exc_info()):
                    for line in record.splitlines():
                        print("  " + line, file=sys.stderr)
                print("\nRemainder of file ignored", file=sys.stderr)
                break
