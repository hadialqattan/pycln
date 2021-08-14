# Get Started

<img src="_media/logo-background-1200.png" width="100%" alt="Logo">

<p align="center">
    <quote>A formatter for finding and removing unused import statements.</quote>
</p>

<p align="center">
    <a href="https://hadialqattan.github.io/pycln"><img src="https://img.shields.io/badge/For%20More%20Information%20See-Pycln%20Docs-B5FFB3.svg?style=flat-square" alt="Code style: prettier"></a>
    <a href="https://github.com/hadialqattan/pycln/actions?query=workflow%3ACI"><img src="https://img.shields.io/github/workflow/status/hadialqattan/pycln/CI/master?label=CI&logo=github&style=flat-square" alt="CI"></a>
    <a href="https://github.com/hadialqattan/pycln/actions?query=workflow%3ACD"><img src="https://img.shields.io/github/workflow/status/hadialqattan/pycln/CD?label=CD&logo=github&style=flat-square" alt="CD"></a>
    <a href="https://www.codacy.com/manual/hadialqattan/pycln/dashboard?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=hadialqattan/pycln&amp;utm_campaign=Badge_Grade"><img src="https://img.shields.io/codacy/grade/e7c6c290c3c149e484634ac1905800d6/master?style=flat-square" alt="Codacy Badge"></a>
    <a href="https://codecov.io/gh/hadialqattan/pycln"><img src="https://img.shields.io/codecov/c/gh/hadialqattan/pycln/master?token=VVYBDCZPHR&style=flat-square" alt="Codecov"></a>
    <a href="https://codeclimate.com/github/hadialqattan/pycln/maintainability"><img src="https://img.shields.io/codeclimate/maintainability/hadialqattan/pycln?style=flat-square" alt="Maintainability"></a>
</p>

<p align="center">
    <img src="https://img.shields.io/pypi/pyversions/pycln?style=flat-square" alt="PYPI - Python Version">
    <a href="https://pypi.org/project/pycln/"><img src="https://img.shields.io/pypi/v/pycln?style=flat-square" alt="PYPI - Pycln Version"></a>
    <a href="https://pypi.org/project/pycln/"><img src="https://img.shields.io/pypi/dm/pycln?color=dark-green&style=flat-square" alt="Downloads"></a>
    <a href="https://hits.seeyoufarm.com"><img src="https://hits.seeyoufarm.com/api/count/incr/badge.svg?url=https%3A%2F%2Fgithub.com%2Fhadialqattan%2Fpycln&count_bg=%2344CC10&title_bg=%23555555&icon=&icon_color=%23E7E7E7&title=hits&edge_flat=true"/></a>
    <a href="_blank"><img src="https://img.shields.io/tokei/lines/github.com/hadialqattan/pycln?style=flat-square" alt="Lines Of Code"></a>
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

<p align="center">
    <a href="https://docutils.sourceforge.io/rst.html"><img src="https://img.shields.io/badge/docstrings-reStructuredText-gree.svg?style=flat-square" alt="Docstrings: reStructuredText"></a>
    <a href="https://github.com/psf/black"><img src="https://img.shields.io/badge/code%20style-black-000000.svg?style=flat-square" alt="Code style: black"></a>
    <a href="https://github.com/prettier/prettier"><img src="https://img.shields.io/badge/code%20style-prettier-ff69b4.svg?style=flat-square" alt="Code style: prettier"></a>
</p>

# Installation

## Latest Release (PYPI)

Pycln requires Python 3.6+ and can be easily installed using the most common Python
packaging tools. We recommend installing the latest stable release from PyPI with pip:

```bash
$ pip3 install pycln
```

## Unreleased (REPOSITORY)

