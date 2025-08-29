#!/bin/bash
# Deploy frontend service to Cloud Run
set -e

# Configuration
PROJECT_ID="${PROJECT_ID:-karlcam}"
REGION="${REGION:-us-central1}"
FRONTEND_IMAGE_TAG="${FRONTEND_IMAGE_TAG:-latest}"

echo "🌐 Deploying KarlCam Frontend"
echo "=============================="

# Set project
gcloud config set project ${PROJECT_ID}

# Build and push frontend image
echo "📦 Building frontend image..."
cd /Users/reed/Code/Homelab/KarlCam

# Build frontend (no longer needs API URL at build time)
docker build --platform linux/amd64 \
  -f frontend/Dockerfile \
  -t gcr.io/${PROJECT_ID}/karlcam-frontend:${FRONTEND_IMAGE_TAG} .

echo "⬆️  Pushing frontend image..."
docker push gcr.io/${PROJECT_ID}/karlcam-frontend:${FRONTEND_IMAGE_TAG}

# Deploy frontend service
echo "☁️  Deploying frontend service to Cloud Run..."
gcloud run deploy karlcam-frontend \
  --image gcr.io/${PROJECT_ID}/karlcam-frontend:${FRONTEND_IMAGE_TAG} \
  --region ${REGION} \
  --memory 256Mi \
  --cpu 1 \
  --timeout 30 \
  --concurrency 100 \
  --port 80 \
  --allow-unauthenticated \
  --min-instances 0 \
  --max-instances 5

# Get frontend URL
FRONTEND_URL=$(gcloud run services describe karlcam-frontend --region ${REGION} --format 'value(status.url)')

echo ""
echo "✅ Frontend Deployed!"
echo "===================="
echo "  • URL: ${FRONTEND_URL}"
echo "  • Custom Domain: https://karlcam.xyz (if configured)"
echo "  • API Endpoint: https://api.karlcam.xyz"
echo "  • Logs: gcloud run logs read karlcam-frontend --region=${REGION}"