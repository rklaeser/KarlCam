"""
Flexible labeling system supporting multiple techniques
"""

from .base import BaseLabeler
from .gemini import GeminiLabeler
from .gemini_masked import GeminiMaskedLabeler

# Factory function to create labelers
def create_labeler(labeler_type: str, **kwargs) -> BaseLabeler:
    """Create a labeler instance by type"""
    labelers = {
        "gemini": GeminiLabeler,
        "gemini_masked": GeminiMaskedLabeler,
    }
    
    if labeler_type not in labelers:
        raise ValueError(f"Unknown labeler type: {labeler_type}. Available: {list(labelers.keys())}")
    
    return labelers[labeler_type](**kwargs)

__all__ = ["BaseLabeler", "GeminiLabeler", "GeminiMaskedLabeler", "create_labeler"]