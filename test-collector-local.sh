#!/bin/bash
# Test the collector locally using Docker (same as production)

set -e

echo "🐳 Testing KarlCam Collector Locally with Docker"
echo "==============================================="

# Check if .env exists in cloudrun/deploy
if [ -f "cloudrun/deploy/.env" ]; then
    source cloudrun/deploy/.env
    echo "✅ Loaded environment variables from cloudrun/deploy/.env"
else
    echo "⚠️  No .env file found. Create cloudrun/deploy/.env with:"
    echo "   GEMINI_API_KEY=your_key_here"
    echo "   DATABASE_PASSWORD=your_password_here"
    exit 1
fi

# Build the container if needed
echo "🔨 Building collector container..."
docker build --platform linux/amd64 -f cloudrun/docker/Dockerfile.collector -t karlcam-collector:local .

# Create local output directory
mkdir -p test_data/output

# Run the collector container locally without database
echo "🚀 Running collector..."
echo "📁 Output will be saved to: test_data/output/"
echo "📝 Results will be saved as JSON files (no database)"
docker run --rm \
  -v $(pwd)/test_data/output:/output \
  -e GEMINI_API_KEY="${GEMINI_API_KEY}" \
  -e USE_CLOUD_STORAGE="false" \
  -e OUTPUT_DIR="/output" \
  -e LOCAL_TESTING="true" \
  -e PYTHONPATH="/app" \
  karlcam-collector:local \
  python -m collect.collect_and_label

echo ""
echo "✅ Test complete! Check test_data/output/ for results"
echo ""
echo "📝 To test with Cloud SQL connection, add:"
echo "   -e DATABASE_URL='your_connection_string'"
echo ""