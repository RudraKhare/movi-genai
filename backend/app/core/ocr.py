"""
Google Cloud Vision OCR Module

Handles image preprocessing and text extraction using Google Cloud Vision API.
"""

import base64
import json
import os
import io
from typing import Optional, Dict, Any
from PIL import Image, ImageEnhance, ImageFilter
from google.cloud import vision
from google.oauth2 import service_account

# Initialize Vision API client
def get_vision_client():
    """
    Initialize Google Cloud Vision client from base64-encoded service account key.
    """
    key_base64 = os.getenv("GOOGLE_VISION_KEY_BASE64")
    
    if not key_base64:
        raise ValueError("GOOGLE_VISION_KEY_BASE64 environment variable not set")
    
    try:
        # Decode base64 to JSON
        key_json = base64.b64decode(key_base64).decode('utf-8')
        key_data = json.loads(key_json)
        
        # Create credentials from service account info
        credentials = service_account.Credentials.from_service_account_info(key_data)
        
        # Initialize Vision client
        client = vision.ImageAnnotatorClient(credentials=credentials)
        return client
    except Exception as e:
        raise ValueError(f"Failed to initialize Vision API client: {str(e)}")


def preprocess_image(image_bytes: bytes) -> bytes:
    """
    Preprocess image to improve OCR accuracy.
    
    Steps:
    1. Convert to grayscale
    2. Enhance contrast
    3. Apply sharpening filter
    4. Resize if too large
    5. Apply threshold for better text detection
    
    Args:
        image_bytes: Raw image bytes
        
    Returns:
        Preprocessed image bytes
    """
    try:
        # Load image
        image = Image.open(io.BytesIO(image_bytes))
        
        # Convert to RGB if necessary
        if image.mode not in ('RGB', 'L'):
            image = image.convert('RGB')
        
        # Resize if too large (max 2000px on longest side)
        max_dimension = 2000
        if max(image.size) > max_dimension:
            ratio = max_dimension / max(image.size)
            new_size = tuple(int(dim * ratio) for dim in image.size)
            image = image.resize(new_size, Image.Resampling.LANCZOS)
        
        # Convert to grayscale
        image = image.convert('L')
        
        # Enhance contrast
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(2.0)
        
        # Sharpen
        image = image.filter(ImageFilter.SHARPEN)
        
        # Apply adaptive threshold (convert to binary)
        # Use point() with threshold
        threshold = 128
        image = image.point(lambda x: 255 if x > threshold else 0)
        
        # Convert back to bytes
        output = io.BytesIO()
        image.save(output, format='PNG')
        return output.getvalue()
        
    except Exception as e:
        # If preprocessing fails, return original image
        print(f"Warning: Image preprocessing failed: {e}")
        return image_bytes


def extract_text_from_image(image_bytes: bytes, preprocess: bool = True) -> Dict[str, Any]:
    """
    Extract text from image using Google Cloud Vision OCR.
    
    Args:
        image_bytes: Raw image bytes
        preprocess: Whether to preprocess image before OCR
        
    Returns:
        Dictionary containing:
        - text: Full extracted text
        - confidence: Average confidence score
        - annotations: List of text annotations with bounding boxes
        - success: Boolean indicating if text was found
    """
    try:
        # Preprocess image if requested
        if preprocess:
            processed_bytes = preprocess_image(image_bytes)
        else:
            processed_bytes = image_bytes
        
        # Initialize Vision client
        client = get_vision_client()
        
        # Create image object
        image = vision.Image(content=processed_bytes)
        
        # Perform text detection
        response = client.text_detection(image=image)
        
        # Check for errors
        if response.error.message:
            raise Exception(f"Vision API error: {response.error.message}")
        
        # Extract text annotations
        annotations = response.text_annotations
        
        if not annotations:
            return {
                "text": "",
                "confidence": 0.0,
                "annotations": [],
                "success": False,
                "message": "No text detected in image"
            }
        
        # First annotation contains full text
        full_text = annotations[0].description
        
        # Calculate average confidence
        confidences = [ann.confidence for ann in annotations[1:] if hasattr(ann, 'confidence')]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        
        # Extract detailed annotations
        detailed_annotations = []
        for annotation in annotations[1:]:  # Skip first (full text)
            detailed_annotations.append({
                "text": annotation.description,
                "confidence": getattr(annotation, 'confidence', 0.0),
                "bounds": [
                    {"x": vertex.x, "y": vertex.y}
                    for vertex in annotation.bounding_poly.vertices
                ] if hasattr(annotation, 'bounding_poly') else []
            })
        
        return {
            "text": full_text,
            "confidence": avg_confidence,
            "annotations": detailed_annotations,
            "success": True,
            "message": "Text extracted successfully"
        }
        
    except Exception as e:
        return {
            "text": "",
            "confidence": 0.0,
            "annotations": [],
            "success": False,
            "message": f"OCR failed: {str(e)}"
        }


def extract_text(image_bytes: bytes) -> str:
    """
    Simple wrapper to extract just the text string from an image.
    
    Args:
        image_bytes: Raw image bytes
        
    Returns:
        Extracted text string
    """
    result = extract_text_from_image(image_bytes, preprocess=True)
    return result.get("text", "")
