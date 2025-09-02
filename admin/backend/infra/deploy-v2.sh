#!/bin/bash
# Deploy v2 admin backend service to Cloud Run with karl.cam domain
set -e

# Get script directory for relative paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../../../.." && pwd)"

# Configuration
PROJECT_ID="${PROJECT_ID:-karlcam}"
REGION="${REGION:-us-central1}"
ADMIN_BACKEND_IMAGE_TAG="${ADMIN_BACKEND_IMAGE_TAG:-v2}"
BUCKET_NAME="${BUCKET_NAME:-karlcam-v2-data}"

echo "🔍 Deploying KarlCam V2 Admin Backend"
echo "====================================="
echo "  • Project: ${PROJECT_ID}"
echo "  • Region: ${REGION}"
echo "  • Image Tag: ${ADMIN_BACKEND_IMAGE_TAG}"
echo "  • Bucket: ${BUCKET_NAME}"
echo "  • Domain: admin-api.karl.cam"

# Set project
gcloud config set project ${PROJECT_ID}

# Get Cloud SQL connection details (shared instance)
DB_INSTANCE_NAME="karlcam-db"
CONNECTION_NAME=$(gcloud sql instances describe ${DB_INSTANCE_NAME} --format='value(connectionName)' 2>/dev/null || echo "")

if [ -z "$CONNECTION_NAME" ]; then
    echo "❌ Cloud SQL instance not found. Run init-v2.sh first."
    exit 1
fi

# Build and push admin backend image using production Dockerfile
echo "📦 Building v2 admin backend image..."
cd "${PROJECT_ROOT}"
docker build --platform linux/amd64 -f admin/backend/infra/Dockerfile.prod -t gcr.io/${PROJECT_ID}/karlcam-admin-backend:${ADMIN_BACKEND_IMAGE_TAG} .

echo "⬆️  Pushing v2 admin backend image..."
docker push gcr.io/${PROJECT_ID}/karlcam-admin-backend:${ADMIN_BACKEND_IMAGE_TAG}

# Deploy v2 admin backend service
echo "☁️  Deploying v2 admin backend service to Cloud Run..."
gcloud run deploy karlcam-admin-backend-v2 \
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
  --set-secrets "DATABASE_URL=database-url-v2:latest"

# Get service URL
ADMIN_BACKEND_URL=$(gcloud run services describe karlcam-admin-backend-v2 --region ${REGION} --format 'value(status.url)')

echo ""
echo "✅ V2 Admin Backend Deployed!"
echo "============================="
echo "  • URL: ${ADMIN_BACKEND_URL}"
echo "  • Health: ${ADMIN_BACKEND_URL}/api/health"
echo "  • API Docs: ${ADMIN_BACKEND_URL}/docs"
echo "  • Logs: gcloud run services logs read karlcam-admin-backend-v2 --region=${REGION}"
echo ""
echo "🌐 Domain Setup:"
echo "  • Point admin-api.karl.cam CNAME to: ${ADMIN_BACKEND_URL#https://}"
echo "  • Configure custom domain: gcloud run domain-mappings create --service karlcam-admin-backend-v2 --domain admin-api.karl.cam --region ${REGION}"