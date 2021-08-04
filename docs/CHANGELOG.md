# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and
this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

<!-- Please use the below template. -->
<!-- - [description by @username](https://github.com/hadialqattan/pycln/pull/{pull_number}) -->

## [Unreleased]

### Added

- [Support `__all__` with add augmented assignment operation by @hadialqattan](https://github.com/hadialqattan/pycln/pull/65)
- [Support `__all__` with add binary operator (concatenation) by @hadialqattan](https://github.com/hadialqattan/pycln/pull/64)
- [Support `__all__` list operations (append & extend) by @hadialqattan](https://github.com/hadialqattan/pycln/pull/63)

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

- [Support implicit imports from sub-packages by @hadialqattan](https://github.com/hadialqattan/pycln/pull/36)
- [Support semi string type hint by @hadialqattan](https://github.com/hadialqattan/pycln/pull/35)
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
