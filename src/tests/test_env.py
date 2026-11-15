"""Tests for env.py."""
import os
import unittest
from os.path import isdir, isfile, join
from unittest import mock

from core.env import Env, ToolNotFoundError
from tests.unit_utils import leftover_files, use_private_temp_dirs


class TestEnv(unittest.TestCase):
    """Test all of the functions relating to the environment."""

    def setUp(self) -> None:
        """Point the temp directories at a private directory so the checkout is never touched."""
        self._root = use_private_temp_dirs(self)

    def test_project_path_is_checkout(self) -> None:
        """Paths derive from the checkout containing main.py, not a fixed /app location."""
        self.assertTrue(os.path.isfile(join(Env.PROJECT_PATH, "main.py")))
        self.assertEqual(Env.project_file("tests/dotFiles"),
                         join(Env.PROJECT_PATH, "tests", "dotFiles"))
        self.assertEqual(Env.project_file("/abs/path"), "/abs/path")

    def test_clean_temp(self) -> None:
        """Test the clean_temps function."""
        Env.make_temp()
        for path in (Env.TMP_DOT_PATH, Env.TMP_PATH):
            with open(join(path, "test_file"), "w") as new_file:
                new_file.write("test file")

        Env.clean_temps()

        self.assertEqual(leftover_files(Env.TMP_DOT_PATH), [])
        self.assertEqual(leftover_files(Env.TMP_PATH), [])

    def test_make_temp(self) -> None:
        """make_temp creates both directories, is idempotent, and reports failure by raising."""
        Env.make_temp()
        Env.make_temp()
        self.assertTrue(isdir(Env.TMP_PATH))
        self.assertTrue(isdir(Env.TMP_DOT_PATH))

        blocker = join(self._root, "file")
        with open(blocker, "w") as file:
            file.write("not a directory")
        with mock.patch.object(Env, "TMP_PATH", join(blocker, "tmp")):
            with self.assertRaises(OSError):
                Env.make_temp()

    def test_get_output_path(self) -> None:
        """Test the get_output_path function."""
        self.assertEqual(Env.get_output_path("/somewhere/test.foo"), join(Env.TMP_DOT_PATH, "test"))

    def test_fake_libc_include(self) -> None:
        """The fake libc headers resolve from the override, else the package, else a clear error."""
        Env.fake_libc_include.cache_clear()
        self.addCleanup(Env.fake_libc_include.cache_clear)
        with mock.patch.dict(os.environ, {"METRINOME_FAKE_LIBC": "/custom/fake_libc"}):
            self.assertEqual(Env.fake_libc_include(), "/custom/fake_libc")
        Env.fake_libc_include.cache_clear()
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("METRINOME_FAKE_LIBC", None)
            with mock.patch.dict("sys.modules", {"pycparser_fake_libc": None}):
                with self.assertRaises(ToolNotFoundError):
                    Env.fake_libc_include()
            Env.fake_libc_include.cache_clear()
            self.assertTrue(isfile(join(Env.fake_libc_include(), "stdio.h")))


if __name__ == '__main__':
    unittest.main()
