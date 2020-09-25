"""pycln/utils/_nodes.py tests."""
# pylint: disable=R0201,W0613
import pytest

from pycln.utils import _nodes


class TestNodePosition:

    """`NodePosition` dataclass test case."""

    @pytest.mark.parametrize("line, col", [(1, 0), (1, None)])
    def test_init(self, line, col):
        position = _nodes.NodePosition(line, col)
        assert position.line == line
        assert position.col == col

    @pytest.mark.parametrize(
        "line, col, expec_hash",
        [
            pytest.param(1, 2, hash(3), id="hash with col"),
            pytest.param(1, None, hash(1), id="hash without col"),
        ],
    )
    def test_hash_dunder(self, line, col, expec_hash):
        position = _nodes.NodePosition(line, col)
        assert hash(position) == expec_hash


class TestNodeLocation:

    """`NodeLocation` dataclass test case."""

    @pytest.mark.parametrize("start, end", [((1, 0), 1)])
    def test_init(self, start, end):
        location = _nodes.NodeLocation(start, end)
        assert location.start.line == start[0]
        assert location.start.col == start[1]
        assert location.end.line == end

    @pytest.mark.parametrize(
        "start, end, expec_hash",
        [((1, 2), 1, hash(hash(3) + hash(1)))],
    )
    def test_hash_dunder(self, start, end, expec_hash):
        location = _nodes.NodeLocation(start, end)
        assert hash(location) == expec_hash

    @pytest.mark.parametrize(
        "start, end, expec_len",
        [((1, 0), 1, 1), ((1, 0), 2, 2), ((4, 0), 8, 5)],
    )
    def test_len_dunder(self, start, end, expec_len):
        location = _nodes.NodeLocation(start, end)
        assert len(location) == expec_len


class TestImport:

    """`Import` dataclass test case."""

    @pytest.mark.parametrize(
        "location, names",
        [pytest.param(_nodes.NodeLocation((1, 0), 1), [], id="normal init")],
    )
    def test_init(self, location, names):
        node = _nodes.Import(location, names)
        assert node.location == location
        assert node.names == names

    def test_hash_dunder(self):
        location = _nodes.NodeLocation((1, 4), 1)
        node = _nodes.Import(location, [])
        assert hash(node) == hash(node.location)


class TestImportFrom:

    """`ImportFrom` dataclass test case."""

    @pytest.mark.parametrize(
        "location, names, module, level",
        [
            pytest.param(
                _nodes.NodeLocation((1, 0), 1), [], "xxx", 0, id="with module"
            ),
            pytest.param(
                _nodes.NodeLocation((1, 0), 1), [], None, 1, id="without module"
            ),
        ],
    )
    def test_init(self, location, names, module, level):
        node = _nodes.ImportFrom(location, names, module, level)
        assert node.location == location
        assert node.names == names
        assert node.module == module
        assert node.level == level

    @pytest.mark.parametrize(
        "module, level, expec_rel_name",
        [
            pytest.param("xxx", 0, "xxx", id="non-relative"),
            pytest.param("xxx", 1, ".xxx", id="relative"),
            pytest.param(None, 2, "..", id="no-module, relative"),
        ],
    )
    def test_relative_name_property(self, module, level, expec_rel_name):
        location = _nodes.NodeLocation((1, 1), 1)
        node = _nodes.ImportFrom(location, [], module, level)
        assert node.relative_name == expec_rel_name

    def test_hash_dunder(self):
        location = _nodes.NodeLocation((1, 4), 1)
        node = _nodes.ImportFrom(location, [], None, 1)
        assert hash(node) == hash(node.location)
