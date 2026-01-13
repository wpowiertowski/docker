# Llama 3.2 Vision Docker Setup

Docker image that runs Llama 3.2 Vision model with CPU inference (no GPU/NVIDIA acceleration) using the recommended Q4_K_M quantization. The service exposes a Flask webhook interface to accept images and text prompts and provides responses via JSON.

## Features

- 🚀 CPU-only inference using llama.cpp (no GPU required)
- 📸 Vision model support for image understanding
- 🔧 Q4_K_M quantization for optimal CPU performance (as recommended in [llama.cpp PR #5780](https://github.com/ggml-org/llama.cpp/pull/5780))
- 🌐 RESTful API with Flask webhook interface
- 📋 Structured JSON response schema
- 🔍 Health check endpoint
- 📊 Token usage tracking

## Quick Start

### Prerequisites

- Docker installed on your system
- A Llama 3.2 Vision model in GGUF format with Q4_K_M quantization

### Download Model

You can download the recommended Q4_K_M quantized Llama 3.2 Vision model from Hugging Face:

```bash
# Example: Download Llama 3.2 11B Vision Instruct Q4_K_M
# Visit https://huggingface.co/ and search for "llama-3.2-vision Q4_K_M GGUF"
# Download the .gguf file and place it in a models directory
mkdir -p models
# Place your downloaded model in ./models/
```

### Build the Docker Image

```bash
docker build -t llama-vision:latest .
```

### Run the Container

```bash
docker run -d \
  -p 5000:5000 \
  -v $(pwd)/models:/models \
  -e MODEL_NAME="your-model-name.gguf" \
  --name llama-vision \
  llama-vision:latest
```

### Environment Variables

- `MODEL_NAME`: Name of the GGUF model file (default: `llama-3.2-11b-vision-instruct-q4_k_m.gguf`)
- `MODEL_PATH`: Directory containing the model (default: `/models`)
- `PORT`: Port for the Flask server (default: `5000`)

## API Documentation

### Health Check

**Endpoint:** `GET /health`

**Response:**
```json
{
  "status": "healthy",
  "model_loaded": true,
  "model_name": "llama-3.2-11b-vision-instruct-q4_k_m.gguf",
  "timestamp": "2024-01-13T12:00:00.000000"
}
```

### Inference Endpoint

**Endpoint:** `POST /infer`

**Request Body:**
```json
{
  "prompt": "Describe what you see in this image",
  "image": "base64_encoded_image_data",
  "max_tokens": 256,
  "temperature": 0.7,
  "top_p": 0.95
}
```

**Parameters:**
- `prompt` (required): Text prompt/question about the image
- `image` (required): Base64 encoded image data (supports data URL format)
- `max_tokens` (optional): Maximum tokens in response (default: 256)
- `temperature` (optional): Sampling temperature (default: 0.7)
- `top_p` (optional): Nucleus sampling parameter (default: 0.95)

**Success Response (200):**
```json
{
  "success": true,
  "response_text": "The image shows a beautiful sunset over mountains...",
  "model": "llama-3.2-11b-vision-instruct-q4_k_m.gguf",
  "timestamp": "2024-01-13T12:00:00.000000",
  "token_usage": {
    "prompt_tokens": 150,
    "completion_tokens": 200,
    "total_tokens": 350
  },
  "metadata": {
    "max_tokens": 256,
    "temperature": 0.7,
    "top_p": 0.95
  },
  "error": null
}
```

**Error Response (400/500):**
```json
{
  "success": false,
  "error": "Missing required field: prompt",
  "error_type": "validation",
  "timestamp": "2024-01-13T12:00:00.000000",
  "details": null
}
```

## Response Schema

### VisionResponse

```python
{
  "success": bool,              # Request success status
  "response_text": str,         # Generated text response
  "model": str,                 # Model used for inference
  "timestamp": str,             # ISO timestamp
  "token_usage": {              # Token usage statistics
    "prompt_tokens": int,
    "completion_tokens": int,
    "total_tokens": int
  },
  "metadata": dict,             # Additional metadata
  "error": str | null           # Error message if any
}
```

### ErrorResponse

```python
{
  "success": false,             # Always false for errors
  "error": str,                 # Error message
  "error_type": str,            # Error type (validation, model, system)
  "timestamp": str,             # ISO timestamp
  "details": dict | null        # Additional error details
}
```

## Example Usage

### Python Example

```python
import requests
import base64

# Read and encode image
with open("image.jpg", "rb") as f:
    image_data = base64.b64encode(f.read()).decode()

# Make request
response = requests.post(
    "http://localhost:5000/infer",
    json={
        "prompt": "What objects can you see in this image?",
        "image": image_data,
        "max_tokens": 300,
        "temperature": 0.7
    }
)

result = response.json()
print(result["response_text"])
```

### cURL Example

```bash
# Encode image to base64
IMAGE_B64=$(base64 -w 0 image.jpg)

# Make request
curl -X POST http://localhost:5000/infer \
  -H "Content-Type: application/json" \
  -d "{
    \"prompt\": \"Describe this image in detail\",
    \"image\": \"$IMAGE_B64\",
    \"max_tokens\": 256
  }"
```

## Technical Details

### Quantization

This setup uses **Q4_K_M** quantization, which is recommended for CPU inference as it provides:
- Excellent balance between quality and performance
- ~4GB memory footprint for 7B models
- Good accuracy preservation compared to higher precision formats
- Optimized for CPU matrix operations

The recommendation comes from the llama.cpp community discussions, particularly [PR #5780](https://github.com/ggml-org/llama.cpp/pull/5780), where Q4_K_M is noted as the default choice for most use cases.

### Architecture

- **Base Image:** Python 3.11-slim (small footprint)
- **Build:** Multi-stage build for smaller final image
- **Inference Engine:** llama.cpp compiled from source with CPU optimizations
- **Python Bindings:** llama-cpp-python for easy integration
- **Web Framework:** Flask for RESTful API
- **Image Processing:** Pillow for image handling

### Performance Considerations

- CPU threads are automatically configured to use all available cores
- Context window: 2048 tokens (configurable in code)
- No GPU layers (n_gpu_layers=0)
- Optimized for multi-core CPU inference

## Development

### Project Structure

```
llama-vision/
├── Dockerfile              # Multi-stage Docker build
├── requirements.txt        # Python dependencies
├── README.md              # This file
└── app/
    ├── webhook.py         # Flask application
    └── schema.py          # Pydantic response schemas
```

### Building and Testing Locally

```bash
# Build
docker build -t llama-vision:latest .

# Run with mounted models directory
docker run -it --rm \
  -p 5000:5000 \
  -v $(pwd)/models:/models \
  -e MODEL_NAME="your-model.gguf" \
  llama-vision:latest

# Test health endpoint
curl http://localhost:5000/health

# Test inference
curl -X POST http://localhost:5000/infer \
  -H "Content-Type: application/json" \
  -d '{"prompt": "test", "image": "..."}'
```

## Troubleshooting

### Model Not Found

Ensure your model file is in the correct location:
```bash
ls -la models/
```

The model file should match the `MODEL_NAME` environment variable.

### Out of Memory

If you experience OOM errors:
- Use a smaller model (1B or 3B instead of 11B)
- Reduce context window in webhook.py (n_ctx parameter)
- Ensure sufficient RAM (11B models need ~6-8GB RAM with Q4_K_M)

### Slow Inference

CPU inference is inherently slower than GPU:
- Consider using a smaller model for faster responses
- Ensure Docker has access to all CPU cores
- Use Q4_K_M quantization (already configured)

## License

MIT License - see repository LICENSE file for details.

## References

- [llama.cpp](https://github.com/ggerganov/llama.cpp)
- [llama-cpp-python](https://github.com/abetlen/llama-cpp-python)
- [Llama 3.2 Models](https://huggingface.co/meta-llama)
- [GGUF Quantization Guide](https://github.com/ggerganov/llama.cpp/pull/5780)
