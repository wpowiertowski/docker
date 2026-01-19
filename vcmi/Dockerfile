# Multi-stage build for VCMI on ARM64 with web-based GUI
# Build stage - compile VCMI from source
FROM ubuntu:24.04 AS builder

LABEL maintainer="wpowiertowski"
LABEL description="VCMI (Heroes of Might and Magic III engine) builder stage"

# Avoid user interaction during package installation
ARG DEBIAN_FRONTEND=noninteractive
ENV TZ=UTC

# Install build dependencies for VCMI
RUN apt-get update && apt-get install -y \
    # Build tools
    cmake \
    g++ \
    clang \
    git \
    pkg-config \
    wget \
    # SDL2 development libraries
    libsdl2-dev \
    libsdl2-image-dev \
    libsdl2-mixer-dev \
    libsdl2-ttf-dev \
    # Boost libraries
    libboost-filesystem-dev \
    libboost-system-dev \
    libboost-thread-dev \
    libboost-program-options-dev \
    libboost-locale-dev \
    libboost-date-time-dev \
    libboost-atomic-dev \
    libboost-iostreams-dev \
    # FFmpeg libraries
    libavformat-dev \
    libswscale-dev \
    # Other dependencies
    libminizip-dev \
    zlib1g-dev \
    libtbb-dev \
    libfuzzylite-dev \
    libsquish-dev \
    # Qt5 for launcher
    qtbase5-dev \
    libqt5network5 \
    libqt5svg5-dev \
    qttools5-dev \
    # LuaJIT
    libluajit-5.1-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Install ONNX Runtime from GitHub releases
