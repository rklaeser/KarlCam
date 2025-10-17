#!/usr/bin/env python3
"""
Test script for the on-demand image collection and labeling system
"""

import os
import sys
import asyncio
import logging
from datetime import datetime
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_on_demand():
    """Test the on-demand service directly"""
    try:
        # Load environment variables
        from dotenv import load_dotenv
        load_dotenv()
        
        # Get Gemini API key if not set
        if not os.getenv("GEMINI_API_KEY"):
            import subprocess
            result = subprocess.run(
                ["gcloud", "secrets", "versions", "access", "latest", 
                 "--secret=gemini-api-key-staging", "--project=karlcam"],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                os.environ["GEMINI_API_KEY"] = result.stdout.strip()
                logger.info("Loaded GEMINI_API_KEY from Google Cloud secrets")
            else:
                logger.error("Failed to get GEMINI_API_KEY from secrets")
        
        # Import after loading env
        from db.manager import DatabaseManager
        from web.api.services.on_demand_service import OnDemandService
        
        # Initialize database manager
        logger.info(f"Connecting to database...")
        db_manager = DatabaseManager()
        
        # Get list of available webcams
        webcams = db_manager.get_active_webcams()
        logger.info(f"Found {len(webcams)} active webcams")
        
        if not webcams:
            logger.error("No active webcams found in database")
            return
        
        # Test with first webcam
        test_webcam = webcams[0]
        logger.info(f"\nTesting with webcam: {test_webcam.name} (ID: {test_webcam.id})")
        
        # Initialize on-demand service
        service = OnDemandService(db_manager)
        
        # Test 1: Initial fetch (should fetch fresh)
        logger.info("\n=== Test 1: Initial fetch (expecting fresh data) ===")
        start_time = datetime.now()
        result1 = service.get_latest_with_refresh(test_webcam.id)
        elapsed1 = (datetime.now() - start_time).total_seconds()
        
        if result1:
            logger.info(f"✅ Success! Fetched in {elapsed1:.2f} seconds")
            logger.info(f"  - Fog Score: {result1.get('fog_score')}")
            logger.info(f"  - Fog Level: {result1.get('fog_level')}")
            logger.info(f"  - Confidence: {result1.get('confidence')}")
            logger.info(f"  - Age: {result1.get('age_minutes'):.2f} minutes")
            logger.info(f"  - Image URL: {result1.get('image_url')}")
        else:
            logger.error("❌ Failed to fetch data")
            return
        
        # Test 2: Immediate second fetch (should use cache)
        logger.info("\n=== Test 2: Immediate second fetch (expecting cached data) ===")
        start_time = datetime.now()
        result2 = service.get_latest_with_refresh(test_webcam.id)
        elapsed2 = (datetime.now() - start_time).total_seconds()
        
        if result2:
            logger.info(f"✅ Success! Fetched in {elapsed2:.2f} seconds")
            logger.info(f"  - Age: {result2.get('age_minutes'):.2f} minutes")
            
            if elapsed2 < 1.0:
                logger.info("✅ Cache working correctly (fast response)")
            else:
                logger.warning("⚠️  Response slower than expected for cached data")
        
        # Test 3: Test with a different webcam
        if len(webcams) > 1:
            test_webcam2 = webcams[1]
            logger.info(f"\n=== Test 3: Different webcam: {test_webcam2.name} ===")
            start_time = datetime.now()
            result3 = service.get_latest_with_refresh(test_webcam2.id)
            elapsed3 = (datetime.now() - start_time).total_seconds()
            
            if result3:
                logger.info(f"✅ Success! Fetched in {elapsed3:.2f} seconds")
                logger.info(f"  - Fog Level: {result3.get('fog_level')}")
        
        logger.info("\n=== All tests completed successfully! ===")
        
    except Exception as e:
        logger.error(f"Test failed with error: {e}", exc_info=True)
        return 1
    
    return 0


async def test_api_endpoint():
    """Test the API endpoint using HTTP requests"""
    import requests
    
    logger.info("\n=== Testing API Endpoint ===")
    
    # Assuming API is running locally
    api_base = "http://localhost:8002"
    
    try:
        # Get list of cameras
        response = requests.get(f"{api_base}/api/public/cameras")
        if response.status_code != 200:
            logger.error(f"Failed to get cameras: {response.status_code}")
            return
        
        cameras = response.json().get('cameras', [])
        if not cameras:
            logger.error("No cameras returned from API")
            return
        
        # Test the on-demand endpoint with first camera
        camera_id = cameras[0]['id']
        logger.info(f"Testing on-demand endpoint for camera: {camera_id}")
        
        start_time = datetime.now()
        response = requests.get(f"{api_base}/api/public/cameras/{camera_id}/latest")
        elapsed = (datetime.now() - start_time).total_seconds()
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"✅ API test successful! Response in {elapsed:.2f} seconds")
            logger.info(f"  - Fog Score: {data.get('fog_score')}")
            logger.info(f"  - Fog Level: {data.get('fog_level')}")
            logger.info(f"  - Age: {data.get('age_minutes'):.2f} minutes")
        else:
            logger.error(f"API request failed: {response.status_code}")
            logger.error(response.text)
    
    except requests.exceptions.ConnectionError:
        logger.warning("API not running. Start with: make start-api")
    except Exception as e:
        logger.error(f"API test failed: {e}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test on-demand image collection and labeling")
    parser.add_argument("--api", action="store_true", help="Test via API endpoint instead of direct service")
    args = parser.parse_args()
    
    if args.api:
        exit_code = asyncio.run(test_api_endpoint())
    else:
        exit_code = asyncio.run(test_on_demand())
    
    sys.exit(exit_code or 0)