"""Paths and external tools used by Metrinome.

Paths default to this source tree (the directory containing ``main.py``), so Metrinome runs from any
checkout, inside or outside Docker. Every external tool is located lazily on first use and can be
overridden with an environment variable:

    METRINOME_HOME   project directory (default: this ``src`` directory)
    METRINOME_CLANG  clang executable (default: ``clang``, else the newest ``clang-NN`` on PATH)
    METRINOME_OPT    LLVM ``opt`` (default: the ``opt`` next to the selected clang, else PATH)
    JAVA_HOME        JDK used for ``javac``/``java`` (default: PATH)
    METRINOME_KLEE   KLEE executable (default: ``/app/build/bin/klee``)
    METRINOME_KLEE_INCLUDE  KLEE headers (default: ``/app/klee/include``)
    METRINOME_FAKE_LIBC  pycparser fake libc headers (default: the ``pycparser-fake-libc`` package)
"""
import os
import re
import shutil
import subprocess
from enum import Enum
from functools import cache
from os.path import basename, dirname, isfile, join, realpath, splitext
from typing import Optional


class KnownExtensions(Enum):
    """A list of all the file extensions we know how to work with."""

    C      = ".c"
    Python = ".py"
    BC     = ".bc"
    Java   = ".java"


class ToolNotFoundError(RuntimeError):
    """An external program Metrinome needs is not installed."""


def _which_versioned(name: str) -> Optional[str]:
    """Find `name` on PATH, falling back to the newest `name-NN` (Debian/Ubuntu LLVM packages)."""
    if found := shutil.which(name):
        return found
    for version in range(30, 13, -1):
        if found := shutil.which(f"{name}-{version}"):
            return found
    return None


def _require(path: Optional[str], tool: str, hint: str) -> str:
    if path is None:
        raise ToolNotFoundError(f"{tool} not found. {hint}")
    return path


class Env:
    """Project paths and external tool locations."""

    PROJECT_PATH = realpath(os.environ.get("METRINOME_HOME") or dirname(dirname(realpath(__file__))))
    TMP_PATH = join(PROJECT_PATH, "tmp")
    TMP_DOT_PATH = join(PROJECT_PATH, "tmp_dot")
    EXPORT_PATH = join(PROJECT_PATH, "exports")
    CFG_EXTRACTOR_JAR = join(PROJECT_PATH, "lang_to_cfg", "javaextractor", "cfg_extractor",
                             "javaextractor.jar")
    KLEE_PATH = os.environ.get("METRINOME_KLEE", "/app/build/bin/klee")
    KLEE_INCLUDE = os.environ.get("METRINOME_KLEE_INCLUDE", "/app/klee/include")

    @staticmethod
    def project_file(path: str) -> str:
        """Resolve `path` against the project directory; absolute paths are returned unchanged."""
        return join(Env.PROJECT_PATH, path)

    @staticmethod
    @cache
    def clang() -> str:
        """Path of clang, from METRINOME_CLANG or PATH. It compiles C and C++ (chosen by file extension)."""
        override = os.environ.get("METRINOME_CLANG")
        clang = (shutil.which(override) or override) if override else _which_versioned("clang")
        return _require(clang, "clang", "Install clang (LLVM 14 or newer) or set METRINOME_CLANG.")

    @staticmethod
    @cache
    def opt() -> str:
        """Path of LLVM opt matching the selected clang, from METRINOME_OPT, clang's directory, or PATH."""
        if override := os.environ.get("METRINOME_OPT"):
            return override
        version = re.search(r"clang(-\d+)?$", Env.clang())
        suffix = (version.group(1) or "") if version else ""
        for candidate in (join(dirname(realpath(Env.clang())), "opt"),
                          join(dirname(Env.clang()), f"opt{suffix}")):
            if isfile(candidate):
                return candidate
        return _require(_which_versioned("opt"), "LLVM opt",
                        "Install the LLVM tools matching clang or set METRINOME_OPT.")

    @staticmethod
    @cache
    def java(tool: str = "java") -> str:
        """Path of a JDK tool (`java` or `javac`), from JAVA_HOME or PATH."""
        java_home = os.environ.get("JAVA_HOME")
        if java_home and isfile(candidate := join(java_home, "bin", tool)):
            return candidate
        return _require(shutil.which(tool), tool, "Install a JDK (8 or newer) or set JAVA_HOME.")

    @staticmethod
    @cache
    def fake_libc_include() -> str:
        """Directory of pycparser's fake libc headers, from METRINOME_FAKE_LIBC or pycparser-fake-libc."""
        if override := os.environ.get("METRINOME_FAKE_LIBC"):
            return override
        try:
            import pycparser_fake_libc  # type: ignore # pylint: disable=import-outside-toplevel
        except ImportError:
            pycparser_fake_libc = None
        return _require(getattr(pycparser_fake_libc, "directory", None), "pycparser fake libc headers",
                        "Install them with `pip install pycparser-fake-libc` or set METRINOME_FAKE_LIBC.")

    @staticmethod
    def clean_temps() -> None:
        """Remove temp files and directories."""
        proc_one = subprocess.Popen(["rm", "-rf", Env.TMP_PATH])
        proc_two = subprocess.Popen(["rm", "-rf", Env.TMP_DOT_PATH])
        proc_two.wait()
        proc_one.wait()
        Env.make_temp()

    @staticmethod
    def make_temp() -> None:
        """Create the temporary dirs."""
        os.makedirs(Env.TMP_PATH, exist_ok=True)
        os.makedirs(Env.TMP_DOT_PATH, exist_ok=True)

    @staticmethod
    def make_export_dir() -> str:
        """Create the export directory and return its path."""
        os.makedirs(Env.EXPORT_PATH, exist_ok=True)
        return Env.EXPORT_PATH

    @staticmethod
    def get_output_path(name: str) -> str:
        """For a given .jar file, determine what the output path should be for that file."""
        return join(Env.TMP_DOT_PATH, splitext(basename(name))[0])
