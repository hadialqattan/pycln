"""Pycln path finding utility."""
import os
import sys
import sysconfig
from functools import lru_cache
from pathlib import Path
from typing import Generator, Optional, Pattern, Set, Tuple

from pathspec import PathSpec

from vendor.custom import _site

from .. import ISWIN
from . import regexu
from .report import Report

# Constants.
EXCLUDE = "exclude"
INCLUDE = "include"
GITIGNORE = "gitignore"
PY_EXTENSION = ".py"
PTH_EXTENSION = ".pth"
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
PYTHON_STDLIB_PATHS = frozenset(
    {sysconfig.get_path("platstdlib"), sysconfig.get_path("stdlib")}
)


def yield_sources(
    path: Path,
    include: Pattern[str],
    exclude: Pattern[str],
    extend_exclude: Pattern[str],
    gitignore: PathSpec,
    reporter: Report,
) -> Generator[Path, None, None]:
    """Yields `.py` and `.pyi` paths to handle. Walk throw path sub-
    directories/files recursively.

    :param path: A path to start searching from.
    :param include: regex pattern to be included.
    :param exclude: regex pattern to be excluded.
    :param extend_exclude: regex pattern to be excluded in addition to `exclude`.
    :param gitignore: gitignore PathSpec object.
    :param reporter: a `report.Report` object.
    :returns: generator of `.py` and `.pyi` files paths.
    """

    dirs: Set[Path] = set()
    files: Set[Path] = set()

    is_included, is_excluded = regexu.is_included, regexu.is_excluded

    if path.is_dir():
        root_dir = os.scandir(path)  # type: ignore
    else:
        root_dir = {path}  # type: ignore
        path = path.parent

    for entry in root_dir:
        entry_path = Path(entry)

        # Skip symlinks.
        if entry_path.is_symlink():
            continue

        # Compute exclusions.
        if is_excluded(entry_path, exclude):
            reporter.ignored_path(entry_path, EXCLUDE)
            continue

        # Compute extended exclusions.
        if is_excluded(entry_path, extend_exclude):
            reporter.ignored_path(entry_path, EXCLUDE)
            continue

        # Compute `.gitignore`.
        if gitignore.match_file(entry_path):
            reporter.ignored_path(entry_path, GITIGNORE)
            continue

        # Directories.
        if entry_path.is_dir():
            dirs.add(entry_path)
            continue

        # Files.
        if is_included(entry_path, include):
            files.add(entry_path)
        else:
            reporter.ignored_path(entry_path, INCLUDE)

    yield from files

    for dir_ in dirs:
        # If gitignore is None, gitignore usage is disabled, while a Falsey
        # gitignore is when the directory doesn't have a .gitignore file.
        yield from yield_sources(
            dir_,
            include,
            exclude,
            extend_exclude,
            gitignore + regexu.get_gitignore(dir_) if gitignore is not None else None,
            reporter,
        )


@lru_cache()
def get_standard_lib_paths() -> Set[Path]:
    """Get paths to Python standard library modules.

    :returns: set of paths to Python standard library modules.
    """
    paths: Set[Path] = set()

    for lib_path in PYTHON_STDLIB_PATHS:
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
def get_third_party_lib_paths() -> Tuple[Set[Path], Set[Path]]:
    """Get paths to third party library modules.

    :returns: a tuple of a set of paths of third party library modules
        and a set of paths from `.pth` file(s) content, respectively.
    """
    paths: Set[Path] = set()
    pth_paths: Set[Path] = set()

    packages_paths: Set[str] = set()

    for path in sys.path:
        ppath = Path(path)
        if ppath.parts[-1] in (DIST_PACKAGES, SITE_PACKAGES) or (
            ppath.is_dir() and path not in PYTHON_STDLIB_PATHS
        ):
            packages_paths.add(path)

    for path in packages_paths:
        for name in os.listdir(path):
            if name.endswith(PTH_EXTENSION):
                for pth_path in _site.addpackage(path, name):
                    pth_paths.add(Path(pth_path))
            elif not name.startswith("_") and not name.endswith(BIN_PY_EXTENSIONS):
                paths.add(Path(path).joinpath(name))

    return paths, pth_paths


