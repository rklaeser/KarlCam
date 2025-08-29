#!/bin/bash
# Deploy review backend service to Cloud Run
set -e

# Configuration
PROJECT_ID="${PROJECT_ID:-karlcam}"
REGION="${REGION:-us-central1}"
REVIEW_BACKEND_IMAGE_TAG="${REVIEW_BACKEND_IMAGE_TAG:-latest}"
BUCKET_NAME="${BUCKET_NAME:-karlcam-fog-data}"

echo "🔍 Deploying KarlCam Review Backend"
echo "===================================="

# Set project
gcloud config set project ${PROJECT_ID}

# Get Cloud SQL connection details
DB_INSTANCE_NAME="karlcam-db"
CONNECTION_NAME=$(gcloud sql instances describe ${DB_INSTANCE_NAME} --format='value(connectionName)' 2>/dev/null || echo "")

if [ -z "$CONNECTION_NAME" ]; then
    echo "❌ Cloud SQL instance not found. Run deploy-infrastructure.sh first."
    exit 1
fi

# Build and push review backend image
echo "📦 Building review backend image..."
cd /Users/reed/Code/Homelab/KarlCam
docker build --platform linux/amd64 -f cloudrun/docker/Dockerfile.review-backend -t gcr.io/${PROJECT_ID}/karlcam-review-backend:${REVIEW_BACKEND_IMAGE_TAG} .

echo "⬆️  Pushing review backend image..."
docker push gcr.io/${PROJECT_ID}/karlcam-review-backend:${REVIEW_BACKEND_IMAGE_TAG}

# Deploy review backend service
echo "☁️  Deploying review backend service to Cloud Run..."
gcloud run deploy karlcam-review-backend \
  --image gcr.io/${PROJECT_ID}/karlcam-review-backend:${REVIEW_BACKEND_IMAGE_TAG} \
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
REVIEW_BACKEND_URL=$(gcloud run services describe karlcam-review-backend --region ${REGION} --format 'value(status.url)')

echo ""
echo "✅ Review Backend Deployed!"
echo "==========================="
echo "  • URL: ${REVIEW_BACKEND_URL}"
echo "  • Health: ${REVIEW_BACKEND_URL}/api/health"
echo "  • API Docs: ${REVIEW_BACKEND_URL}/docs"
echo "  • Logs: gcloud run logs read karlcam-review-backend --region=${REGION}"