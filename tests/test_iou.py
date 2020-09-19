"""pycln/utils/iou.py tests."""
import os
import tempfile
from pathlib import Path
from typing import List

import pytest

from pycln.utils import iou
from pycln.utils._exceptions import (
    ReadPermissionError,
    UnparsableFile,
    WritePermissionError,
)


class TestIOU:

    """`iou.py` functions test case."""

    @pytest.mark.parametrize(
        "content, expectations, chmod",
        [
            pytest.param(
                "print('Hello')",
                ("print('Hello')", None),
                0o0644,
                id="base case",
            ),
            pytest.param(
                "code...",
                (None, ReadPermissionError),
                0o000,
                id="no read permission",
            ),
            pytest.param(
                "code...",
                (None, WritePermissionError),
                0o444,
                id="no read write",
            ),
            pytest.param(
                #: Make conflict between BOM and encoding Cookie.
                #: For more information: https://bit.ly/32o3eVl
                "\ufeff\n# -*- coding: utf-32 -*-\nbad encoding",
                (None, UnparsableFile),
                0o0644,
                id="bad encoding",
            ),
        ],
    )
    def test_safe_read(self, content, expectations, chmod):
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
        assert (source_code, err_type) == expectations

    @pytest.mark.parametrize(
        "fixed_lines, expectations, chmod",
        [
            pytest.param(
                ["import time\n", "time.time()\n"],
                ("import time\ntime.time()\n", None),
                0o0644,
                id="best case",
            ),
            pytest.param(
                ["code...\n", "code...\n"],
                (None, WritePermissionError),
                0o444,
                id="no write permission",
            ),
        ],
    )
    def test_safe_write(
        self,
        fixed_lines: List[str],
        expectations: tuple,
        chmod: int,
    ) -> None:
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
        assert (source_code, err_type) == expectations
