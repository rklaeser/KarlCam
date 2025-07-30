import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from collect_fogcam_images import FogCamCollector
from packages.classify_images.ClassifyFogCLIP import ClassifyFogCLIP
from datetime import datetime
import pytz
import json

def test_webcam_config():
    """Test loading webcam configuration"""
    print("Testing webcam configuration...")
    print("=" * 50)
    
    try:
        # Test ClassifyFogCLIP webcam loading
        classifier = ClassifyFogCLIP()
        print(f"✓ Loaded {len(classifier.webcams)} webcams:")
        for webcam in classifier.webcams:
            print(f"  - {webcam['name']} ({webcam['id']}): {webcam['url']}")
        
        return classifier.webcams
    except Exception as e:
        print(f"✗ Error loading webcams: {e}")
        return None

def test_image_collection(webcams):
    """Test image collection from all webcams"""
    print("\nTesting image collection...")
    print("=" * 50)
    
    # Create collector instance
    collector = FogCamCollector()
    
    # Show current status
    collector.status()
    
    # Check current time
    sf_tz = pytz.timezone('America/Los_Angeles')
    sf_time = datetime.now(sf_tz)
    print(f"\nCurrent San Francisco time: {sf_time.strftime('%Y-%m-%d %H:%M:%S PST')}")
    print(f"Daylight hours: {collector.start_hour}:00-{collector.end_hour}:00 PST")
    print(f"Within daylight hours: {collector.is_daylight_hours()}")
    
    if not webcams:
        print("No webcams to test")
        return
    
    # Test each webcam
    results = {}
    for webcam in webcams:
        print(f"\nTesting {webcam['name']}...")
        try:
            # Update collector URL for this webcam
            collector.image_url = webcam['url']
            
            # Try to collect an image
            success = collector.collect_single_image()
            results[webcam['id']] = success
            
            if success:
                print(f"✓ Successfully collected image from {webcam['name']}")
            else:
                print(f"✗ Failed to collect image from {webcam['name']}")
                
        except Exception as e:
            print(f"✗ Error testing {webcam['name']}: {e}")
            results[webcam['id']] = False
    
    return results

def test_clip_analysis(webcams, results):
    """Test CLIP analysis on collected images"""
    print("\nTesting CLIP analysis...")
    print("=" * 50)
    
    try:
        classifier = ClassifyFogCLIP()
        
        # Find most recent image
        import glob
        image_pattern = os.path.join("data", "images", "*.jpg")
        images = glob.glob(image_pattern)
        
        if not images:
            print("No images found for analysis")
            return
        
        # Get most recent image
        latest_image = max(images, key=os.path.getctime)
        print(f"Analyzing latest image: {os.path.basename(latest_image)}")
        
        # Load and analyze image
        image = classifier.load_image(latest_image)
        clip_analysis = classifier.analyze_with_clip(image)
        weather_analysis = classifier.analyze_with_weather_context(image)
        
        print(f"✓ CLIP Analysis Results:")
        print(f"  Fog Score: {clip_analysis['fog_score']}")
        print(f"  Fog Level: {clip_analysis['fog_level']}")
        print(f"  Confidence: {clip_analysis['confidence']}")
        print(f"  Weather Detected: {weather_analysis['fog_detected']}")
        print(f"  Weather Confidence: {weather_analysis['confidence']}")
        
    except Exception as e:
        print(f"✗ Error in CLIP analysis: {e}")

def main():
    """Run all tests"""
    print("FogCam Multi-Webcam Collector Test")
    print("=" * 50)
    
    # Test 1: Webcam configuration
    webcams = test_webcam_config()
    
    # Test 2: Image collection
    if webcams:
        results = test_image_collection(webcams)
        
        # Test 3: CLIP analysis
        test_clip_analysis(webcams, results)
        
        # Summary
        print("\nTest Summary:")
        print("=" * 50)
        successful_webcams = [w['name'] for w, success in zip(webcams, results.values()) if success]
        if successful_webcams:
            print(f"✓ Successfully tested: {', '.join(successful_webcams)}")
        else:
            print("✗ No webcams were successfully tested")
    
    # Show when next collection would be
    collector = FogCamCollector()
    next_time = collector.calculate_next_collection_time()
    print(f"\nNext scheduled collection would be: {next_time.strftime('%Y-%m-%d %H:%M PST')}")

if __name__ == "__main__":
    main()