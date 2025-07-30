from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os
import sys
import glob
import json
from typing import List, Optional

# Add parent directory to path to import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from packages.data.data_organization import FogDataOrganizer
from packages.classify_images.ClassifyFogCLIP import ClassifyFogCLIP

app = FastAPI(title="FogCam Labeling API", version="1.0.0")

# CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize data organizer and CLIP classifier
organizer = FogDataOrganizer()
clip_classifier = None  # Lazy load to speed up startup

def get_clip_classifier():
    global clip_classifier
    if clip_classifier is None:
        clip_classifier = ClassifyFogCLIP()
    return clip_classifier

# Ensure images directory exists before mounting
import os
os.makedirs(organizer.raw_images_dir, exist_ok=True)

# Serve images
app.mount("/images", StaticFiles(directory=organizer.raw_images_dir), name="images")

# Pydantic models
class LabelRequest(BaseModel):
    filename: str
    label: str
    confidence: float = 1.0
    clip_prediction: Optional[str] = None
    clip_score: Optional[float] = None

class ImageInfo(BaseModel):
    filename: str
    labeled: bool
    url: str
    current_label: Optional[str] = None
    confidence: Optional[float] = None
    clip_prediction: Optional[str] = None
    clip_score: Optional[float] = None

@app.get("/")
async def root():
    return {"message": "FogCam Labeling API"}

@app.get("/api/images", response_model=List[ImageInfo])
async def get_images():
    """Get list of images to label"""
    # Get all images from raw images directory
    image_patterns = ['*.jpg', '*.jpeg', '*.png']
    all_images = []
    
    for pattern in image_patterns:
        all_images.extend(glob.glob(os.path.join(organizer.raw_images_dir, pattern)))
    
    # Sort by filename
    all_images.sort()
    
    # Get existing labels
    labeled_images = set(organizer.labels_data["labels"].keys())
    
    # Create response with images and their status
    images_data = []
    for img_path in all_images:
        filename = os.path.basename(img_path)
        
        image_info = ImageInfo(
            filename=filename,
            labeled=filename in labeled_images,
            url=f'/images/{filename}'
        )
        
        # Add existing label info if available
        if filename in labeled_images:
            label_info = organizer.labels_data["labels"][filename]
            image_info.current_label = label_info['label']
            image_info.confidence = label_info.get('confidence', 1.0)
            image_info.clip_prediction = label_info.get('clip_prediction')
            image_info.clip_score = label_info.get('clip_score')
        
        images_data.append(image_info)
    
    return images_data

@app.get("/api/predict/{filename}")
async def predict_image(filename: str):
    """Get CLIP prediction for an image"""
    try:
        image_path = os.path.join(organizer.raw_images_dir, filename)
        if not os.path.exists(image_path):
            raise HTTPException(status_code=404, detail="Image not found")
        
        # Get CLIP classifier (lazy load)
        classifier = get_clip_classifier()
        
        # Load image
        image = classifier.load_image(image_path)
        
        # Run CLIP analysis
        clip_analysis = classifier.analyze_with_clip(image)
        weather_analysis = classifier.analyze_with_weather_context(image)
        
        return {
            'clip_analysis': clip_analysis,
            'weather_analysis': weather_analysis,
            'suggested_label': 'fog' if clip_analysis['fog_score'] > 40 else 'clear'
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/label")
async def save_label(label_request: LabelRequest):
    """Save a label for an image"""
    if label_request.label not in ['fog', 'clear']:
        raise HTTPException(status_code=400, detail='Invalid label. Must be "fog" or "clear"')
    
    # Save label
    organizer.add_label(
        filename=label_request.filename,
        label=label_request.label,
        confidence=label_request.confidence,
        clip_prediction=label_request.clip_prediction,
        clip_score=label_request.clip_score
    )
    
    return {"success": True, "message": f"Label saved for {label_request.filename}"}

@app.get("/api/stats")
async def get_stats():
    """Get labeling statistics"""
    stats = organizer.get_label_statistics()
    return stats

@app.post("/api/export")
async def export_data():
    """Export labeled data and create organized dataset"""
    try:
        # Organize labeled images
        labeled_count = organizer.organize_labeled_images()
        
        # Create train/val/test splits if we have enough data
        splits_info = None
        if sum(labeled_count.values()) >= 10:  # Minimum 10 images
            splits_info = organizer.create_train_val_test_splits()
        
        return {
            'success': True,
            'labeled_count': labeled_count,
            'splits_info': splits_info,
            'message': 'Data exported successfully'
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Public API endpoints for the fog map
@app.get("/api/public/current")
async def get_current_conditions():
    """Get current fog conditions"""
    try:
        # Get CLIP classifier (lazy load)
        classifier = get_clip_classifier()
        
        # Download current image
        image = classifier.load_image()
        
        # Run analysis
        clip_analysis = classifier.analyze_with_clip(image)
        weather_analysis = classifier.analyze_with_weather_context(image)
        
        return {
            'timestamp': clip_analysis['timestamp'],
            'location': clip_analysis['location'],
            'fog_score': clip_analysis['fog_score'],
            'fog_level': clip_analysis['fog_level'],
            'confidence': clip_analysis['confidence'],
            'weather_detected': weather_analysis['fog_detected'],
            'weather_confidence': weather_analysis['confidence']
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/public/history")
async def get_fog_history(hours: int = 24):
    """Get fog history for the last N hours"""
    try:
        # Load collection log if it exists
        collection_log_path = os.path.join(organizer.base_dir, "collection_log.json")
        if not os.path.exists(collection_log_path):
            return {"history": [], "message": "No historical data available"}
        
        with open(collection_log_path, 'r') as f:
            log_data = json.load(f)
        
        # Get recent images from collection history
        recent_history = log_data.get('collection_history', [])[-hours:]
        
        # For each recent image, try to get its analysis
        history_with_analysis = []
        for entry in recent_history:
            filename = entry['filename']
            
            # Check if we have analysis for this image
            analysis_file = filename.replace('.jpg', '.json').replace('fogcam_', 'analysis_')
            analysis_path = os.path.join(organizer.base_dir, 'analysis', analysis_file)
            
            if os.path.exists(analysis_path):
                with open(analysis_path, 'r') as f:
                    analysis = json.load(f)
                    history_with_analysis.append({
                        'timestamp': entry['timestamp'],
                        'sf_time': entry['sf_time'],
                        'fog_score': analysis.get('fog_score', 0),
                        'fog_level': analysis.get('fog_level', 'Unknown')
                    })
        
        return {"history": history_with_analysis}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/public/webcams")
async def get_webcam_locations():
    """Get list of all webcam locations"""
    try:
        # Load webcam configuration from JSON file
        webcams_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'webcams.json')
        with open(webcams_file, 'r') as f:
            config = json.load(f)
            return {"webcams": config['webcams']}
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="Webcams configuration file not found")
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Invalid webcams configuration file")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)