"""Pycln path finding utility."""
import os
import sys
from distutils import sysconfig
from functools import lru_cache
from pathlib import Path
from typing import Generator, List, Optional, Pattern, Set

from pathspec import PathSpec

from .. import ISWIN
from . import regexu
from .report import Report

# Constants.
EXCLUDE = "exclude"
INCLUDE = "include"
GITIGNORE = "gitignore"
PY_EXTENSION = ".py"
__INIT__ = "__init__.py"
LIB_DYNLOAD = "Lib" if ISWIN else "lib-dynload"
SITE_PACKAGES = "site-packages"
DIST_PACKAGES = "dist-packages"
LIB_PY_EXTENSIONS = ("so", "py", "pyc")
BIN_PY_EXTENSIONS = ("so", "egg-info", "nspkg.pth")
BIN_IMPORTS = {  # In case they are built into CPython.
    "io",
    "os",
    "sys",
    "grp",
    "pwd",
    "json",
    "math",
    "time",
    "parser",
    "string",
    "operator",
    "datetime",
    "multiprocessing",
}
IMPORTS_WITH_SIDE_EFFECTS = {"this", "antigravity", "rlcompleter"}


def yield_sources(
    path: Path,
    include: Pattern[str],
    exclude: Pattern[str],
    gitignore: PathSpec,
    reporter: Report,
) -> Generator:
    """Yields `.py` paths to handle. Walk throw path sub-directories/files
    recursively.

    :param path: A path to start searching from.
    :param include: regex pattern to be included.
    :param exclude: regex pattern to be excluded.
    :param gitignore: gitignore PathSpec object.
    :param reporter: a `report.Report` object.
    :returns: generator of `.py` files paths.
    """

    dirs: List[str] = []
    files: List[str] = []

    is_included, is_excluded = regexu.is_included, regexu.is_excluded

    if path.is_dir():
        root_dir = os.scandir(path)  # type: ignore
    else:
        root_dir = {path}  # type: ignore
        path = path.parent

    for entry in root_dir:

        # Skip symlinks.
        if entry.is_symlink():
            continue

        name = entry.name if entry.is_file() else f"{entry.name}/"
        entry_path = Path(os.path.join(path, name))

        # Compute exclusions.
        if is_excluded(name, exclude):
            reporter.ignored_path(entry_path, EXCLUDE)
            continue

        # Compute `.gitignore`.
        if gitignore.match_file(name):
            reporter.ignored_path(entry_path, GITIGNORE)
            continue

        # Directories.
        if entry.is_dir():
            dirs.append(name)
            continue

        # Files.
        if is_included(name, include):
            files.append(name)
        else:
            reporter.ignored_path(entry_path, INCLUDE)

    for name in files:
        yield Path(os.path.join(path, name))

    for dirname in dirs:

        child = Path(os.path.join(path, dirname))

        # If gitignore is None, gitignore usage is disabled, while a Falsey
        # gitignore is when the directory doesn't have a .gitignore file.
        yield from yield_sources(
            child,
            include,
            exclude,
            gitignore + regexu.get_gitignore(child) if gitignore is not None else None,
            reporter,
        )


@lru_cache()
def get_standard_lib_paths() -> Set[Path]:
    """Get paths to Python standard library modules.

    :returns: set of paths to Python standard library modules.
    """
    paths: Set[Path] = set()

    for is_plat_specific in [True, False]:

        # Get lib modules paths.
        lib_path = sysconfig.get_python_lib(
            standard_lib=True, plat_specific=is_plat_specific
        )

        for path in os.listdir(lib_path):
            paths.add(Path(os.path.join(lib_path, path)))

        # Get lib dynload modules paths, if exists.
        lib_dynload_path = os.path.join(lib_path, LIB_DYNLOAD)

        if os.path.isdir(lib_dynload_path):

            for path in os.listdir(lib_dynload_path):
                paths.add(Path(os.path.join(lib_dynload_path, path)))

    return paths


@lru_cache()
def get_standard_lib_names() -> Set[str]:
    """Returns a set of Python standard library modules names.

    :returns: a set of Python standard library modules names.
    """
    names: Set[str] = set()
    paths: Set[Path] = get_standard_lib_paths()

    for path in paths:

        name = str(path.parts[-1])

        if name.startswith("_") or "-" in name:
            continue

        if "." in name and not name.endswith(LIB_PY_EXTENSIONS):
            continue

        names.add(name.split(".")[0])

    return (names - IMPORTS_WITH_SIDE_EFFECTS) | BIN_IMPORTS


