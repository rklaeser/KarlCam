import requests
import cv2
import numpy as np
from datetime import datetime, time
import time as time_module
from datetime import timedelta
import os
from PIL import Image
import io
import pytz
import json

class FogCamCollector:
    def __init__(self):
        self.image_url = "https://www.fogcam.org/fogcam2.jpg"
        self.data_dir = "data"
        self.images_dir = f"{self.data_dir}/images"
        self.collection_log = f"{self.data_dir}/collection_log.json"
        
        # San Francisco timezone
        self.sf_tz = pytz.timezone('America/Los_Angeles')
        
        # Daylight hours (6 AM to 8 PM PST)
        self.start_hour = 6
        self.end_hour = 20
        
        # Collection interval (1 hour = 3600 seconds)
        self.interval_seconds = 3600
        
        # Ensure directories exist
        os.makedirs(self.images_dir, exist_ok=True)
        
        # Load or create collection log
        self.load_collection_log()
        
    def load_collection_log(self):
        """Load existing collection log or create new one"""
        if os.path.exists(self.collection_log):
            with open(self.collection_log, 'r') as f:
                self.log = json.load(f)
        else:
            self.log = {
                "total_collected": 0,
                "collection_history": []
            }
    
    def save_collection_log(self):
        """Save collection log"""
        with open(self.collection_log, 'w') as f:
            json.dump(self.log, f, indent=2)
    
    def is_daylight_hours(self):
        """Check if current time is within daylight hours in San Francisco"""
        sf_time = datetime.now(self.sf_tz)
        current_hour = sf_time.hour
        
        return self.start_hour <= current_hour < self.end_hour
    
    def download_image(self):
        """Download the current webcam image"""
        try:
            response = requests.get(self.image_url, timeout=10)
            if response.status_code == 200:
                # Convert to numpy array for OpenCV
                image = Image.open(io.BytesIO(response.content))
                return cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            else:
                print(f"Failed to download image: Status {response.status_code}")
                return None
        except Exception as e:
            print(f"Error downloading image: {e}")
            return None
    
    def save_image(self, image):
        """Save image with timestamp"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"fogcam_{timestamp}.jpg"
        filepath = os.path.join(self.images_dir, filename)
        
        cv2.imwrite(filepath, image)
        
        # Update log
        self.log["total_collected"] += 1
        self.log["collection_history"].append({
            "filename": filename,
            "timestamp": datetime.now().isoformat(),
            "sf_time": datetime.now(self.sf_tz).isoformat()
        })
        self.save_collection_log()
        
        return filepath
    
    def collect_single_image(self):
        """Collect a single image if within daylight hours"""
        sf_time = datetime.now(self.sf_tz)
        
        if not self.is_daylight_hours():
            print(f"[{sf_time.strftime('%Y-%m-%d %H:%M:%S PST')}] Outside daylight hours ({self.start_hour}:00-{self.end_hour}:00 PST). Skipping.")
            return False
        
        print(f"[{sf_time.strftime('%Y-%m-%d %H:%M:%S PST')}] Downloading image...")
        image = self.download_image()
        
        if image is not None:
            filepath = self.save_image(image)
            print(f"  Saved: {os.path.basename(filepath)}")
            print(f"  Total collected: {self.log['total_collected']}")
            return True
        else:
            print("  Failed to download image")
            return False
    
    def calculate_next_collection_time(self):
        """Calculate next collection time (next hour mark during daylight)"""
        now = datetime.now(self.sf_tz)
        
        # Round up to next hour
        if now.minute == 0 and now.second == 0:
            next_hour = now
        else:
            next_hour = now.replace(minute=0, second=0, microsecond=0)
            next_hour += timedelta(hours=1)
        
        # If outside daylight hours, skip to next morning
        if next_hour.hour >= self.end_hour:
            # Skip to next morning at start_hour
            next_hour = next_hour.replace(hour=self.start_hour)
            next_hour += timedelta(days=1)
        elif next_hour.hour < self.start_hour:
            # Skip to start_hour today
            next_hour = next_hour.replace(hour=self.start_hour)
        
        return next_hour
    
    def collect_images(self, target_count=100):
        """Collect images until target count is reached"""
        print(f"FogCam Image Collector")
        print(f"=" * 50)
        print(f"Target: {target_count} images")
        print(f"Daylight hours: {self.start_hour}:00-{self.end_hour}:00 PST")
        print(f"Collection interval: 1 hour")
        print(f"Already collected: {self.log['total_collected']}")
        print(f"=" * 50)
        
        if self.log['total_collected'] >= target_count:
            print(f"Already have {self.log['total_collected']} images. Target reached!")
            return
        
        print("\nStarting collection...")
        
        while self.log['total_collected'] < target_count:
            # Collect image if possible
            self.collect_single_image()
            
            if self.log['total_collected'] >= target_count:
                print(f"\nTarget reached! Collected {self.log['total_collected']} images.")
                break
            
            # Calculate next collection time
            next_collection = self.calculate_next_collection_time()
            wait_seconds = (next_collection - datetime.now(self.sf_tz)).total_seconds()
            
            if wait_seconds > 0:
                wait_hours = wait_seconds / 3600
                print(f"\nNext collection: {next_collection.strftime('%Y-%m-%d %H:%M PST')}")
                print(f"Waiting {wait_hours:.1f} hours...")
                print(f"Progress: {self.log['total_collected']}/{target_count} images")
                print("Press Ctrl+C to stop collection\n")
                
                try:
                    time_module.sleep(wait_seconds)
                except KeyboardInterrupt:
                    print("\n\nCollection stopped by user.")
                    print(f"Total collected: {self.log['total_collected']} images")
                    break
    
    def status(self):
        """Show collection status"""
        print(f"Collection Status")
        print(f"=" * 50)
        print(f"Total images collected: {self.log['total_collected']}")
        
        if self.log['collection_history']:
            first = self.log['collection_history'][0]
            last = self.log['collection_history'][-1]
            print(f"First image: {first['timestamp']}")
            print(f"Last image: {last['timestamp']}")
            
            # Show images by day
            images_by_day = {}
            for entry in self.log['collection_history']:
                date = entry['timestamp'][:10]
                images_by_day[date] = images_by_day.get(date, 0) + 1
            
            print(f"\nImages by day:")
            for date, count in sorted(images_by_day.items()):
                print(f"  {date}: {count} images")

# Example usage
if __name__ == "__main__":
    collector = FogCamCollector()
    
    # Show current status
    collector.status()
    
    # Collect images (will run until 100 images are collected)
    # This will respect daylight hours and collect one image per hour
    collector.collect_images(target_count=100)