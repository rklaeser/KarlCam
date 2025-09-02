"""
Standard Gemini Vision API labeler
"""

import os
import json
import re
from pathlib import Path
from PIL import Image
from typing import Dict
from .base import BaseLabeler

def load_env_file():
    """Load environment variables from .env file"""
    env_path = Path(__file__).parent.parent / '.env'
    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    if key not in os.environ:
                        os.environ[key] = value.strip('"\'')

load_env_file()

class GeminiLabeler(BaseLabeler):
    """Standard Gemini Vision API based labeler"""
    
    def __init__(self, model_name: str = "gemini-1.5-flash", version: str = "1.0"):
        super().__init__(f"gemini_{model_name.replace('.', '_').replace('-', '_')}", version)
        self.model_name = model_name
        self.gemini_model = None
        
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=api_key)
                self.gemini_model = genai.GenerativeModel(model_name)
                self.logger.info(f"✅ Initialized {self.name}")
            except Exception as e:
                self.logger.error(f"Failed to initialize Gemini: {e}")
                raise
        else:
            raise ValueError("GEMINI_API_KEY not found")
    
    def label_image(self, image: Image.Image, metadata: Dict) -> Dict:
        """Label image using standard Gemini Vision API"""
        prompt = """Analyze this image for fog conditions. 
        Provide your assessment in JSON format:
        {
            "fog_score": <0-100, where 0=perfectly clear, 100=dense fog>,
            "fog_level": "<Clear|Light Fog|Moderate Fog|Heavy Fog|Very Heavy Fog>",
            "confidence": <0.0-1.0>,
            "reasoning": "<brief explanation of visual indicators>",
            "visibility_estimate": "<estimated visibility in meters>",
            "weather_conditions": ["list", "of", "observed", "conditions"]
        }"""
        
        try:
            response = self.gemini_model.generate_content([prompt, image])
            
            json_str = response.text
            # Extract JSON if wrapped in markdown
            json_match = re.search(r'```json\s*(.*?)\s*```', json_str, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            
            data = json.loads(json_str)
            
            return self._create_success_result(
                fog_score=float(data.get("fog_score", 0)),
                fog_level=data.get("fog_level", "Unknown"),
                confidence=float(data.get("confidence", 0)),
                reasoning=data.get("reasoning", ""),
                visibility_estimate=data.get("visibility_estimate", "Unknown"),
                weather_conditions=data.get("weather_conditions", [])
            )
            
        except Exception as e:
            return self._create_error_result(e)

if __name__ == "__main__":
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description='Test Gemini labeler on an image')
    parser.add_argument('--image', required=True, help='Path to image file')
    parser.add_argument('--model', default='gemini-1.5-flash', help='Gemini model to use')
    args = parser.parse_args()
    
    # Test the labeler
    labeler = GeminiLabeler(model_name=args.model)
    image = Image.open(args.image).convert('RGB')
    
    result = labeler.label_image(image, {"webcam": {"name": "test"}})
    print(json.dumps(result, indent=2))