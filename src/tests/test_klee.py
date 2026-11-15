"""Tests for the KLEE integration: tool discovery, harness generation, and the REPL workflow."""
import os
import re
import tempfile
import unittest
from os.path import join, realpath
from unittest import mock

from core.command import Command, Options, REPLOptions
from core.env import Env, ToolNotFoundError
from klee.klee_utils import KleeUtils
from core.log import Log
from tests.unit_utils import captured_output, use_private_temp_dirs

SIGN = Env.project_file("tests/cFiles/fse_2020_benchmark/03_sign.c")
KLEE_TOOLS = (Env.clang, Env.klee, Env.klee_include, Env.klee_lib, Env.klee_clang)


def clear_tool_cache() -> None:
    """Drop the functools.cache'd tool paths."""
    for tool in KLEE_TOOLS:
        tool.cache_clear()


def klee_available() -> bool:
    """Whether KLEE, its headers, and a clang that can produce bitcode for it are installed."""
    try:
        for tool in KLEE_TOOLS:
            tool()
    except ToolNotFoundError:
        return False
    return True


class TestKleeToolDiscovery(unittest.TestCase):
    """Env finds a KLEE installation and a clang whose bitcode that KLEE can read."""

    def setUp(self) -> None:
        """Give each test an empty KLEE prefix whose bin dir is the whole PATH."""
        clear_tool_cache()
        self.addCleanup(clear_tool_cache)
        prefix = tempfile.TemporaryDirectory()  # pylint: disable=consider-using-with
        self.addCleanup(prefix.cleanup)
        self.prefix = realpath(prefix.name)
        self.bin = join(self.prefix, "bin")
        os.makedirs(self.bin)
        patch = mock.patch.dict(os.environ, {"PATH": self.bin})
        patch.start()
        self.addCleanup(patch.stop)
        for name in ("METRINOME_CLANG", "METRINOME_KLEE", "METRINOME_KLEE_INCLUDE", "METRINOME_KLEE_CLANG"):
            os.environ.pop(name, None)

    def fake_tool(self, name: str, version_line: str = "") -> str:
        """Create an executable `name` printing `version_line` (as `--version` would)."""
        path = join(self.bin, name)
        with open(path, "w") as tool:
            tool.write(f"#!/bin/sh\necho '{version_line}'\n")
        os.chmod(path, 0o755)
        return path

    def fake_klee(self, llvm: int) -> str:
        """A klee reporting LLVM `llvm`, like `klee --version` does."""
        return self.fake_tool("klee", f"  LLVM version {llvm}.1.8")

    def test_installation_layout(self) -> None:
        """Headers, libkleeRuntest, and klee-stats come from the installation holding klee."""
        klee = self.fake_klee(18)
        stats = self.fake_tool("klee-stats")
        os.makedirs(join(self.prefix, "include", "klee"))
        open(join(self.prefix, "include", "klee", "klee.h"), "w").close()
        os.makedirs(join(self.prefix, "lib64"))
        open(join(self.prefix, "lib64", "libkleeRuntest.so"), "w").close()
        self.assertEqual(klee, Env.klee())
        self.assertEqual(stats, Env.klee("klee-stats"))
        self.assertEqual(join(self.prefix, "include"), Env.klee_include())
        self.assertEqual(join(self.prefix, "lib64"), Env.klee_lib())

    def test_missing_klee(self) -> None:
        """No KLEE: ToolNotFoundError naming the override variable."""
        with self.assertRaises(ToolNotFoundError) as raised:
            Env.klee()
        self.assertIn("METRINOME_KLEE", str(raised.exception))

    def test_missing_headers(self) -> None:
        """KLEE without klee/klee.h next to it: ToolNotFoundError naming the override variable."""
        self.fake_klee(18)
        with self.assertRaises(ToolNotFoundError) as raised:
            Env.klee_include()
        self.assertIn("METRINOME_KLEE_INCLUDE", str(raised.exception))

    def test_clang_matching_klee_llvm(self) -> None:
        """clang-N matching KLEE's LLVM N wins over a newer default clang."""
        self.fake_klee(18)
        self.fake_tool("clang", "clang version 20.1.8")
        matching = self.fake_tool("clang-18", "clang version 18.1.8")
        self.assertEqual(matching, Env.klee_clang())

    def test_older_clang_is_accepted(self) -> None:
        """KLEE reads bitcode from an older LLVM, so an older clang is used."""
        self.fake_klee(18)
        clang = self.fake_tool("clang", "clang version 16.0.6")
        self.assertEqual(clang, Env.klee_clang())

    def test_newer_clang_is_rejected(self) -> None:
        """Only a newer clang: ToolNotFoundError naming both versions and the override variable."""
        self.fake_klee(18)
        self.fake_tool("clang", "clang version 20.1.8")
        with self.assertRaises(ToolNotFoundError) as raised:
            Env.klee_clang()
        message = str(raised.exception)
        for expected in ("LLVM 18", "LLVM 20", "clang-18", "METRINOME_KLEE_CLANG"):
            self.assertIn(expected, message)

    def test_klee_clang_override(self) -> None:
        """METRINOME_KLEE_CLANG wins even when the versions say otherwise."""
        self.fake_klee(18)
        override = self.fake_tool("my-clang", "clang version 20.1.8")
        os.environ["METRINOME_KLEE_CLANG"] = override
        self.assertEqual(override, Env.klee_clang())


