#!/usr/bin/env python3
"""
Heuristic fog scoring based on image analysis
Used until MobileNet model is trained
"""

import numpy as np
from PIL import Image, ImageStat
import cv2
from typing import Dict, Tuple
import logging

logger = logging.getLogger(__name__)

class HeuristicFogScorer:
    """
    Analyzes fog in images using computer vision heuristics.
    
    Fog characteristics:
    - Low contrast (uniform gray appearance)
    - Reduced color saturation
    - Fewer visible edges/details
    - Higher brightness in dark scenes (fog reflects light)
    - Uniform brightness distribution
    """
    
    def __init__(self):
        self.methods_weights = {
            'contrast': 0.3,      # Most reliable indicator
            'edges': 0.25,        # Fog obscures edges
            'saturation': 0.2,    # Fog reduces colors
            'brightness_std': 0.15,  # Fog creates uniform brightness
            'laplacian': 0.1      # Fog reduces high-frequency details
        }
    
    def score_image(self, image: Image.Image) -> Dict:
        """
        Score fog level using multiple heuristics
        Returns fog_score (0-100), fog_level, and confidence
        """
        # Convert PIL to numpy array
        img_array = np.array(image)
        
        # Calculate individual metrics
        metrics = {
            'contrast': self._calculate_contrast(image),
            'edges': self._calculate_edge_density(img_array),
            'saturation': self._calculate_saturation(image),
            'brightness_std': self._calculate_brightness_uniformity(image),
            'laplacian': self._calculate_laplacian_variance(img_array)
        }
        
        # Normalize each metric to 0-1 (where 1 = maximum fog)
        fog_indicators = {
            'contrast': 1.0 - min(metrics['contrast'] / 100, 1.0),  # Low contrast = fog
            'edges': 1.0 - metrics['edges'],  # Fewer edges = fog
            'saturation': 1.0 - metrics['saturation'],  # Low saturation = fog
            'brightness_std': 1.0 - min(metrics['brightness_std'] / 50, 1.0),  # Uniform = fog
            'laplacian': 1.0 - min(metrics['laplacian'] / 1000, 1.0)  # Low variance = fog
        }
        
        # Weighted combination
        fog_score = sum(
            fog_indicators[method] * weight 
            for method, weight in self.methods_weights.items()
        ) * 100
        
        # Ensure score is in valid range
        fog_score = max(0, min(100, fog_score))
        
        # Calculate confidence based on metric agreement
        metric_values = list(fog_indicators.values())
        confidence = 1.0 - np.std(metric_values)  # High agreement = high confidence
        confidence = max(0.5, min(0.95, confidence))  # Clamp to reasonable range
        
        # Determine fog level
        if fog_score < 20:
            fog_level = "Clear"
        elif fog_score < 40:
            fog_level = "Light Fog"
        elif fog_score < 60:
            fog_level = "Moderate Fog"
        elif fog_score < 80:
            fog_level = "Heavy Fog"
        else:
            fog_level = "Very Heavy Fog"
        
        # Log metrics for debugging
        logger.debug(f"Fog metrics: {metrics}")
        logger.debug(f"Fog indicators: {fog_indicators}")
        
        return {
            'fog_score': round(fog_score, 1),
            'fog_level': fog_level,
            'confidence': round(confidence, 2),
            'method': 'heuristic',
            'metrics': metrics  # Include raw metrics for analysis
        }
    
    def _calculate_contrast(self, image: Image.Image) -> float:
        """
        Calculate RMS contrast (standard deviation of pixel intensities)
        Lower contrast indicates fog
        """
        gray = image.convert('L')
        stat = ImageStat.Stat(gray)
        return stat.stddev[0]
    
    def _calculate_edge_density(self, img_array: np.ndarray) -> float:
        """
        Calculate proportion of image with strong edges
        Fog reduces edge visibility
        """
        # Convert to grayscale if needed
        if len(img_array.shape) == 3:
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        else:
            gray = img_array
        
        # Apply Canny edge detection
        edges = cv2.Canny(gray, 50, 150)
        
        # Calculate edge density
        edge_density = np.sum(edges > 0) / edges.size
        return edge_density
    
    def _calculate_saturation(self, image: Image.Image) -> float:
        """
        Calculate color saturation (0-1)
        Fog reduces color vibrancy
        """
        # Convert to HSV
        hsv = image.convert('RGB').convert('HSV')
        hsv_array = np.array(hsv)
        
        # Get saturation channel (S in HSV)
        saturation = hsv_array[:, :, 1]
        
        # Return normalized mean saturation
        return np.mean(saturation) / 255
    
    def _calculate_brightness_uniformity(self, image: Image.Image) -> float:
        """
        Calculate standard deviation of brightness
        Fog creates more uniform brightness
        """
        gray = image.convert('L')
        pixels = np.array(gray)
        return np.std(pixels)
    
    def _calculate_laplacian_variance(self, img_array: np.ndarray) -> float:
        """
        Calculate variance of Laplacian (measures image sharpness)
        Lower variance indicates fog/blur
        """
        if len(img_array.shape) == 3:
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        else:
            gray = img_array
        
        # Calculate Laplacian
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        return laplacian.var()
    
    def get_fog_color(self, fog_score: float) -> str:
        """Get color code for visualization"""
        if fog_score < 20:
            return '#28a745'  # Green - Clear
        elif fog_score < 40:
            return '#ffc107'  # Yellow - Light fog
        elif fog_score < 60:
            return '#fd7e14'  # Orange - Moderate fog
        elif fog_score < 80:
            return '#dc3545'  # Red - Heavy fog
        else:
            return '#6f42c1'  # Purple - Very heavy fog

# Example usage
if __name__ == "__main__":
    # Test with a sample image
    scorer = HeuristicFogScorer()
    
    # Create test images
    # Clear day simulation (high contrast)
    clear_img = Image.new('RGB', (100, 100))
    pixels = clear_img.load()
    for i in range(100):
        for j in range(100):
            # High contrast pattern
            val = 255 if (i + j) % 20 < 10 else 0
            pixels[i, j] = (val, val, val)
    
    # Foggy day simulation (low contrast, gray)
    foggy_img = Image.new('RGB', (100, 100))
    pixels = foggy_img.load()
    for i in range(100):
        for j in range(100):
            # Low contrast, gray pattern
            val = 128 + (i + j) % 20
            pixels[i, j] = (val, val, val)
    
    print("Clear image score:", scorer.score_image(clear_img))
    print("Foggy image score:", scorer.score_image(foggy_img))