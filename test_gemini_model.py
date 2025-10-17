#!/usr/bin/env python3
"""
Test script to verify Gemini model availability
"""

import os
import sys
from PIL import Image
import requests
from io import BytesIO

# Add the current directory to Python path
sys.path.append('.')

def test_model(model_name):
    """Test a specific Gemini model"""
    print(f"\n🧪 Testing model: {model_name}")
    
    try:
        import google.generativeai as genai
        
        # Get API key
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("❌ GEMINI_API_KEY not found in environment")
            return False
        
        # Configure API
        genai.configure(api_key=api_key)
        
        # Initialize model
        model = genai.GenerativeModel(model_name)
        print(f"✅ Model {model_name} initialized successfully")
        
        # Test with a simple text prompt
        print("🔤 Testing text generation...")
        response = model.generate_content("Say 'Hello from Gemini' in exactly those words.")
        print(f"📝 Text response: {response.text}")
        
        # Test with an image (use a simple test image)
        print("🖼️  Testing vision capabilities...")
        
        # Create a simple test image (red square)
        test_image = Image.new('RGB', (100, 100), color='red')
        
        vision_prompt = """Look at this image and respond with this exact JSON format:
        {
            "color": "red",
            "shape": "square",
            "test_successful": true
        }"""
        
        vision_response = model.generate_content([vision_prompt, test_image])
        print(f"👁️  Vision response: {vision_response.text}")
        
        print(f"✅ Model {model_name} is working correctly!")
        return True
        
    except Exception as e:
        print(f"❌ Model {model_name} failed: {e}")
        return False

def main():
    print("🚀 Gemini Model Testing")
    print("=" * 50)
    
    # Test different model names
    models_to_test = [
        "gemini-2.0-flash",
        "gemini-1.5-flash",
        "gemini-1.5-flash-latest",
        "gemini-1.5-pro"
    ]
    
    working_models = []
    
    for model in models_to_test:
        if test_model(model):
            working_models.append(model)
    
    print("\n" + "=" * 50)
    print("📊 RESULTS")
    print("=" * 50)
    
    if working_models:
        print("✅ Working models:")
        for model in working_models:
            print(f"   - {model}")
    else:
        print("❌ No models are working")
    
    print(f"\n🎯 Recommended model: {working_models[0] if working_models else 'None'}")

if __name__ == "__main__":
    main()