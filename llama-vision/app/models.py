"""
Request and response models for runtime validation in the Llama Vision webhook.
For the formal JSON schema definitions, see request_schema.json and response_schema.json.
"""

from typing import Optional, Dict, Any, Literal
from pydantic import BaseModel, Field, validator
from datetime import datetime


class InferenceRequest(BaseModel):
    """Request format for vision inference with image and text prompt."""
    
    prompt: str = Field(
        description="Text prompt or question about the image",
        min_length=1
    )
    image: str = Field(
        description="Base64 encoded image data. Can include data URL prefix or be raw base64 string",
        min_length=1
    )
    max_tokens: Optional[int] = Field(
        default=256,
        description="Maximum number of tokens to generate in the response",
        ge=1,
        le=4096
    )
    temperature: Optional[float] = Field(
        default=0.7,
        description="Sampling temperature for response generation",
        ge=0.0,
        le=2.0
    )
    top_p: Optional[float] = Field(
        default=0.95,
        description="Nucleus sampling parameter",
        ge=0.0,
        le=1.0
    )


class TokenUsage(BaseModel):
    """Token usage statistics."""
    prompt_tokens: int = Field(description="Number of tokens in the prompt")
    completion_tokens: int = Field(description="Number of tokens in the completion")
    total_tokens: int = Field(description="Total number of tokens used")


class VisionResponse(BaseModel):
    """Standard response format for vision inference requests."""
    
    success: bool = Field(description="Whether the request was successful")
    response_text: str = Field(description="The generated text response from the model")
    model: str = Field(description="The model used for inference")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat(), 
                          description="ISO timestamp of the response")
    token_usage: Optional[TokenUsage] = Field(None, description="Token usage statistics")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, 
                                               description="Additional metadata")
    error: Optional[str] = Field(None, description="Error message if success is False")


class ErrorResponse(BaseModel):
    """Error response format."""
    
    success: bool = Field(default=False, description="Always False for error responses")
    error: str = Field(description="Error message describing what went wrong")
    error_type: Literal["validation", "model", "system"] = Field(
        description="Type of error (validation, model, or system)"
    )
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat(),
                          description="ISO timestamp of the error")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")


class HealthResponse(BaseModel):
    """Health check response format."""
    
    status: Literal["healthy", "unhealthy", "degraded"] = Field(
        description="Health status (healthy, unhealthy, or degraded)"
    )
    model_loaded: bool = Field(description="Whether the model is loaded and ready")
    model_name: str = Field(description="Name of the loaded model")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat(),
                          description="ISO timestamp of health check")
