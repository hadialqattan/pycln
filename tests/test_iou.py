"""pycln/utils/iou.py unit tests."""
import os
import tempfile
from pathlib import Path
from typing import List

from pycln.utils import iou
from pycln.utils._exceptions import (
    ReadPermissionError,
    UnparsableFile,
    WritePermissionError,
)


class TestIOU:

    """`iou.py` functions test case."""

    def _temp_safe_read(
        self,
        content: str,
        expectations: tuple,
        chmod: int = 0o0644,
    ) -> None:
        # Open temp file for `safe_read` tests.
        source_code, err_type = None, None
        with tempfile.NamedTemporaryFile(mode="w+", suffix=".py") as tmp:
            try:
                tmp.write(content)
                tmp.seek(0)
                tmp_path = Path(tmp.name)
                os.chmod(tmp_path, chmod)
                # default param: permissions: tuple = (os.R_OK, os.W_OK).
                source_code, _ = iou.safe_read(tmp_path)
            except Exception as err:
                err_type = type(err)
        assert expectations == (source_code, err_type)

    def test_safe_read_valid(self):
        # Test `safe_read` function.
        content = "print('Hello')"
        expectations = (content, None)
        self._temp_safe_read(content, expectations)

    def test_safe_read_no_read_permission(self):
        # Test `safe_read` function.
        expectations = (None, ReadPermissionError)
        self._temp_safe_read("", expectations, chmod=0o000)

    def test_safe_read_no_write_permission(self):
        # Test `safe_read` function.
        expectations = (None, WritePermissionError)
        self._temp_safe_read("", expectations, chmod=0o444)

    def test_safe_read_bad_encoding(self):
        #: Test `safe_read` function.
        #:
        #: Make conflict between BOM and encoding Cookie.
        #: https://docs.python.org/3/library/tokenize.html#tokenize.detect_encoding
        content = "\ufeff\n# -*- coding: utf-32 -*-\nbad encoding"
        expectations = (None, UnparsableFile)
        self._temp_safe_read(content, expectations)

    def _temp_safe_write(
        self,
        fixed_lines: List[str],
        expectations: tuple,
        chmod: int = 0o0644,
    ) -> None:
        # Open temp file for `safe_write` tests.
        source_code, err_type = None, None
        with tempfile.NamedTemporaryFile(mode="w+", suffix=".py") as tmp:
            try:
                tmp_path = Path(tmp.name)
                os.chmod(tmp_path, chmod)
                iou.safe_write(tmp_path, fixed_lines, "utf-8")
                tmp.seek(0)
                source_code = tmp.read()
            except Exception as err:
                err_type = type(err)
        assert expectations == (source_code, err_type)

    def test_safe_write_valid(self):
        # Test `safe_write` function.
        fixed_lines = ["import time\n", "time.time()\n"]
        expectations = ("".join(fixed_lines), None)
        self._temp_safe_write(fixed_lines, expectations)

    def test_safe_write_no_write_permission(self):
        # Test `safe_write` function.
        expectations = (None, WritePermissionError)
        self._temp_safe_write("", expectations, chmod=0o444)
