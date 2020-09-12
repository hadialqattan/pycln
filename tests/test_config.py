"""pycln/utils/config.py unit tests."""
import re
from pathlib import Path
from unittest.mock import patch

import pytest
from typer import Exit

from pycln.utils import config

from .utils import std

# Constants.
CONFIG_DIR = Path(__file__).parent.joinpath(Path("config"))
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
}


class TestConfig:

    """`config.Config` class tests."""

    @patch("pycln.utils.config.Config._check_path")
    @patch("pycln.utils.config.Config._check_regex")
    def test_normal_config(self, _check_regex, _check_path):
        # Test `__post_init__` method.
        configs = config.Config(
            path=Path("."),
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

    @patch("pycln.utils.config.ParseConfigFile.__init__")
    @patch("pycln.utils.config.Config._check_path")
    @patch("pycln.utils.config.Config._check_regex")
    def test_file_config(self, _check_regex, _check_path, init):
        # Test `__post_init__` method.
        configs = config.Config(
            path=Path("."),
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

    @patch("pycln.utils.config.Config._check_regex")
    def test_empty_path(self, _check_regex):
        # Test `_check_path` method.
        path = None
        expected_err = "No Path provided. Nothing to do 😴\n"
        with std.redirect(std.STD.ERR) as stderr:
            try:
                config.Config(path=path)
            except Exit:
                err_type = Exit
            err_msg = stderr.getvalue()
        assert err_type == Exit
        assert err_msg == expected_err

    @patch("pycln.utils.config.Config._check_regex")
    def test_invalid_path(self, _check_regex):
        # Test `_check_path` method.
        path = "invalid"
        expected_err = (
            f"{path!r} is not a directory or a file. Maybe it does not exist 😅\n"
        )
        with std.redirect(std.STD.ERR) as stderr:
            try:
                config.Config(path=Path(path))
            except Exit:
                err_type = Exit
            err_msg = stderr.getvalue()
        assert err_type == Exit
        assert err_msg == expected_err

    @patch("pycln.utils.config.Config._check_path")
    def test_valid_regex(self, _check_path):
        # Test `_check_regex` method.
        configs = config.Config(
            path=None, include=r".*_util.py$", exclude=r".*_test.py$"
        )
        for r in ("include", "exclude"):
            assert getattr(configs, r) == CONFIG[r]

    @patch("pycln.utils.config.Config._check_path")
    def test_invalid_regex(self, _check_path):
        # Test `_check_regex` method.
        regex = r"**invalid**"
        expected_err = f"Invalid regular expression for include given: {regex!r} ⛔\n"
        with std.redirect(std.STD.ERR) as stderr:
            try:
                config.Config(path=None, include=regex, exclude=regex)
            except Exit:
                err_type = Exit
            err_msg = stderr.getvalue()
        assert err_type == Exit
        assert err_msg == expected_err


class TestParseConfigFile:

    """`config.ParseConfigFile` class tests."""

    @patch("pycln.utils.config.ParseConfigFile.__init__")
    @patch("pycln.utils.config.Config.__post_init__")
    def setup_method(self, method, post_init, init):
        self.configs = config.Config(path=Path("."))

    @patch("pycln.utils.config.Config.__post_init__")
    def test_invalid_path(self, post_init):
        # Test `parse` method.
        path = Path("invalide_path.cfg")
        expected_err = f"Config file {str(path)!r} does not exist 😅\n"
        with std.redirect(std.STD.ERR) as stderr:
            try:
                config.ParseConfigFile(path, self.configs)
            except Exit:
                err_type = Exit
            err_msg = stderr.getvalue()
        assert err_type == Exit
        assert err_msg == expected_err

    @patch("pycln.utils.config.Config.__post_init__")
    def test_invaid_file_type(self, post_init):
        # Test `parse` method.
        path = CONFIG_DIR.joinpath("invalid_type.invalid")
        expected_err = (
            f"Config file {str(path)!r} is not supported 😅\n"
            f"Supported types: {CONFIG_SECTIONS.keys()}.\n"
        )
        with std.redirect(std.STD.ERR) as stderr:
            try:
                config.ParseConfigFile(path, self.configs)
            except Exit:
                err_type = Exit
            err_msg = stderr.getvalue()
        assert err_type == Exit
        assert err_msg == expected_err

    @patch("pycln.utils.config.Config.__post_init__")
    @patch("pycln.utils.config.ParseConfigFile.parse")
    def test_valid_args(self, parse, post_init):
        # Test `_config_loader` method.
        config_parser = config.ParseConfigFile(Path(""), self.configs)
        config_parser._config_loader(CONFIG)
        for attr, val in CONFIG.items():
            if attr != "all":
                print(attr, getattr(self.configs, attr), val)
                assert getattr(self.configs, attr) == val

    @patch("pycln.utils.config.Config.__post_init__")
    @patch("pycln.utils.config.ParseConfigFile.parse")
    def test_invalide_args(self, parse, post_init):
        # Test `_config_loader` method.
        config_parser = config.ParseConfigFile(Path(""), self.configs)
        config_parser._config_loader({"invalid": "value"})
        for attr, val in self.configs.__dict__.items():
            assert getattr(self.configs, attr) == val
        assert getattr(self.configs, "invalid", None) is None

    @pytest.mark.parametrize("file_path", CONFIG_FILES)
    def test_parse_methods(self, file_path):
        # Test `_parse_*` methods:
        #:  - _parse_cfg.
        #:  - _parse_toml.
        #:  - _parse_json.
        #:  - _parse_yaml.
        #:  - _parse_yml.
        with patch("pycln.utils.config.Config.__post_init__"):
            config.ParseConfigFile(file_path, self.configs)
            for type_ in ("include", "exclude"):
                regex = getattr(self.configs, type_)
                setattr(self.configs, type_, re.compile(regex, re.IGNORECASE))
            for attr, val in CONFIG.items():
                if attr != "all":
                    assert getattr(self.configs, attr) == val
