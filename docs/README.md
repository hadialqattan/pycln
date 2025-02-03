# Get Started

<img src="_media/logo-background-1200.png" width="100%" alt="Logo">

<p align="center">
    <quote>A formatter for finding and removing unused import statements.</quote>
</p>

<p align="center">
    <a href="https://hadialqattan.github.io/pycln"><img src="https://img.shields.io/badge/more%20info-Pycln%20Docs-B5FFB3.svg?style=flat-square" alt="Pycln Docs"></a>
    <a href="https://github.com/hadialqattan/pycln/actions?query=workflow%3ACI"><img src="https://img.shields.io/github/actions/workflow/status/hadialqattan/pycln/ci.yml?branch=master&label=CI&logo=github&style=flat-square" alt="CI"></a>
    <a href="https://github.com/hadialqattan/pycln/actions?query=workflow%3ACD"><img src="https://img.shields.io/github/actions/workflow/status/hadialqattan/pycln/cd.yml?label=CD&logo=github&style=flat-square" alt="CD"></a>
    <a href="https://github.com/hadialqattan/pycln/actions?query=workflow%3AFUZZ"><img src="https://img.shields.io/github/actions/workflow/status/hadialqattan/pycln/fuzz.yml?label=FUZZ&logo=github&style=flat-square" alt="FUZZ"></a>
    <a href="https://www.codacy.com/manual/hadialqattan/pycln/dashboard?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=hadialqattan/pycln&amp;utm_campaign=Badge_Grade"><img src="https://img.shields.io/codacy/grade/e7c6c290c3c149e484634ac1905800d6/master?style=flat-square" alt="Codacy Badge"></a>
    <a href="https://codecov.io/gh/hadialqattan/pycln"><img src="https://img.shields.io/codecov/c/gh/hadialqattan/pycln/master?token=VVYBDCZPHR&style=flat-square" alt="Codecov"></a>
    <a href="https://codeclimate.com/github/hadialqattan/pycln/maintainability"><img src="https://img.shields.io/codeclimate/maintainability/hadialqattan/pycln?style=flat-square" alt="Maintainability"></a>
</p>

<p align="center">
    <img src="https://img.shields.io/pypi/pyversions/pycln?style=flat-square" alt="PYPI - Python Version">
    <a href="https://pypi.org/project/pycln/"><img src="https://img.shields.io/pypi/v/pycln?style=flat-square" alt="PYPI - Pycln Version"></a>
    <a href="https://pepy.tech/project/pycln/"><img src="https://static.pepy.tech/personalized-badge/pycln?period=total&units=international_system&left_color=grey&right_color=brightgreen&left_text=total downloads" alt="Total Downloads"></a>
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

<p align="center">
    <a href="https://docutils.sourceforge.io/rst.html"><img src="https://img.shields.io/badge/docstrings-reStructuredText-gree.svg?style=flat-square" alt="Docstrings: reStructuredText"></a>
    <a href="https://github.com/psf/black"><img src="https://img.shields.io/badge/code%20style-black-000000.svg?style=flat-square" alt="Code style: black"></a>
    <a href="https://github.com/prettier/prettier"><img src="https://img.shields.io/badge/code%20style-prettier-ff69b4.svg?style=flat-square" alt="Code style: prettier"></a>
</p>

# Installation

## Latest Release (PYPI)

Pycln requires Python 3.8+ and can be easily installed using the most common Python
packaging tools. We recommend installing the latest stable release from PyPI with pip:

```bash
$ pip install pycln
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

It doesn't matter which installation method you have used, Uninstall can be done with
[`uninstall.sh`](https://github.com/hadialqattan/pycln/tree/master/scripts/uninstall.sh)
(pip):

```bash
$ ./scripts/uninstall.sh
```

# Usage

> NOTE: Make sure the Python version you run Pycln with is the same or more recent than
> the Python version your codebase targets.

## The Simplest Usage

By **default** Pycln **removes** any unused import statement, So the simplest usage is
to specify only the path:

```bash
$ pycln [PATH]  # using -a/--all flag is recommended.
```

## Pycln Skips

### Import Skip

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

### File Wide Skip

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

### Global skip

> Skip module/package/library imports for all files (globally).

Please see [--skip-imports](?id=-skip-imports-option) option.

## CLI Arguments

### Paths

> Directories' paths and/or files' paths and/or reading from stdin.

NOTE: Pycln treats `.pyi` files as regular `.py` files in the pathfinding functionality,
so anything true for `.py` files is true for `.pyi` files as well.

#### Usage

- Specify a directory to handle all its subdirs/files (recursively):
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
- Reading from `STDIN` (`-` as a file path):

  ```bash
  $ cat file.py | pycln -  # please read the notes below which clarifies the necessity of using `-s/--silence` flag.
  ```

  Notes about reading from `STDIN`:

  - For the time being, both the final report and the formatted code will be sent to
    `STDOUT`, therefore, it's necessary to use [`-s/--silence`](?id=-s-silence-flag)
    flag in order to receive only the formatted code via `STDOUT`.
  - You can read from `STDIN` and provide normal paths at the same time (the order
    doesn't matter).

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

A NOTE BEFORE THE EXAMPLES:

```note
#: The path argument can be passed either
#: via `paths` keyword as a *list* like:
paths = ["/path/to/src", "./file.py"]

