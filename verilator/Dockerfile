# Minimal Verilator simulator Docker image
# Based on https://github.com/lowRISC/opentitan/tree/master/util/container

FROM ubuntu:22.04

LABEL version="1.0"
LABEL description="Minimal Verilator development container for RTL simulation."
LABEL maintainer="wpowiertowski"

# Avoid user interaction with tzdata during install
ARG DEBIAN_FRONTEND=noninteractive
ENV TZ=UTC

# Use bash as default shell
RUN ln -sf /bin/bash /bin/sh

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
    libfl2 \
    libfl-dev \
    libgoogle-perftools-dev \
    make \
    numactl \
    perl \
    perl-doc \
    python3 \
    python3-pip \
    verilator \
    wget \
    zlib1g \
    zlib1g-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* /usr/share/doc/*

# Set locale
ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8
ENV LANGUAGE=en_US:en

# Create working directory
WORKDIR /work

# Default command shows Verilator version
CMD ["verilator", "--version"]
