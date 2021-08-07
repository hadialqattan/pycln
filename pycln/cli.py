"""Pycln CLI implementation."""
from pathlib import Path
from typing import Generator, List, Optional

import typer

from . import __doc__, __name__, version_callback
from .utils import pathu, refactor, regexu, report
from .utils.config import Config

app = typer.Typer(name=__name__, add_completion=True)


@app.command(context_settings=dict(help_option_names=["-h", "--help"]))
def main(  # pylint: disable=R0913,R0914
    paths: List[Path] = typer.Argument(None, help="Directories or files paths."),
    config: Optional[Path] = typer.Option(
        None,
        "--config",
        show_default=False,
        help="Read configuration from a file.",
    ),
    include: str = typer.Option(
        regexu.INCLUDE_REGEX,
        "--include",
        "-i",
        show_default=True,
        help=(
            "A regular expression that matches files and directories"
            " that should be included on recursive searches."
            " An empty value means all files are included regardless of the name."
            " Use forward slashes for directories on all platforms (Windows, too)."
            " Exclusions are calculated first, inclusions later."
        ),
    ),
    exclude: str = typer.Option(
        regexu.EXCLUDE_REGEX,
        "--exclude",
        "-e",
        show_default=True,
        help=(
            "A regular expression that matches files and directories"
            " that should be exclude on recursive searches."
            " An empty value means no paths are excluded."
            " Use forward slashes for directories on all platforms (Windows, too)."
            " Exclusions are calculated first, inclusions later."
        ),
    ),
    all_: bool = typer.Option(
        False,
        "--all",
        "-a",
        show_default=True,
        help="Remove all unused imports (not just those checked from side effects).",
    ),
    check: bool = typer.Option(
        False,
        "--check",
        "-c",
        show_default=True,
        help=(
            "Do not write the files back, just return the status."
            " Return code 0 means nothing would change."
            " Return code 1 means some files would be changed."
            " Return code 250 means there was an internal error."
        ),
    ),
    diff: bool = typer.Option(
        False,
        "--diff",
        "-d",
        show_default=True,
        help="Do not write the files back, just output a diff for each file on stdout.",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        show_default=True,
        help=(
            "Also emit messages to stderr about files"
            " that were not changed and about files/imports that were ignored."
        ),
    ),
    quiet: bool = typer.Option(
        False,
        "--quiet",
        "-q",
        show_default=True,
        help=(
            "Do not emit both removed and expanded imports "
            "and non-error messages to stderr."
            " Errors are still emitted;"
            " silence those with `-s, --silence`"
        ),
    ),
    silence: bool = typer.Option(
        False,
        "--silence",
        "-s",
        show_default=True,
        help=(
            "Silence both stdout and stderr."
            " Uncaught errors are sill emitted;"
            " silence those with 2>/dev/null."
            " (not recommended)."
        ),
    ),
    expand_stars: bool = typer.Option(
        False,
        "--expand-stars",
        "-x",
        help=(
            "Expand wildcard star imports."
            " It works if only if the module is importable."
        ),
    ),
    no_gitignore: bool = typer.Option(
        False,
        "--no-gitignore",
        show_default=True,
        help="Do not ignore `.gitignore` patterns. if present.",
    ),
    version: bool = typer.Option(  # pylint: disable=W0613
        None,
        "--version",
        callback=version_callback,
        help="Show the version and exit.",
    ),
):
    configs = Config(
        paths=paths,
        config=config,
        include=include,  # type: ignore
        exclude=exclude,  # type: ignore
        all_=all_,
        check=check,
        diff=diff,
        verbose=verbose,
        quiet=quiet,
        silence=silence,
        expand_stars=expand_stars,
        no_gitignore=no_gitignore,
    )
    reporter = report.Report(configs)
    session_maker = refactor.Refactor(configs, reporter)
    for path in configs.paths:
        gitignore = regexu.get_gitignore(
            path if path.is_dir() else path.parent, configs.no_gitignore
        )
        sources: Generator = pathu.yield_sources(
            path, configs.include, configs.exclude, gitignore, reporter
        )
        for source in sources:
            session_maker.session(source)
    # Print the report.
    typer.echo(str(reporter), nl=False)
    # Set the correct exit code and exit.
    exit(reporter.exit_code)


# Override main function `__doc__`.
# This `__doc__` has read from `pyproject.toml`.
main.__doc__ = __doc__
