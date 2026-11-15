# Metrinome development image: clang/LLVM 14 for the C front end, a JDK for the Java front end,
# KLEE (built against LLVM 15, the oldest LLVM KLEE 3.3 supports), and the Python dependencies.
# The source tree is mounted at /app/code by `make run` (see src/Makefile); build from the repo root:
#   docker build -t apcmetrinome/develop:latest -f src/Dockerfile .

FROM ubuntu:22.04 AS klee
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential cmake git ca-certificates clang-15 llvm-15 llvm-15-dev \
        libz3-dev libsqlite3-dev zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*
ARG KLEE_VERSION=v3.3
RUN git clone --depth 1 --branch "$KLEE_VERSION" https://github.com/klee/klee.git /src/klee \
    && cmake -S /src/klee -B /build -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=/opt/klee \
        -DLLVM_DIR=/usr/lib/llvm-15/lib/cmake/llvm -DLLVMCC=/usr/bin/clang-15 -DLLVMCXX=/usr/bin/clang++-15 \
        -DENABLE_SOLVER_Z3=ON -DENABLE_SOLVER_STP=OFF -DENABLE_TCMALLOC=OFF \
        -DENABLE_UNIT_TESTS=OFF -DENABLE_SYSTEM_TESTS=OFF -DENABLE_DOCS=OFF \
    && cmake --build /build -j"$(nproc)" \
    && cmake --install /build

FROM ubuntu:22.04
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        clang-14 llvm-14 clang-15 libz3-4 libsqlite3-0 openjdk-17-jdk-headless python3 python3-pip git \
    && rm -rf /var/lib/apt/lists/*

COPY --from=klee /opt/klee /opt/klee
# The C front end stays on LLVM 14; KLEE bitcode is compiled with clang-15, which Metrinome finds itself.
ENV PATH=/opt/klee/bin:$PATH METRINOME_CLANG=clang-14

COPY requirements.txt /tmp/requirements.txt
RUN pip3 install --no-cache-dir -r /tmp/requirements.txt wllvm tabulate

WORKDIR /app/code/
ENV PYTHONPATH=/app/code/
# customize command line prompt to look nice :)
RUN /bin/bash -c "echo \"PS1='\[\033[01;32m\]➜ \[\033[00m\] \[\033[01;36m\]\W \[\033[00m\]'\" >> /root/.bashrc "
