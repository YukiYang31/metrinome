<img src="resources/Metrinome.svg" height="100">

[![CI](https://github.com/YukiYang31/metrinome/actions/workflows/ci.yml/badge.svg)](https://github.com/YukiYang31/metrinome/actions/workflows/ci.yml)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)

## Overview

Metrinome is an all-purpose tool for working with code complexity metrics. It can be used as both a REPL and API, and includes:

- Converters to turn C, C++, Java, and Python code into control flow graphs (CFGs)
- Metric calculators for NPath, Cyclomatic, and (asymptotic) Path Complexity, including interprocedural and recursive path complexity
- KLEE utilities to automatically analyze C++ code

<img src="resources/repl_screenshot.png" height="300">

## Getting started

### Native

Requirements:

- Python 3.10 or newer
- clang and the matching LLVM `opt`, version 14 or newer (for C/C++)
- a JDK, version 8 or newer (for Java; `javac` and `java`)

```bash
pip install -r requirements.txt
python3 src/main.py            # start the REPL; flags: --interprocedural, --recursion, --poor, --debug
```

Inside the REPL, for example:

```
convert path/to/file.c
metrics *
export metrics *
```

Exports are written to `src/exports/`.

Metrinome finds its tools on `PATH`. Override them with environment variables when needed:

| Variable | Default |
|---|---|
| `METRINOME_CLANG` | `clang`, else the newest `clang-NN` on `PATH` |
| `METRINOME_OPT` | the `opt` installed next to the selected clang, else `opt` on `PATH` |
| `JAVA_HOME` | `javac`/`java` on `PATH` |
| `METRINOME_HOME` | the `src/` directory of this checkout (temporary and export files live here) |
| `METRINOME_KLEE`, `METRINOME_KLEE_INCLUDE` | `/app/build/bin/klee`, `/app/klee/include` |

On Ubuntu: `sudo apt install clang-14 llvm-14 openjdk-17-jdk-headless`. Without root, conda-forge provides everything:
`micromamba create -p ./toolchain -c conda-forge clang llvm-tools openjdk` and then add `./toolchain/bin` to `PATH`.

### Docker

```bash
docker build -t apcmetrinome/develop:latest -f src/Dockerfile .
cd src && make run             # mounts src/ at /app/code and starts a shell in the image
```

The self-contained replication image (`replication/Dockerfile`) copies the sources in and opens the paper benchmark menu.

## Paper benchmarks

`src/Benchmark.sh` reproduces the published results (ICSE 2021, FormaliSE 2023, ICSE 2024 poster, ISSTA 2024):

```bash
bash src/Benchmark.sh
```

Experiment scripts under `src/experiments` import Metrinome's modules, so run them with `PYTHONPATH=src`.

## Tests

```bash
pip install -r requirements-dev.txt
cd src && python3 -m unittest discover -s tests -t .
```

The suite includes regression tests that pin the published ICSE 2021 and ISSTA 2024 results. CI runs it on every push.

## Links

- **Documentation** https://github.com/hmc-alpaqa/metrinome/wiki
- **DockerHub** https://hub.docker.com/repository/docker/harveymudd/metrinome
- **Initial Paper** https://www.cs.hmc.edu/~bang/research/metrinome.pdf
