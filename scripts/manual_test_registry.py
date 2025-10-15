#!/usr/bin/env python3
"""
Test script for labeler registry
"""

import sys
import logging
from pathlib import Path

# Add pipeline to path
sys.path.insert(0, str(Path(__file__).parent / "pipeline"))

from labelers.registry import LabelerRegistry, get_registry

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_registry_basic():
    """Test basic registry functionality"""
    logger.info("=== Testing Registry Basic Functionality ===")
    
    try:
        registry = LabelerRegistry()
        
        # Test configuration loading
        logger.info(f"Loaded {len(registry.configs)} configurations")
        
        # Test enabled labelers
        enabled = registry.get_all_enabled_labelers()
        logger.info(f"Enabled labelers: {[cfg['name'] for cfg in enabled]}")
        
        # Test ready labelers
        ready = registry.get_ready_labelers()
        logger.info(f"Ready labelers: {len(ready)}")
        
        for labeler, config in ready:
            logger.info(f"  - {config['name']}: {type(labeler).__name__}")
        
        logger.info("✅ Registry basic test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Registry basic test failed: {e}")
        return False

def test_safe_fallback():
    """Test safe fallback functionality"""
    logger.info("=== Testing Safe Fallback ===")
    
    registry = get_registry()
    if registry is None:
        logger.info("✅ Safe fallback works - registry returned None")
        return True
    else:
        logger.info(f"✅ Registry created successfully with {len(registry.configs)} configs")
        return True

def test_backwards_compatibility():
    """Test that existing labeler creation still works"""
    logger.info("=== Testing Backwards Compatibility ===")
    
    try:
        from labelers import create_labeler
        
        # Test existing factory function
        labeler = create_labeler("gemini")
        logger.info(f"✅ Direct labeler creation works: {type(labeler).__name__}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Backwards compatibility test failed: {e}")
        return False

if __name__ == "__main__":
    logger.info("🧪 Testing Labeler Registry")
    
    tests = [
        test_backwards_compatibility,
        test_safe_fallback,
        test_registry_basic,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            logger.error(f"Test {test.__name__} crashed: {e}")
            results.append(False)
    
    passed = sum(results)
    total = len(results)
    
    logger.info(f"🎯 Test Results: {passed}/{total} passed")
    
    if passed == total:
        logger.info("🎉 All tests passed!")
        sys.exit(0)
    else:
        logger.error("❌ Some tests failed!")
        sys.exit(1)