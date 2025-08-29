#!/usr/bin/env python3
"""
Collect webcam images and score with Gemini Vision API
All images saved for review interface
"""

import os
import json
import requests
from datetime import datetime, timezone
from typing import Dict, List, Optional
from PIL import Image
from io import BytesIO
import logging
import sys
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load .env file if it exists
def load_env_file():
    """Load environment variables from .env file in the collect folder"""
    env_path = Path(__file__).parent / '.env'
    if env_path.exists():
        logger.info(f"📄 Loading environment from {env_path}")
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    # Only set if not already in environment (env vars take precedence)
                    if key not in os.environ:
                        os.environ[key] = value.strip('"\'')
    else:
        logger.info("📄 No .env file found, using environment variables")

# Load .env before other imports
load_env_file()

# No longer need heuristic scorer

# Import database utilities
try:
    from collect.database import DatabaseManager
except ImportError:
    from database import DatabaseManager

# Configuration
USE_CLOUD_STORAGE = os.getenv("USE_CLOUD_STORAGE", "true").lower() == "true"
BUCKET_NAME = os.getenv("OUTPUT_BUCKET", "karlcam-fog-data")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")

class GeminiFogScorer:
    """Score images using only Gemini Vision API"""
    
    def __init__(self):
        self.gemini_model = None
        
        # Setup Gemini if API key available
        if GEMINI_API_KEY:
            try:
                import google.generativeai as genai
                genai.configure(api_key=GEMINI_API_KEY)
                self.gemini_model = genai.GenerativeModel('gemini-1.5-flash')
                logger.info("✅ Gemini API initialized")
            except Exception as e:
                logger.warning(f"Could not initialize Gemini: {e}")
                raise RuntimeError("Gemini API is required but failed to initialize")
    
    def score_image(self, image: Image.Image, image_path: str) -> Dict:
        """Score image with Gemini Vision API"""
        
        result = {
            "image_path": image_path,
            "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
        }
        
        # Score with Gemini
        try:
            gemini_result = self.score_with_gemini(image)
            result.update(gemini_result)  # Flatten structure - no more nested "methods"
        except Exception as e:
            logger.error(f"Gemini scoring failed: {e}")
            result.update({
                "fog_score": 0,
                "fog_level": "Error",
                "confidence": 0.0,
                "status": "error",
                "error": str(e)
            })
        
        return result
    
    def score_with_gemini(self, image: Image.Image) -> Dict:
        """Score using Gemini Vision API"""
        prompt = """Analyze this image for fog conditions. 
        Provide your assessment in JSON format:
        {
            "fog_score": <0-100, where 0=perfectly clear, 100=dense fog>,
            "fog_level": "<Clear|Light Fog|Moderate Fog|Heavy Fog|Very Heavy Fog>",
            "confidence": <0.0-1.0>,
            "reasoning": "<brief explanation of visual indicators>",
            "visibility_estimate": "<estimated visibility in meters>",
            "weather_conditions": ["list", "of", "observed", "conditions"]
        }"""
        
        try:
            response = self.gemini_model.generate_content([prompt, image])
            
            # Parse JSON response
            import re
            json_str = response.text
            # Extract JSON if wrapped in markdown
            json_match = re.search(r'```json\s*(.*?)\s*```', json_str, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            
            data = json.loads(json_str)
            
            return {
                "fog_score": float(data.get("fog_score", 0)),
                "fog_level": data.get("fog_level", "Unknown"),
                "confidence": float(data.get("confidence", 0)),
                "reasoning": data.get("reasoning", ""),
                "visibility_estimate": data.get("visibility_estimate", "Unknown"),
                "weather_conditions": data.get("weather_conditions", []),
                "status": "success"
            }
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            raise
    
    def get_agreement_level(self, difference: float) -> str:
        """Categorize agreement between methods"""
        if difference < 10:
            return "strong_agreement"
        elif difference < 20:
            return "moderate_agreement"
        elif difference < 30:
            return "weak_agreement"
        else:
            return "disagreement"
    
    def calculate_consensus_confidence(self, h_conf: float, g_conf: float, difference: float) -> float:
        """Calculate confidence in consensus score"""
        # Average confidence weighted by agreement
        base_confidence = (h_conf + g_conf) / 2
        
        # Reduce confidence based on disagreement
        agreement_factor = max(0.5, 1.0 - (difference / 100))
        
        return round(base_confidence * agreement_factor, 2)

def save_to_cloud_storage(data: dict, filename: str) -> bool:
    """Save data to Cloud Storage"""
    if not USE_CLOUD_STORAGE:
        return False
        
    try:
        from google.cloud import storage
        client = storage.Client()
        bucket = client.bucket(BUCKET_NAME)
        blob = bucket.blob(filename)
        
        blob.upload_from_string(
            json.dumps(data, indent=2),
            content_type='application/json'
        )
        
        logger.info(f"✅ Saved {filename} to gs://{BUCKET_NAME}/{filename}")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to save to Cloud Storage: {e}")
        return False

def save_image_to_cloud_storage(image: Image.Image, filename: str) -> bool:
    """Save image to Cloud Storage"""
    if not USE_CLOUD_STORAGE:
        return False
        
    try:
        from google.cloud import storage
        client = storage.Client()
        bucket = client.bucket(BUCKET_NAME)
        blob = bucket.blob(f"images/{filename}")
        
        # Convert PIL image to bytes
        img_byte_arr = BytesIO()
        image.save(img_byte_arr, format='JPEG', quality=85)
        img_byte_arr.seek(0)
        
        blob.upload_from_file(img_byte_arr, content_type='image/jpeg')
        logger.info(f"✅ Saved image to gs://{BUCKET_NAME}/images/{filename}")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to save image to Cloud Storage: {e}")
        return False

def collect_and_label_with_gemini():
    """Main collection function with Gemini scoring using Cloud SQL"""
    logger.info("Starting Gemini fog data collection...")
    
    # Check if we're in local testing mode
    local_testing = os.getenv("LOCAL_TESTING", "false").lower() == "true"
    
    if local_testing:
        logger.info(f"💾 Local testing mode - saving to: {os.getenv('OUTPUT_DIR', './output')}")
        logger.info("🗄️ Database disabled for testing")
        db = None
        # Load webcams from webcams.json for testing
        webcams_file = Path("data/webcams.json")
        if webcams_file.exists():
            with open(webcams_file, 'r') as f:
                webcams_data = json.load(f)
                webcam_urls = [w for w in webcams_data.get("webcams", []) if w.get("active", True)]
            logger.info(f"📷 Loaded {len(webcam_urls)} webcams from {webcams_file}")
        else:
            logger.error(f"❌ Could not find {webcams_file} for local testing")
            raise RuntimeError("webcams.json not found")
    else:
        logger.info(f"💾 Using Cloud Storage: gs://{BUCKET_NAME}")
        logger.info(f"🗄️ Using Cloud SQL database")
        db = DatabaseManager()
        # Load webcams from database
        try:
            webcam_urls = db.get_active_webcams()
        except Exception as e:
            logger.error(f"❌ Failed to load webcams from database: {e}")
            logger.info("💡 Trying to load from webcams.json as fallback...")
            
            # Fallback to JSON file
            webcams_file = Path("data/webcams.json")
            if webcams_file.exists():
                with open(webcams_file, 'r') as f:
                    webcams_data = json.load(f)
                    webcam_urls = [w for w in webcams_data.get("webcams", []) if w.get("active", True)]
                logger.info(f"🎥 Loaded {len(webcam_urls)} webcams from {webcams_file}")
            else:
                logger.error("❌ No webcams configured and database unavailable!")
                raise RuntimeError("Unable to load webcam data")
    
    if not webcam_urls:
        logger.error("❌ No active webcams found!")
        raise RuntimeError("No active webcams configured")
    
    # Initialize the scorer
    scorer = GeminiFogScorer()
    
    # Log active webcams
    logger.info(f"🎥 Active webcams: {', '.join([w['name'] for w in webcam_urls])}")
    
    # Create collection run in database (if not local testing)
    collection_run_id = None
    if db:
        collection_run_id = db.create_collection_run(total_images=len(webcam_urls))
    collection_results = []
    
    for webcam in webcam_urls:
        try:
            # Fetch image
            response = requests.get(webcam["url"], timeout=10)
            image = Image.open(BytesIO(response.content)).convert('RGB')
            
            # Generate filename
            timestamp = datetime.now(timezone.utc)
            image_filename = f"{webcam['id']}_{timestamp.strftime('%Y%m%d_%H%M%S')}.jpg"
            
            # Score with Gemini
            scoring_result = scorer.score_image(image, image_filename)
            scoring_result["webcam"] = webcam
            
            # Save image
            if local_testing:
                # Save to local directory
                output_dir = Path(os.getenv('OUTPUT_DIR', './output'))
                output_dir.mkdir(parents=True, exist_ok=True)
                image_path = output_dir / image_filename
                image.save(image_path)
                
                # Save scoring results as JSON
                json_path = output_dir / f"{image_filename}.json"
                with open(json_path, 'w') as f:
                    json.dump(scoring_result, f, indent=2, default=str)
                
                logger.info(f"💾 Saved locally: {image_path}")
            else:
                # Save to Cloud Storage (main location)
                save_image_to_cloud_storage(image, image_filename)
                
                # Save to review directory for all images (no more flagging logic)
                save_image_to_cloud_storage(image, f"review/pending/{image_filename}")
                
                # Save JSON metadata for review backend
                save_to_cloud_storage(scoring_result, f"review/metadata/{image_filename}.json")
            
            # Save to database (if not local testing)
            if db:
                db.save_collection_result(collection_run_id, scoring_result)
            
            collection_results.append(scoring_result)
            
            # Log result
            g_score = scoring_result.get("fog_score", "N/A")
            confidence = scoring_result.get("confidence", 0)
            
            logger.info(f"✅ {webcam['name']}: Score={g_score}, Confidence={confidence:.2f}")
            
        except Exception as e:
            logger.error(f"Failed to process {webcam['name']}: {e}")
    
    # Update collection run with final summary
    successful_results = [r for r in collection_results if r.get("status") != "error"]
    summary = {
        "collection_time": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
        "total_images": len(successful_results),
        "webcams_processed": [w['name'] for w in webcam_urls],
        "collection_run_id": collection_run_id
    }
    
    # Update database with summary (if not local testing)
    if db:
        db.update_collection_run_summary(collection_run_id, summary)
    
    logger.info(f"""
    ========================================
    Collection Complete:
    - Collection Run ID: {collection_run_id}
    - Images collected: {summary['total_images']}
    - Images processed: {len(successful_results)}
    - Storage: Cloud SQL + Cloud Storage
    ========================================
    """)

if __name__ == "__main__":
    collect_and_label_with_gemini()