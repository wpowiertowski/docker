# Multi-stage build for llama.cpp with Llama 3.2 Vision support
FROM python:3.11-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Build llama.cpp from source
WORKDIR /build
RUN git clone https://github.com/ggerganov/llama.cpp.git
WORKDIR /build/llama.cpp
RUN cmake -B build -DLLAMA_CURL=ON
RUN cmake --build build --config Release

# Final runtime image
FROM python:3.11-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy llama.cpp build from builder
COPY --from=builder /build/llama.cpp/build/bin/llama-server /usr/local/bin/
COPY --from=builder /build/llama.cpp/build/bin/llama-cli /usr/local/bin/

# Set working directory
WORKDIR /app

# Copy application files
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ /app/

# Environment variables
ENV MODEL_NAME="llama-3.2-11b-vision-instruct-q4_k_m.gguf"
ENV CLIP_MODEL_NAME="mmproj-model-f16.gguf"
ENV MODEL_PATH="/models"
ENV FLASK_APP=webhook.py
ENV PYTHONUNBUFFERED=1

# Create models directory
RUN mkdir -p /models

# Expose Flask port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Run Flask app
CMD ["python", "webhook.py"]
