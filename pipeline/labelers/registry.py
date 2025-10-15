"""
Labeler registry with dynamic configuration and mode management
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import time
import sys
from pathlib import Path

# Add parent directory to path for database imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from db.manager import DatabaseManager
from db.connection import execute_query
from .base import BaseLabeler
from . import create_labeler
from .config import get_model_name

logger = logging.getLogger(__name__)


class LabelerRegistry:
    """
    Registry for managing labelers with dynamic configuration and mode support.
    
    Loads configuration from database once at startup and provides filtered
    access to labelers based on mode (production, shadow, experimental).
    """
    
    def __init__(self):
        self.configs = []
        self._db = None
        self._load_configs()
    
    def _load_configs(self):
        """Load labeler configurations from database"""
        try:
            self._db = DatabaseManager()
            
            # Query labeler configurations using KarlCam's database pattern
            query = """
                SELECT name, mode, enabled, version, config
                FROM labeler_config
                ORDER BY name
            """
            
            rows = execute_query(query)
                    
            # Convert to dict format
            self.configs = []
            for row in rows:
                config = {
                    'name': row[0],
                    'mode': row[1], 
                    'enabled': row[2],
                    'version': row[3],
                    'config': row[4] or {}
                }
                self.configs.append(config)
                
            logger.info(f"✅ Loaded {len(self.configs)} labeler configurations from database")
            for cfg in self.configs:
                logger.info(f"   - {cfg['name']}: mode={cfg['mode']}, enabled={cfg['enabled']}")
                
        except Exception as e:
            logger.error(f"❌ Failed to load labeler configurations: {e}")
            logger.info("📝 Using empty configuration list")
            self.configs = []
    
    def get_labelers_by_mode(self, mode: str) -> List[Dict[str, Any]]:
        """Get enabled labelers filtered by mode"""
        return [
            cfg for cfg in self.configs 
            if cfg['enabled'] and cfg['mode'] == mode
        ]
    
    def get_production_labelers(self) -> List[Dict[str, Any]]:
        """Get enabled production labelers"""
        return self.get_labelers_by_mode('production')
    
    def get_shadow_labelers(self) -> List[Dict[str, Any]]:
        """Get enabled shadow labelers"""
        return self.get_labelers_by_mode('shadow')
    
    def get_experimental_labelers(self) -> List[Dict[str, Any]]:
        """Get enabled experimental labelers"""
        return self.get_labelers_by_mode('experimental')
    
    def get_all_enabled_labelers(self) -> List[Dict[str, Any]]:
        """Get all enabled labelers regardless of mode"""
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
        """Map database configuration to labeler-specific parameters"""
        mapped = {}
        
        # Handle parameter mapping for different labelers
        if labeler_name == 'gemini':
            # GeminiLabeler only accepts model_name and version
            if 'model' in config:
                # Use centralized config to resolve model name
                mapped['model_name'] = get_model_name(config['model'])
            # Filter out unsupported parameters like 'temperature'
            
        elif labeler_name == 'gemini_masked':
            # GeminiMaskedLabeler - check what parameters it accepts
            if 'model' in config:
                # Use centralized config to resolve model name
                mapped['model_name'] = get_model_name(config['model'])
            # TODO: Add other supported parameters as needed
        
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
                        'labeler_mode': config['mode'],
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
    
    def get_ready_labelers(self, modes: Optional[List[str]] = None) -> List[tuple]:
        """
        Get labelers ready for execution with their configurations.
        
        Args:
            modes: List of modes to include (default: ['production'])
            
        Returns:
            List of (labeler_instance, config) tuples
        """
        if modes is None:
            modes = ['production']
        
        ready_labelers = []
        
        for mode in modes:
            configs = self.get_labelers_by_mode(mode)
            
            for config in configs:
                try:
                    # Create labeler instance
                    labeler = self.create_labeler_instance(config)
                    
                    # Wrap with metrics collection
                    labeler = self.wrap_labeler_with_metrics(labeler, config)
                    
                    ready_labelers.append((labeler, config))
                    logger.info(f"✅ Prepared {config['name']} labeler (mode: {config['mode']})")
                    
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