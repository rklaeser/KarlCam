#!/bin/bash
# Deploy admin frontend service to Cloud Run
set -e

# Get script directory for relative paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../../../.." && pwd)"

# Configuration
PROJECT_ID="${PROJECT_ID:-karlcam}"
REGION="${REGION:-us-central1}"
ADMIN_FRONTEND_IMAGE_TAG="${ADMIN_FRONTEND_IMAGE_TAG:-latest}"

echo "🎨 Deploying KarlCam Admin Frontend"
echo "===================================="
echo "  • Project: ${PROJECT_ID}"
echo "  • Region: ${REGION}"
echo "  • Image Tag: ${ADMIN_FRONTEND_IMAGE_TAG}"

# Set project
gcloud config set project ${PROJECT_ID}

# Get admin backend URL (if deployed)
ADMIN_BACKEND_URL=$(gcloud run services describe karlcam-admin-backend --region ${REGION} --format 'value(status.url)' 2>/dev/null || echo "")

if [ -z "$ADMIN_BACKEND_URL" ]; then
    echo "⚠️  Admin backend not found. Using default backend URL."
    ADMIN_BACKEND_URL="http://localhost:8001"
fi

# Build and push admin frontend image using production Dockerfile
echo "📦 Building admin frontend image..."
cd "${PROJECT_ROOT}"
docker build --platform linux/amd64 \
  --build-arg REACT_APP_API_URL="${ADMIN_BACKEND_URL}" \
  -f admin/frontend/infra/Dockerfile.prod \
  -t gcr.io/${PROJECT_ID}/karlcam-admin-frontend:${ADMIN_FRONTEND_IMAGE_TAG} .

echo "⬆️  Pushing admin frontend image..."
docker push gcr.io/${PROJECT_ID}/karlcam-admin-frontend:${ADMIN_FRONTEND_IMAGE_TAG}

# Deploy admin frontend service
echo "☁️  Deploying admin frontend service to Cloud Run..."
gcloud run deploy karlcam-admin-frontend \
  --image gcr.io/${PROJECT_ID}/karlcam-admin-frontend:${ADMIN_FRONTEND_IMAGE_TAG} \
  --region ${REGION} \
  --memory 256Mi \
  --cpu 1 \
  --timeout 30 \
  --concurrency 100 \
  --port 8080 \
  --allow-unauthenticated \
  --min-instances 0 \
  --max-instances 5 \
  --set-env-vars "BACKEND_URL=${ADMIN_BACKEND_URL}"

# Get frontend URL
ADMIN_FRONTEND_URL=$(gcloud run services describe karlcam-admin-frontend --region ${REGION} --format 'value(status.url)')

echo ""
echo "✅ Admin Frontend Deployed!"
echo "==========================="
echo "  • URL: ${ADMIN_FRONTEND_URL}"
echo "  • Backend: ${ADMIN_BACKEND_URL}"
echo "  • Logs: gcloud run logs read karlcam-admin-frontend --region=${REGION}"
echo ""
echo "📝 Note: The admin frontend is for labeling and reviewing fog detection data."