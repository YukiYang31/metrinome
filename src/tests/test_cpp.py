"""This module tests that we can convert C++ to Graph objects representing its CFG."""

import unittest

from core.env import Env
from core.log import Log, LogLevel
from graph.graph import EdgeListGraph
from lang_to_cfg.cpp import CPPConvert
from metric.cyclomatic_complexity import CyclomaticComplexity
from tests.unit_utils import leftover_files, use_private_temp_dirs


class TestCPPConvert(unittest.TestCase):
    """All tests for the object that converts arbitrary C++ code to Graph objects."""

    def test_to_graph(self) -> None:
        """
        Check that it returns the correct graphs.

        Graphs are keyed `<file>_.<function>.dot`, using the (mangled) LLVM function name.
        """
        converter = CPPConvert(Log(log_level=LogLevel.REGULAR))
        self.assertEqual(converter.name(), "CPP")
        use_private_temp_dirs(self)
        straight_line = EdgeListGraph([[0, 1], [1, 2]], 3)
        result = converter.to_graph(Env.project_file("tests/cppFiles/blank"), ".cpp")
        self.assertEqual(leftover_files(Env.TMP_DOT_PATH), [])
        self.assertEqual(leftover_files(Env.TMP_PATH), [])
        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(set(result), {"blank_.main.dot"})
        self.assertEqual(straight_line, result["blank_.main.dot"].graph)

        graphs = converter.to_graph(Env.project_file("tests/cppFiles/names"), ".cpp")
        self.assertIsNotNone(graphs)
        assert graphs is not None
        # main is a single basic block; Jar::pull has one `if` whose two returns merge.
        self.assertEqual(straight_line, graphs["names_.main.dot"].graph)
        self.assertEqual(EdgeListGraph([[0, 1], [0, 2], [1, 3], [2, 3]], 4),
                         graphs["names_._ZN3Jar4pullEi.dot"].graph)
        self.assertEqual(CyclomaticComplexity(Log()).evaluate(graphs["names_._ZN3Jar4pullEi.dot"]), 2)


if __name__ == '__main__':
    unittest.main()