class TestKleeHarness(unittest.TestCase):
    """to_klee_format writes a main() that makes each parameter symbolic and calls the function."""

    def test_sign_harness(self) -> None:
        """GCC attributes are parsed, and the harness includes the source by absolute path."""
        with captured_output():
            harnesses = KleeUtils(Log()).show_func_defs(os.path.relpath(SIGN))
        self.assertEqual(["sign"], list(harnesses))
        harness = harnesses["sign"]
        self.assertIn(f'#include "{SIGN}"', harness)
        self.assertIn('klee_make_symbolic(&num, sizeof(num), "num");', harness)
        self.assertIn("return sign(num);", harness)


@unittest.skipUnless(klee_available(), "KLEE is not installed")
class TestKleeWorkflow(unittest.TestCase):
    """The REPL commands to_klee_format, klee_to_bc, klee, and klee_replay on sign()."""

    def setUp(self) -> None:
        """Keep KLEE's output in a private directory."""
        root = use_private_temp_dirs(self)
        patch = mock.patch.object(Env, "KLEE_OUT_PATH", join(root, "klee_out"))
        patch.start()
        self.addCleanup(patch.stop)
        self.command = Command(REPLOptions(os.getcwd(), False, False, False, False), None)

    def test_sign(self) -> None:
        """sign() has three paths (negative, zero, positive); replay runs each test natively."""
        opts = Options()
        with captured_output() as (out, _):
            self.command.do_to_klee_format(opts, SIGN)
            self.command.do_klee_to_bc(opts, "sign")
            self.command.do_klee(opts, "sign")
            self.command.do_klee_replay(opts, "sign")

        stats = self.command.data.klee_stats["sign"]
        self.assertEqual((3, 3, False), (stats.tests, stats.paths, stats.timeout))
        replay = out.getvalue()
        inputs = [int(value) for value in re.findall(r"object 0: int : (-?\d+)", replay)]
        statuses = [int(value) for value in re.findall(r"exit status: (\d+)", replay)]
        self.assertEqual(3, len(inputs))
        # main returns sign(num); -1 becomes exit status 255.
        expected = [(value > 0) - (value < 0) for value in inputs]
        self.assertEqual([status - 256 if status > 127 else status for status in statuses], expected)
        self.assertEqual({-1, 0, 1}, set(expected))


if __name__ == "__main__":
    unittest.main()
