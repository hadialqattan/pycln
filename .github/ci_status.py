"""Perform an exit code that indicates the last CI workflow status."""
import sys

import requests

CI_RUNS_URL = "https://api.github.com/repos/hadialqattan/pycln/actions/runs"


def get_ci_runs_dict() -> dict:
    """Get CI runs request data as dict object.

    :returns: dict of CI runs data.
    """
    try:
        res = requests.get(CI_RUNS_URL, timeout=5)
        assert res.status_code == 200, f"Unexpected status code: {res.status_code}."
        return dict(res.json())
    except (requests.ConnectionError, requests.Timeout, AssertionError) as err:
        print(err, file=sys.stderr)
        return {}


def get_last_run_status(data: dict) -> int:
    """Get the proper exit code for the last run status.

    :param data: data dict to parse.
    :returns: 0 if success otherwise 1.
    """
    # No run!
    if not data.get("total_count", 0):
        return 1

    for run in data.get("workflow_runs", {}):

        # Determine the status.
        is_master_push = (run["head_branch"], run["event"]) == ("master", "push")
        is_success = (run["status"], run["conclusion"]) == ("completed", "success")
        is_not_fork = not run["repository"]["fork"]

        if is_master_push and is_not_fork:
            if is_success:
                # status == success.
                return 0
            else:
                # status in {"failure", "cancelled"}.
                return 1

    # No master branch push run.
    return 1


def main() -> int:
    """Return the computed exit code."""
    code = get_last_run_status(get_ci_runs_dict())
    status = "succeed" if code == 0 else "failed"
    print(f"The last master brach push run has {status}.")
    return code


if __name__ == "__main__":
    exit(main())
