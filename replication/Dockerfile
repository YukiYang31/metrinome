# Self-contained replication image: the source tree is copied in and the paper benchmark menu starts.
# Build from the repo root (see replication/run.sh):
#   docker build -t apcmetrinome/dockerapc -f replication/Dockerfile .
FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        clang-14 llvm-14 openjdk-17-jdk-headless python3 python3-pip git lolcat \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /tmp/requirements.txt
RUN pip3 install --no-cache-dir -r /tmp/requirements.txt wllvm

COPY src/ /app/code/
WORKDIR /app/code/
ENV PYTHONPATH=/app/code/
CMD ["bash", "Benchmark.sh"]
