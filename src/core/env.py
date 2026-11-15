"""Paths and external tools used by Metrinome.

Paths default to this source tree (the directory containing ``main.py``), so Metrinome runs from any
checkout, inside or outside Docker. Every external tool is located lazily on first use and can be
overridden with an environment variable:

    METRINOME_HOME   project directory (default: this ``src`` directory)
    METRINOME_CLANG  clang executable (default: ``clang``, else the newest ``clang-NN`` on PATH)
    METRINOME_OPT    LLVM ``opt`` (default: the ``opt`` next to the selected clang, else PATH)
    JAVA_HOME        JDK used for ``javac``/``java`` (default: PATH)
    METRINOME_KLEE   KLEE executable (default: ``klee`` on PATH); ``klee-stats``, ``ktest-tool`` and
                     ``libkleeRuntest`` are taken from the same installation
    METRINOME_KLEE_INCLUDE  KLEE headers (default: ``include`` of the KLEE installation)
    METRINOME_KLEE_CLANG  clang for KLEE bitcode (default: ``clang-N`` or the selected clang, where N
                     is KLEE's LLVM version; KLEE cannot read bitcode from a newer LLVM)
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


def _llvm_major(executable: str) -> Optional[int]:
    """LLVM major version printed by `executable --version` (clang or KLEE)."""
    output = subprocess.run([executable, "--version"], capture_output=True, text=True, check=False).stdout
    match = re.search(r"(?:clang|LLVM) version (\d+)", output)
    return int(match.group(1)) if match else None


class Env:
    """Project paths and external tool locations."""

    PROJECT_PATH = realpath(os.environ.get("METRINOME_HOME") or dirname(dirname(realpath(__file__))))
    TMP_PATH = join(PROJECT_PATH, "tmp")
    TMP_DOT_PATH = join(PROJECT_PATH, "tmp_dot")
    EXPORT_PATH = join(PROJECT_PATH, "exports")
    KLEE_OUT_PATH = join(PROJECT_PATH, "klee_out")
    CFG_EXTRACTOR_JAR = join(PROJECT_PATH, "lang_to_cfg", "javaextractor", "cfg_extractor",
                             "javaextractor.jar")

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
    @cache
    def klee(tool: str = "klee") -> str:
        """Path of a KLEE tool (`klee`, `klee-stats`, `ktest-tool`), from METRINOME_KLEE's directory or PATH."""
        if override := os.environ.get("METRINOME_KLEE"):
            klee = shutil.which(override) or override
            path: Optional[str] = klee if tool == "klee" else join(dirname(klee), tool)
            if not isfile(path):
                path = shutil.which(tool)
        else:
            path = shutil.which(tool)
        return _require(path, tool, "Install KLEE (3.0 or newer) or set METRINOME_KLEE.")

    @staticmethod
    @cache
    def klee_include() -> str:
        """Directory containing klee/klee.h, from METRINOME_KLEE_INCLUDE or the KLEE installation."""
        if override := os.environ.get("METRINOME_KLEE_INCLUDE"):
            return override
        include = join(dirname(dirname(realpath(Env.klee()))), "include")
        return _require(include if isfile(join(include, "klee", "klee.h")) else None, "KLEE headers",
                        "Set METRINOME_KLEE_INCLUDE to the directory containing klee/klee.h.")

    @staticmethod
    @cache
    def klee_lib() -> str:
        """Directory containing libkleeRuntest, in the KLEE installation or build tree."""
        prefix = dirname(dirname(realpath(Env.klee())))
        found = next((join(prefix, lib) for lib in ("lib", "lib64")
                      if isfile(join(prefix, lib, "libkleeRuntest.so"))), None)
        return _require(found, "libkleeRuntest", f"Expected it in {prefix}/lib or {prefix}/lib64.")

    @staticmethod
    @cache
    def klee_clang() -> str:
        """clang producing bitcode KLEE can read: METRINOME_KLEE_CLANG, clang-N, or clang if not newer."""
        if override := os.environ.get("METRINOME_KLEE_CLANG"):
            return shutil.which(override) or override
        klee_llvm = _llvm_major(Env.klee())
        if klee_llvm is None:
            return Env.clang()
        if versioned := shutil.which(f"clang-{klee_llvm}"):
            return versioned
        try:
            clang: Optional[str] = Env.clang()
        except ToolNotFoundError:
            clang = None
        clang_llvm = _llvm_major(clang) if clang else None
        if clang and clang_llvm is not None and clang_llvm <= klee_llvm:
            return clang
        found = f"{clang} is LLVM {clang_llvm}" if clang else "no clang was found"
        raise ToolNotFoundError(f"KLEE uses LLVM {klee_llvm} and cannot read bitcode from newer LLVM; "
                                f"{found}. Install clang-{klee_llvm} or set METRINOME_KLEE_CLANG.")

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
