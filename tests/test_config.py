"""pycln/utils/config.py tests."""
# pylint: disable=R0201,W0613
import re
from pathlib import Path
from unittest import mock

import pytest
from typer import Exit

from pycln.utils import config

from . import CONFIG_DIR
from .utils import sysu

# Constants.
MOCK = "pycln.utils.config.%s"
CONFIG_SECTIONS = config.CONFIG_SECTIONS
CONFIG_FILES = {
    CONFIG_DIR.joinpath(path)
    for path in (
        "setup.cfg",
        "pyproject.toml",
        "settings.json",
        "pycln.yaml",
        "pycln.yml",
    )
}
CONFIG_ATTR = frozenset(
    {
        "paths",
        "include",
        "exclude",
        "extend_exclude",
        "all_",
        "check",
        "diff",
        "verbose",
        "quiet",
        "silence",
        "expand_stars",
        "no_gitignore",
    }
)
DEFAULTS = {
    "paths": [Path(".")],
    "include": re.compile(r".*_util.py$", re.IGNORECASE),
    "exclude": re.compile(r".*_test.py$", re.IGNORECASE),
    "extend_exclude": re.compile(r".*fuzz.py$", re.IGNORECASE),
    "all": True,  # For `TestParserConfigFile`.
    "all_": True,  # For `TestConfig`.
    "check": False,
    "diff": True,
    "verbose": True,
    "quiet": False,
    "silence": False,
    "expand_stars": True,
    "no_gitignore": False,
}


class TestConfig:

    """`config.Config` class tests."""

    @pytest.mark.parametrize(
        "config_",
        [
            pytest.param(None, id="no config file"),
            pytest.param(Path(CONFIG_DIR).joinpath("setup.cfg"), id="with config file"),
        ],
    )
    @mock.patch(MOCK % "ParseConfigFile.__init__")
    @mock.patch(MOCK % "Config._check_path")
    @mock.patch(MOCK % "Config._check_regex")
    def test_post_init(self, _check_regex, _check_path, init, config_):
        init.return_value = None
        configs = config.Config(
            paths=[Path(".")],
            config=config_,
            include=DEFAULTS["include"],
            exclude=DEFAULTS["exclude"],
            extend_exclude=DEFAULTS["extend_exclude"],
            expand_stars=True,
            verbose=True,
            diff=True,
            all_=True,
        )
        for attr in CONFIG_ATTR:
            if attr != "all":
                assert getattr(configs, attr) == DEFAULTS[attr]
        assert configs.paths == [Path(".")]

    @pytest.mark.parametrize(
        "paths, expec_paths",
        [
            pytest.param([Path(".")], [Path(".")], id="single directory"),
            pytest.param([Path(__file__)], [Path(__file__)], id="single file"),
            pytest.param(
                [Path("."), Path("..")],
                [Path("."), Path("..")],
                id="multiple directories",
            ),
            pytest.param([Path(__file__)], [Path(__file__)], id="single file"),
            pytest.param(
                [Path(__file__), Path(__file__).parent.joinpath("test_cli.py")],
                [Path(__file__), Path(__file__).parent.joinpath("test_cli.py")],
                id="mltiple files",
            ),
        ],
    )
    @mock.patch(MOCK % "Config._check_regex")
    def test_check_path(self, _check_regex, paths, expec_paths):
        configs = config.Config(paths=paths)
        assert configs.paths == expec_paths

    @pytest.mark.xfail(raises=Exit)
    @pytest.mark.parametrize(
        "paths",
        [
            pytest.param(None, id="empty path"),
            pytest.param(
                [Path("not_exists1"), Path("not_exists2")],
                id="multiple not exist paths",
            ),
            pytest.param(
                [Path("not_exists")],
                id="not exists path",
            ),
        ],
    )
    @mock.patch(MOCK % "Config._check_regex")
    def test_check_path_xfail(self, _check_regex, paths):
        with sysu.std_redirect(sysu.STD.ERR):
            config.Config(paths=paths)


class TestParseConfigFile:

    """`config.ParseConfigFile` class tests."""

    @mock.patch(MOCK % "ParseConfigFile.__init__")
    @mock.patch(MOCK % "Config.__post_init__")
    def setup_method(self, method, post_init, init):
        self.configs = config.Config(paths=[Path(".")])

    def test_cast_paths(self):
        str_paths = ["./pycln/src", "home/src/__init__.py"]
        casted_paths = config.ParseConfigFile._cast_paths(str_paths)
        expec = [Path("./pycln/src"), Path("home/src/__init__.py")]
        assert casted_paths == expec

    @pytest.mark.xfail(raises=Exit)
    @pytest.mark.parametrize(
        "path",
        [
            pytest.param(
                Path("not_exists_path.cfg"),
                id="not exists path",
            ),
            pytest.param(
                CONFIG_DIR.joinpath("invalid_type.invalid"),
                id="not supported type",
            ),
        ],
    )
    @mock.patch(MOCK % "Config.__post_init__")
    def test_parse(self, post_init, path):
        with sysu.std_redirect(sysu.STD.ERR):
            config.ParseConfigFile(path, self.configs)

    @pytest.mark.parametrize(
        "configs",
        [
            pytest.param(DEFAULTS, id="valid"),
            pytest.param({**DEFAULTS, **{"Invalid": "data"}}, id="invalid"),
        ],
    )
    @mock.patch(MOCK % "Config.__post_init__")
    @mock.patch(MOCK % "ParseConfigFile.parse")
    def test_config_loader(self, parse, post_init, configs):
        config_parser = config.ParseConfigFile(Path(""), self.configs)
        config_parser._config_loader(configs)
        for attr in CONFIG_ATTR:
            if attr != "all":
                assert getattr(self.configs, attr) == configs[attr]
        assert getattr(self.configs, "Invalid", None) is None

    @pytest.mark.parametrize(
        "configs",
        [
            pytest.param({**DEFAULTS, **{"path": "/path/file.py"}}, id="single-path"),
            pytest.param(
                {**DEFAULTS, **{"paths": ["/path/src", "/path/file.py"]}},
                id="multiple-paths",
            ),
        ],
    )
    @mock.patch(MOCK % "Config.__post_init__")
    @mock.patch(MOCK % "ParseConfigFile.parse")
    def test_config_loader_with_paths(self, parse, post_init, configs):
        config_parser = config.ParseConfigFile(Path(""), self.configs)
        config_parser._config_loader(configs)
        if configs.get("path", None) is not None:
            configs["paths"] = [configs["path"]]
        paths = [Path(p) for p in configs["paths"]]
        assert getattr(self.configs, "paths") == paths
        assert getattr(self.configs, "path", None) is None

    @pytest.mark.parametrize(
        "file_path",
        [pytest.param(path, id=path.parts[-1]) for path in CONFIG_FILES],
    )
    @mock.patch(MOCK % "Config.__post_init__")
    def test_parse_methods(self, post_init, file_path):
        # Test `_parse_*` methods:
        #:  - _parse_cfg.
        #:  - _parse_toml.
        #:  - _parse_json.
        #:  - _parse_yaml.
        #:  - _parse_yml.
        config.ParseConfigFile(file_path, self.configs)
        for type_ in ("include", "exclude", "extend_exclude"):
            regex = getattr(self.configs, type_)
            setattr(self.configs, type_, re.compile(regex, re.IGNORECASE))
        for attr in CONFIG_ATTR:
            if attr != "all":
                assert getattr(self.configs, attr) == DEFAULTS[attr]
