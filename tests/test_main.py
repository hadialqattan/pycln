"""`pycln/__main__.py` tests."""
from importlib import import_module

from .utils import sysu


class TestMain:

    """`__main__.py` side effects tests."""

    def test_main(self):
        msg = "It looks like pycln/__main__.py has %s!"
        with sysu.hide_sys_argv():
            with sysu.std_redirect(sysu.STD.ERR) as stream:
                try:
                    try:
                        import_module("pycln.__main__")
                    except ModuleNotFoundError:
                        assert False, msg % "deleted"
                except SystemExit as err:
                    assert err.code == 1 and str(stream.getvalue()), msg % "modified"
                else:
                    assert False, msg % "modified"
