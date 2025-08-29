#!/bin/bash
# Setup script for local collector testing

echo "🧪 Setting up KarlCam Collector for Local Testing"
echo "================================================="

cd "$(dirname "$0")"

# Step 1: Check Python dependencies
echo "📦 Checking Python dependencies..."
python3 -c "
import sys
missing = []
try:
    from PIL import Image
except ImportError:
    missing.append('pillow')
try:
    import requests
except ImportError:
    missing.append('requests')
try:
    import cv2
except ImportError:
    missing.append('opencv-python-headless')
try:
    import numpy
except ImportError:
    missing.append('numpy')
try:
    import google.generativeai
except ImportError:
    missing.append('google-generativeai')

if missing:
    print(f'Missing dependencies: {missing}')
    print('Install with: pip install ' + ' '.join(missing))
    sys.exit(1)
else:
    print('✅ All dependencies found')
"

if [ $? -ne 0 ]; then
    echo ""
    echo "💡 To install missing dependencies:"
    echo "   pip install pillow requests opencv-python-headless numpy google-generativeai"
    echo ""
    exit 1
fi

# Step 2: Setup .env file
echo ""
echo "⚙️  Setting up environment file..."
if [ ! -f "collect/.env" ]; then
    cp collect/.env.example collect/.env
    echo "✅ Created collect/.env from example"
    echo ""
    echo "🔑 IMPORTANT: Edit collect/.env and add your Gemini API key!"
    echo "   Open: collect/.env"
    echo "   Set: GEMINI_API_KEY=your-actual-api-key"
    echo ""
    echo "💡 Get a Gemini API key at: https://makersuite.google.com/app/apikey"
else
    echo "✅ Found existing collect/.env"
fi

# Step 3: Create test data directory
echo ""
echo "📁 Creating test data directory..."
mkdir -p test_data/{raw/{images,labels},review/{pending,metadata}}
echo "✅ Test data directory created"

echo ""
echo "✅ Setup Complete!"
echo "=================="
echo ""
echo "🚀 To run the collector locally:"
echo "   python -m collect.collect_and_label"
echo ""
echo "📊 Test data will be saved to:"
echo "   ./test_data/"
echo ""
echo "🔍 To view results:"
echo "   ls -la test_data/raw/labels/"
echo "   cat test_data/raw/labels/*.json | jq ."
echo ""
echo "⚠️  Don't forget to set your Gemini API key in collect/.env!"