#!/usr/bin/env python3
"""
Example script to test the Llama Vision API.
"""

import requests
import base64
import json
import sys
from pathlib import Path


def test_health(base_url: str = "http://localhost:5000"):
    """Test the health endpoint."""
    print("Testing health endpoint...")
    response = requests.get(f"{base_url}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 200


def test_inference(image_path: str, prompt: str, base_url: str = "http://localhost:5000"):
    """Test the inference endpoint with an image."""
    print(f"\nTesting inference endpoint...")
    print(f"Image: {image_path}")
    print(f"Prompt: {prompt}")
    
    # Read and encode image
    try:
        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode()
    except FileNotFoundError:
        print(f"Error: Image file not found: {image_path}")
        return False
    
    # Prepare request
    payload = {
        "prompt": prompt,
        "image": image_data,
        "max_tokens": 300,
        "temperature": 0.7,
        "top_p": 0.95
    }
    
    # Make request
    try:
        print("Sending request...")
        response = requests.post(
            f"{base_url}/infer",
            json=payload,
            timeout=120  # 2 minutes timeout for slow CPU inference
        )
        
        print(f"Status: {response.status_code}")
        result = response.json()
        print(f"Response: {json.dumps(result, indent=2)}")
        
        if result.get("success"):
            print(f"\n✅ Success!")
            print(f"Model Response: {result.get('response_text')}")
            if result.get("token_usage"):
                usage = result["token_usage"]
                print(f"Tokens: {usage['total_tokens']} (prompt: {usage['prompt_tokens']}, completion: {usage['completion_tokens']})")
        else:
            print(f"\n❌ Error: {result.get('error')}")
        
        return response.status_code == 200
        
    except requests.exceptions.Timeout:
        print("Error: Request timed out (inference may take a long time on CPU)")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False


def main():
    """Main function."""
    base_url = "http://localhost:5000"
    
    # Test health
    if not test_health(base_url):
        print("\n❌ Health check failed! Is the service running?")
        sys.exit(1)
    
    print("\n✅ Health check passed!")
    
    # Test inference if image provided
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
        prompt = sys.argv[2] if len(sys.argv) > 2 else "Describe this image in detail."
        
        if test_inference(image_path, prompt, base_url):
            print("\n✅ Inference test passed!")
        else:
            print("\n❌ Inference test failed!")
            sys.exit(1)
    else:
        print("\nℹ️  To test inference, run:")
        print(f"  python {sys.argv[0]} <image_path> [prompt]")
        print("\nExample:")
        print(f"  python {sys.argv[0]} test_image.jpg 'What objects are in this image?'")


if __name__ == "__main__":
    main()
