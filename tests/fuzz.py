"""Property-based tests for Pycln."""

from pathlib import Path

import hypothesmith
from hypothesis import HealthCheck, given, settings

from pycln.utils import config, refactor, report

FORM_FEED_CHAR = "\x0c"


# This test uses the Hypothesis and Hypothesmith libraries to generate random
# syntatically-valid Python source code and run Pycln in odd modes.
@settings(
    max_examples=1750,  # roughly 1750 tests/minute,
    derandomize=True,  # deterministic mode to avoid CI flakiness
    deadline=None,  # ignore Hypothesis' health checks; we already know that
    suppress_health_check=HealthCheck.all(),  # this is slow and filter-heavy.
)
@given(
    # Note that while Hypothesmith might generate code unlike that written by
    # humans, it's a general test that should pass for any *valid* source code.
    # (so e.g. running it against code scraped of the internet might also help)
    src_contents=hypothesmith.from_grammar()
    | hypothesmith.from_node()
)
def test_idempotent_any_syntatically_valid_python(src_contents: str) -> None:

    # Form feed char is detected by `pycln.utils.iou.safe_read`.
    if FORM_FEED_CHAR not in src_contents:

        # Before starting, let's confirm that the input string is valid Python:
        compile(src_contents, "<string>", "exec")  # else the bug is in hypothesmith

        # Then format the code...
        configs = config.Config(paths=[Path("pycln/")], skip_imports=set({}), all_=True)
        reporter = report.Report(configs)
        session_maker = refactor.Refactor(configs, reporter)
        dst_contents = session_maker._code_session(src_contents)

        # After formatting, let's check that the ouput is valid Python:
        compile(dst_contents, "<string>", "exec")


if __name__ == "__main__":

    # Run tests, including shrinking and reporting any known failures.
    test_idempotent_any_syntatically_valid_python()  # pylint: disable=E1120