@lru_cache()
def get_third_party_lib_paths() -> Set[Path]:
    """Get paths to third party library modules.

    :returns: set of paths to third party library modules.
    """
    paths: Set[Path] = set()

    packages_paths: Set[str] = {
        path
        for path in sys.path
        if path and Path(path).parts[-1] in [DIST_PACKAGES, SITE_PACKAGES]
    }

    for path in packages_paths:

        for name in os.listdir(path):
            if not name.startswith("_") and not name.endswith(BIN_PY_EXTENSIONS):
                paths.add(Path(os.path.join(path, name)))

    return paths


def get_local_import_path(path: Path, module: str) -> Optional[Path]:
    """Find the given local module file.py/__init_.py path.

    Written FOR `ast.Import`.

    :param path: where `module` has imported.
    :param module: module name.
    :returns: a full `module/__init__.py` path.
    """
    dirnames = Path(os.path.dirname(path)).parts
    names = module.split(".")

    # Test different levels.
    for i in [None] + list(range(-10, -0)):  # type: ignore

        # If it's a file.
        fpath = os.path.join(*dirnames[:i], *names[:-1], f"{names[-1]}{PY_EXTENSION}")
        if os.path.isfile(fpath):
            return Path(fpath)

        # If it's a module.
        mpath = os.path.join(*dirnames[:i], *names, __INIT__)
        if os.path.isfile(mpath):
            return Path(mpath)

    # Path not found.
    return None


def get_local_import_from_path(
    path: Path, module: str, package: str, level: int
) -> Optional[Path]:
    """Find the given local module file.py/__init_.py path.

    Written FOR `ast.ImportFrom`.

    :param path: where `module` has imported.
    :param module: module name.
    :param package: package name.
    :param level: `ast.ImportFrom.level`.
    :returns: a full `module/__init__.py` path.
    """
    dirname = Path(os.path.dirname(path))
    dirparts = dirname.parts[: (level * -1) + 1] if level > 1 else dirname.parts
    modules = module.split(".") if module != "*" and module else []
    packages = package.split(".") if package else []

    # Test different levels.
    for i in [None] + list(range(-10, -0)):  # type: ignore
        # If it's a file.
        if modules:
            fpath = os.path.join(
                *dirparts[:i],
                *packages,
                *modules[:-1],
                f"{modules[-1]}{PY_EXTENSION}",
            )
        else:
            # IMPORT "*" CASE.
            fpath = os.path.join(
                *dirparts[:i],
                *packages[:-1] if level > 0 else "",
                f"{packages[-1]}{PY_EXTENSION}",
            )
        if os.path.isfile(fpath):
            return Path(fpath)

        # If it's a module.
        if modules:
            mpath = os.path.join(
                *dirparts[:i],
                *packages,
                *modules,
                __INIT__,
            )
        else:
            # IMPORT "*" CASE.
            mpath = os.path.join(
                *dirparts[:i],
                *packages,
                __INIT__,
            )

        if os.path.isfile(mpath) and package.split(".")[0] in mpath:
            return Path(mpath)

    # Path not found.
    return None


def get_module_path(paths: Set[Path], module: str) -> Optional[Path]:
    """Get the `module` path from the given `paths`.

    :param paths: a list of paths to search.
    :param module: module name.
    :returns: `module` path if exist else None.
    """
    module = module.split(".")[0]
    for path in paths:
        name = str(path.parts[-1]).split(".")[0]
        if name == module:
            if str(path).endswith(PY_EXTENSION):
                return path
            else:
                return Path(os.path.join(path, __INIT__))
    # Path not found.
    return None


@lru_cache()
def get_import_path(path: Path, module: str) -> Optional[Path]:
    """Find the given module file.py/__init__.py path.

    Written for `ast.Import` nodes.

    :param path: where module has imported.
    :param module: module name.
    :returns: `module` file.py/__init_.py path, if found else None.
    """
    mpath = get_local_import_path(path, module)
    if mpath:
        return mpath

    elif module in get_standard_lib_names():
        return get_module_path(get_standard_lib_paths(), module)

    else:
        return get_module_path(get_third_party_lib_paths(), module)


@lru_cache()
def get_import_from_path(
    path: Path, module: str, package: str, level: int
) -> Optional[Path]:
    """Find the given module file.py/__init_.py path.

    Written for `ast.ImportFrom` nodes.

    :param path: where module has imported.
    :param module: module name.
    :param package: package name.
    :param level: `ast.ImportFrom.level`.
    :returns: `module` file.py/__init_.py path, if found else None.
    """
    mpath = get_local_import_from_path(path, module, package, level)
    if mpath:
        return mpath

    if module == "*":
        module = package

    if module in get_standard_lib_names():
        return get_module_path(get_standard_lib_paths(), module)

    elif package in get_standard_lib_names():
        return get_module_path(get_standard_lib_paths(), package)

    else:
        path = get_module_path(get_third_party_lib_paths(), module)
        if not path and package:
            path = get_module_path(get_third_party_lib_paths(), package)
        return path
