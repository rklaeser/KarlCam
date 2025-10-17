"""
Gemini Vision API service for on-demand fog labeling
"""

import os
import json
import re
import logging
from typing import Dict, Optional
from PIL import Image
import io
import google.generativeai as genai

logger = logging.getLogger(__name__)


class GeminiService:
    """Service for analyzing images using Gemini Vision API"""
    
    def __init__(self):
        self.model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
        self.model = None
        self._initialize()
    
    def _initialize(self):
        """Initialize Gemini client"""
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")
        
        try:
            genai.configure(api_key=api_key.strip())
            self.model = genai.GenerativeModel(self.model_name)
            logger.info(f"Initialized Gemini service with model: {self.model_name}")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini: {e}")
            raise
    
    def analyze_image(self, image_data: bytes, webcam_name: str = "Unknown") -> Dict:
        """
        Analyze image for fog conditions
        
        Args:
            image_data: Raw image bytes
            webcam_name: Name of the webcam for context
            
        Returns:
            Dictionary with fog analysis results
        """
        try:
            # Convert bytes to PIL Image
            image = Image.open(io.BytesIO(image_data)).convert('RGB')
            
            prompt = f"""Analyze this image from the {webcam_name} webcam for fog conditions. 
            Provide your assessment in JSON format:
            {{
                "fog_score": <0-100, where 0=perfectly clear, 100=dense fog>,
                "fog_level": "<Clear|Light Fog|Moderate Fog|Heavy Fog|Very Heavy Fog>",
                "confidence": <0.0-1.0>,
                "reasoning": "<brief explanation of visual indicators>",
                "visibility_estimate": "<estimated visibility in meters>",
                "weather_conditions": ["list", "of", "observed", "conditions"]
            }}"""
            
            # Generate content with retry logic
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    response = self.model.generate_content([prompt, image])
                    
                    # Extract JSON from response
                    json_str = response.text
                    json_match = re.search(r'```json\s*(.*?)\s*```', json_str, re.DOTALL)
                    if json_match:
                        json_str = json_match.group(1)
                    
                    data = json.loads(json_str)
                    
                    # Validate and normalize the response
                    return {
                        "fog_score": float(data.get("fog_score", 0)),
                        "fog_level": data.get("fog_level", "Unknown"),
                        "confidence": float(data.get("confidence", 0)),
                        "reasoning": data.get("reasoning", ""),
                        "visibility_estimate": data.get("visibility_estimate", "Unknown"),
                        "weather_conditions": data.get("weather_conditions", []),
                        "labeler_name": f"gemini_{self.model_name.replace('.', '_').replace('-', '_')}",
                        "labeler_version": "1.0"
                    }
                    
                except json.JSONDecodeError as e:
                    logger.warning(f"JSON decode error on attempt {attempt + 1}: {e}")
                    if attempt == max_retries - 1:
                        raise
                except Exception as e:
                    logger.warning(f"Gemini API error on attempt {attempt + 1}: {e}")
                    if attempt == max_retries - 1:
                        raise
                    
        except Exception as e:
            logger.error(f"Failed to analyze image: {e}")
            # Return default values on error
            return {
                "fog_score": None,
                "fog_level": "Unknown",
                "confidence": 0,
                "reasoning": f"Analysis failed: {str(e)}",
                "visibility_estimate": "Unknown",
                "weather_conditions": [],
                "labeler_name": f"gemini_{self.model_name.replace('.', '_').replace('-', '_')}",
                "labeler_version": "1.0",
                "error": str(e)
            }


# Singleton instance
_gemini_service: Optional[GeminiService] = None


def get_gemini_service() -> GeminiService:
    """Get or create the Gemini service singleton"""
    global _gemini_service
    if _gemini_service is None:
        _gemini_service = GeminiService()
    return _gemini_service