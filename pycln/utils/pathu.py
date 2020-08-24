"""
Pycln path utils.
"""
import os
import sys
from distutils import sysconfig
from functools import lru_cache
from pathlib import Path
from typing import Generator, List, Pattern, Set, Union

from pathspec import PathSpec

from . import regexu
from .report import Report

# Constants.
DOT = "."
STAR = "*"
DASH = "-"
EMPTY = ""
EXCLUDE = "exclude"
INCLUDE = "include"
GITIGNORE = "gitignore"
UNDERSCORE = "_"
FORWARD_SLASH = "/"
PY_EXTENSION = ".py"
__INIT__ = "__init__.py"
LIB_DYNLOAD = "lib-dynload"
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
    """Yields `.py` files paths to handle. Walk throw path sub-directories/files recursively.

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

    scandir = os.scandir(path)
    for entry in scandir:

        # Skip symlinks.
        if entry.is_symlink():
            continue

        name = entry.name if entry.is_file() else f"{entry.name}{FORWARD_SLASH}"
        entry_path = os.path.join(path, name)

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
        yield os.path.join(path, name)

    for dirname in dirs:

        dir_path = os.path.join(path, dirname)

        # Compute exclusions.
        if is_excluded(dirname, exclude):
            reporter.ignored_path(dir_path, EXCLUDE)
            continue

        # Compute `.gitignore`.
        if gitignore.match_file(dirname):
            reporter.ignored_path(dir_path, GITIGNORE)
            continue

        yield from yield_sources(dir_path, include, exclude, gitignore, reporter)


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
def get_third_party_lib_paths() -> Set[Path]:
    """Get paths to third party library modules.

    :returns: set of paths to Third party library modules.
    """
    paths: Set[Path] = set()

    packages_paths: Set[str] = set(
        [
            path
            for path in sys.path
            if Path(path).parts[-1] in [DIST_PACKAGES, SITE_PACKAGES]
        ]
    )

    for path in packages_paths:

        for name in os.listdir(path):
            if not name.startswith(UNDERSCORE) and not name.endswith(BIN_PY_EXTENSIONS):
                paths.add(Path(os.path.join(path, name)))

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

        if name.startswith(UNDERSCORE) or DASH in name:
            continue

        if DOT in name and not name.endswith(LIB_PY_EXTENSIONS):
            continue

        names.add(name.split(DOT)[0])

    return (names - IMPORTS_WITH_SIDE_EFFECTS) | BIN_IMPORTS


def get_local_import_path(source: Path, module_name: str) -> Union[str, None]:
    """Find the given local module_name file.py/__init_.py path.
    
    Written FOR `ast.Import`.

    :param source: where module has imported.
    :param module_name: target module name.
    :returns: a full `module_name/__init__.py` path.
    """
    dirname = os.path.dirname(source)
    names = module_name.split(DOT)

    # If it's a module.
    path = os.path.join(dirname, *names, __INIT__)
    if os.path.isfile(path):
        return path

    # If it's a file.
    path = os.path.join(dirname, *names[:-1], f"{names[-1]}{PY_EXTENSION}")
    if os.path.isfile(path):
        return path


def get_local_import_from_path(
    source: Path, module_name: str, from_module_name: str, level: int
) -> Union[str, None]:
    """Find the given local module_name file.py/__init_.py path.

    Written FOR `ast.ImportFrom`

    :param source: where module has imported.
    :param module_name: target module name.
    :param from_module_name: `from from_module_name import ...`.
    :param level: `ast.ImportFrom.level`.
    """
    dirname = Path(os.path.dirname(source))
    leveled_dirnames = dirname.parts[: (level * -1) + 1] if level > 1 else dirname.parts

    module_names = (
        module_name.split(DOT) if not module_name == STAR and module_name else []
    )
    from_module_names = from_module_name.split(DOT) if from_module_name else []

    # If it's a module.
    path = os.path.join(*leveled_dirnames, *from_module_names, *module_names, __INIT__,)
    if os.path.isfile(path):
        return path

    # If it's a file.
    if module_names:
        path = os.path.join(
            *leveled_dirnames,
            *from_module_names,
            *module_names[:-1],
            f"{module_names[-1]}{PY_EXTENSION}",
        )
    else:
        # IMPORT STAR CASE.
        path = os.path.join(
            *leveled_dirnames,
            *from_module_names[:-1],
            f"{from_module_names[-1]}{PY_EXTENSION}",
        )
    if os.path.isfile(path):
        return path


@lru_cache()
def get_import_path(source: Path, module_name: str):
    """Find the given module_name file.py/__init__.py path.

    Written for `ast.Import` nodes.

    :param source: where module has imported.
    :param module_name: target module name.
    :returns: The given module_name file.py/__init_.py path, if found else None.
    """
    path = get_local_import_path(source, module_name)
    if path:
        return path

    elif module_name in get_standard_lib_names():
        for path in get_standard_lib_paths():
            name = str(path.parts[-1]).split(DOT)[0]
            if name == module_name:
                return path

    else:
        for path in get_third_party_lib_paths():
            name = str(path.parts[-1]).split(DOT)[0]
            if name == module_name:
                return path


@lru_cache()
def get_import_from_path(
    source: Path, module_name: str, from_module_name: str, level: int
) -> Union[Path, None]:
    """Find the given module_name file.py/__init_.py path.

    Written for `ast.ImportFrom` nodes.

    :param source: where module has imported.
    :param module_name: target module name.
    :param from_module_name: `from from_module_name import ...`.
    :param level: `ast.ImportFrom.level`.
    :returns: The given module_name file.py/__init_.py path, if found else None.
    """
    if level > 0:
        return get_local_import_from_path(source, module_name, from_module_name, level)

    elif from_module_name in get_standard_lib_names():
        for path in get_standard_lib_paths():
            name = str(path.parts[-1]).split(DOT)[0]
            if name == from_module_name:
                return path

    else:
        for path in get_third_party_lib_paths():
            name = str(path.parts[-1]).split(DOT)[0]
            if name == from_module_name:
                return path