If you want the latest unreleased Pycln version, you can install it from the repository
using
[`install.sh`](https://github.com/hadialqattan/pycln/tree/master/scripts/install.sh)
(pip):

- Clone the repository:

  ```bash
  $ git clone https://github.com/hadialqattan/pycln
  ```

- CD into it:

  ```bash
  $ cd pycln
  ```

- Install with
  [`install.sh`](https://github.com/hadialqattan/pycln/tree/master/scripts/install.sh):
  ```bash
  $ ./scripts/install.sh
  ```

## Uninstall

It doesn't matter which installation method you has used, Uninstall can be done with
[`uninstall.sh`](https://github.com/hadialqattan/pycln/tree/master/scripts/uninstall.sh)
(pip):

```bash
$ ./scripts/uninstall.sh
```

# Usage

## The Simplest Usage

By **default** Pycln will **remove** any unused import statement, So the simplest usage
is to specify only the path:

```bash
$ pycln [PATH]
```

## Pycln Skips

### Import Skips

> Skip an import statement from Pycln check.

- Using `# nopycln: import` comment:

  ```python
  import x  # nopycln: import
  from xxx import (  # nopycln: import
      x,
      y,
      z
  )
  ```

- Using `# noqa` comment:
  ```python
  import x  # noqa
  from xxx import (  # noqa
      x,
      y,
      z
  )
  ```

### File Wide Skips

> Skip a file by typing `# nopycln: file` anywhere on it.

- At the beginning:
  ```python
  # nopycln: file
  import x
  ```
- At the end:

  ```python
  import x
  # nopycln: file
  ```

## CLI Arguments

### Paths

> Directories or files paths.

#### Usage

- Specify a directory to handle all it's subdirs/files (recursively):
  ```bash
  $ pycln my/project/directory
  ```
- Specify a file:
  ```bash
  $ pycln my_python_file.py
  ```
- Specify multiple directories and files:
  ```bash
  $ pycln dir1/ dir2/ main.py cli.py
  ```

## CLI Options

### `--config PATH` option

> Read configuration from a file.

#### Default

> `None`

#### Behaviour

- All Pycln arguments, options, and flags can be read from a config file.
- Only these types are accepted `.cfg`, `.toml`, `.json`, `.yaml`, and `.yml`.
- Overrides CLI arguments, options, and flags.

#### Usage

- Get configs only from a config file:
  ```bash
  $ pycln --config config_file.cfg  # .toml, .json, .yaml, .yml
  ```
- Get from both the CLI and a config file:
  ```bash
  $ pycln /path/ --diff --config config_file.cfg  # .toml, .json, .yaml, .yml
  ```

#### Example

<details>
  <summary><code>.cfg</code></summary>

```cfg
[pycln]
path = /project/path/
include = .*_util\.py$
exclude = .*_test\.py$
expand_stars = True
verbose = True
diff = True
all = True
no_gitignore = False
```

</details>

<details>
  <summary><code>.toml</code></summary>

```toml
[tool.pycln]
path = "/project/path/"
include=".*_util\.py$"
exclude=".*_test\.py$"
expand_stars=true
verbose=true
diff=true
all=true
no_gitignore=false
```

</details>

<details>
  <summary><code>.yaml</code>/<code>.yml</code></summary>

```yaml
pycln:
  path: /project/path/
  include: .*_util\.py$
  exclude: .*_test\.py$
  expand_stars: true
  verbose: true
  diff: true
  all: true
  no_gitignore: false
```

</details>

<details>
  <summary><code>.json</code></summary>

```json
{
  "pycln": {
    "path": "/project/path/",
    "include": ".*_util.py$",
    "exclude": ".*_test.py$",
    "expand_stars": true,
    "verbose": true,
    "diff": true,
    "all": true,
    "no_gitignore": false
  }
}
```

</details>

### `-i, --include TEXT` option

> A regular expression that matches files and directories that should be included on
> recursive searches.

#### Default

> `.*\.py$`

#### Behaviour

- An empty value means all files are included regardless of the name.
- Use forward slashes for directories on all platforms (Windows, too).
- Exclusions are calculated first, inclusions later.

#### Usage

Assume that we have three files (`util_a.py`, `util_b.py`, `test_a.py`) on a directory
called `project` and we want to reformat only files that start with `util_`:

```bash
$ pycln /path_to/project/ --include util_.*  # or -i util_.*
```

### `-e, --exclude TEXT` option

> A regular expression that matches files and directories that should be exclude on
> recursive searches.

#### Default

> `(\.eggs|\.git|\.hg|\.mypy_cache|__pycache__|\.nox|\.tox|\.venv|\.svn|buck-out|build|dist)/`

#### Behaviour

- An empty value means no paths are excluded.
- Use forward slashes for directories on all platforms (Windows, too).
- Exclusions are calculated first, inclusions later.

#### Usage

Assume that we have four files (`util_a.py`, `util_b.py`, `test_a.py`, `test_b.py`) on a
directory called `project` and we want to reformat files that not start with `test_`:

```bash
$ pycln /path_to/project/ --exclude test_.*  # or -e test_.*
```

### `-a, --all` flag

> Remove all unused imports (not just those
> [checked from side effects](?id=side-effects)).

#### Default

> `False`

#### Behaviour

- Remove all unused import statements whether they has side effects or not!
- Faster results, because Pycln will skip side effects analyzing.

#### Usage

```bash
$ pycln /path/ --all  # or -a
```

#### Example

> original /example.py

```python
import x  # has unnecessary side effects
import y
```

> fixed /example.py (without `-a, --all`, default)

`x` module has considered as import with side effects. no change.

```python
import x  # has unnecessary side effects
import y
```

> fixed /example.py (with `-a, --all`)

`x` module has considered as unused import. has removed.

```python
import y
```

### `-c, --check` flag

> Do not write the files back, just return the status.

#### Default

> `False`

#### Behaviour

- Return code 0 means nothing would change.
- Return code 1 means some files would be changed.
- Return code 250 means there was an internal error.

#### Usage

```bash
$ pycln /path/ --check  # or -c
```

### `-d, --diff` flag

> Do not write the files back, just output a diff for each file on stdout.

#### Default

> `False`

#### Behaviour

- Output useful diffs without modifying the files.

#### Usage

```bash
$ pycln /path/ --diff  # or -d
```

#### Example

> original /example.py

```python
import x  # unused import
import y, z

y, z
```

> `$ pycln example.py --diff --all`

```bash
--- original/ example.py
+++ fixed/ example.py
@@ -1,4 +1,3 @@
-import x  # unused import
 import y, z

 y, z

All done! 💪 😎
1 import would be removed, 1 file would be changed.
```

### `-v, --verbose` flag

> Also emit messages to stderr about files that were not changed and about files/imports
> that were ignored.

#### Default

> `False`

#### Behaviour

- Also the report ignored files/imports counters will be enabled.

#### Usage

```bash
$ pycln /path/ --verbose  # or -v
```

### `-q, --quiet` flag

> Do not emit both removed and expanded imports and non-error messages to stderr.

#### Default

> `False`

#### Behaviour

- Errors are still emitted; silence those with `-s, --silence`.
- Has no effect when used with `--diff`.
- Counters are still enabled.

#### Usage

```bash
$ pycln /path/ --quiet  # or -q
```

### `-s, --silence` flag

> Silence both stdout and stderr.

#### Default

> `False`

#### Behaviour

- Uncaught errors are sill emitted; silence those with `2>/dev/null`. (not recommended)
- No output even when `--check` has specified.
- `--diff` output is still emitted.

#### Usage

```bash
$ pycln /path/ --silence  # or -s
```

### `-x, --expand-stars` flag

> Expand wildcard star imports.

#### Default

> `False`

#### Behaviour

- It works if only if the module is importable.
- Slower results, because Pycln will do importables analyzing.
- UnexpandableImportStar message will be emitted to stderr if the module is not
  importable.

#### Usage

```bash
$ pycln /path/ --expand-stars  # or -x
```

#### Example

> original /example.py

```python
from time import *
from os import *

sleep(time())
print(path.join("projects", "pycln"))
```

> `$ pycln example.py --expand-stars --diff`

```bash
--- original/ example.py
+++ fixed/ example.py
@@ -1,5 +1,5 @@
-from time import *
-from os import *
+from time import sleep, time
+from os import path

 sleep(time())
 print(path.join("projects", "pycln"))

All done! 💪 😎
2 imports would be expanded, 1 file would be changed.
```

### `--no-gitignore` flag

> Do not ignore `.gitignore` patterns.

#### Default

> `False`

#### Behaviour

- Also reformat `.gitignore` excluded files.
- Do nothing if `.gitignore` is not present.

#### Usage

```bash
$ pycln /path/ --no-gitignore
```

### `--version` flag

> Show the version and exit.

#### Default

> `False`

#### Behaviour

- Show the current Pycln version.
- Exit with code 0.

#### Usage

```bash
$ pycln --version
```

### `--install-completion` flag

> Install completion for the current shell.

#### Default

> `None`

#### Behaviour

- Windows Powershell is not supported.

#### Usage

```bash
$ pycln --install-completion
```

### `--show-completion` flag

> Show completion for the current shell, to copy it or customize the installation.

#### Default

> `None`

#### Behaviour

- Only output the completion script.

#### Usage

```bash
$ pycln --show-completion
```

## GUI For Windows

> Come on! 😂

# Supported Cases

## General

> All bellow cases and more are considered as used.

### Single Line

- Import:

  ```python
  import x, y
  import a as b
  import foo.bar

  foo.bar(b)
  y = 5
  print(x)
  ```

- Import From:

  ```python
  from xxx import x, y
  from abc import a as b
  from metasyntactic import foo.bar
  from metasyntactic.foo import baz

  foo.bar(baz(b))
  y = 5
  print(x)
  ```

### Multi Line

- Import:

  ```python
  import \
      x, y

  print(x, y)
  ```

- Import From:

  ```python
  from xxx import (
      x,
      y
  )
  from metasyntactic import foo, \
      bar

  print(foo(bar(x, y)))
  ```

## Special cases

### Side Effects

> Pycln takes imports that has side effects into account.

Some behaviours:

- These behaviours will be changed if [`-a, --all` flag](?id=-a-all-flag) has specified.
- All Python standrad modules are considered as imports without side effects **except**
  ([this](https://www.python.org/dev/peps/pep-0020/),
  [antigravity](http://python-history.blogspot.com/2010/06/import-antigravity.html),
  [rlcompleter](https://docs.python.org/3.8/library/rlcompleter.html)).
- Third party and local modules will be statically analyzed, there are three cases:
  - `HasSideEffects.YES` ~> considered as used.
  - `HasSideEffects.MAYBE` ~> considered as used.
  - `HasSideEffects.NO` ~> considered as not used.

### Try..Except

> Pycln can understand `try..except (Some Import Exceptions..)` case.

Supported built-in exceptions:

- [ModuleNotFoundError](https://docs.python.org/3/library/exceptions.html#ModuleNotFoundError).
- [ImportError](https://docs.python.org/3/library/exceptions.html#ImportError).
- [ImportWarning](https://docs.python.org/3/library/exceptions.html#ImportWarning).

Supported blocks:

- [try](https://docs.python.org/3/tutorial/errors.html#handling-exceptions).
- [except](https://docs.python.org/3/tutorial/errors.html#handling-exceptions).
- [else](https://docs.python.org/3/tutorial/errors.html#handling-exceptions).

All bellow imports are considered as used:

- `try..except`:
  ```python
  try:
      import x_for_py38
  except ModuleNotFoundError:  # Can be tuple of exceptions.
      import x_for_py36
  ```
- `try..except..else`:
  ```python
  try:
      import x_for_py38
  except ModuleNotFoundError:  # Can be tuple of exceptions.
      import x_for_py36
  else:
      import y
  ```

### Implicit Imports From Sub-Packages

> Pycln can deal with implicit imports from sub-packages.

For example:

```python
import os.path  # marked as used.

print(os.getpid())
```

### Import With Importlib

> Not supported, also not on the
> [roadmap](https://github.com/hadialqattan/pycln/projects/3).

### Typing

> Pycln takes [Python 3.5+ type hints](https://www.python.org/dev/peps/pep-0484/) into
> account.

```python
from typing import List, Tuple  # marked as used.

foo: List[str] = []

def bar() -> Tuple[int, int]:
    return (0, 1)
```

#### String

> Pycln can understand string type hints.

All bellow imports are considered as used:

- Fully string A:

  ```python
  from ast import Import
  from typing import List

  def foo(bar: "List[Import]"):
      pass
  ```

- Fully string B:

  ```python
  from ast import Import
  from typing import List

  def foo(bar: "List['Import']"):
      pass
  ```

- Semi string:

  ```python
  from ast import Import
  from typing import List

  def foo(bar: List["Import"]):
      pass
  ```

#### Comments

> Pycln takes
> [Python 3.8+ variable annotations](https://www.python.org/dev/peps/pep-0526/) into
> account.

All bellow imports are considered as used:

- Assign:

  ```python
  from typing import List

  foo = []  # type: List[str]
  ```

- Argument:

  ```python
  from typing import List

  def foo(
      bar  # type: List[str]
  ):
      pass
  ```

- Function:

  ```python
  from typing import List, Tuple

  def foo(bar):
      # type: (List[str]) -> Tuple[int]
      return (int(bar[0][0]), 1)
  ```

#### Cast

> Pycln can understand `typing.cast` case.

All bellow imports are considered as used:

```python
from typing import cast
import foo, bar

baz = cast("foo", bar)  # or typing.cast("foo", bar)
```

### All (`__all__`)

> Pycln looks at the items in the `__all__` list, if it match the imports, marks it as
> used.

```python
import os, time  # These imports are considered as used.

__all__ = ["os", "time"]
```

#### List Operations (append and extend)

> Pycln considers `__all__.append` arguments and `__all__.extend` list items as used
> names.

- Append:

  ```python
  import os, time  # These imports are considered as used.

  __all__.append("os", "time")
  ```

- Extend:

  ```python
  import os, time  # These imports are considered as used.

  __all__.extend(["os", "time"])
  ```

#### List Concatenation

> Pycln can deal with almost all types of list concatenation.

- Normal concatenation:

  ```python
  import os, time  # These imports are considered as used.

  __all__ = ["os"] + ["time"]
  ```

- Augmented assignment:

  ```python
  import os, time  # These imports are considered as used.

  __all__ += ["os", "time"]
  ```

- Augmented assignment with concatenation:

  ```python
  import os, time  # These imports are considered as used.

  __all__ += ["os"] + ["time"]
  ```

#### List Comprehension

> Not supported, also not on the
> [roadmap](https://github.com/hadialqattan/pycln/projects/3).

# Integrations

## Version Control Integration

- Use [pre-commit](https://pre-commit.com/). Once you have it
  [installed](https://pre-commit.com/#install), add this to the
  `.pre-commit-config.yaml` in your project:

  ```yaml
  - repo: https://github.com/hadialqattan/pycln
    rev: stable # Possible releases: https://github.com/hadialqattan/pycln/releases
    hooks:
      - id: pycln
        args: [--config=pyproject.toml]
  ```

  - Avoid using `args` in the hook. Instead, store necessary configuration in
    [pyproject.toml](?id=-config-path-option) so that CLI usage of Pycln behave
    consistently for your project.

  - Stable branch points to the latest released version.

- On your `pyproject.toml` add this section (optional):

  ```toml
  [tool.pycln]
  all = true
  ```

- Then run `pre-commit install` and you’re ready to go.
