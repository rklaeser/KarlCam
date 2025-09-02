#!/bin/bash
# Deploy API service to Cloud Run
set -e

# Get script directory for relative paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../../../.." && pwd)"

# Configuration
PROJECT_ID="${PROJECT_ID:-karlcam}"
REGION="${REGION:-us-central1}"
API_IMAGE_TAG="${API_IMAGE_TAG:-latest}"
BUCKET_NAME="${BUCKET_NAME:-karlcam-fog-data}"

echo "🚀 Deploying KarlCam API Service"
echo "================================="
echo "  • Project: ${PROJECT_ID}"
echo "  • Region: ${REGION}"
echo "  • Image Tag: ${API_IMAGE_TAG}"
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

# Build and push API image using production Dockerfile
echo "📦 Building API image..."
cd "${PROJECT_ROOT}"
docker build --platform linux/amd64 -f web/api/infra/Dockerfile.prod -t gcr.io/${PROJECT_ID}/karlcam-api:${API_IMAGE_TAG} .

echo "⬆️  Pushing API image..."
docker push gcr.io/${PROJECT_ID}/karlcam-api:${API_IMAGE_TAG}

# Deploy API service
echo "☁️  Deploying API service to Cloud Run..."
gcloud run deploy karlcam-api \
  --image gcr.io/${PROJECT_ID}/karlcam-api:${API_IMAGE_TAG} \
  --region ${REGION} \
  --memory 512Mi \
  --cpu 1 \
  --timeout 60 \
  --concurrency 100 \
  --port 8000 \
  --allow-unauthenticated \
  --min-instances 0 \
  --max-instances 10 \
  --set-env-vars "BUCKET_NAME=${BUCKET_NAME}" \
  --add-cloudsql-instances ${CONNECTION_NAME} \
  --set-secrets "DATABASE_URL=database-url:latest"

# Get service URL
API_URL=$(gcloud run services describe karlcam-api --region ${REGION} --format 'value(status.url)')

echo ""
echo "✅ API Service Deployed!"
echo "========================"
echo "  • URL: ${API_URL}"
echo "  • Health: ${API_URL}/health"
echo "  • Test: curl ${API_URL}/api/public/cameras"
echo "  • Logs: gcloud run logs read karlcam-api --region=${REGION}"