import os
import json
import shutil
from datetime import datetime
import pandas as pd

class FogDataOrganizer:
    def __init__(self, base_dir="data"):
        self.base_dir = base_dir
        self.raw_images_dir = os.path.join(base_dir, "images")  # Your current collection dir
        self.labeled_dataset_dir = os.path.join(base_dir, "labeled_dataset")
        self.splits_dir = os.path.join(base_dir, "splits")
        self.labels_file = os.path.join(base_dir, "labels.json")
        
        # Create directories
        self._create_directories()
        
        # Load existing labels
        self.load_labels()
    
    def _create_directories(self):
        """Create directory structure for organized dataset"""
        # Main directories
        dirs = [
            self.labeled_dataset_dir,
            os.path.join(self.labeled_dataset_dir, "fog"),
            os.path.join(self.labeled_dataset_dir, "clear"),
            self.splits_dir
        ]
        
        # Train/val/test splits
        for split in ["train", "val", "test"]:
            for label in ["fog", "clear"]:
                dirs.append(os.path.join(self.splits_dir, split, label))
        
        for dir_path in dirs:
            os.makedirs(dir_path, exist_ok=True)
    
    def load_labels(self):
        """Load existing labels from JSON file"""
        if os.path.exists(self.labels_file):
            with open(self.labels_file, 'r') as f:
                self.labels_data = json.load(f)
        else:
            self.labels_data = {
                "version": "1.0",
                "created": datetime.now().isoformat(),
                "labeled_by": "manual",
                "labels": {}
            }
    
    def save_labels(self):
        """Save labels to JSON file"""
        with open(self.labels_file, 'w') as f:
            json.dump(self.labels_data, f, indent=2)
        
        # Also save as CSV for easy viewing
        self.export_labels_to_csv()
    
    def add_label(self, filename, label, confidence=1.0, clip_prediction=None, clip_score=None):
        """Add or update a label for an image"""
        self.labels_data["labels"][filename] = {
            "label": label,
            "confidence": confidence,
            "verified_by": "user",
            "timestamp": datetime.now().isoformat(),
            "clip_prediction": clip_prediction,
            "clip_score": clip_score
        }
        self.save_labels()
    
    def organize_labeled_images(self):
        """Copy labeled images to organized directories"""
        labeled_count = {"fog": 0, "clear": 0}
        
        for filename, label_info in self.labels_data["labels"].items():
            src_path = os.path.join(self.raw_images_dir, filename)
            if os.path.exists(src_path):
                label = label_info["label"]
                dst_path = os.path.join(self.labeled_dataset_dir, label, filename)
                
                # Copy file if not already there
                if not os.path.exists(dst_path):
                    shutil.copy2(src_path, dst_path)
                    labeled_count[label] += 1
        
        print(f"Organized images - Fog: {labeled_count['fog']}, Clear: {labeled_count['clear']}")
        return labeled_count
    
    def create_train_val_test_splits(self, train_ratio=0.7, val_ratio=0.15):
        """Create train/validation/test splits"""
        import random
        
        # Get all labeled images
        fog_images = [f for f, l in self.labels_data["labels"].items() if l["label"] == "fog"]
        clear_images = [f for f, l in self.labels_data["labels"].items() if l["label"] == "clear"]
        
        # Shuffle
        random.shuffle(fog_images)
        random.shuffle(clear_images)
        
        splits_info = {}
        
        for label, images in [("fog", fog_images), ("clear", clear_images)]:
            n = len(images)
            train_n = int(n * train_ratio)
            val_n = int(n * val_ratio)
            
            train_images = images[:train_n]
            val_images = images[train_n:train_n+val_n]
            test_images = images[train_n+val_n:]
            
            splits_info[label] = {
                "train": len(train_images),
                "val": len(val_images),
                "test": len(test_images)
            }
            
            # Copy images to split directories
            for split, split_images in [("train", train_images), ("val", val_images), ("test", test_images)]:
                for img in split_images:
                    src = os.path.join(self.labeled_dataset_dir, label, img)
                    dst = os.path.join(self.splits_dir, split, label, img)
                    if os.path.exists(src):
                        shutil.copy2(src, dst)
        
        print("\nData splits created:")
        for label in ["fog", "clear"]:
            print(f"{label}: Train={splits_info[label]['train']}, "
                  f"Val={splits_info[label]['val']}, Test={splits_info[label]['test']}")
        
        return splits_info
    
    def export_labels_to_csv(self):
        """Export labels to CSV for easy viewing"""
        data = []
        for filename, info in self.labels_data["labels"].items():
            row = {"filename": filename}
            row.update(info)
            data.append(row)
        
        df = pd.DataFrame(data)
        csv_path = os.path.join(self.base_dir, "labels.csv")
        df.to_csv(csv_path, index=False)
        return csv_path
    
    def get_label_statistics(self):
        """Get statistics about labeled data"""
        labels = self.labels_data["labels"]
        
        stats = {
            "total_labeled": len(labels),
            "fog_count": sum(1 for l in labels.values() if l["label"] == "fog"),
            "clear_count": sum(1 for l in labels.values() if l["label"] == "clear"),
            "verified_count": sum(1 for l in labels.values() if l.get("verified_by") == "user"),
            "clip_agreed": sum(1 for f, l in labels.items() 
                             if l.get("clip_prediction") and 
                             ("fog" in l["clip_prediction"].lower()) == (l["label"] == "fog"))
        }
        
        if stats["total_labeled"] > 0:
            stats["fog_percentage"] = round(stats["fog_count"] / stats["total_labeled"] * 100, 1)
            stats["clip_agreement_rate"] = round(stats["clip_agreed"] / stats["total_labeled"] * 100, 1)
        
        return stats

# Example usage
if __name__ == "__main__":
    organizer = FogDataOrganizer()
    
    # Show current statistics
    stats = organizer.get_label_statistics()
    print("Current Label Statistics:")
    print(f"Total labeled: {stats['total_labeled']}")
    print(f"Fog images: {stats['fog_count']}")
    print(f"Clear images: {stats['clear_count']}")
    
    # Example: Add a label
    # organizer.add_label("fogcam_20250730_123456.jpg", "fog", confidence=0.95)