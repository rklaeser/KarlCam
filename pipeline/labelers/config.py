"""
Centralized configuration for labelers
"""

# Model configurations
GEMINI_MODELS = {
    # The default Gemini model to use across the application
    "default": "gemini-1.5-flash-latest",
    
    # Available model variants
    "flash": "gemini-1.5-flash-latest",
    "flash_latest": "gemini-1.5-flash-latest",
    "flash_001": "gemini-1.5-flash-001",
    "flash_002": "gemini-1.5-flash-002",
    
    # Pro models (if needed in future)
    "pro": "gemini-1.5-pro-latest",
    "pro_latest": "gemini-1.5-pro-latest",
    "pro_001": "gemini-1.5-pro-001",
    "pro_002": "gemini-1.5-pro-002",
}

# Default model to use when not specified
DEFAULT_GEMINI_MODEL = GEMINI_MODELS["default"]

# Model parameters
MODEL_CONFIGS = {
    "gemini-1.5-flash-latest": {
        "temperature": 0.1,
        "max_output_tokens": 1024,
        "top_p": 0.95,
        "top_k": 40,
    },
    "gemini-1.5-pro-latest": {
        "temperature": 0.1,
        "max_output_tokens": 2048,
        "top_p": 0.95,
        "top_k": 40,
    },
}

def get_model_name(model_key: str = None) -> str:
    """
    Get the full model name for a given key or default.
    
    Args:
        model_key: Optional key to look up in GEMINI_MODELS
        
    Returns:
        Full model name string
    """
    if model_key is None:
        return DEFAULT_GEMINI_MODEL
    
    # If it's already a full model name, return it
    if model_key in MODEL_CONFIGS:
        return model_key
    
    # Look up in the model mapping
    return GEMINI_MODELS.get(model_key, DEFAULT_GEMINI_MODEL)

def get_model_config(model_name: str = None) -> dict:
    """
    Get the configuration parameters for a model.
    
    Args:
        model_name: Model name to get config for
        
    Returns:
        Dictionary of model configuration parameters
    """
    if model_name is None:
        model_name = DEFAULT_GEMINI_MODEL
    
    # Resolve model name if it's a key
    model_name = get_model_name(model_name)
    
    return MODEL_CONFIGS.get(model_name, MODEL_CONFIGS[DEFAULT_GEMINI_MODEL])