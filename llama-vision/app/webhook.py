"""
Flask webhook interface for Llama 3.2 Vision model inference.
Accepts images and text prompts, returns JSON responses.
"""

import os
import logging
import base64
import tempfile
from io import BytesIO
from pathlib import Path
from typing import Optional, List, Dict, Any

from flask import Flask, request, jsonify
from PIL import Image
from llama_cpp import Llama

from schema import VisionResponse, ErrorResponse, HealthResponse, TokenUsage


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Global model instance
llama_model: Optional[Llama] = None
model_name: str = ""


def load_model():
    """Load the Llama model from the specified path."""
    global llama_model, model_name
    
    model_path_env = os.environ.get('MODEL_PATH', '/models')
    model_name_env = os.environ.get('MODEL_NAME', 'llama-3.2-11b-vision-instruct-q4_k_m.gguf')
    clip_model_name_env = os.environ.get('CLIP_MODEL_NAME', 'mmproj-model-f16.gguf')
    
    full_model_path = Path(model_path_env) / model_name_env
    full_clip_path = Path(model_path_env) / clip_model_name_env
    
    logger.info(f"Loading model from: {full_model_path}")
    logger.info(f"Loading CLIP model from: {full_clip_path}")
    
    if not full_model_path.exists():
        logger.error(f"Model file not found at: {full_model_path}")
        raise FileNotFoundError(f"Model file not found at: {full_model_path}")
    
    if not full_clip_path.exists():
        logger.warning(f"CLIP model file not found at: {full_clip_path}")
        logger.warning("Vision features may not work without CLIP model")
    
    try:
        # Initialize with vision support
        # For Llama 3.2 Vision models, we need both the main model and CLIP projector
        
        # Configure CPU threads conservatively to avoid resource contention
        # Use environment variable if set, otherwise use half of available CPUs
        n_threads = int(os.environ.get('N_THREADS', 0))
        if n_threads <= 0:
            cpu_count = os.cpu_count() or 4
            n_threads = max(1, cpu_count // 2)
        
        logger.info(f"Using {n_threads} CPU threads for inference")
        
        model_kwargs = {
            "model_path": str(full_model_path),
            "n_ctx": 2048,  # Context window
            "n_threads": n_threads,
            "n_gpu_layers": 0,  # CPU only, no GPU layers
            "verbose": False,
        }
        
        # Add CLIP model if available
        if full_clip_path.exists():
            model_kwargs["clip_model_path"] = str(full_clip_path)
            model_kwargs["chat_format"] = "llava-1-5"  # Vision chat format
            logger.info("CLIP model loaded for vision support")
        else:
            logger.warning("Running without CLIP model - vision features disabled")
        
        llama_model = Llama(**model_kwargs)
        model_name = model_name_env
        logger.info(f"Model loaded successfully: {model_name}")
        return True
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        raise


def process_image(image_data: str, image_format: str = "base64") -> str:
    """
    Process image data and return path to temporary file.
    
    Args:
        image_data: Base64 encoded image or image bytes
        image_format: Format of the image data (base64, bytes)
    
    Returns:
        Path to temporary image file
    """
    try:
        if image_format == "base64":
            # Remove data URL prefix if present
            if "," in image_data:
                image_data = image_data.split(",", 1)[1]
            
            image_bytes = base64.b64decode(image_data)
        else:
            image_bytes = image_data
        
        # Open image with PIL to validate and potentially convert
        img = Image.open(BytesIO(image_bytes))
        
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
        img.save(temp_file.name, format="PNG")
        temp_file.close()
        
        return temp_file.name
    except Exception as e:
        logger.error(f"Failed to process image: {e}")
        raise ValueError(f"Invalid image data: {e}")


def create_vision_prompt(text: str, image_path: str) -> List[Dict[str, Any]]:
    """
    Create a prompt in the format expected by llama-cpp-python for vision models.
    
    Args:
        text: Text prompt
        image_path: Path to the image file
    
    Returns:
        Formatted prompt as list of message dicts
    """
    return [
        {
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": f"file://{image_path}"}},
                {"type": "text", "text": text}
            ]
        }
    ]


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    try:
        is_loaded = llama_model is not None
        status = "healthy" if is_loaded else "unhealthy"
        
        response = HealthResponse(
            status=status,
            model_loaded=is_loaded,
            model_name=model_name if is_loaded else "not loaded"
        )
        
        return jsonify(response.model_dump()), 200 if is_loaded else 503
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({"status": "error", "error": str(e)}), 500


