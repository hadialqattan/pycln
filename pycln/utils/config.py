"""Pycln configuration management utility."""
import configparser
import json
import tokenize
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Pattern, Set, Union

import tomlkit
import typer
import yaml

from . import iou, regexu

# Constants.
CONFIG_SECTIONS = {
    ".cfg": "pycln",
    ".toml": "tool.pycln",
    ".json": "pycln",
    ".yaml": "pycln",
    ".yml": "pycln",
}


@dataclass
class Config:

    """Pycln configs dataclass."""

    def __post_init__(self):
        if self.config is not None:
            file_path = self.config
            self.config = None
            ParseConfigFile(file_path, self)
        else:
            self._check_path()
            self._check_regex()
            self._parse_skip_imports()
            self._check_skip_imports()

    paths: List[Path]
    skip_imports: Set[str]
    config: Optional[Path] = None
    include: Pattern[str] = regexu.INCLUDE_REGEX  # type: ignore
    exclude: Pattern[str] = regexu.EXCLUDE_REGEX  # type: ignore
    extend_exclude: Pattern[str] = regexu.EMPTY_REGEX  # type: ignore
    all_: bool = False
    check: bool = False
    diff: bool = False
    verbose: bool = False
    quiet: bool = False
    silence: bool = False
    expand_stars: bool = False
    no_gitignore: bool = False
    disable_all_dunder_policy: bool = False

    def _parse_skip_imports(self) -> None:
        #: Converts "x,y,z" syntax into {"x", "y", "z"} set.
        #:
        #: Given {"x,y,z", "m", "n"}, `self.skip_imports`
        #: turns into {"x", "y", "z", "m", "n"}.
        names: Set[str] = set({})
        for name in self.skip_imports:
            if "," in name:
                names.update(name.strip(",").split(","))
            else:
                names.add(name)
        self.skip_imports = names

    def _check_path(self) -> None:
        # Validate `self.paths`.
        if self.paths:
            for path in self.paths.copy():
                if not (path.is_dir() or path.is_file()):
                    if path == iou.STDIN_NOTATION:
                        continue
                    self.paths.remove(path)

        if not self.paths:
            typer.secho(
                "No Path provided. Nothing to do 😴",
                bold=True,
                err=True,
            )
            raise typer.Exit(1)

    def _check_skip_imports(self) -> None:
        #: Validate `self.skip_imports`.
        #:
        #: NOTE: This method should be invocated
        #: just after `_parse_skip_imports`.
        for name in self.skip_imports:
            if not name.isidentifier():
                typer.secho(
                    f"--skip-imports: {name!r} is not a valid module name! 😅",
                    bold=True,
                    err=True,
                )
                raise typer.Exit(1)

    def _check_regex(self) -> None:
        # Validate `self.include/exclude/extend_exclude`.
        self.include: Pattern[str] = regexu.safe_compile(
            str(self.include), regexu.INCLUDE
        )
        self.exclude: Pattern[str] = regexu.safe_compile(
            str(self.exclude), regexu.EXCLUDE
        )
        self.extend_exclude: Pattern[str] = regexu.safe_compile(
            str(self.extend_exclude), regexu.EXCLUDE
        )


class ParseConfigFile:

    """Conifg file parser.

    :param file_path: config file path.
    :param config: Config instance as base.
    """

    def __init__(self, file_path: Path, config: Config):
        self._path = file_path
        self._config = config
        self._section = CONFIG_SECTIONS.get(self._path.suffix, None)
        self.parse()
        self._config.__post_init__()

    @staticmethod
    def _cast_paths(paths: List[str]) -> List[Path]:
        """`paths` List[str] ~> List[Path]."""
        return [Path(p) for p in paths]

    def parse(self) -> None:
        """Get conifg from a `cfg`/`toml`/`json`/`yaml`/`yml` file."""
        if not self._path.is_file():
            typer.secho(
                f"Config file {str(self._path)!r} does not exist 😅",
                bold=True,
                err=True,
            )
            raise typer.Exit(1)
        if self._section is None:
            typer.secho(
                f"Config file {str(self._path)!r} is not supported 😅",
                bold=True,
                err=True,
            )
            typer.secho(f"Supported types: {CONFIG_SECTIONS.keys()}.", err=True)
            raise typer.Exit(1)
        getattr(self, f"_parse_{self._path.suffix.strip('.')}")()

    def _parse_cfg(self) -> None:
        # Parse `.cfg` file.
        parser = configparser.ConfigParser(allow_no_value=True)
        parser.read(self._path)
        cfg_data = parser._sections.get(self._section, {})  # type: ignore

        def cast_bool(v: str) -> Union[str, bool]:
            if v.lower() == "true":
                return True
            elif v.lower() == "false":
                return False
            return v

        configs = {k: cast_bool(v) for k, v in cfg_data.items()}

        if configs.get("skip_imports", None) is not None:
            #: parse `skip_imports` cases:
            #:
            #: skip_imports = [x, y]
            #: skip_imports = x,y
            skip_imports = configs["skip_imports"]
            skip_imports = set(
                skip_imports.strip('[]"').replace(" ", "").split(",")  # type: ignore
            )
            configs["skip_imports"] = skip_imports

        self._config_loader(configs)

    def _parse_toml(self) -> None:
        # Parse `.toml` file.
        with tokenize.open(self._path) as stream:
            parsed_toml = tomlkit.parse(stream.read())
        tool, pycln = self._section.split(".")
        configs = parsed_toml.get(tool, {}).get(pycln, {})
        self._config_loader(configs)

    def _parse_json(self) -> None:
        # Parse `.json` file.
        with tokenize.open(self._path) as stream:
            parsed_json = json.load(stream)
        configs = parsed_json.get(self._section, {})
        self._config_loader(configs)

    def _parse_yaml(self) -> None:
        # Parse `.yaml` file.
        with tokenize.open(self._path) as stream:
            parsed_yaml = yaml.load(stream, Loader=yaml.SafeLoader)
        configs = parsed_yaml.get(self._section, {})
        self._config_loader(configs)

    def _parse_yml(self) -> None:
        # Support `.yml` file.
        return self._parse_yaml()

    def _config_loader(self, config_dict: dict) -> None:
        # k, v: config loader.
        if config_dict:
            for k, v in config_dict.items():
                # Python preserved name.
                # `all` ~> `all_`.
                if k == "all":
                    k = "all_"

                # Set defaultable CLI options.
                if hasattr(Config, k):
                    setattr(self._config, k, v)

                # Set non-defaultable CLI options manually.
                elif k == "skip_imports":
                    setattr(self._config, k, set(v))

                # Both `path` and `paths` can be used as `paths` CLI arg.
                if k in ("path", "paths"):
                    if k == "path":
                        k = "paths"
                        v = [v]

                    # List[str] ~> List[Path]
                    v = ParseConfigFile._cast_paths(v)

                    # Set the [paths] CLI argument.
                    setattr(self._config, k, v)
