#!/bin/bash
# Deploy review frontend service to Cloud Run
set -e

# Configuration
PROJECT_ID="${PROJECT_ID:-karlcam}"
REGION="${REGION:-us-central1}"
REVIEW_FRONTEND_IMAGE_TAG="${REVIEW_FRONTEND_IMAGE_TAG:-latest}"

echo "🎨 Deploying KarlCam Review Frontend"
echo "====================================="

# Set project
gcloud config set project ${PROJECT_ID}

# Get review backend URL (if deployed)
REVIEW_BACKEND_URL=$(gcloud run services describe karlcam-review-backend --region ${REGION} --format 'value(status.url)' 2>/dev/null || echo "")

if [ -z "$REVIEW_BACKEND_URL" ]; then
    echo "⚠️  Review backend not found. Using default backend URL."
    REVIEW_BACKEND_URL="http://localhost:8001"
fi

# Build and push review frontend image
echo "📦 Building review frontend image..."
cd /Users/reed/Code/Homelab/KarlCam
docker build --platform linux/amd64 \
  -f cloudrun/docker/Dockerfile.review-frontend \
  -t gcr.io/${PROJECT_ID}/karlcam-review-frontend:${REVIEW_FRONTEND_IMAGE_TAG} .

echo "⬆️  Pushing review frontend image..."
docker push gcr.io/${PROJECT_ID}/karlcam-review-frontend:${REVIEW_FRONTEND_IMAGE_TAG}

# Deploy review frontend service
echo "☁️  Deploying review frontend service to Cloud Run..."
gcloud run deploy karlcam-review-frontend \
  --image gcr.io/${PROJECT_ID}/karlcam-review-frontend:${REVIEW_FRONTEND_IMAGE_TAG} \
  --region ${REGION} \
  --memory 256Mi \
  --cpu 1 \
  --timeout 30 \
  --concurrency 100 \
  --port 80 \
  --allow-unauthenticated \
  --min-instances 0 \
  --max-instances 5 \
  --set-env-vars "BACKEND_URL=${REVIEW_BACKEND_URL}"

# Get frontend URL
REVIEW_FRONTEND_URL=$(gcloud run services describe karlcam-review-frontend --region ${REGION} --format 'value(status.url)')

echo ""
echo "✅ Review Frontend Deployed!"
echo "============================"
echo "  • URL: ${REVIEW_FRONTEND_URL}"
echo "  • Backend: ${REVIEW_BACKEND_URL}"
echo "  • Logs: gcloud run logs read karlcam-review-frontend --region=${REGION}"
echo ""
echo "📝 Note: The review frontend is for labeling and reviewing fog detection data."