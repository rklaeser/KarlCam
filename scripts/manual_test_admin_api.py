#!/usr/bin/env python3
"""
Test script for admin API labeler management endpoints
"""

import requests
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Admin API base URL (adjust if running on different port)
BASE_URL = "http://localhost:8001"

def test_get_all_labelers():
    """Test getting all labeler configurations"""
    logger.info("=== Testing GET /api/labelers ===")
    
    try:
        response = requests.get(f"{BASE_URL}/api/labelers")
        
        if response.status_code == 200:
            labelers = response.json()
            logger.info(f"✅ Retrieved {len(labelers)} labelers")
            for labeler in labelers:
                logger.info(f"  - {labeler['name']}: {labeler['mode']}, enabled={labeler['enabled']}")
            return True
        else:
            logger.error(f"❌ Request failed: {response.status_code} - {response.text}")
            return False
            
    except requests.RequestException as e:
        logger.error(f"❌ Connection error: {e}")
        return False

def test_get_labelers_by_mode():
    """Test getting labelers by mode"""
    logger.info("=== Testing GET /api/labelers/by-mode/production ===")
    
    try:
        response = requests.get(f"{BASE_URL}/api/labelers/by-mode/production")
        
        if response.status_code == 200:
            labelers = response.json()
            logger.info(f"✅ Retrieved {len(labelers)} production labelers")
            for labeler in labelers:
                logger.info(f"  - {labeler['name']}")
            return True
        else:
            logger.error(f"❌ Request failed: {response.status_code} - {response.text}")
            return False
            
    except requests.RequestException as e:
        logger.error(f"❌ Connection error: {e}")
        return False

def test_get_performance_summary():
    """Test getting performance summary"""
    logger.info("=== Testing GET /api/labelers/performance/summary ===")
    
    try:
        response = requests.get(f"{BASE_URL}/api/labelers/performance/summary")
        
        if response.status_code == 200:
            performance_data = response.json()
            logger.info(f"✅ Retrieved performance data for {len(performance_data)} labelers")
            for perf in performance_data:
                logger.info(f"  - {perf['labeler_name']}: {perf['total_executions']} executions, "
                           f"avg time: {perf['avg_execution_time_ms']}ms")
            return True
        else:
            logger.error(f"❌ Request failed: {response.status_code} - {response.text}")
            return False
            
    except requests.RequestException as e:
        logger.error(f"❌ Connection error: {e}")
        return False

def test_update_labeler():
    """Test updating a labeler configuration (if gemini exists)"""
    logger.info("=== Testing PUT /api/labelers/gemini ===")
    
    try:
        # First, check if gemini exists
        response = requests.get(f"{BASE_URL}/api/labelers/gemini")
        if response.status_code != 200:
            logger.info("ℹ️ Gemini labeler not found, skipping update test")
            return True
        
        # Try to update the labeler (just change enabled status back and forth)
        original = response.json()
        new_enabled = not original['enabled']
        
        update_data = {
            "enabled": new_enabled
        }
        
        response = requests.put(f"{BASE_URL}/api/labelers/gemini", json=update_data)
        
        if response.status_code == 200:
            logger.info(f"✅ Successfully updated gemini labeler enabled={new_enabled}")
            
            # Restore original state
            restore_data = {"enabled": original['enabled']}
            requests.put(f"{BASE_URL}/api/labelers/gemini", json=restore_data)
            logger.info("✅ Restored original labeler state")
            return True
        else:
            logger.error(f"❌ Update failed: {response.status_code} - {response.text}")
            return False
            
    except requests.RequestException as e:
        logger.error(f"❌ Connection error: {e}")
        return False

def test_api_health():
    """Test basic API health"""
    logger.info("=== Testing API Health ===")
    
    try:
        response = requests.get(f"{BASE_URL}/api/health")
        
        if response.status_code == 200:
            logger.info("✅ Admin API is running and healthy")
            return True
        else:
            logger.error(f"❌ Health check failed: {response.status_code}")
            return False
            
    except requests.RequestException as e:
        logger.error(f"❌ Admin API not reachable: {e}")
        logger.info("ℹ️ Make sure admin backend is running: cd admin/backend && python main.py")
        return False

if __name__ == "__main__":
    logger.info("🧪 Testing Admin API Labeler Management Endpoints")
    
    tests = [
        test_api_health,
        test_get_all_labelers,
        test_get_labelers_by_mode,
        test_get_performance_summary,
        test_update_labeler,
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
        logger.info("🎉 All API tests passed!")
        logger.info("✨ Admin API endpoints are ready for dynamic labeler management!")
    else:
        logger.error("❌ Some API tests failed!")
        logger.info("💡 Try running the admin backend: cd admin/backend && python main.py")