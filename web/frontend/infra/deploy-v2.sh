#!/bin/bash
# Deploy v2 frontend service to Cloud Run with karl.cam domain
set -e

# Get script directory for relative paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../../../.." && pwd)"

# Configuration
PROJECT_ID="${PROJECT_ID:-karlcam}"
REGION="${REGION:-us-central1}"
FRONTEND_IMAGE_TAG="${FRONTEND_IMAGE_TAG:-v2}"

echo "🌐 Deploying KarlCam V2 Frontend"
echo "================================="
echo "  • Project: ${PROJECT_ID}"
echo "  • Region: ${REGION}"
echo "  • Image Tag: ${FRONTEND_IMAGE_TAG}"
echo "  • Domain: karl.cam"

# Set project
gcloud config set project ${PROJECT_ID}

# Build and push frontend image using production Dockerfile
echo "📦 Building v2 frontend image..."
cd "${PROJECT_ROOT}"

# Build frontend using production Dockerfile
docker build --platform linux/amd64 \
  -f web/frontend/infra/Dockerfile.prod \
  -t gcr.io/${PROJECT_ID}/karlcam-frontend:${FRONTEND_IMAGE_TAG} .

echo "⬆️  Pushing v2 frontend image..."
docker push gcr.io/${PROJECT_ID}/karlcam-frontend:${FRONTEND_IMAGE_TAG}

# Deploy v2 frontend service
echo "☁️  Deploying v2 frontend service to Cloud Run..."
gcloud run deploy karlcam-frontend-v2 \
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
FRONTEND_URL=$(gcloud run services describe karlcam-frontend-v2 --region ${REGION} --format 'value(status.url)')

echo ""
echo "✅ V2 Frontend Deployed!"
echo "======================="
echo "  • URL: ${FRONTEND_URL}"
echo "  • API Endpoint: https://api.karl.cam"
echo "  • Logs: gcloud run services logs read karlcam-frontend-v2 --region=${REGION}"
echo ""
echo "🌐 Domain Setup:"
echo "  • Point karl.cam CNAME to: ${FRONTEND_URL#https://}"
echo "  • Configure custom domain: gcloud run domain-mappings create --service karlcam-frontend-v2 --domain karl.cam --region ${REGION}"