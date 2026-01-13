"""
Response schema definitions for the Llama Vision webhook.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


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
    error_type: str = Field(description="Type of error (e.g., validation, model, system)")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat(),
                          description="ISO timestamp of the error")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")


class HealthResponse(BaseModel):
    """Health check response format."""
    
    status: str = Field(description="Health status (healthy, unhealthy, degraded)")
    model_loaded: bool = Field(description="Whether the model is loaded and ready")
    model_name: str = Field(description="Name of the loaded model")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat(),
                          description="ISO timestamp of health check")
