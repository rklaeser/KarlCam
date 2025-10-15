"""
Centralized configuration for labelers using environment variables
"""
import os

# Gemini model configuration from environment
DEFAULT_GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

# Model parameters from environment with defaults
MODEL_CONFIG = {
    "temperature": float(os.getenv("GEMINI_TEMPERATURE", "0.1")),
    "max_output_tokens": int(os.getenv("GEMINI_MAX_TOKENS", "1024")),
    "top_p": float(os.getenv("GEMINI_TOP_P", "0.95")),
    "top_k": int(os.getenv("GEMINI_TOP_K", "40")),
}

# Labeler configuration 
LABELER_CONFIG = {
    "gemini": {
        "enabled": os.getenv("GEMINI_LABELER_ENABLED", "true").lower() == "true",
        "model_name": DEFAULT_GEMINI_MODEL,
        "version": os.getenv("GEMINI_LABELER_VERSION", "1.0"),
    },
    "gemini_masked": {
        "enabled": os.getenv("GEMINI_MASKED_LABELER_ENABLED", "false").lower() == "true", 
        "model_name": DEFAULT_GEMINI_MODEL,
        "version": os.getenv("GEMINI_MASKED_LABELER_VERSION", "1.0"),
    }
}

def get_model_name(model_key: str = None) -> str:
    """
    Get the model name from environment configuration.
    
    Args:
        model_key: Ignored, kept for compatibility
        
    Returns:
        The configured Gemini model name
    """
    return DEFAULT_GEMINI_MODEL

def get_model_config(model_name: str = None) -> dict:
    """
    Get the model configuration parameters from environment.
    
    Args:
        model_name: Ignored, kept for compatibility
        
    Returns:
        Dictionary of model configuration parameters
    """
    return MODEL_CONFIG

def get_enabled_labelers() -> list[str]:
    """
    Get list of enabled labeler names from configuration.
    
    Returns:
        List of enabled labeler names
    """
    return [name for name, config in LABELER_CONFIG.items() if config["enabled"]]

def get_labeler_config(labeler_name: str) -> dict:
    """
    Get configuration for specific labeler.
    
    Args:
        labeler_name: Name of the labeler
        
    Returns:
        Dictionary of labeler configuration
    """
    return LABELER_CONFIG.get(labeler_name, {})