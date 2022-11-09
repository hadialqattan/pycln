# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and
this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

<!-- Please use the below template. -->
<!-- - [description by @username](https://github.com/hadialqattan/pycln/pull/{pull_number}) -->

## [Unreleased]

## [2.1.2] - 2022-11-09

### Fixed

- [Imports used in generics and wrapped in string get removed by @hadialqattan](https://github.com/hadialqattan/pycln/pull/178)
- [Setting an artificial lock to LibCST version `+0.4.0` for Python `3.6.x`; a bug introduced in LibCST `+0.4.0` that affects `PY3.6` by @hadialqattan](https://github.com/hadialqattan/pycln/pull/174)

### Added

- [Adding a CLI flag for disabling the enforcement of the `__all__` dunder in `__init__.py` policy by @hadialqattan](https://github.com/hadialqattan/pycln/pull/175)

### Changed

- [Bump typer from 0.6.1 to 0.7.0 by @dependabot[bot]](https://github.com/hadialqattan/pycln/pull/176)
- [Bump pytest-cov from 3.0.0 to 4.0.0 by @dependabot[bot]](https://github.com/hadialqattan/pycln/pull/171)
- [Bump JRubics/poetry-publish from 1.12 to 1.13 by @dependabot[bot]](https://github.com/hadialqattan/pycln/pull/168)

## [2.1.1] - 2022-07-28

### Changed

- [Now Pycln uses `tomlkit` instead of `toml` library for parsing toml config files in order to support toml v1.0.0 by @hadialqattan](https://github.com/hadialqattan/pycln/pull/165)

## [2.0.4] - 2022-07-18 (a quick release solving v2.0.3 problem \[affects PY3.9+\])

### Fixed

- [Possible internal attr errors due to lack of some ast node type-checking (affects only Python3.9+) by @hadialqattan](https://github.com/hadialqattan/pycln/pull/162)

### Changed

- [Bump typer from 0.5.0 to 0.6.1 by @dependabot[bot]](https://github.com/hadialqattan/pycln/pull/160)
- [Bump JRubics/poetry-publish from 1.11 to 1.12 by @dependabot[bot]](https://github.com/hadialqattan/pycln/pull/159)

## [2.0.3] - 2022-07-17 (a broken release \[affects PY3.9+\], goto v2.0.4)

### Fixed

- [Fully, nested, and semi string type commnets get ignored by @hadialqattan](https://github.com/hadialqattan/pycln/pull/156)

- [Semi string third-party generic type annotations get ignored by @hadialqattan](https://github.com/hadialqattan/pycln/pull/155)

## [2.0.2] - 2022-07-13

### Added

- [Pycln skips `from foo import *` imports in compliance with PEP 484 in stub files (`.pyi`) by @AlexWaygood](https://github.com/hadialqattan/pycln/pull/153)

### Changed

- [Bump typer from 0.4.1 to 0.5.0 by @dependabot[bot]](https://github.com/hadialqattan/pycln/pull/151)

## [2.0.1] - 2022-07-05

### Added

- [Pycln skips redundant alias imports in compliance with PEP 484 in stub files (`.pyi`) by @hadialqattan](https://github.com/hadialqattan/pycln/pull/150)

### Changed

- [Now Pycln treats `.pyi` files as regular `.py` files in the pathfinding functionality by @hadialqattan](https://github.com/hadialqattan/pycln/pull/150)

### Fixed

- [Outputting code diff when both `--check` and `--diff` options are used by @hadialqattan](https://github.com/hadialqattan/pycln/pull/147)

## [1.3.5] - 2022-06-23

### Fixed

- [In the modules' path finding functionality non-directory paths are treated as directories causing `Permission denied` errors crashing Pycln by @hadialqattan](https://github.com/hadialqattan/pycln/pull/145)

- [Useful `pass` statements are removed from `orelse` parent nodes when both `finallybody` and `orelse` exist causing syntax errors by @hadialqattan](https://github.com/hadialqattan/pycln/pull/144)

## [1.3.4] - 2022-06-22

### Fixed

- [`pass` statements are removed from `finallybody` parent nodes causing syntax errors by @hadialqattan](https://github.com/hadialqattan/pycln/pull/143)

## [1.3.3] - 2022-05-20

### Fixed

- [Support `typing.TypeVar` when types passed as `str` @hadialqattan](https://github.com/hadialqattan/pycln/pull/137)

## [1.3.2] - 2022-04-27

### Changed

- [Bump libcst from 0.3.23 to 0.4.1 by @dependabot[bot]](https://github.com/hadialqattan/pycln/pull/133)

- [Bump pytest from 6.2.5 to 7.0.1 by @dependabot[bot]](https://github.com/hadialqattan/pycln/pull/132)

- [Bump pyyaml from 5.4.1 to 6.0 by @dependabot[bot]](https://github.com/hadialqattan/pycln/pull/131)

- [Bump pytest-cov from 2.12.1 to 3.0.0 by @dependabot[bot]](https://github.com/hadialqattan/pycln/pull/130)

- [Bump actions/checkout from 2 to 3 by @dependabot[bot]](https://github.com/hadialqattan/pycln/pull/129)

- [Bump actions/setup-python from 2 to 3 by @dependabot[bot]](https://github.com/hadialqattan/pycln/pull/128)

- [Bump JRubics/poetry-publish from 1.8 to 1.10 by @dependabot[bot]](https://github.com/hadialqattan/pycln/pull/127)

- [Bump codecov/codecov-action from 2.1.0 to 3.1.0 by @dependabot[bot]](https://github.com/hadialqattan/pycln/pull/126)

## [1.3.1] - 2022-04-16 (a quick release solving v1.3.0 problem)

### Fixed

- [Include `vendor/` directory in the final distribution avoiding `No module named 'vendor'` error by @hadialqattan]()

## [1.3.0] - 2022-04-16 (a broken release, goto v1.3.1)

### Added

- [A global module/package/library imports skipping option (`--skip-imports`) by @hadialqattan](https://github.com/hadialqattan/pycln/pull/121)

- [Add support for `.pth` files by @hadialqattan](https://github.com/hadialqattan/pycln/pull/120)

- [Add support for reading from STDIN by @hadialqattan](https://github.com/hadialqattan/pycln/pull/118)

### Fixed

- [Pycln crashes when facing a `.pth` file by @hadialqattan](https://github.com/hadialqattan/pycln/pull/120)

## [1.2.5] - 2022-03-12

### Fixed

- [Pycln does not cleanup `finally` blocks' bodies from useless `pass` statements by @hadialqattan](https://github.com/hadialqattan/pycln/pull/114)

- [Pycln unnecessarily skips `try..except` imports when standard import exception(s) exist(s) by @hadialqattan](https://github.com/hadialqattan/pycln/pull/113)

## [1.2.4] - 2022-02-27

### Fixed

- [Support nested string type annotation by @hadialqattan](https://github.com/hadialqattan/pycln/pull/110)

## [1.2.3] - 2022-02-26

### Added

- [Add extend exclude CLI option @hadialqattan](https://github.com/hadialqattan/pycln/pull/108)

### Fixed

- [Pycln crashes with `IndexError` or `AttributeError` in case of `from . import *` by @hadialqattan](https://github.com/hadialqattan/pycln/pull/103)

- [Skip any file containing a form feed character instead of breaking the code by @hadialqattan](https://github.com/hadialqattan/pycln/pull/102)

- [Consider any import statement that is inlined with `:` as an unsupported case instead of breaking the code by @hadialqattan](https://github.com/hadialqattan/pycln/pull/101)

## [1.2.2] - 2022-02-25

### Fixed

- [`pass` statements are removed from `orelse` parent nodes causing syntax errors by @hadialqattan](https://github.com/hadialqattan/pycln/pull/100)

### Changed

- [In case of `(async)func`/`class` contains docstring, keep only one `pass` statement instead of none by @hadialqattan](https://github.com/hadialqattan/pycln/pull/100)

## [1.2.1] - 2022-02-24

### Fixed

- [Make the `__init__.py` file without `__all__` dunder's warning more precise by @hadialqattan](https://github.com/hadialqattan/pycln/pull/98)

## [1.2.0] - 2022-02-18

### Fixed

- [Pycln removes imported names that should be exported in case of `__init__.py` file without `__all__` dunder by @hadialqattan](https://github.com/hadialqattan/pycln/pull/97)
- [The path argument is ignored when passed in a config file by @hadialqattan](https://github.com/hadialqattan/pycln/pull/95)
- [Remove star imports when nothing's actually imported by @pmourlanne](https://github.com/hadialqattan/pycln/pull/92)

## [1.1.0] - 2021-11-12

### Added

- [Add support for Python 3.10 by @hadialqattan](https://github.com/hadialqattan/pycln/pull/81)

### Fixed

- [Pycln does not skip imports that have "# nopycln: import" or "# noqa" on the last line by @hadialqattan](https://github.com/hadialqattan/pycln/pull/88)
- [Pycln removes extra lines in import-from multiline case (shown below) by @hadialqattan](https://github.com/hadialqattan/pycln/pull/87)

  ```python3
  from xxx import (i,
      j,
      k)
  # if j isn't used, Pycln will remove this line no matter what it is!
  ```

- [Preserving trailing comma style in multi-line imports by @hadialqattan](https://github.com/hadialqattan/pycln/pull/86)
- [Exit normally (code 0) when no files were present to be cleaned by @rooterkyberian](https://github.com/hadialqattan/pycln/pull/84)
- [Parsing local path import with null-pacakge causes AttributeError by @hadialqattan](https://github.com/hadialqattan/pycln/pull/76)
- [RecursionError occurs when expanding a star import that has too many related modules by @hadialqattan](https://github.com/hadialqattan/pycln/pull/75)

## [1.0.3] - 2021-08-18

### Changed

- [Prevent the path finding method from searching inside any of the excluded directories' children by @hadialqattan](https://github.com/hadialqattan/pycln/pull/68)

## [0.0.5] - 2021-08-07

### Added

- [Support `__all__` with add augmented assignment operation by @hadialqattan](https://github.com/hadialqattan/pycln/pull/65)
- [Support `__all__` with add binary operator (concatenation) by @hadialqattan](https://github.com/hadialqattan/pycln/pull/64)
- [Support `__all__` list operations (append & extend) by @hadialqattan](https://github.com/hadialqattan/pycln/pull/63)

### Fixed

- [Gitignore, include, and exclude path matching rules don't apply for file sources by @hadialqattan](https://github.com/hadialqattan/pycln/pull/67)

## [0.0.4] - 2021-07-07

### Fixed

- [Invalid PIP-526 type comments make Pycln crashes with an UnparsableFile error by @hadialqattan](https://github.com/hadialqattan/pycln/pull/59)

## [0.0.3] - 2021-07-01

### Changed

- [Respect `.gitignore` files in all levels, not only `root/.gitignore` file (apply `.gitignore` rules like `git` does) by @hadialqattan](https://github.com/hadialqattan/pycln/pull/57)

### Fixed

- [UnicodeEncodeError in non-utf8 terminals by @hadialqattan](https://github.com/hadialqattan/pycln/pull/56)

## [0.0.2] - 2021-04-27

### Fixed

- [Pycln always exits with 0 status code by @hadialqattan](https://github.com/hadialqattan/pycln/pull/53)

## [0.0.1] - 2021-04-10

### Added

- [First stable version](https://pypi.org/project/pycln/), Happy 🍰 Day 2021!

## [0.0.1-beta.3] - 2021-03-12

### Fixed

- [Keep the original format of line break by @hadialqattan](https://github.com/hadialqattan/pycln/pull/48)

## [0.0.1-beta.2] - 2021-01-01

### Fixed

- [Spaces inside Literal type annotations breaks pycln by @hadialqattan [the raw idea by @zealotous]](https://github.com/hadialqattan/pycln/pull/45)

## [0.0.1-beta.1] - 2020-12-31

### Fixed

- [Poetry python39 issue by @hadialqattan](https://github.com/hadialqattan/pycln/pull/44)

## [0.0.1-beta.0] - 2020-10-14

### Added

- [Support implicit imports from sub-packages by @hadialqattan](https://github.com/hadialqattan/pycln/pull/37)
- [Support semi string type hint by @hadialqattan](https://github.com/hadialqattan/pycln/pull/36)
- [Support casting case by @hadialqattan](https://github.com/hadialqattan/pycln/pull/34)

## [0.0.1-alpha.3] - 2020-10-07

### Changed

- [now --expand-stars can't expand C wrapped modules @hadialqattan](https://github.com/hadialqattan/pycln/pull/20)

### Security

- [C wrapped modules import star expanding related vulnerability by @hadialqattan](https://github.com/hadialqattan/pycln/pull/20)

## [0.0.1-alpha.2] - 2020-10-03

### Added

- [Add Pycln hook to `pre-commit-config.yaml` by @hadialqattan](https://github.com/hadialqattan/pycln/pull/13)

### Removed

- [Remove <quote> tags on PyPI/README.md (can't be rendered) by @hadialqattan](https://github.com/hadialqattan/pycln/pull/13)

## [0.0.1-alpha.1] - 2020-10-02

### Changed

- [Handle multiple paths by @hadialqattan](https://github.com/hadialqattan/pycln/pull/12)

### Fixed

- [CD badge always shows 'no status' by @hadialqattan](https://github.com/hadialqattan/pycln/pull/11)
- [Pycln logo does not appear on PyPI/README.md by @hadialqattan](https://github.com/hadialqattan/pycln/pull/11)

## [0.0.1-alpha.0] - 2020-10-02

### Added

- [First published version](https://pypi.org/project/pycln/), Happy 🍰 Day 2020!
- [Alpha quality](https://techterms.com/definition/alpha_software).
- [Semantically versioned](https://semver.org/spec/v2.0.0.html)
- [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) formatted.
