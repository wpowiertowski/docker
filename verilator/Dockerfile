# Minimal Verilator simulator Docker image
# Based on https://github.com/lowRISC/opentitan/tree/master/util/container

FROM ubuntu:24.04

LABEL version="1.0"
LABEL description="Minimal Verilator development container for RTL simulation."
LABEL maintainer="wpowiertowski"

# Avoid user interaction with tzdata during install
ARG DEBIAN_FRONTEND=noninteractive
ENV TZ=America/Los_Angeles

# Install system packages required for Verilator and build tools
RUN apt-get update && apt-get install -y \
    autoconf \
    automake \
    autotools-dev \
    bc \
    bison \
    build-essential \
    ca-certificates \
    ccache \
    clang \
    curl \
    flex \
    g++ \
    git \
    help2man \
    libfl2 \
    libfl-dev \
    libgoogle-perftools-dev \
    make \
    numactl \
    perl \
    perl-doc \
    python3 \
    python3-dev \
    python3-pip \
    software-properties-common \
    wget \
    zlib1g \
    zlib1g-dev \
    zsh \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* /usr/share/doc/*

# Build and install Verilator 5.044 from source
RUN cd /tmp \
    && git clone https://github.com/verilator/verilator.git \
    && cd verilator \
    && git checkout v5.044 \
    && autoconf \
    && ./configure \
    && make -j$(nproc) \
    && make install \
    && cd / \
    && rm -rf /tmp/verilator

# Use zsh as default shell
RUN ln -sf /bin/zsh /bin/sh

# Install cocotb 2.0.0 and related Python packages
RUN python3 -m pip install --break-system-packages --trusted-host pypi.org --trusted-host files.pythonhosted.org "cocotb==2.0.0" cocotb-bus pytest

# Set locale
ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8
ENV LANGUAGE=en_US:en

# Create working directory
WORKDIR /work

# Default command shows Verilator version
CMD ["verilator", "--version"]
