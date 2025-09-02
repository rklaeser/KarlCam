#!/bin/bash
# Deploy admin backend service to Cloud Run
set -e

# Get script directory for relative paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../../../.." && pwd)"

# Configuration
PROJECT_ID="${PROJECT_ID:-karlcam}"
REGION="${REGION:-us-central1}"
ADMIN_BACKEND_IMAGE_TAG="${ADMIN_BACKEND_IMAGE_TAG:-latest}"
BUCKET_NAME="${BUCKET_NAME:-karlcam-fog-data}"

echo "🔍 Deploying KarlCam Admin Backend"
echo "=================================="
echo "  • Project: ${PROJECT_ID}"
echo "  • Region: ${REGION}"
echo "  • Image Tag: ${ADMIN_BACKEND_IMAGE_TAG}"
echo "  • Bucket: ${BUCKET_NAME}"

# Set project
gcloud config set project ${PROJECT_ID}

# Get Cloud SQL connection details
DB_INSTANCE_NAME="karlcam-db"
CONNECTION_NAME=$(gcloud sql instances describe ${DB_INSTANCE_NAME} --format='value(connectionName)' 2>/dev/null || echo "")

if [ -z "$CONNECTION_NAME" ]; then
    echo "❌ Cloud SQL instance not found. Run init.sh first."
    exit 1
fi

# Build and push admin backend image using production Dockerfile
echo "📦 Building admin backend image..."
cd "${PROJECT_ROOT}"
docker build --platform linux/amd64 -f admin/backend/infra/Dockerfile.prod -t gcr.io/${PROJECT_ID}/karlcam-admin-backend:${ADMIN_BACKEND_IMAGE_TAG} .

echo "⬆️  Pushing admin backend image..."
docker push gcr.io/${PROJECT_ID}/karlcam-admin-backend:${ADMIN_BACKEND_IMAGE_TAG}

# Deploy admin backend service
echo "☁️  Deploying admin backend service to Cloud Run..."
gcloud run deploy karlcam-admin-backend \
  --image gcr.io/${PROJECT_ID}/karlcam-admin-backend:${ADMIN_BACKEND_IMAGE_TAG} \
  --region ${REGION} \
  --memory 1Gi \
  --cpu 1 \
  --timeout 60 \
  --concurrency 100 \
  --port 8001 \
  --allow-unauthenticated \
  --min-instances 0 \
  --max-instances 5 \
  --set-env-vars "BUCKET_NAME=${BUCKET_NAME},DATA_DIR=/app/data" \
  --add-cloudsql-instances ${CONNECTION_NAME} \
  --set-secrets "DATABASE_URL=database-url:latest"

# Get service URL
ADMIN_BACKEND_URL=$(gcloud run services describe karlcam-admin-backend --region ${REGION} --format 'value(status.url)')

echo ""
echo "✅ Admin Backend Deployed!"
echo "========================="
echo "  • URL: ${ADMIN_BACKEND_URL}"
echo "  • Health: ${ADMIN_BACKEND_URL}/api/health"
echo "  • API Docs: ${ADMIN_BACKEND_URL}/docs"
echo "  • Logs: gcloud run logs read karlcam-admin-backend --region=${REGION}"