#: OR

#: via `path` keyword as a *string*, for example:
path = "/path/to/src"
```

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
disable_all_dunder_policy = False
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
disable_all_dunder_policy=false
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
  disable_all_dunder_policy: false
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
    "no_gitignore": false,
    "disable_all_dunder_policy": false
  }
}
```

</details>

### `--skip-imports` option

> Skip module/package/library imports for all files (globally).

#### Default

> `[]`

#### Behaviour

- Takes a list of module/package/library names and skips any import belonging to them.

#### Usage

- Via CLI by providing:

  - a list of names in a pythonic list format:
    ```bash
    $ pycln --skip-imports [x, y, z]
    ```
  - a list of names in a comma separated str format:
    ```bash
    $ pycln --skip-imports x,y,z
    ```
  - `--skip-imports` multiple times:
    ```bash
    $ pycln --skip-imports x --skip-imports y
    ```

- Via a [config file](?id=-config-path-option) (`.toml`, `.cfg`, `.yaml`, `.yml`,
  `.json`) by providing:
  - a list of names in a pythonic list format (`.toml` example):
    ```.toml
    skip_imports = [x, y, z]
    ```
  - a list of names in a comma separated str format (`.toml` example):
    ```.toml
    skip_imports = "x,y,z"
    ```
  - unlike CLI, you can't provide multiple `skip_imports` keys.

### `-i, --include TEXT` option

> A regular expression that matches files and directories that should be included on
> recursive searches.

#### Default

> `.*\.pyi?$`

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

### `-ee, --extend-exclude TEXT` option

> Like --exclude, but adds additional files and directories on top of the excluded ones.
> (Useful if you simply want to add to the default).

#### Default

> `^$` (empty regex)

#### Behaviour

- An empty value means no paths are excluded.
- Use forward slashes for directories on all platforms (Windows, too).
- Exclusions are calculated first, inclusions later.

#### Usage

Assume that we have four files (`util_a.py`, `util_b.py`, `test_a.py`, `test_b.py`) on a
directory called `project` and we want to reformat files that not start with `test_`:

```bash
$ pycln /path_to/project/ --extend-exclude test_.*  # or -ee test_.*
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

### `--disable-all-dunder-policy` flag

> Stop enforcing the existence of the `__all__` dunder in `__init__.py` files.
> ([disabling this policy](#init-file-__init__py))

#### Default

> `False`

#### Behaviour

- Stop showing the missing `__all__` dunder in `__init__.py` files warning.
- Treating `__init__.py` files like regular `.py` files (formatting them even without
  the existence of the `__all__` dunder).

#### Usage

```bash
$ pycln /path/ --disable-all-dunder-policy
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

> All the cases below and more are considered as used.

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

All the imports below are considered as used:

- Fully string:

  ```python
  from ast import Import
  from typing import List

  def foo(bar: "List[Import]"):
      pass
  ```

- Nested string (Python 3.7+):

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

All the imports below are considered as used:

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

All the imports below are considered as used:

```python
from typing import cast
import foo, bar

baz = cast("foo", bar)  # or typing.cast("foo", bar)
```

#### TypeVar

> Pycln can understand `typing.TypeVar` 'str' cases.

All the imports below are considered as used:

```python
from typing import TypeVar
import Foo, Bar, Baz

T1 = TypeVar("T1", "Foo", "Bar")  # unbounded
T2 = TypeVar("T2", bound="Baz")  # bounded
```

#### TypeAlias

> Pycln can understand `typing.TypeAlias` and `typing_extensions.TypeAlias` annotation.

All the imports below are considered as used:

- `TypeAlias`:

  ```python
  from foo import BarClass
  from typing import TypeAlias  # OR: from typing_extensions import TypeAlias

  Baz: TypeAlias = "BarClass[str]"
  ```

- `typing.TypeAlias`:

  ```python
  from foo import BarClass
  import typing

  Baz: typing.TypeAlias = "BarClass[str]"
  ```

- `typing_extensions.TypeAlias`:

  ```python
  from foo import BarClass
  import typing_extensions

  Baz: typing_extensions.TypeAlias = "BarClass[str]"
  ```

#### Callable

> Pycln can understand `typing.Callable` and `collections.abc.Callable` function
> parameters types.

All the imports below are considered as used:

- `typing.Callable`:

  ```python
  from foo import BarClass
  from typing import Callable

  Baz: Callable[["BarClass"], None]
  ```

