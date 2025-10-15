"""
Labeler registry with simple file-based configuration
"""

import logging
from typing import Dict, List, Optional, Any
import time

from .base import BaseLabeler
from . import create_labeler
from .config import get_enabled_labelers, get_labeler_config

logger = logging.getLogger(__name__)


class LabelerRegistry:
    """
    Registry for managing labelers with file-based configuration.
    
    Loads configuration from environment variables and provides
    simple access to enabled labelers.
    """
    
    def __init__(self):
        self.configs = []
        self._load_configs()
    
    def _load_configs(self):
        """Load labeler configurations from file-based config"""
        try:
            enabled_labelers = get_enabled_labelers()
            
            self.configs = []
            for labeler_name in enabled_labelers:
                labeler_config = get_labeler_config(labeler_name)
                config = {
                    'name': labeler_name,
                    'enabled': True,  # Only enabled labelers are returned
                    'version': labeler_config.get('version', '1.0'),
                    'config': {
                        'model_name': labeler_config.get('model_name'),
                    }
                }
                self.configs.append(config)
                
            logger.info(f"✅ Loaded {len(self.configs)} labeler configurations from environment")
            for cfg in self.configs:
                logger.info(f"   - {cfg['name']}: enabled={cfg['enabled']}")
                
        except Exception as e:
            logger.error(f"❌ Failed to load labeler configurations: {e}")
            logger.info("📝 Using empty configuration list")
            self.configs = []
    
    def get_all_enabled_labelers(self) -> List[Dict[str, Any]]:
        """Get all enabled labelers"""
        return [cfg for cfg in self.configs if cfg['enabled']]
    
    def create_labeler_instance(self, config: Dict[str, Any]) -> BaseLabeler:
        """Create a labeler instance from configuration"""
        labeler_name = config['name']
        labeler_config = config.get('config', {})
        
        # Map database config to labeler parameters
        mapped_config = self._map_config_for_labeler(labeler_name, labeler_config)
        
        # Use existing factory function for backwards compatibility
        return create_labeler(labeler_name, **mapped_config)
    
    def _map_config_for_labeler(self, labeler_name: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Map configuration to labeler-specific parameters"""
        mapped = {}
        
        # Handle parameter mapping for different labelers
        if labeler_name in ['gemini', 'gemini_masked']:
            # GeminiLabeler only accepts model_name and version
            if 'model_name' in config:
                mapped['model_name'] = config['model_name']
        else:
            # For unknown labelers, pass through all config
            mapped = config.copy()
        
        return mapped
    
    def wrap_labeler_with_metrics(self, labeler: BaseLabeler, config: Dict[str, Any]):
        """Wrap labeler to collect performance metrics"""
        original_label_image = labeler.label_image
        
        def label_image_with_metrics(image, metadata=None):
            start_time = time.time()
            
            try:
                # Call original labeling method
                result = original_label_image(image, metadata)
                
                # Calculate execution time
                execution_time_ms = int((time.time() - start_time) * 1000)
                
                # Add performance metadata to result
                if isinstance(result, dict) and result.get('status') == 'success':
                    result['_performance'] = {
                        'execution_time_ms': execution_time_ms,
                        'labeler_version': config['version']
                    }
                
                return result
                
            except Exception as e:
                # Still track timing even on failure
                execution_time_ms = int((time.time() - start_time) * 1000)
                logger.error(f"Labeler {config['name']} failed after {execution_time_ms}ms: {e}")
                raise
        
        # Replace the method
        labeler.label_image = label_image_with_metrics
        return labeler
    
    def get_ready_labelers(self) -> List[tuple]:
        """
        Get labelers ready for execution with their configurations.
            
        Returns:
            List of (labeler_instance, config) tuples
        """
        ready_labelers = []
        configs = self.get_all_enabled_labelers()
        
        for config in configs:
            try:
                # Create labeler instance
                labeler = self.create_labeler_instance(config)
                
                # Wrap with metrics collection
                labeler = self.wrap_labeler_with_metrics(labeler, config)
                
                ready_labelers.append((labeler, config))
                logger.info(f"✅ Prepared {config['name']} labeler")
                
            except Exception as e:
                logger.error(f"❌ Failed to create {config['name']} labeler: {e}")
                continue
        
        return ready_labelers


def get_registry() -> Optional[LabelerRegistry]:
    """
    Get labeler registry instance with safe fallback.
    
    Returns None if registry cannot be created, allowing calling code
    to fall back to direct labeler creation.
    """
    try:
        return LabelerRegistry()
    except Exception as e:
        logger.warning(f"Failed to create labeler registry: {e}")
        return None