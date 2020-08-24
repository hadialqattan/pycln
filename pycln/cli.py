"""
Pycln CLI implementation.
"""
from pathlib import Path
from typing import Generator

import typer

from . import __name__, version_callback
from .utils import config, pathu, refactor, regexu, report

# Constants.
EMPTY = ""

app = typer.Typer(name=__name__, add_completion=False)


@app.command(context_settings=dict(help_option_names=["-h", "--help"]))
def main(
    path: Path = typer.Argument(None, help="A path to start searching from."),
    include: str = typer.Option(
        regexu.INCLUDE_REGEX,
        "--include",
        "-i",
        show_default=True,
        help="A regular expression that matches files and directories that should be included on recursive searches. An empty value means all files are included regardless of the name. Use forward slashes for directories on all platforms (Windows, too). Exclusions are calculated first, inclusions later.",
    ),
    exclude: str = typer.Option(
        regexu.EXCLUDE_REGEX,
        "--exclude",
        "-e",
        show_default=True,
        help="A regular expression that matches files and directories that should be exclude on recursive searches. An empty value means no paths are excluded. Use forward slashes for directories on all platforms (Windows, too). Exclusions are calculated first, inclusions later.",
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
        help="Don't write the files back, just return the status. Return code 0 means nothing would change. Return code 1 means some files would be changed. Return code 500 means there was an internal error.",
    ),
    diff: bool = typer.Option(
        False,
        "--diff",
        "-d",
        show_default=True,
        help="Don't write the files back, just output a diff for each file on stdout.",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        show_default=True,
        help="Also emit messages to stdout about removed imports and to stderr about files that were not changed or were ignored due to `--exclude` or `.gitignore`.",
    ),
    quiet: bool = typer.Option(
        False,
        "--quiet",
        "-q",
        show_default=True,
        help="Don't emit non-error messages to stderr. Errors are still emitted; silence those with `-s, --silence` or with 2>/dev/null.",
    ),
    silence: bool = typer.Option(
        False,
        "--silence",
        "-s",
        show_default=True,
        help="Silence both stdout and stderr. it is not recommended.",
    ),
    expand_star_imports: bool = typer.Option(
        False,
        "--expand-star-imports",
        help="Expand wildcard star imports. it works if only if the module is importable.",
    ),
    no_gitignore: bool = typer.Option(
        False,
        "--no-gitignore",
        show_default=True,
        help="Set to ignore `.gitignore` patterns. if present.",
    ),
    version: bool = typer.Option(
        None, "--version", callback=version_callback, help="Show the version and exit.",
    ),
) -> None:
    configs = config.Config(
        path=path,
        include=include,
        exclude=exclude,
        all_=all_,
        check=check,
        diff=diff,
        verbose=verbose,
        quiet=quiet,
        silence=silence,
        expand_star_imports=expand_star_imports,
        no_gitignore=no_gitignore,
    )
    reporter = report.Report(configs)
    gitignore = regexu.get_gitignore(
        configs.path if not configs.no_gitignore else EMPTY
    )
    sources: Generator = pathu.yield_sources(
        configs.path, configs.include, configs.exclude, gitignore, reporter
    )
    refactor.Refactor(configs, reporter, sources)
    # Print the report.
    typer.echo(str(reporter))
    # Set the correct exit code and exit.
    typer.Exit(reporter.exit_code)
