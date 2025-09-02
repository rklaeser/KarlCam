#!/bin/bash
# Deploy v2 API service to Cloud Run with karl.cam domain
set -e

# Get script directory for relative paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../../../.." && pwd)"

# Configuration
PROJECT_ID="${PROJECT_ID:-karlcam}"
REGION="${REGION:-us-central1}"
API_IMAGE_TAG="${API_IMAGE_TAG:-v2}"
BUCKET_NAME="${BUCKET_NAME:-karlcam-v2-data}"

echo "🚀 Deploying KarlCam V2 API Service"
echo "==================================="
echo "  • Project: ${PROJECT_ID}"
echo "  • Region: ${REGION}"
echo "  • Image Tag: ${API_IMAGE_TAG}"
echo "  • Bucket: ${BUCKET_NAME}"
echo "  • Domain: api.karl.cam"

# Set project
gcloud config set project ${PROJECT_ID}

# Get Cloud SQL connection details (shared instance)
DB_INSTANCE_NAME="karlcam-db"
CONNECTION_NAME=$(gcloud sql instances describe ${DB_INSTANCE_NAME} --format='value(connectionName)' 2>/dev/null || echo "")

if [ -z "$CONNECTION_NAME" ]; then
    echo "❌ Cloud SQL instance not found. Run init-v2.sh first."
    exit 1
fi

# Build and push API image using production Dockerfile
echo "📦 Building v2 API image..."
cd "${PROJECT_ROOT}"
docker build --platform linux/amd64 -f web/api/infra/Dockerfile.prod -t gcr.io/${PROJECT_ID}/karlcam-api:${API_IMAGE_TAG} .

echo "⬆️  Pushing v2 API image..."
docker push gcr.io/${PROJECT_ID}/karlcam-api:${API_IMAGE_TAG}

# Deploy v2 API service
echo "☁️  Deploying v2 API service to Cloud Run..."
gcloud run deploy karlcam-api-v2 \
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
  --set-secrets "DATABASE_URL=database-url-v2:latest"

# Get service URL
API_URL=$(gcloud run services describe karlcam-api-v2 --region ${REGION} --format 'value(status.url)')

echo ""
echo "✅ V2 API Service Deployed!"
echo "=========================="
echo "  • URL: ${API_URL}"
echo "  • Health: ${API_URL}/health"
echo "  • Test: curl ${API_URL}/api/public/cameras"
echo "  • Logs: gcloud run services logs read karlcam-api-v2 --region=${REGION}"
echo ""
echo "🌐 Domain Setup:"
echo "  • Point api.karl.cam CNAME to: ${API_URL#https://}"
echo "  • Configure custom domain: gcloud run domain-mappings create --service karlcam-api-v2 --domain api.karl.cam --region ${REGION}"