@app.route('/infer', methods=['POST'])
def infer():
    """
    Main inference endpoint.
    
    Expected JSON payload:
    {
        "prompt": "Describe this image",
        "image": "base64_encoded_image_data",
        "max_tokens": 256,
        "temperature": 0.7,
        "top_p": 0.95
    }
    """
    try:
        # Validate model is loaded
        if llama_model is None:
            error = ErrorResponse(
                error="Model not loaded",
                error_type="model",
                details={"message": "Model failed to load at startup"}
            )
            return jsonify(error.model_dump()), 503
        
        # Parse request JSON
        data = request.get_json()
        if not data:
            error = ErrorResponse(
                error="No JSON data provided",
                error_type="validation"
            )
            return jsonify(error.model_dump()), 400
        
        # Extract required fields
        prompt_text = data.get('prompt')
        image_data = data.get('image')
        
        if not prompt_text:
            error = ErrorResponse(
                error="Missing required field: prompt",
                error_type="validation"
            )
            return jsonify(error.model_dump()), 400
        
        if not image_data:
            error = ErrorResponse(
                error="Missing required field: image",
                error_type="validation"
            )
            return jsonify(error.model_dump()), 400
        
        # Extract optional parameters
        max_tokens = data.get('max_tokens', 256)
        temperature = data.get('temperature', 0.7)
        top_p = data.get('top_p', 0.95)
        
        logger.info(f"Processing inference request (prompt length: {len(prompt_text)} chars)")
        
        # Process image
        image_path = None
        try:
            image_path = process_image(image_data)
        except ValueError as e:
            error = ErrorResponse(
                error=str(e),
                error_type="validation"
            )
            return jsonify(error.model_dump()), 400
        
        try:
            # Create vision prompt
            messages = create_vision_prompt(prompt_text, image_path)
            
            # Run inference
            result = llama_model.create_chat_completion(
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
            )
            
            # Extract response
            response_text = result['choices'][0]['message']['content']
            
            # Get token usage
            usage = result.get('usage', {})
            token_usage = TokenUsage(
                prompt_tokens=usage.get('prompt_tokens', 0),
                completion_tokens=usage.get('completion_tokens', 0),
                total_tokens=usage.get('total_tokens', 0)
            )
            
            # Create response
            response = VisionResponse(
                success=True,
                response_text=response_text,
                model=model_name,
                token_usage=token_usage,
                metadata={
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "top_p": top_p
                }
            )
            
            logger.info(f"Inference completed successfully")
            return jsonify(response.model_dump()), 200
            
        finally:
            # Clean up temporary image file
            if image_path:
                try:
                    os.unlink(image_path)
                except Exception as e:
                    logger.warning(f"Failed to delete temporary image: {e}")
    
    except Exception as e:
        logger.error(f"Inference error: {e}", exc_info=True)
        error = ErrorResponse(
            error=str(e),
            error_type="system",
            details={"traceback": str(e)}
        )
        return jsonify(error.model_dump()), 500


@app.route('/', methods=['GET'])
def index():
    """Root endpoint with API information."""
    return jsonify({
        "service": "Llama 3.2 Vision Inference API",
        "version": "1.0.0",
        "endpoints": {
            "/health": "GET - Health check",
            "/infer": "POST - Run inference with image and text prompt",
        },
        "model": model_name if llama_model else "not loaded"
    }), 200


if __name__ == '__main__':
    # Load model at startup
    try:
        load_model()
    except Exception as e:
        logger.error(f"Failed to load model at startup: {e}")
        logger.warning("Starting server anyway, but inference will fail")
    
    # Start Flask server
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
