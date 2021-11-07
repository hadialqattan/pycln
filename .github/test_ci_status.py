"""pycln/.github/ci_status.py tests."""
# pylint: disable=R0201,W0613
from unittest import mock

import pytest
from ci_status import get_ci_runs_dict, get_last_run_status, main

from tests.utils import sysu

# Constants.
MOCK = "ci_status.%s"


def runs(runs: list) -> dict:
    """Generate Github runs like dict."""
    return {"total_count": len(runs), "workflow_runs": runs}


def run(
    *,  # Force kwargs.
    head_branch="master",
    event="push",
    status="completed",
    conclusion="success",
    is_fork=False
) -> dict:
    """Generate Github run like dict."""
    return {
        "head_branch": head_branch,
        "event": event,
        "status": status,
        "conclusion": conclusion,
        "repository": {"fork": is_fork},
    }


class TestCiStatus:

    """`ci_status.py` functions test case."""

    @pytest.mark.parametrize(
        "status_code, data, expec_data",
        [
            pytest.param(200, {"data": "..."}, {"data": "..."}, id="success"),
            pytest.param(404, {"data": "not-found"}, {}, id="not-found"),
        ],
    )
    @mock.patch(MOCK % "requests.get")
    def test_get_ci_runs_dict(self, get, status_code, data, expec_data):
        get.return_value.json.return_value = data
        type(get.return_value).status_code = mock.PropertyMock(return_value=status_code)
        with sysu.std_redirect(sysu.STD.ERR) as stderr:
            assert get_ci_runs_dict() == expec_data
            if data != expec_data:
                assert str(status_code) in stderr.getvalue()

    @pytest.mark.parametrize(
        "data, expec_code",
        [
            pytest.param({}, 1, id="empty data"),
            pytest.param(runs([]), 1, id="no run"),
            pytest.param(
                runs([run(head_branch="not-master")]),
                1,
                id="not-master",
            ),
            pytest.param(
                runs([run(event="not-push")]),
                1,
                id="not-push",
            ),
            pytest.param(
                runs([run(status="not-success")]),
                1,
                id="not-success",
            ),
            pytest.param(
                runs([run(status="not-completed")]),
                1,
                id="not-completed",
            ),
            pytest.param(
                runs([run(conclusion="not-success")]),
                1,
                id="not-success",
            ),
            pytest.param(
                runs([run()]),
                0,
                id="base-case, first",
            ),
            pytest.param(
                runs([run(event="not-push"), run()]),
                0,
                id="base-case, second",
            ),
        ],
    )
    def test_get_last_run_status(self, data, expec_code):
        assert get_last_run_status(data) == expec_code

    @pytest.mark.parametrize(
        "code, expec_in",
        [
            (0, "succeed"),
            (1, "failed"),
        ],
    )
    @mock.patch(MOCK % "get_last_run_status")
    @mock.patch(MOCK % "get_ci_runs_dict")
    def test_main(self, gcrd, glrs, code, expec_in):
        glrs.return_value = code
        with sysu.std_redirect(sysu.STD.OUT) as stdout:
            main()
            assert expec_in in stdout.getvalue()
