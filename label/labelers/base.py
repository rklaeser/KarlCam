"""
Base class for all labeling techniques
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict
from PIL import Image
from datetime import datetime, timezone

class BaseLabeler(ABC):
    """Base class for all labeling techniques"""
    
    def __init__(self, name: str, version: str = "1.0"):
        self.name = name
        self.version = version
        self.logger = logging.getLogger(f"{__name__}.{name}")
    
    @abstractmethod
    def label_image(self, image: Image.Image, metadata: Dict) -> Dict:
        """
        Label an image and return results
        
        Args:
            image: PIL Image to label
            metadata: Image metadata including webcam info
            
        Returns:
            Dict with labeling results including:
            - labeler: unique key for this labeler
            - timestamp: when labeling occurred
            - fog_score: 0-100 fog intensity
            - fog_level: text description
            - confidence: 0.0-1.0 confidence score
            - reasoning: explanation of decision
            - status: "success" or "error"
        """
        pass
    
    def get_label_key(self) -> str:
        """Get unique key for this labeler's results"""
        return f"{self.name}_v{self.version}"
    
    def _create_error_result(self, error: Exception) -> Dict:
        """Create standardized error result"""
        self.logger.error(f"Labeling failed: {error}")
        return {
            "labeler": self.get_label_key(),
            "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            "status": "error",
            "error": str(error)
        }
    
    def _create_success_result(self, **data) -> Dict:
        """Create standardized success result"""
        return {
            "labeler": self.get_label_key(),
            "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            "status": "success",
            **data
        }