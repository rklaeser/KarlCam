import torch
from transformers import pipeline
from PIL import Image
import cv2
import numpy as np
import os
import json
from datetime import datetime
import matplotlib.pyplot as plt
import requests
from io import BytesIO

class ClassifyFogCLIP:
    def __init__(self):
        self.data_dir = "data"
        
        # Load webcam configuration
        self.load_webcams()
        
        # Default to first webcam for backward compatibility
        self.image_url = self.webcams[0]["url"]
        self.location = {
            "name": self.webcams[0]["name"],
            "lat": self.webcams[0]["lat"],
            "lon": self.webcams[0]["lon"],
            "url": self.webcams[0]["url"]
        }
        
        # Initialize models - AUTO-DETECT GPU
        if torch.cuda.is_available():
            self.device = torch.device("cuda")
            device_id = 0  # Use first GPU
            print(f"Using GPU: {torch.cuda.get_device_name(0)}")
            print(f"GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")
        else:
            self.device = torch.device("cpu")
            device_id = -1  # CPU fallback
            print("Warning: CUDA not available, falling back to CPU")
        
        print(f"Using device: {self.device}")
        
        # Initialize CLIP for zero-shot classification with GPU support
        self.init_clip_model(device_id)
    
    def load_webcams(self):
        """Load webcam configuration from JSON file"""
        try:
            # Try multiple possible locations for webcams.json
            possible_paths = [
                'data/webcams.json',
                'webcams.json',
                os.path.join(os.path.dirname(__file__), 'data', 'webcams.json'),
                os.path.join(os.path.dirname(__file__), 'webcams.json')
            ]
            
            config = None
            for path in possible_paths:
                try:
                    with open(path, 'r') as f:
                        config = json.load(f)
                        break
                except FileNotFoundError:
                    continue
            
            if config is None:
                raise FileNotFoundError("webcams.json configuration file not found in any expected location")
                
            self.webcams = config['webcams']
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON format in webcams.json")
        
    def init_clip_model(self, device_id):
        """Initialize CLIP model for zero-shot fog classification"""
        print("Loading CLIP model for zero-shot classification...")
        
        # Load model with GPU support
        self.clip_classifier = pipeline(
            "zero-shot-image-classification",
            model="openai/clip-vit-base-patch32",
            device=device_id  # 0 for GPU, -1 for CPU
        )
        
        # Warm up GPU with dummy inference (reduces first inference latency)
        if device_id >= 0:
            try:
                dummy_image = Image.new('RGB', (224, 224))
                _ = self.clip_classifier(dummy_image, candidate_labels=["test"])
                print("GPU warmup completed")
            except Exception as e:
                print(f"GPU warmup failed: {e}")
        
        # Define fog-related labels for classification
        self.fog_labels = [
            "clear blue sky",
            "light fog in the air", 
            "moderate fog obscuring view",
            "heavy fog with low visibility",
            "dense fog completely obscuring view",
            "hazy atmosphere",
            "misty conditions",
            "clear visibility"
        ]
        
        
    def load_image(self, image_path=None, url=None):
        """Load image from file or URL"""
        if image_path:
            if image_path.endswith('.png') or image_path.endswith('.jpg') or image_path.endswith('.jpeg'):
                return Image.open(image_path).convert('RGB')
            else:
                # OpenCV format
                img_cv = cv2.imread(image_path)
                return Image.fromarray(cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB))
        elif url:
            response = requests.get(url)
            return Image.open(BytesIO(response.content)).convert('RGB')
        else:
            # Download from fogcam
            response = requests.get(self.image_url)
            return Image.open(BytesIO(response.content)).convert('RGB')
            
    def analyze_with_clip(self, image):
        """Analyze fog using CLIP zero-shot classification"""
        # Run zero-shot classification (GPU accelerated if available)
        with torch.cuda.amp.autocast(enabled=torch.cuda.is_available()):
            results = self.clip_classifier(image, candidate_labels=self.fog_labels)
        
        # Process results
        fog_indicators = ["fog", "hazy", "misty", "obscuring"]
        clear_indicators = ["clear", "blue sky", "visibility"]
        
        fog_score = 0
        clear_score = 0
        
        for result in results:
            label = result['label'].lower()
            score = result['score']
            
            # Check if label indicates fog
            if any(indicator in label for indicator in fog_indicators):
                fog_score += score
            # Check if label indicates clear conditions
            elif any(indicator in label for indicator in clear_indicators):
                clear_score += score
                
        # Normalize scores
        total_score = fog_score + clear_score
        if total_score > 0:
            fog_probability = fog_score / total_score
        else:
            fog_probability = 0.5  # Uncertain
            
        # Determine fog level based on top prediction
        top_label = results[0]['label']
        top_score = results[0]['score']
        
        if "clear" in top_label.lower() and top_score > 0.5:
            fog_level = "Clear"
            adjusted_fog_score = fog_probability * 30  # Scale down for clear conditions
        elif "light fog" in top_label.lower():
            fog_level = "Light Fog"
            adjusted_fog_score = 20 + fog_probability * 20
        elif "moderate fog" in top_label.lower():
            fog_level = "Moderate Fog"
            adjusted_fog_score = 40 + fog_probability * 20
        elif "heavy fog" in top_label.lower() or "dense fog" in top_label.lower():
            fog_level = "Heavy Fog"
            adjusted_fog_score = 60 + fog_probability * 40
        elif "hazy" in top_label.lower() or "misty" in top_label.lower():
            fog_level = "Hazy/Misty"
            adjusted_fog_score = 30 + fog_probability * 30
        else:
            fog_level = "Uncertain"
            adjusted_fog_score = fog_probability * 100
            
        return {
            "timestamp": datetime.now().isoformat(),
            "fog_score": round(adjusted_fog_score, 2),
            "fog_probability": round(fog_probability * 100, 2),
            "fog_level": fog_level,
            "top_prediction": top_label,
            "confidence": round(top_score * 100, 2),
            "all_predictions": [
                {"label": r['label'], "score": round(r['score'] * 100, 2)} 
                for r in results[:5]  # Top 5 predictions
            ],
            "location": self.location,
            "method": "CLIP Zero-Shot",
            "device": str(self.device)  # Include device info
        }
        
    def analyze_with_weather_context(self, image):
        """Enhanced analysis using weather-specific CLIP prompts"""
        # More specific weather condition prompts
        weather_labels = [
            "a photo of clear blue sky with no fog",
            "a photo of light morning fog",
            "a photo of thick fog reducing visibility", 
            "a photo of dense fog completely obscuring the view",
            "a photo of hazy atmospheric conditions",
            "a photo of crystal clear weather",
            "a photo of misty weather conditions",
            "a photo of foggy weather obscuring buildings",
            "a photo showing good visibility with no fog",
            "a photo of San Francisco fog rolling in"
        ]
        
        # GPU accelerated inference
        with torch.cuda.amp.autocast(enabled=torch.cuda.is_available()):
            results = self.clip_classifier(image, candidate_labels=weather_labels)
        
        # Calculate fog score based on results
        fog_related_score = 0
        clear_related_score = 0
        
        for result in results:
            label = result['label'].lower()
            score = result['score']
            
            if any(word in label for word in ["fog", "mist", "hazy", "obscuring", "reducing visibility"]):
                fog_related_score += score
            elif any(word in label for word in ["clear", "no fog", "good visibility", "blue sky"]):
                clear_related_score += score
                
        # More nuanced scoring
        if fog_related_score > clear_related_score * 1.5:
            fog_detected = True
            confidence = fog_related_score / (fog_related_score + clear_related_score)
        elif clear_related_score > fog_related_score * 1.5:
            fog_detected = False
            confidence = clear_related_score / (fog_related_score + clear_related_score)
        else:
            fog_detected = fog_related_score > clear_related_score
            confidence = 0.5 + abs(fog_related_score - clear_related_score) * 0.5
            
        return {
            "fog_detected": fog_detected,
            "confidence": round(confidence * 100, 2),
            "fog_score": round(fog_related_score / (fog_related_score + clear_related_score) * 100, 2),
            "top_prediction": results[0]['label'],
            "detailed_scores": {
                "fog_related": round(fog_related_score * 100, 2),
                "clear_related": round(clear_related_score * 100, 2)
            },
            "device": str(self.device)
        }
        
    def create_visualization(self, image, analysis):
        """Create visualization of the analysis results"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
        
        # Show image
        ax1.imshow(image)
        ax1.set_title(f"Fog Score: {analysis['fog_score']:.1f} - {analysis['fog_level']}")
        ax1.axis('off')
        
        # Add GPU indicator if using GPU
        if 'device' in analysis and 'cuda' in analysis['device']:
            ax1.text(0.02, 0.98, '🚀 GPU', transform=ax1.transAxes, 
                    fontsize=12, verticalalignment='top',
                    bbox=dict(boxstyle='round', facecolor='green', alpha=0.5))
        
        # Show predictions
        labels = [p['label'] for p in analysis['all_predictions']]
        scores = [p['score'] for p in analysis['all_predictions']]
        
        y_pos = np.arange(len(labels))
        ax2.barh(y_pos, scores)
        ax2.set_yticks(y_pos)
        ax2.set_yticklabels(labels)
        ax2.set_xlabel('Confidence (%)')
        ax2.set_title('CLIP Predictions')
        ax2.set_xlim(0, 100)
        
        # Add confidence text
        for i, score in enumerate(scores):
            ax2.text(score + 1, i, f'{score:.1f}%', va='center')
        
        plt.tight_layout()
        
        # Save
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        save_path = f"{self.data_dir}/analysis/clip_analysis_{timestamp}.png"
        plt.savefig(save_path)
        plt.close()
        
        return save_path
        
        
    def compare_methods(self, image_path):
        """Compare all fog detection methods"""
        image = self.load_image(image_path)
        
        # Run CLIP analysis
        clip_result = self.analyze_with_clip(image)
        
        # Run weather-context analysis  
        weather_result = self.analyze_with_weather_context(image)
        
        # Combine results
        combined_analysis = {
            "timestamp": datetime.now().isoformat(),
            "image_path": image_path,
            "clip_analysis": clip_result,
            "weather_context_analysis": weather_result,
            "final_verdict": {
                "fog_detected": clip_result['fog_score'] > 30 or weather_result['fog_detected'],
                "confidence": max(clip_result['confidence'], weather_result['confidence']),
                "method_agreement": abs(clip_result['fog_score'] - weather_result['fog_score']) < 20
            },
            "gpu_accelerated": torch.cuda.is_available()
        }
        
        return combined_analysis

# Example usage
if __name__ == "__main__":
    print("CLIP-based Fog Classifier (GPU-Enabled)")
    print("=" * 50)
    
    # Check GPU availability
    if torch.cuda.is_available():
        print(f"✅ GPU Available: {torch.cuda.get_device_name(0)}")
        print(f"   Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")
    else:
        print("⚠️  No GPU detected - using CPU")
    
    # Initialize classifier
    detector = ClassifyFogCLIP()
    
    # Test with local image
    test_image_path = "data/images/fogcam.png"
    
    if os.path.exists(test_image_path):
        print(f"\nAnalyzing image: {test_image_path}")
        
        # Load image
        image = detector.load_image(test_image_path)
        
        # Benchmark GPU vs CPU if available
        import time
        start_time = time.time()
        
        # Run CLIP analysis
        print("\n1. CLIP Zero-Shot Analysis:")
        print("-" * 30)
        clip_analysis = detector.analyze_with_clip(image)
        
        inference_time = time.time() - start_time
        print(f"Inference Time: {inference_time:.3f} seconds")
        print(f"Fog Score: {clip_analysis['fog_score']}")
        print(f"Fog Level: {clip_analysis['fog_level']}")
        print(f"Top Prediction: {clip_analysis['top_prediction']} ({clip_analysis['confidence']}% confidence)")
        print(f"\nTop 5 Predictions:")
        for pred in clip_analysis['all_predictions']:
            print(f"  - {pred['label']}: {pred['score']}%")
            
        # Run weather context analysis
        print("\n2. Weather Context Analysis:")
        print("-" * 30)
        weather_analysis = detector.analyze_with_weather_context(image)
        print(f"Fog Detected: {weather_analysis['fog_detected']}")
        print(f"Confidence: {weather_analysis['confidence']}%")
        print(f"Fog Score: {weather_analysis['fog_score']}%")
        
        # Create visualization
        vis_path = detector.create_visualization(image, clip_analysis)
        print(f"\nVisualization saved to: {vis_path}")
        
        # Compare both methods
        print("\n3. Method Comparison:")
        print("-" * 30)
        comparison = detector.compare_methods(test_image_path)
        print(f"Final Verdict - Fog Detected: {comparison['final_verdict']['fog_detected']}")
        print(f"Method Agreement: {comparison['final_verdict']['method_agreement']}")
        print(f"GPU Accelerated: {comparison['gpu_accelerated']}")
        
        # Save results
        results_path = f"{detector.data_dir}/analysis/clip_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_path, 'w') as f:
            json.dump({
                "clip_analysis": clip_analysis,
                "weather_analysis": weather_analysis,
                "inference_time_seconds": inference_time
            }, f, indent=2)
        print(f"Results saved to: {results_path}")
    else:
        print(f"Test image not found at {test_image_path}")
        
    # Also test with current FogCam image
    print("\n\nTesting with current FogCam image...")
    try:
        current_image = detector.load_image()
        current_analysis = detector.analyze_with_clip(current_image)
        print(f"Current Fog Level: {current_analysis['fog_level']} (Score: {current_analysis['fog_score']})")
    except Exception as e:
        print(f"Error loading current FogCam image: {e}")