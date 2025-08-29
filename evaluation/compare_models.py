#!/usr/bin/env python3
"""
Compare Gemini API vs Trained MobileNet predictions
Collect accuracy metrics and identify disagreements for active learning
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple
import numpy as np
from PIL import Image
import torch
import torchvision.transforms as transforms
import google.generativeai as genai
from dataclasses import dataclass, asdict
import sqlite3
import cv2
import sys

# Add packages to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from packages.fog_heuristics import HeuristicFogScorer

@dataclass
class Comparison:
    image_path: str
    timestamp: str
    gemini_fog_score: float
    gemini_confidence: float
    gemini_reasoning: str
    mobilenet_fog_score: float
    mobilenet_confidence: float
    heuristic_fog_score: float
    heuristic_confidence: float
    disagreement_score: float  # Max disagreement between methods
    needs_review: bool

class ModelComparator:
    def __init__(self, mobilenet_path: str = "data/models/best_model.pth"):
        self.data_dir = Path("data/comparison")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize database for tracking
        self.init_database()
        
        # Initialize heuristic scorer (always available)
        self.heuristic_scorer = HeuristicFogScorer()
        
        # Load MobileNet
        self.mobilenet = self.load_mobilenet(mobilenet_path)
        
        # Initialize Gemini
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        self.gemini = genai.GenerativeModel('gemini-1.5-flash')
        
        # Image preprocessing for MobileNet
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], 
                               std=[0.229, 0.224, 0.225])
        ])
    
    def init_database(self):
        """Create SQLite database for tracking comparisons"""
        self.db_path = self.data_dir / "comparisons.db"
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS comparisons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                image_path TEXT,
                timestamp TEXT,
                gemini_fog_score REAL,
                gemini_confidence REAL,
                gemini_reasoning TEXT,
                mobilenet_fog_score REAL,
                mobilenet_confidence REAL,
                heuristic_fog_score REAL,
                heuristic_confidence REAL,
                disagreement_score REAL,
                needs_review BOOLEAN,
                human_label REAL,  -- Ground truth if reviewed
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def load_mobilenet(self, model_path: str):
        """Load trained MobileNet model"""
        import sys
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from training.train_mobilenet import FogDetector
        
        model = FogDetector(num_outputs=2, pretrained=False)
        if os.path.exists(model_path):
            model.load_state_dict(torch.load(model_path, map_location='cpu'))
            model.eval()
            print(f"Loaded MobileNet from {model_path}")
        else:
            print(f"Warning: No trained model at {model_path}, using untrained MobileNet")
        
        return model
    
    def predict_mobilenet(self, image_path: str) -> Tuple[float, float]:
        """Get MobileNet prediction with confidence"""
        image = Image.open(image_path).convert('RGB')
        image_tensor = self.transform(image).unsqueeze(0)
        
        with torch.no_grad():
            fog_score, fog_level = self.mobilenet(image_tensor)
            
            # Get confidence from softmax probabilities
            probs = torch.softmax(fog_level, dim=1)
            confidence = torch.max(probs).item()
            
            fog_score_val = torch.sigmoid(fog_score).item()
        
        return fog_score_val, confidence
    
    def predict_gemini(self, image_path: str) -> Tuple[float, float, str]:
        """Get Gemini prediction with confidence and reasoning"""
        image = Image.open(image_path)
        
        prompt = """Analyze this security camera image for fog conditions.
        Provide your response in JSON format:
        {
            "fog_score": <float 0.0-1.0, where 0=clear, 1=heavy fog>,
            "confidence": <float 0.0-1.0>,
            "reasoning": "<brief explanation of visual cues>"
        }"""
        
        try:
            response = self.gemini.generate_content([prompt, image])
            result = json.loads(response.text.strip().replace('```json', '').replace('```', ''))
            
            return (
                result['fog_score'],
                result['confidence'],
                result['reasoning']
            )
        except Exception as e:
            print(f"Gemini error: {e}")
            return 0.5, 0.0, "Error in Gemini API"
    
    def calculate_disagreement(self, score1: float, score2: float) -> float:
        """Calculate disagreement between two predictions"""
        return abs(score1 - score2)
    
    def predict_heuristic(self, image_path: str) -> Tuple[float, float]:
        """Get heuristic prediction"""
        image = Image.open(image_path).convert('RGB')
        result = self.heuristic_scorer.score_image(image)
        return result['fog_score'] / 100, result['confidence']
    
    def compare_image(self, image_path: str) -> Comparison:
        """Compare predictions from all methods"""
        # Get predictions from all methods
        mobilenet_score, mobilenet_conf = self.predict_mobilenet(image_path)
        gemini_score, gemini_conf, gemini_reasoning = self.predict_gemini(image_path)
        heuristic_score, heuristic_conf = self.predict_heuristic(image_path)
        
        # Calculate disagreements between all pairs
        disagreements = [
            abs(mobilenet_score - gemini_score),
            abs(mobilenet_score - heuristic_score),
            abs(gemini_score - heuristic_score)
        ]
        max_disagreement = max(disagreements)
        
        # Flag for review if:
        # 1. High disagreement (>0.3 difference)
        # 2. All models have low confidence (<0.7)
        # 3. Edge cases (scores near 0.5)
        needs_review = (
            max_disagreement > 0.3 or
            (mobilenet_conf < 0.7 and gemini_conf < 0.7 and heuristic_conf < 0.7) or
            (0.4 < mobilenet_score < 0.6)
        )
        
        comparison = Comparison(
            image_path=str(image_path),
            timestamp=datetime.now().isoformat(),
            gemini_fog_score=gemini_score,
            gemini_confidence=gemini_conf,
            gemini_reasoning=gemini_reasoning,
            mobilenet_fog_score=mobilenet_score,
            mobilenet_confidence=mobilenet_conf,
            heuristic_fog_score=heuristic_score,
            heuristic_confidence=heuristic_conf,
            disagreement_score=max_disagreement,
            needs_review=needs_review
        )
        
        # Save to database
        self.save_comparison(comparison)
        
        return comparison
    
    def save_comparison(self, comparison: Comparison):
        """Save comparison to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO comparisons 
            (image_path, timestamp, gemini_fog_score, gemini_confidence, 
             gemini_reasoning, mobilenet_fog_score, mobilenet_confidence,
             heuristic_fog_score, heuristic_confidence,
             disagreement_score, needs_review)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            comparison.image_path,
            comparison.timestamp,
            comparison.gemini_fog_score,
            comparison.gemini_confidence,
            comparison.gemini_reasoning,
            comparison.mobilenet_fog_score,
            comparison.mobilenet_confidence,
            comparison.heuristic_fog_score,
            comparison.heuristic_confidence,
            comparison.disagreement_score,
            comparison.needs_review
        ))
        
        conn.commit()
        conn.close()
    
    def get_statistics(self) -> Dict:
        """Get comparison statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        stats = {}
        
        # Overall stats
        cursor.execute("SELECT COUNT(*) FROM comparisons")
        stats['total_comparisons'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT AVG(disagreement_score) FROM comparisons")
        stats['avg_disagreement'] = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT COUNT(*) FROM comparisons WHERE needs_review = 1")
        stats['needs_review'] = cursor.fetchone()[0]
        
        # Model performance (only where we have human labels)
        cursor.execute("""
            SELECT 
                AVG(ABS(mobilenet_fog_score - human_label)) as mobilenet_error,
                AVG(ABS(gemini_fog_score - human_label)) as gemini_error
            FROM comparisons 
            WHERE human_label IS NOT NULL
        """)
        result = cursor.fetchone()
        if result[0] is not None:
            stats['mobilenet_avg_error'] = result[0]
            stats['gemini_avg_error'] = result[1]
            stats['better_model'] = 'MobileNet' if result[0] < result[1] else 'Gemini'
        
        conn.close()
        return stats
    
    def get_disagreements(self, limit: int = 10) -> List[Dict]:
        """Get top disagreements for review"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM comparisons 
            WHERE needs_review = 1 AND human_label IS NULL
            ORDER BY disagreement_score DESC
            LIMIT ?
        """, (limit,))
        
        columns = [desc[0] for desc in cursor.description]
        results = []
        for row in cursor.fetchall():
            results.append(dict(zip(columns, row)))
        
        conn.close()
        return results
    
    def update_human_label(self, image_path: str, human_label: float):
        """Update comparison with human ground truth"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE comparisons 
            SET human_label = ?, needs_review = 0
            WHERE image_path = ?
        """, (human_label, image_path))
        
        conn.commit()
        conn.close()

def main():
    """Run comparison on recent images"""
    comparator = ModelComparator()
    
    # Compare recent images
    image_dir = Path("data/raw/images")
    recent_images = sorted(image_dir.glob("*.jpg"))[-10:]  # Last 10 images
    
    print("Comparing models on recent images...")
    print("-" * 60)
    
    for image_path in recent_images:
        print(f"\nProcessing: {image_path.name}")
        comparison = comparator.compare_image(image_path)
        
        print(f"  Gemini:    {comparison.gemini_fog_score:.2f} (conf: {comparison.gemini_confidence:.2f})")
        print(f"  MobileNet: {comparison.mobilenet_fog_score:.2f} (conf: {comparison.mobilenet_confidence:.2f})")
        print(f"  Heuristic: {comparison.heuristic_fog_score:.2f} (conf: {comparison.heuristic_confidence:.2f})")
        print(f"  Max Disagreement: {comparison.disagreement_score:.2f}")
        
        if comparison.needs_review:
            print("  ⚠️  Flagged for review!")
    
    # Show statistics
    print("\n" + "=" * 60)
    print("STATISTICS")
    print("=" * 60)
    
    stats = comparator.get_statistics()
    for key, value in stats.items():
        print(f"{key}: {value}")
    
    # Show top disagreements
    print("\n" + "=" * 60)
    print("TOP DISAGREEMENTS (need human review)")
    print("=" * 60)
    
    disagreements = comparator.get_disagreements(5)
    for d in disagreements:
        print(f"\n{d['image_path']}:")
        print(f"  Gemini: {d['gemini_fog_score']:.2f}, MobileNet: {d['mobilenet_fog_score']:.2f}")
        print(f"  Disagreement: {d['disagreement_score']:.2f}")

if __name__ == "__main__":
    main()