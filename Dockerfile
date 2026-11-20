FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get -y install --no-install-recommends \
    ca-certificates \
    build-essential \
    clang \
    cmake \
    gdb \
    git \
    libboost-all-dev \
    python3-dev \
    python3-pip \
    python3-tk \
    python3-venv \
    wget \
    xvfb \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*