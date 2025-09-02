#!/bin/bash
# Deploy frontend service to Cloud Run
set -e

# Get script directory for relative paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../../../.." && pwd)"

# Configuration
PROJECT_ID="${PROJECT_ID:-karlcam}"
REGION="${REGION:-us-central1}"
FRONTEND_IMAGE_TAG="${FRONTEND_IMAGE_TAG:-latest}"

echo "🌐 Deploying KarlCam Frontend"
echo "=============================="
echo "  • Project: ${PROJECT_ID}"
echo "  • Region: ${REGION}"
echo "  • Image Tag: ${FRONTEND_IMAGE_TAG}"

# Set project
gcloud config set project ${PROJECT_ID}

# Build and push frontend image using production Dockerfile
echo "📦 Building frontend image..."
cd "${PROJECT_ROOT}"

# Build frontend using production Dockerfile
docker build --platform linux/amd64 \
  -f web/frontend/infra/Dockerfile.prod \
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