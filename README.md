<img src="https://raw.githubusercontent.com/hadialqattan/pycln/master/docs/_media/logo-background.png" width="100%" alt="Logo">

<h2 align="center">
    A formatter for finding and removing unused import statements.
</h2>

<p align="center">
    <a href="https://hadialqattan.github.io/pycln"><img src="https://img.shields.io/badge/more%20info-Pycln%20Docs-B5FFB3.svg?style=flat-square" alt="Pycln Docs"></a>
    <a href="https://github.com/hadialqattan/pycln/actions?query=workflow%3ACI"><img src="https://img.shields.io/github/actions/workflow/status/hadialqattan/pycln/ci.yml?branch=master&label=CI&logo=github&style=flat-square" alt="CI"></a>
    <a href="https://github.com/hadialqattan/pycln/actions?query=workflow%3ACD"><img src="https://img.shields.io/github/actions/workflow/status/hadialqattan/pycln/cd.yml?label=CD&logo=github&style=flat-square" alt="CD"></a>
    <a href="https://github.com/hadialqattan/pycln/actions?query=workflow%3AFUZZ"><img src="https://img.shields.io/github/actions/workflow/status/hadialqattan/pycln/fuzz.yml?label=FUZZ&logo=github&style=flat-square" alt="FUZZ"></a>
    <a href="https://codecov.io/gh/hadialqattan/pycln"><img src="https://img.shields.io/codecov/c/gh/hadialqattan/pycln/master?token=VVYBDCZPHR&style=flat-square" alt="Codecov"></a>
</p>

<p align="center">
    <img src="https://img.shields.io/pypi/pyversions/pycln?style=flat-square" alt="PYPI - Python Version">
    <a href="https://pypi.org/project/pycln/"><img src="https://img.shields.io/pypi/v/pycln?style=flat-square" alt="PYPI - Pycln Version"></a>
    <a href="https://pepy.tech/projects/pycln"><img src="https://static.pepy.tech/badge/pycln" alt="PyPI Downloads"></a>
    <a href="https://pypi.org/project/pycln/"><img src="https://img.shields.io/pypi/dm/pycln?color=dark-green&style=flat-square" alt="Downloads"></a>
</p>

<p align="center">
    <a href="https://github.com/hadialqattan/pycln/fork"><img src="https://img.shields.io/github/forks/hadialqattan/pycln?style=flat-square" alt="Forks"></a>
    <a href="https://github.com/hadialqattan/pycln/stargazers"><img src="https://img.shields.io/github/stars/hadialqattan/pycln?style=flat-square" alt="Stars"></a>
    <a href="https://github.com/hadialqattan/pycln/issues"><img src="https://img.shields.io/github/issues/hadialqattan/pycln?style=flat-square" alt="Issues"></a>
    <a href="https://github.com/hadialqattan/pycln/pulls"><img src="https://img.shields.io/github/issues-pr/hadialqattan/pycln?style=flat-square" alt="Pull Requests"></a>
    <a href="https://github.com/hadialqattan/pycln/graphs/contributors"><img src="https://img.shields.io/github/contributors/hadialqattan/pycln?style=flat-square" alt="Contributors"></a>
    <a href="https://github.com/hadialqattan/pycln/commits/master"><img src="https://img.shields.io/github/last-commit/hadialqattan/pycln.svg?style=flat-square" alt="Last Commit"></a>
    <a href="https://github.com/hadialqattan/pycln/blob/master/LICENSE"><img src="https://img.shields.io/github/license/hadialqattan/pycln.svg?color=A31F34&style=flat-square" alt="License"></a>
</p>

---

**[Read the documentation on Github pages!](https://hadialqattan.github.io/pycln)**

---

## Installation and usage

### Installation

Pycln requires Python 3.8+ and can be easily installed using the most common Python
packaging tools. We recommend installing the latest stable release from PyPI with
[`pipx`](https://pipx.pypa.io/)

```bash
$ pip install pipx
$ pipx install pycln
```

### Usage

By **default** Pycln will remove any unused import statement, So the simplest usage is
to specify the path only:

```bash
$ pycln [PATH]
```

Also, it's possible to run `pycln` as a package:

```bash
$ python3 -m pycln [PATH]
```

NOTE: you may need to use `-a/--all` option for more satisfying results. see
[-a/--all flag](https://hadialqattan.github.io/pycln/#/?id=-a-all-flag).

Further information can be found in our docs:

- [Usage and Configuration](https://hadialqattan.github.io/pycln/#/?id=usage)

## Configuration

**Pycln** is able to read project-specific default values for its command line options
from a configuration file like `pyproject.toml` or `setup.cfg`. This is especially
useful for specifying custom CLI arguments/options like `path/paths`, `--include`,
`--exclude`/`--extend-exclude`, or even `--all`.

You can find more details in our documentation:

- [--config [PATH] CLI option](https://hadialqattan.github.io/pycln/#/?id=-config-path-option)

And if you're looking for more general configuration documentation:

- [Usage and Configuration](https://hadialqattan.github.io/pycln/#/?id=usage)

## Used by

The following notable open-source projects trust and use _Pycln_:

- [cibuildwheel](https://github.com/pypa/cibuildwheel)
- [Open Event Server](https://github.com/fossasia/open-event-server)
- [pybind11](https://github.com/pybind/pybind11)
- [pywin32](https://github.com/mhammond/pywin32)
- [Poetry](https://github.com/python-poetry/poetry)
- [Pyodide](https://github.com/pyodide/pyodide)
- [Rich](https://github.com/Textualize/rich)
- [typeshed](https://github.com/python/typeshed)

The following organizations use _Pycln_:

- [FOSSASIA](https://github.com/fossasia)
- [Poetry](https://github.com/python-poetry)
- [Python Packaging Authority](https://github.com/pypa)
- [Scikit-HEP](https://github.com/scikit-hep)

Are we missing anyone? Let us know.

## License

MIT

## Contributing

A big welcome for considering contributing to make the project better!

You can get started by reading this:

- [General guidlines](https://hadialqattan.github.io/pycln/#/CONTRIBUTING?id=general-guidelines)

You can also dive directly into the technicalities:

- [Contributing technicalities](https://hadialqattan.github.io/pycln/#/CONTRIBUTING?id=technicalities)

## Change log

The log has become rather long. It moved to its own file.

See [CHANGELOG](https://hadialqattan.github.io/pycln/#/CHANGELOG).

## Authors

The author list is quite long nowadays, so it lives in its own file.

See [AUTHORS](https://hadialqattan.github.io/pycln/#/AUTHORS)

## Code of Conduct

Everyone participating in the _Pycln_ project, and in particular in the issue tracker,
and pull requests is expected to treat other people with respect.

---

Give a ⭐️ if this project helped you!