@lru_cache()
def get_local_import_path(path: Path, module: str) -> Optional[Path]:
    """Find the given local module file.py/__init_.py path.

    Written FOR `ast.Import`.

    :param path: where `module` has imported.
    :param module: a module name.
    :returns: a full `module/__init__.py` path.
    """
    dirnames = path.parts if path.is_dir() else path.parent.parts
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


def get_local_import_pth_path(pth_paths: Set[Path], module: str) -> Optional[Path]:
    """Find the given local module file.py/__init__.py path base on the
    provided `pth_paths` set.

    :param pth_paths: a set of local paths read from a `.pth` file.
    :param module: a module name.
    :returns: a full `module/__init__.py` path.
    """
    for path in pth_paths:
        local_path = get_local_import_path(path, module)
        if local_path:
            return local_path

    # Path not found.
    return None


@lru_cache()
def get_local_import_from_path(
    path: Path, module: str, package: str, level: int
) -> Optional[Path]:
    """Find the given local module file.py/__init_.py path.

    Written FOR `ast.ImportFrom`.

    :param path: where `module` has imported.
    :param module: a module name.
    :param package: a package name.
    :param level: `ast.ImportFrom.level`.
    :returns: a full `module/__init__.py` path.
    """
    dirname = path if path.is_dir() else path.parent
    dirparts = dirname.parts[: (level * -1) + 1] if level > 1 else dirname.parts
    modules = module.split(".") if module != "*" and module else []
    packages = package.split(".") if package else []

    # Test different levels.
    for i in [None] + list(range(-10, -0)):  # type: ignore
        # If it's a file.
        if modules:
            fpath = os.path.join(
                *dirparts[:i],
                *packages if module != package else "",
                *modules[:-1],
                f"{modules[-1]}{PY_EXTENSION}",
            )
        else:
            # IMPORT "*" CASE.
            fpath = os.path.join(
                *dirparts[:i],
                *packages[:-1] if level > 0 else "",
                f"{packages[-1] if packages else '__init__'}{PY_EXTENSION}",
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

        if (
            os.path.isfile(mpath)
            and package is not None
            and package.split(".")[0] in mpath
        ):
            return Path(mpath)

    # Path not found.
    return None


def get_local_import_from_pth_path(
    pth_paths: Set[Path], module: str, package: str, level: int
) -> Optional[Path]:
    """Find the given local module file.py/__init__.py path base on the
    provided `pth_paths` set.

    Written FOR `ast.ImportFrom`.

    :param pth_paths: a set of local paths read from a `.pth` file.
    :param module: a module name.
    :param package: a package name.
    :param level: `ast.ImportFrom.level`.
    :returns: a full `module/__init__.py` path.
    """
    for path in pth_paths:
        local_path = get_local_import_from_path(path, module, package, level)
        if local_path:
            return local_path

    # Path not found.
    return None


def get_module_path(
    paths: Set[Path], module: str, package: str = "", level: int = 0
) -> Optional[Path]:
    """Get the `module` path from the given `paths`.

    :param paths: a list of paths to search.
    :param module: a module name.
    :param package: a package name.
    :param level: `ast.ImportFrom.level`.
    :returns: `module` path if exist else None.
    """
    if module is not None:
        module = module.split(".")[0]
        for path in paths:
            name = str(path.parts[-1]).split(".")[0]
            if name == module:
                if str(path).endswith(PY_EXTENSION):
                    return path
                if Path(path).is_dir():
                    return Path(path).joinpath(__INIT__)
            if name == package:
                mpath = get_local_import_from_path(path, module, package, level)
                if mpath:
                    return mpath
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
        paths, pth_paths = get_third_party_lib_paths()
        mpath = get_local_import_pth_path(pth_paths, module)
        if mpath:
            return mpath
        return get_module_path(paths, module)


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
        paths, pth_paths = get_third_party_lib_paths()
        mpath = get_local_import_from_pth_path(pth_paths, module, package, level)
        if mpath:
            return mpath
        path = get_module_path(paths, module)
        if not path and package:
            path = get_module_path(paths, module, package, level)
        return path
