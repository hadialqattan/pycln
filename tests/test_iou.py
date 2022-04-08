"""pycln/utils/iou.py tests."""
# pylint: disable=R0201,W0613
import os
from typing import List
from unittest import mock

import pytest
from oschmod import set_mode

from pycln import ISWIN
from pycln.utils import iou
from pycln.utils._exceptions import (
    ReadPermissionError,
    UnparsableFile,
    WritePermissionError,
)

from .utils import sysu

# Constants.
MOCK = "pycln.utils.iou.%s"


class TestIOU:

    """`iou.py` functions test case."""

    @pytest.mark.parametrize(
        "content, expec_code, expec_newline, expec_err",
        [
            pytest.param(
                "print('Hello')", "print('Hello')", iou.LF, sysu.Pass, id="best case"
            ),
            pytest.param(
                #: Make conflict between BOM and encoding Cookie.
                #: For more information: https://bit.ly/32o3eVl
                "\ufeff\n# -*- coding: utf-32 -*-\nbad encoding",
                "",
                None,
                UnparsableFile,
                id="bad encoding",
            ),
            pytest.param(
                "try: pass\x0c;\nfinally: pass",
                "",
                None,
                UnparsableFile,
                id="form feed char",
            ),
            pytest.param(
                "print('Hello')\r\n",
                "print('Hello')\n",
                iou.CRLF,
                sysu.Pass,
                id="detect CRLF",
            ),
            pytest.param(
                "print('Hello')\n",
                "print('Hello')\n",
                iou.LF,
                sysu.Pass,
                id="detect LF",
            ),
        ],
    )
    @mock.patch(MOCK % "sys.stdin.buffer.read")
    def test_read_stdin(
        self, stdin, content: str, expec_code: str, expec_newline: str, expec_err
    ):
        with pytest.raises(expec_err):
            stdin.return_value = content.encode()
            source_code, _, newline = iou.read_stdin()
            assert source_code == expec_code
            assert newline == expec_newline
            raise sysu.Pass()

    @pytest.mark.parametrize(
        "content, expec_code, expec_newline, expec_err, chmod",
        [
            pytest.param(
                "print('Hello')",
                "print('Hello')",
                iou.LF,
                sysu.Pass,
                0o0644,
                id="bast case",
            ),
            pytest.param(
                "code...",
                None,
                None,
                ReadPermissionError,
                0o000,
                id="no read permission",
                marks=pytest.mark.skipif(
                    ISWIN, reason="os.access doesn't support Windows."
                ),
            ),
            pytest.param(
                "code...",
                None,
                None,
                WritePermissionError,
                0o444,
                id="no read write",
                marks=pytest.mark.skipif(
                    ISWIN, reason="os.access doesn't support Windows."
                ),
            ),
            pytest.param(
                #: Make conflict between BOM and encoding Cookie.
                #: For more information: https://bit.ly/32o3eVl
                "\ufeff\n# -*- coding: utf-32 -*-\nbad encoding",
                None,
                None,
                UnparsableFile,
                0o0644,
                id="bad encoding",
            ),
            pytest.param(
                "try: pass\x0c;\nfinally: pass",
                None,
                None,
                UnparsableFile,
                0o0644,
                id="form feed char",
            ),
            pytest.param(
                "print('Hello')\r\n",
                "print('Hello')\n\n",
                iou.CRLF,
                sysu.Pass,
                0o0644,
                id="detect CRLF",
            ),
            pytest.param(
                "print('Hello')\n",
                "print('Hello')\n",
                iou.LF,
                sysu.Pass,
                0o0644,
                id="detect LF",
                marks=pytest.mark.skipif(
                    ISWIN, reason="Unnecessary as long as WindowsOS uses CRLF."
                ),
            ),
        ],
    )
    def test_safe_read(
        self, content: str, expec_code: str, expec_newline: str, expec_err, chmod: int
    ):
        with pytest.raises(expec_err):
            if expec_newline:
                content = content.replace(os.linesep, expec_newline)
            with sysu.reopenable_temp_file(content) as tmp_path:
                set_mode(str(tmp_path), chmod)
                # default param: permissions: tuple = (os.R_OK, os.W_OK).
                source_code, _, newline = iou.safe_read(tmp_path)
                assert source_code == expec_code
                assert newline == expec_newline
            raise sysu.Pass()

    @pytest.mark.parametrize(
        "fixed_lines, expec_code, expec_newline, expec_err, chmod",
        [
            pytest.param(
                ["import time\n", "time.time()\n"],
                "import time\ntime.time()\n",
                iou.LF,
                sysu.Pass,
                0o0644,
                id="best case",
            ),
            pytest.param(
                ["code...\n", "code...\n"],
                None,
                None,
                WritePermissionError,
                0o444,
                id="no write permission",
                marks=pytest.mark.skipif(
                    ISWIN, reason="os.access doesn't support Windows."
                ),
            ),
            pytest.param(
                ["import time\n", "time.time()\n"],
                "import time\ntime.time()\n",
                iou.CRLF,
                sysu.Pass,
                0o0644,
                id="newline - CRLF",
            ),
            pytest.param(
                ["import time\r\n", "time.time()\r\n"],
                "import time\ntime.time()\n",
                iou.LF,
                sysu.Pass,
                0o0644,
                id="newline - LF",
            ),
        ],
    )
    def test_safe_write(
        self,
        fixed_lines: List[str],
        expec_code: str,
        expec_newline: str,
        expec_err,
        chmod: int,
    ):
        with pytest.raises(expec_err):
            with sysu.reopenable_temp_file("".join(fixed_lines)) as tmp_path:
                set_mode(str(tmp_path), chmod)
                iou.safe_write(tmp_path, fixed_lines, "utf-8", expec_newline)
                with open(tmp_path) as tmp0:
                    assert tmp0.read() == expec_code
                with open(tmp_path, "rb") as tmp1:
                    assert expec_newline.encode() in tmp1.readline()
            raise sysu.Pass()
