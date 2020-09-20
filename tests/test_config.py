"""pycln/utils/config.py tests."""
import re
from pathlib import Path

import pytest
from pytest_mock import mock
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
CONFIG = {
    "include": re.compile(r".*_util.py$", re.IGNORECASE),
    "exclude": re.compile(r".*_test.py$", re.IGNORECASE),
    "expand_stars": True,
    "verbose": True,
    "diff": True,
    "all": True,  # For `TestParserConfigFile`.
    "all_": True,  # For `TestConfig`.
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
            path=Path("."),
            config=config_,
            include=CONFIG["include"],
            exclude=CONFIG["exclude"],
            expand_stars=True,
            verbose=True,
            diff=True,
            all_=True,
        )
        for attr, val in CONFIG.items():
            if attr != "all":
                assert getattr(configs, attr) == val
        assert configs.path == Path(".")

    @pytest.mark.parametrize(
        "path, expec_err",
        [
            pytest.param(None, "No Path provided. Nothing to do 😴\n", id="empty path"),
            pytest.param(
                Path("not_exists"),
                (
                    "'not_exists' is not a directory or a file."
                    " Maybe it does not exist 😅\n"
                ),
                id="not exists path",
            ),
        ],
    )
    @mock.patch(MOCK % "Config._check_regex")
    def test_check_path(self, _check_regex, path, expec_err):
        err_type, err_msg = None, None
        with sysu.std_redirect(sysu.STD.ERR) as stderr:
            try:
                config.Config(path=path)
            except Exit:
                err_type = Exit
            err_msg = stderr.getvalue()
        assert err_type == Exit
        assert err_msg == expec_err


class TestParseConfigFile:

    """`config.ParseConfigFile` class tests."""

    @mock.patch(MOCK % "ParseConfigFile.__init__")
    @mock.patch(MOCK % "Config.__post_init__")
    def setup_method(self, method, post_init, init):
        self.configs = config.Config(path=Path("."))

    @pytest.mark.parametrize(
        "path, expec_err",
        [
            pytest.param(
                Path("not_exists_path.cfg"),
                "Config file 'not_exists_path.cfg' does not exist 😅\n",
                id="not exists path",
            ),
            pytest.param(
                CONFIG_DIR.joinpath("invalid_type.invalid"),
                (
                    "Config file "
                    f"{str(CONFIG_DIR.joinpath('invalid_type.invalid'))!r}"
                    " is not supported 😅\n"
                    f"Supported types: {CONFIG_SECTIONS.keys()}.\n"
                ),
                id="not supported type",
            ),
        ],
    )
    @mock.patch(MOCK % "Config.__post_init__")
    def test_parse(self, post_init, path, expec_err):
        err_type, err_msg = None, None
        with sysu.std_redirect(sysu.STD.ERR) as stderr:
            try:
                config.ParseConfigFile(path, self.configs)
            except Exit:
                err_type = Exit
            err_msg = stderr.getvalue()
        assert err_type == Exit
        assert err_msg == expec_err

    @pytest.mark.parametrize(
        "configs",
        [
            pytest.param(CONFIG, id="valid"),
            pytest.param({**CONFIG, **{"Invalid": "data"}}, id="invalid"),
        ],
    )
    @mock.patch(MOCK % "Config.__post_init__")
    @mock.patch(MOCK % "ParseConfigFile.parse")
    def test_config_loader(self, parse, post_init, configs):
        config_parser = config.ParseConfigFile(Path(""), self.configs)
        config_parser._config_loader(configs)
        for attr, val in CONFIG.items():
            if attr != "all":
                print(attr, getattr(self.configs, attr), val)
                assert getattr(self.configs, attr) == val
        assert getattr(self.configs, "Invalid", None) is None

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
        for type_ in ("include", "exclude"):
            regex = getattr(self.configs, type_)
            setattr(self.configs, type_, re.compile(regex, re.IGNORECASE))
        for attr, val in CONFIG.items():
            if attr != "all":
                assert getattr(self.configs, attr) == val