- `collections.abc.Callable`:

  ```python
  from foo import BarClass
  from collections.abc import Callable

  Baz: Callable[["BarClass"], None]
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

### Generics wrapping strings

> Pycln can understand imports used in generics and wrapped in string.

```python
from typing import Generic, TypeVar
from xxx import Baz  # marked as used.

CustomType = TypeVar("CustomType")

class Foo(Generic[CustomType]):
    ...

class Bar(Foo["Baz"]):  # <~
    ...
```

### Init file (`__init__.py`)

> Pycln can not decide whether the unused imported names are useless or imported to be
> used somewhere else (exported) in case of an `__init__.py` file with no `__all__`
> dunder.

> NOTE: this policy could be disabled using the
> [--disable-all-dunder-policy](#-disable-all-dunder-policy-flag) flag.

A detailed description of the problem:

consider the following two cases below:

- case a1:

  ```bash
  # Assume that we have this project structure:
  .
  ├── __init__.py
  └── file.py
  ```

  where `__init__.py`:

  ```python
  import x, y  #: These names are unused but imported to be used in another
              #: file in the same package.
              #:
              #: (Pycln should *NOT* remove this import statement).
  ```

  and `file.py`:

  ```python
  from . import x, y

  print(y(x))
  ```

- case a2:

  ```bash
  # Assume that we have this project structure:
  .
  └── __init__.py
  ```

  where `__init__.py`:

  ```python
  import x, y  #: These names are unused.
              #:
              #: (Pycln should remove this import statement).
  ```

Due to the nature of Pycln where it checks every file individually, it can not decide
whether `x` and `y` are imported to be exported (case a1) or imported but unused (case
a2), therefore, I consider using an `__all__` dunder is a good solution for this
problem.

NOTE: in case you're not sure about what an `__all__` dunder does, please consider
reading this stackoverflow [answer](https://stackoverflow.com/a/35710527/12738844)

Now let us review the same two cases but with an `__all__` dunder:

- case b1:

  ```bash
  # Assume that we have this project structure:
  .
  ├── __init__.py
  └── file.py
  ```

  where `__init__.py`:

  ```python
  import x, y  #: Luckily, Pycln can understand that `x` and `y`
              #: are exported so it would not remove them.
  __all__ = ["x", "y"]
  ```

  and `file.py`:

  ```python
  from . import x, y

  print(y(x))
  ```

- case b2:

  ```bash
  # Assume that we have this project structure:
  .
  └── __init__.py
  ```

  where `__init__.py`:

  ```python
  import x, y  #: In this case where an `__all__` dunder is used, Pycln
              #: can consider these names as unused confidently
              #: where they are inaccessible from other files
              #: (not exported).
  __all__ = ["something else or even an empty list"]
  ```

You may notice that using an `__all__` dunder makes the two cases distinguishable for
both the developers and QA tools.

### Stub files (`.pyi`) redundant aliases

> Pycln skips redundant alias imports in compliance with
> [PEP 484](https://peps.python.org/pep-0484/#stub-files) for the purposes of exporting
> modules and symbols for static type checking. Additionally, all symbols imported using
> `from foo import *` imports are considered publicly exported in a stub file, so these
> import statements are also ignored for `.pyi` extensions.

- case a:

  ```python
  import X as X  # marked as used.
  ```

- case b:

  ```python
  from X import Y as Y  # marked as used.
  ```

- case c:
  ```python
  from socket import *  # marked as used.
  ```

# Unsupported Cases

## Specific

> All the cases below are unsupported and not in the
> [roadmap](https://github.com/hadialqattan/pycln/projects/3). Only certain import
> statements are effected (not the entire file). Also, Pycln will not touch these cases
> at all to avoid any code break.

### Semicolon separation

```python
import x; import y

#: Pycln can not handle the above format.
#:
#: Of course you can fix this issue by rewriting the above code as:

import x
import y
```

### Colon inlined

```python
try: import x
finally: import y

#: Pycln can not handle the above format.
#:
#: Of course you can fix this issue by rewriting the above code as:

try:
    import x
finally:
    import y
```

## Global

> In case a file contains one of the below cases, the entire file would be skipped.

### Form feed character

> A form feed is a page-breaking ASCII control character. It forces the printer to eject
> the current page and to continue printing at the top of another.

```python
# It's a hidden character.
# Forms:
\x0c
\f
```

# Integrations

## Version Control Integration

- Use [pre-commit](https://pre-commit.com/). Once you have it
  [installed](https://pre-commit.com/#install), add this to the
  `.pre-commit-config.yaml` in your project:

  ```yaml
  - repo: https://github.com/hadialqattan/pycln
    rev: v2.5.0 # Possible releases: https://github.com/hadialqattan/pycln/releases
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

- You must have [Rust installed](https://www.rust-lang.org/tools/install) for the pycln hook to install in the pre-commit environment.

- Then run `pre-commit install` and you’re ready to go.
