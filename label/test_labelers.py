#!/usr/bin/env python3
"""
Test script for comparing labeling techniques
Useful for Vertex AI Workbench experimentation
"""

import os
import json
from pathlib import Path
from PIL import Image
from io import BytesIO
import matplotlib.pyplot as plt
import pandas as pd
from typing import List, Dict

# Setup for notebook environment
def setup_environment():
    """Setup environment for notebook testing"""
    import sys
    from pathlib import Path
    
    # Add current directory and parent collect directory to path
    current_dir = Path(__file__).parent
    sys.path.append(str(current_dir))
    sys.path.append(str(current_dir.parent / 'collect'))
    
    # Load env from collect folder if available
    env_path = current_dir.parent / 'collect' / '.env'
    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    if key not in os.environ:
                        os.environ[key] = value.strip('"\'')

def load_test_images_from_cloud(bucket_name: str, prefix: str = "raw_images/", limit: int = 10) -> List[Dict]:
    """Load sample images from cloud storage for testing"""
    try:
        from google.cloud import storage
        client = storage.Client()
        bucket = client.bucket(bucket_name)
        
        blobs = list(bucket.list_blobs(prefix=prefix, max_results=limit))
        images = []
        
        for blob in blobs:
            if blob.name.endswith('.jpg'):
                # Download image
                image_bytes = blob.download_as_bytes()
                image = Image.open(BytesIO(image_bytes)).convert('RGB')
                
                # Try to load metadata
                metadata_path = blob.name.replace("raw_images/", "raw_metadata/") + ".json"
                try:
                    metadata_blob = bucket.blob(metadata_path)
                    metadata = json.loads(metadata_blob.download_as_text())
                except:
                    metadata = {"webcam": {"name": "unknown"}}
                
                images.append({
                    "filename": blob.name.split('/')[-1],
                    "image": image,
                    "metadata": metadata
                })
        
        return images
    except Exception as e:
        print(f"Error loading from cloud: {e}")
        return []

def load_test_images_local(directory: str, limit: int = 10) -> List[Dict]:
    """Load sample images from local directory for testing"""
    images_dir = Path(directory) / "raw_images"
    metadata_dir = Path(directory) / "raw_metadata"
    
    if not images_dir.exists():
        print(f"Directory {images_dir} not found")
        return []
    
    images = []
    for img_path in list(images_dir.glob("*.jpg"))[:limit]:
        try:
            image = Image.open(img_path).convert('RGB')
            
            # Try to load metadata
            metadata_path = metadata_dir / f"{img_path.name}.json"
            if metadata_path.exists():
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
            else:
                metadata = {"webcam": {"name": "unknown"}}
            
            images.append({
                "filename": img_path.name,
                "image": image,
                "metadata": metadata
            })
        except Exception as e:
            print(f"Error loading {img_path}: {e}")
    
    return images

def compare_labelers(image: Image.Image, metadata: Dict, labeler_types: List[str]) -> Dict:
    """Run multiple labelers on same image and return comparison"""
    from labelers import create_labeler
    
    results = {}
    for labeler_type in labeler_types:
        try:
            labeler = create_labeler(labeler_type)
            result = labeler.label_image(image, metadata)
            results[labeler_type] = result
            print(f"✅ {labeler_type}: Score={result.get('fog_score', 'N/A')}, Level={result.get('fog_level', 'N/A')}")
        except Exception as e:
            print(f"❌ {labeler_type}: {e}")
            results[labeler_type] = {"status": "error", "error": str(e)}
    
    return results

def visualize_comparison(image: Image.Image, results: Dict, save_path: str = None):
    """Visualize labeling results side by side"""
    fig, axes = plt.subplots(1, len(results) + 1, figsize=(5 * (len(results) + 1), 5))
    
    if len(results) == 0:
        axes = [axes]
    
    # Show original image
    axes[0].imshow(image)
    axes[0].set_title("Original Image")
    axes[0].axis('off')
    
    # Show results for each labeler
    for i, (labeler_type, result) in enumerate(results.items(), 1):
        if i < len(axes):
            axes[i].imshow(image)
            
            if result.get('status') == 'success':
                title = f"{labeler_type}\nScore: {result.get('fog_score', 'N/A')}\nLevel: {result.get('fog_level', 'N/A')}\nConfidence: {result.get('confidence', 'N/A'):.2f}"
            else:
                title = f"{labeler_type}\nError: {result.get('error', 'Unknown')}"
                
            axes[i].set_title(title, fontsize=10)
            axes[i].axis('off')
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"Saved visualization to {save_path}")
    
    plt.show()

def create_comparison_dataframe(all_results: List[Dict]) -> pd.DataFrame:
    """Create a pandas DataFrame for easy analysis of results"""
    rows = []
    
    for img_data in all_results:
        filename = img_data['filename']
        results = img_data['results']
        
        for labeler_type, result in results.items():
            if result.get('status') == 'success':
                rows.append({
                    'filename': filename,
                    'labeler': labeler_type,
                    'fog_score': result.get('fog_score'),
                    'fog_level': result.get('fog_level'),
                    'confidence': result.get('confidence'),
                    'visibility_estimate': result.get('visibility_estimate'),
                    'reasoning': result.get('reasoning', '')[:100] + '...' if len(result.get('reasoning', '')) > 100 else result.get('reasoning', '')
                })
    
    return pd.DataFrame(rows)

def run_comparison_experiment(data_source: str, labeler_types: List[str] = None, limit: int = 5):
    """Run a full comparison experiment"""
    if labeler_types is None:
        labeler_types = ["gemini", "gemini_masked"]
    
    print(f"🧪 Running labeler comparison experiment")
    print(f"📊 Labelers: {', '.join(labeler_types)}")
    print(f"📁 Data source: {data_source}")
    print(f"🔢 Sample limit: {limit}")
    
    # Load test images
    if data_source.startswith("gs://"):
        bucket_name = data_source.replace("gs://", "").split("/")[0]
        images = load_test_images_from_cloud(bucket_name, limit=limit)
    else:
        images = load_test_images_local(data_source, limit=limit)
    
    if not images:
        print("❌ No images loaded")
        return None, None
    
    print(f"📷 Loaded {len(images)} images")
    
    # Run comparisons
    all_results = []
    for img_data in images:
        print(f"\n🖼️  Processing {img_data['filename']}")
        results = compare_labelers(img_data['image'], img_data['metadata'], labeler_types)
        
        all_results.append({
            'filename': img_data['filename'],
            'image': img_data['image'],
            'results': results
        })
        
        # Visualize first few images
        if len(all_results) <= 3:
            visualize_comparison(img_data['image'], results)
    
    # Create summary DataFrame
    df = create_comparison_dataframe(all_results)
    
    print(f"\n📈 Summary Statistics:")
    print(df.groupby('labeler')[['fog_score', 'confidence']].describe())
    
    return all_results, df

# Example usage for notebook:
if __name__ == "__main__":
    # For testing in Vertex AI Workbench:
    setup_environment()
    
    # Test with cloud storage
    # results, df = run_comparison_experiment("gs://karlcam-fog-data", ["gemini", "gemini_masked"], limit=3)
    
    # Or test locally
    results, df = run_comparison_experiment("./output", ["gemini", "gemini_masked"], limit=3)