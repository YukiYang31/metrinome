# Metrinome development image: clang/LLVM 14, a JDK for the Java front end, and the Python dependencies.
# The source tree is mounted at /app/code by `make run` (see src/Makefile); build from the repo root:
#   docker build -t apcmetrinome/develop:latest -f src/Dockerfile .
FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        clang-14 llvm-14 openjdk-17-jdk-headless python3 python3-pip git \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /tmp/requirements.txt
RUN pip3 install --no-cache-dir -r /tmp/requirements.txt wllvm

WORKDIR /app/code/
ENV PYTHONPATH=/app/code/
# customize command line prompt to look nice :)
RUN /bin/bash -c "echo \"PS1='\[\033[01;32m\]➜ \[\033[00m\] \[\033[01;36m\]\W \[\033[00m\]'\" >> /root/.bashrc "
