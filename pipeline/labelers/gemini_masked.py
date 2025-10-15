"""
Gemini Vision API labeler with sky masking for ground-level fog detection
"""

import os
import json
import re
from pathlib import Path
from PIL import Image
from typing import Dict
import numpy as np
from .base import BaseLabeler
from .config import DEFAULT_GEMINI_MODEL, get_model_name

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

class GeminiMaskedLabeler(BaseLabeler):
    """Gemini Vision API labeler with sky masking for better ground-level fog detection"""
    
    def __init__(self, model_name: str = None, version: str = "1.0"):
        # Use centralized config for model name
        if model_name is None:
            model_name = DEFAULT_GEMINI_MODEL
        else:
            # Resolve model name if it's a key
            model_name = get_model_name(model_name)
        
        super().__init__(f"gemini_masked_{model_name.replace('.', '_').replace('-', '_')}", version)
        self.model_name = model_name
        self.gemini_model = None
        
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=api_key)
                self.gemini_model = genai.GenerativeModel(model_name)
                self.logger.info(f"✅ Initialized {self.name} with sky masking")
            except Exception as e:
                self.logger.error(f"Failed to initialize Gemini: {e}")
                raise
        else:
            raise ValueError("GEMINI_API_KEY not found")
    
    def detect_and_mask_sky(self, image: Image.Image) -> Image.Image:
        """
        Detect sky region and mask it out to focus on ground-level fog
        """
        # Convert to numpy array
        img_array = np.array(image)
        
        # Simple sky detection based on position
        # Sky is usually in upper portion - create gradient mask
        height, width = img_array.shape[:2]
        
        # Create a gradient mask - darken upper portions progressively
        # More aggressive masking in top 30%, gradual transition to 70%
        gradient_mask = np.ones((height, width))
        
        # Top 30% gets heavily darkened
        top_30_pct = int(height * 0.3)
        gradient_mask[:top_30_pct] = 0.2
        
        # Next 40% gets gradual transition
        transition_end = int(height * 0.7)
        transition_zone = transition_end - top_30_pct
        for i in range(transition_zone):
            y = top_30_pct + i
            gradient_mask[y] = 0.2 + (i / transition_zone) * 0.8
        
        # Bottom 30% unchanged
        gradient_mask[transition_end:] = 1.0
        
        # Apply gradient to darken upper portions
        masked_img = img_array.copy()
        for channel in range(3):  # RGB channels
            masked_img[:,:,channel] = (masked_img[:,:,channel] * gradient_mask).astype(np.uint8)
        
        return Image.fromarray(masked_img)
    
    def label_image(self, image: Image.Image, metadata: Dict) -> Dict:
        """Label image using Gemini with sky masking and enhanced prompt"""
        
        try:
            # Apply sky masking to focus on ground-level conditions
            masked_image = self.detect_and_mask_sky(image)
            
            prompt = """Analyze this image for FOG conditions. 
            
            IMPORTANT: Focus on the FOREGROUND and GROUND-LEVEL visibility only. 
            - The upper portion of this image has been darkened to help you focus on ground conditions
            - Ignore any remaining sky or cloud elements
            - Look for reduced visibility of objects near the ground (buildings, trees, roads, etc.)
            - Fog is characterized by reduced visibility at ground level, NOT clouds in the sky
            - Pay attention to:
              * Haziness or obscuration of nearby objects
              * Reduced contrast in the foreground and middle distance
              * Objects fading into white/gray haze at short distances
              * Light sources creating halos or being diffused
              * Loss of detail in vegetation, buildings, or terrain features
            
            Provide your assessment in JSON format:
            {
                "fog_score": <0-100, where 0=perfectly clear ground visibility, 100=dense ground fog>,
                "fog_level": "<Clear|Light Fog|Moderate Fog|Heavy Fog|Very Heavy Fog>",
                "confidence": <0.0-1.0>,
                "reasoning": "<detailed explanation focusing on ground-level visibility indicators>",
                "visibility_estimate": "<estimated ground-level visibility in meters>",
                "weather_conditions": ["list", "of", "observed", "conditions"],
                "foreground_clarity": "<description of foreground visibility and contrast>",
                "masking_notes": "<any observations about how the sky masking affected the analysis>"
            }"""
            
            response = self.gemini_model.generate_content([prompt, masked_image])
            
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
                weather_conditions=data.get("weather_conditions", []),
                foreground_clarity=data.get("foreground_clarity", ""),
                masking_notes=data.get("masking_notes", ""),
                used_sky_masking=True
            )
            
        except Exception as e:
            return self._create_error_result(e)
    
    def save_masked_image(self, original_image: Image.Image, output_path: str):
        """Save the masked image for inspection (useful for testing)"""
        masked = self.detect_and_mask_sky(original_image)
        masked.save(output_path)
        self.logger.info(f"Saved masked image to {output_path}")

if __name__ == "__main__":
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description='Test Gemini masked labeler on an image')
    parser.add_argument('--image', required=True, help='Path to image file')
    parser.add_argument('--model', default=None, help='Gemini model to use (defaults to config default)')
    parser.add_argument('--save-masked', help='Save masked image to this path')
    args = parser.parse_args()
    
    # Test the labeler
    labeler = GeminiMaskedLabeler(model_name=args.model)
    image = Image.open(args.image).convert('RGB')
    
    # Save masked image if requested
    if args.save_masked:
        labeler.save_masked_image(image, args.save_masked)
        print(f"Masked image saved to {args.save_masked}")
    
    result = labeler.label_image(image, {"webcam": {"name": "test"}})
    print(json.dumps(result, indent=2))