RUN ONNX_VERSION=1.23.2 && \
    wget -q https://github.com/microsoft/onnxruntime/releases/download/v${ONNX_VERSION}/onnxruntime-linux-aarch64-${ONNX_VERSION}.tgz && \
    tar -xzf onnxruntime-linux-aarch64-${ONNX_VERSION}.tgz && \
    mkdir -p /usr/local/include/onnxruntime && \
    cp -r onnxruntime-linux-aarch64-${ONNX_VERSION}/include/* /usr/local/include/onnxruntime/ && \
    cp -r onnxruntime-linux-aarch64-${ONNX_VERSION}/lib/* /usr/local/lib/ && \
    ln -s /usr/local/lib /usr/local/lib64 && \
    ldconfig && \
    rm -rf onnxruntime-linux-aarch64-${ONNX_VERSION}*

# Clone VCMI from develop branch
WORKDIR /build
RUN git clone --branch develop --depth 1 https://github.com/vcmi/vcmi.git

# Build VCMI
WORKDIR /build/vcmi
RUN git submodule update --init --recursive

RUN mkdir build && cd build && \
    cmake .. \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_INSTALL_PREFIX=/opt/vcmi \
    -DENABLE_TEST=OFF \
    && make -j$(nproc) && \
    make install

# Runtime stage - minimal image with only runtime dependencies
FROM ubuntu:24.04

LABEL maintainer="wpowiertowski"
LABEL description="VCMI (Heroes of Might and Magic III engine) with web-based GUI access via noVNC"
LABEL version="1.0"

# Avoid user interaction during package installation
ARG DEBIAN_FRONTEND=noninteractive
ENV TZ=UTC

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    # SDL2 runtime libraries
    libsdl2-2.0-0 \
    libsdl2-image-2.0-0 \
    libsdl2-mixer-2.0-0 \
    libsdl2-ttf-2.0-0 \
    # Boost runtime libraries
    libboost-filesystem1.83.0 \
    libboost-system1.83.0 \
    libboost-thread1.83.0 \
    libboost-program-options1.83.0 \
    libboost-locale1.83.0 \
    libboost-date-time1.83.0 \
    libboost-atomic1.83.0 \
    libboost-iostreams1.83.0 \
    # FFmpeg runtime libraries
    libavformat60 \
    libswscale7 \
    # Other runtime dependencies
    libminizip1t64 \
    zlib1g \
    libtbb12 \
    libfuzzylite6.0 \
    libsquish0 \
    # Qt5 runtime
    libqt5core5t64 \
    libqt5gui5t64 \
    libqt5widgets5t64 \
    libqt5network5t64 \
    # LuaJIT
    libluajit-5.1-2 \
    # X11 and GUI support
    xvfb \
    x11vnc \
    openbox \
    supervisor \
    git \
    curl \
    wget \
    python3 \
    python3-pip \
    net-tools \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Install ONNX Runtime from GitHub releases
RUN ONNX_VERSION=1.23.2 && \
    wget -q https://github.com/microsoft/onnxruntime/releases/download/v${ONNX_VERSION}/onnxruntime-linux-aarch64-${ONNX_VERSION}.tgz && \
    tar -xzf onnxruntime-linux-aarch64-${ONNX_VERSION}.tgz && \
    cp -r onnxruntime-linux-aarch64-${ONNX_VERSION}/lib/* /usr/local/lib/ && \
    ldconfig && \
    rm -rf onnxruntime-linux-aarch64-${ONNX_VERSION}*

# Install noVNC and websockify
RUN git clone --branch v1.4.0 --depth 1 https://github.com/novnc/noVNC.git /opt/noVNC && \
    git clone --branch v0.11.0 --depth 1 https://github.com/novnc/websockify /opt/noVNC/utils/websockify && \
    ln -s /opt/noVNC/vnc.html /opt/noVNC/index.html

# Copy VCMI from builder stage
COPY --from=builder /opt/vcmi /opt/vcmi

# Add VCMI to PATH
ENV PATH="/opt/vcmi/bin:${PATH}"
ENV LD_LIBRARY_PATH="/opt/vcmi/lib"

# Create non-root user for running VCMI
RUN useradd -m -s /bin/bash vcmi && \
    mkdir -p /home/vcmi/.local/share/vcmi && \
    chown -R vcmi:vcmi /home/vcmi

# Create supervisor configuration directory
RUN mkdir -p /etc/supervisor/conf.d

# Create supervisor configuration
RUN echo '[supervisord]' > /etc/supervisor/conf.d/supervisord.conf && \
    echo 'nodaemon=true' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'user=root' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'logfile=/var/log/supervisor/supervisord.log' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'pidfile=/var/run/supervisord.pid' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo '' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo '[program:xvfb]' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'command=/usr/bin/Xvfb :99 -screen 0 1280x720x24 -ac +extension GLX +render -noreset' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'autostart=true' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'autorestart=true' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'priority=10' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'user=root' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'stdout_logfile=/var/log/supervisor/xvfb.log' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'stderr_logfile=/var/log/supervisor/xvfb_error.log' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo '' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo '[program:openbox]' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'command=/usr/bin/openbox-session' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'autostart=true' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'autorestart=true' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'priority=20' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'user=vcmi' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'environment=DISPLAY=":99",HOME="/home/vcmi"' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'stdout_logfile=/var/log/supervisor/openbox.log' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'stderr_logfile=/var/log/supervisor/openbox_error.log' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo '' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo '[program:x11vnc]' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'command=/usr/bin/x11vnc -display :99 -nopw -listen 0.0.0.0 -xkb -forever -shared' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'autostart=true' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'autorestart=true' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'priority=30' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'user=root' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'stdout_logfile=/var/log/supervisor/x11vnc.log' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'stderr_logfile=/var/log/supervisor/x11vnc_error.log' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo '' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo '[program:novnc]' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'command=/opt/noVNC/utils/novnc_proxy --vnc localhost:5900 --listen 6080' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'autostart=true' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'autorestart=true' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'priority=40' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'user=root' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'stdout_logfile=/var/log/supervisor/novnc.log' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'stderr_logfile=/var/log/supervisor/novnc_error.log' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo '' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo '[program:vcmilauncher]' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'command=/opt/vcmi/bin/vcmilauncher' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'autostart=true' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'autorestart=true' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'priority=50' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'user=vcmi' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'environment=DISPLAY=":99",HOME="/home/vcmi",XDG_RUNTIME_DIR="/tmp/runtime-vcmi"' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'stdout_logfile=/var/log/supervisor/vcmilauncher.log' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'stderr_logfile=/var/log/supervisor/vcmilauncher_error.log' >> /etc/supervisor/conf.d/supervisord.conf

# Create entrypoint script
RUN printf '#!/bin/bash\n\
set -e\n\
\n\
# Set up XDG runtime directory for the vcmi user\n\
export XDG_RUNTIME_DIR="/tmp/runtime-vcmi"\n\
mkdir -p "$XDG_RUNTIME_DIR"\n\
chown vcmi:vcmi "$XDG_RUNTIME_DIR"\n\
chmod 700 "$XDG_RUNTIME_DIR"\n\
\n\
# Create VCMI data directories\n\
mkdir -p /home/vcmi/.local/share/vcmi/config\n\
mkdir -p /home/vcmi/.local/share/vcmi/Games\n\
mkdir -p /home/vcmi/.local/share/vcmi/Mods\n\
chown -R vcmi:vcmi /home/vcmi/.local/share/vcmi\n\
\n\
# Create supervisor log directory\n\
mkdir -p /var/log/supervisor\n\
\n\
echo "=========================================="\n\
echo "VCMI Docker Container"\n\
echo "=========================================="\n\
echo ""\n\
echo "Web GUI Access:"\n\
echo "  Open your browser and navigate to:"\n\
echo "  http://localhost:6080"\n\
echo ""\n\
echo "VCMI Data Directory:"\n\
echo "  /home/vcmi/.local/share/vcmi"\n\
echo ""\n\
echo "Important Notes:"\n\
echo "  1. You need to provide Heroes III game data files"\n\
echo "  2. Place game data in the mounted volume at /home/vcmi/.local/share/vcmi"\n\
echo "  3. The VCMI launcher will start automatically in the background"\n\
echo "  4. Access the GUI through your browser at http://localhost:6080"\n\
echo ""\n\
echo "To manually start VCMI launcher:"\n\
echo "  supervisorctl start vcmilauncher"\n\
echo ""\n\
echo "Starting services..."\n\
echo "=========================================="\n\
\n\
# Start supervisord\n\
exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf\n' > /entrypoint.sh

RUN chmod +x /entrypoint.sh

# Create volume for VCMI data
VOLUME ["/home/vcmi/.local/share/vcmi"]

# Expose noVNC port
EXPOSE 6080

# Switch to working directory
WORKDIR /home/vcmi

# Set entrypoint
ENTRYPOINT ["/entrypoint.sh"]
